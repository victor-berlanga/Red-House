"""Validate Xcode/Gradle variant identity without reading application credentials.

The framework phase records build provenance; it does not certify signing,
installation, TLS or physical capabilities. The artifact phase is run separately
against the finished .app, before any installation.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
from urllib.parse import urlsplit

NORMAL_BUNDLE = "org.redhouse.mobile"
NORMAL_GATEWAY = "https://34.18.186.116"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def identity(environment):
    variant = environment.get("REDHOUSE_VARIANT")
    require(variant in {"normal", "lab"}, "Unknown iOS variant")
    bundle = NORMAL_BUNDLE + (".lab" if variant == "lab" else "")
    require(environment.get("PRODUCT_BUNDLE_IDENTIFIER") == bundle, "Bundle/variant mismatch")
    configuration = environment.get("CONFIGURATION")
    require(configuration in ({"DebugLab"} if variant == "lab" else {"Debug", "Release"}),
            "Configuration/variant mismatch")
    if variant == "lab":
        require(environment.get("ACTION", "build") == "build", "Lab archive/install action rejected")
        require(environment.get("KOTLIN_FRAMEWORK_BUILD_TYPE") == "Debug", "Lab framework must be Debug")
    gateway = environment.get("REDHOUSE_GATEWAY", "")
    require(gateway.isascii() and not any(c.isspace() for c in gateway), "Invalid gateway")
    parsed = urlsplit(gateway)
    require(parsed.scheme == "https" and parsed.hostname and not parsed.username and
            not parsed.password and not parsed.query and not parsed.fragment and not parsed.path,
            "Gateway must be an exact HTTPS origin, without a trailing slash")
    require(parsed.port is None or 1 <= parsed.port <= 65535, "Invalid gateway port")
    normal = urlsplit(NORMAL_GATEWAY)
    same_origin = (parsed.scheme.lower(), parsed.hostname.rstrip(".").lower(), parsed.port or 443) == (
        normal.scheme, normal.hostname.rstrip(".").lower(), normal.port or 443)
    require((gateway == NORMAL_GATEWAY) if variant == "normal" else not same_origin,
            "Gateway/variant mismatch")
    ca_hash = ""
    if variant == "lab":
        ca = Path(environment.get("REDHOUSE_LAB_CA_DER", ""))
        require(ca.is_file() and 0 < ca.stat().st_size <= 65536, "Lab CA missing or invalid")
        ca_hash = environment.get("REDHOUSE_LAB_CA_SHA256", "")
        require(bool(re.fullmatch(r"[0-9a-f]{64}", ca_hash)) and sha256(ca) == ca_hash,
                "Lab CA fingerprint mismatch")
    return {"variant": variant, "bundle_identifier": bundle, "gateway": gateway,
            "background_task": bundle + ".observations", "configuration": configuration,
            "ca_sha256": ca_hash, "tls": "lab_pinned_ca" if variant == "lab" else "system_default_only"}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def framework_manifest(environment):
    result = identity(environment)
    source_root = Path(environment["SRCROOT"]).resolve()
    sdk = environment["SDK_NAME"]
    require(bool(re.fullmatch(r"iphone(?:os|simulator)[0-9.]*", sdk)), "Unexpected iOS SDK")
    output = source_root.parent / "composeApp" / "build" / ("ios-" + result["variant"])
    generated = output / "generated/mobileEnvironment/MobileEnvironment.kt"
    source = generated.read_text()
    constants = dict(re.findall(r'const val (\w+) = "([^"\n]*)"', source))
    for key, value in {"gateway": result["gateway"], "iosVariant": result["variant"],
                       "iosBundleIdentifier": result["bundle_identifier"],
                       "iosBackgroundTask": result["background_task"]}.items():
        require(constants.get(key) == value, "Generated environment mismatch: " + key)
    framework = output / "xcode-frameworks" / result["configuration"] / sdk / "RedHouse.framework/RedHouse"
    require(framework.is_file(), "Variant framework is missing")
    result.update(framework_sha256=sha256(framework), generated_environment_sha256=sha256(generated),
                  sdk=sdk, state="PREPARED_NOT_INSTALLED_NOT_PHYSICALLY_VERIFIED")
    (Path(environment["TARGET_TEMP_DIR"]) / "ios-framework-manifest.json").write_text(
        json.dumps(result, indent=2) + "\n")
    return result


def verify_artifact(app, manifest):
    result = json.loads(manifest.read_text())
    require(result.get("variant") in {"normal", "lab"}, "Manifest variant missing")
    expected_bundle = NORMAL_BUNDLE + (".lab" if result["variant"] == "lab" else "")
    require(result.get("bundle_identifier") == expected_bundle, "Manifest bundle mismatch")
    ca = app / "redhouse-lab-ca.der"
    if result["variant"] == "lab":
        require(result.get("tls") == "lab_pinned_ca" and ca.is_file() and
                sha256(ca) == result.get("ca_sha256"), "Lab CA missing or mismatched")
    else:
        require(result.get("ca_sha256") == "" and result.get("tls") == "system_default_only" and
                not ca.exists(), "Normal artifact contains lab trust")
    with (app / "Info.plist").open("rb") as file:
        info = plistlib.load(file)
    for field, expected in {"CFBundleIdentifier": expected_bundle, "RedHouseVariant": result["variant"],
                            "RedHouseGateway": result["gateway"], "RedHouseLabCASHA256": result["ca_sha256"],
                            "BGTaskSchedulerPermittedIdentifiers": [expected_bundle + ".observations"]}.items():
        require(info.get(field) == expected, "Artifact identity mismatch: " + field)
    executable = info.get("CFBundleExecutable", "")
    require(executable and Path(executable).name == executable, "Invalid executable name")
    require((app / executable).is_file(), "Application executable is missing")
    result["executable_sha256"] = sha256(app / executable)
    result["info_plist_sha256"] = sha256(app / "Info.plist")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("preflight", "framework", "artifact"))
    parser.add_argument("--app", type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    if args.phase == "preflight":
        identity(os.environ)
    elif args.phase == "framework":
        framework_manifest(os.environ)
    else:
        require(args.app is not None and args.manifest is not None, "App and manifest are required")
        print(json.dumps(verify_artifact(args.app, args.manifest), indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError) as error:
        raise SystemExit("iOS build identity rejected: " + str(error)) from None
