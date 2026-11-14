"""Pure checks: no Gradle, Xcode, services, devices or real credentials."""
import importlib.util
import hashlib
import json
from pathlib import Path
import plistlib
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("ios_identity", Path(__file__).parents[1] / "iosApp/verify_build_identity.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BuildIdentityTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.ca = Path(self.directory.name) / "ca.der"
        self.ca.write_bytes(b"synthetic-test-ca")

    def normal(self):
        return dict(REDHOUSE_VARIANT="normal", PRODUCT_BUNDLE_IDENTIFIER="org.redhouse.mobile",
                    CONFIGURATION="Debug", REDHOUSE_GATEWAY="https://34.18.186.116")

    def lab(self):
        return dict(REDHOUSE_VARIANT="lab", PRODUCT_BUNDLE_IDENTIFIER="org.redhouse.mobile.lab",
                    CONFIGURATION="DebugLab", REDHOUSE_GATEWAY="https://192.0.2.10:8443",
                    KOTLIN_FRAMEWORK_BUILD_TYPE="Debug", REDHOUSE_LAB_CA_DER=str(self.ca),
                    REDHOUSE_LAB_CA_SHA256=hashlib.sha256(self.ca.read_bytes()).hexdigest())

    def test_normal_namespace_remains_exact(self):
        result = MODULE.identity(self.normal())
        self.assertEqual(result["bundle_identifier"], "org.redhouse.mobile")
        self.assertEqual(result["background_task"], "org.redhouse.mobile.observations")
        self.assertEqual(result["ca_sha256"], "")

    def test_local_network_description_is_lab_only(self):
        root = Path(__file__).parents[1] / "iosApp"
        normal = plistlib.loads((root / "Info.plist").read_bytes())
        lab = plistlib.loads((root / "InfoLab.plist").read_bytes())
        self.assertTrue(lab.pop("NSLocalNetworkUsageDescription"))
        self.assertNotIn("NSLocalNetworkUsageDescription", normal)
        self.assertEqual(normal, lab)

    def test_lab_is_separate_and_default_tls_only(self):
        result = MODULE.identity(self.lab())
        self.assertEqual(result["background_task"], "org.redhouse.mobile.lab.observations")
        self.assertEqual(result["tls"], "lab_pinned_ca")

    def test_mismatched_hosts_fail_before_build(self):
        cases = [dict(PRODUCT_BUNDLE_IDENTIFIER="org.redhouse.mobile"), dict(CONFIGURATION="Release"),
                 dict(REDHOUSE_GATEWAY="https://34.18.186.116"), dict(ACTION="install"),
                 dict(REDHOUSE_GATEWAY="https://34.18.186.116:443"),
                 dict(REDHOUSE_GATEWAY="https://34.18.186.116/"),
                 dict(REDHOUSE_GATEWAY="https://34.18.186.116.:443"),
                 dict(KOTLIN_FRAMEWORK_BUILD_TYPE="Release"), dict(REDHOUSE_GATEWAY="http://192.0.2.10"),
                 dict(REDHOUSE_GATEWAY="https://user:secret@192.0.2.10"), dict(REDHOUSE_GATEWAY=""),
                 dict(REDHOUSE_LAB_CA_SHA256="0" * 64), dict(REDHOUSE_LAB_CA_DER="/missing")]
        for changes in cases:
            with self.subTest(changes=tuple(changes)):
                with self.assertRaises(ValueError):
                    MODULE.identity(self.lab() | changes)
        with self.assertRaises(ValueError):
            MODULE.identity(self.normal() | dict(REDHOUSE_GATEWAY="https://192.0.2.10"))

    def test_framework_identity_and_hash_are_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ios = root / "iosApp"; ios.mkdir()
            output = root / "composeApp/build/ios-lab"
            source = output / "generated/mobileEnvironment/MobileEnvironment.kt"
            source.parent.mkdir(parents=True)
            source.write_text('const val gateway = "https://192.0.2.10:8443"\n'
                              'const val iosVariant = "lab"\n'
                              'const val iosBundleIdentifier = "org.redhouse.mobile.lab"\n'
                              'const val iosBackgroundTask = "org.redhouse.mobile.lab.observations"\n')
            binary = output / "xcode-frameworks/DebugLab/iphoneos/RedHouse.framework/RedHouse"
            binary.parent.mkdir(parents=True); binary.write_bytes(b"synthetic-framework")
            env = self.lab() | dict(SRCROOT=str(ios), SDK_NAME="iphoneos", TARGET_TEMP_DIR=directory)
            result = MODULE.framework_manifest(env)
            self.assertEqual(result["framework_sha256"], MODULE.sha256(binary))
            source.write_text(source.read_text().replace('iosVariant = "lab"', 'iosVariant = "normal"'))
            with self.assertRaises(ValueError):
                MODULE.framework_manifest(env)

    def test_artifact_wrong_bundle_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps(MODULE.identity(self.lab())))
            app = root / "RedHouseLab.app"; app.mkdir()
            info = dict(CFBundleIdentifier="org.redhouse.mobile", CFBundleExecutable="RedHouseLab",
                        RedHouseVariant="lab", RedHouseGateway="https://192.0.2.10:8443",
                        RedHouseLabCASHA256=MODULE.identity(self.lab())["ca_sha256"],
                        BGTaskSchedulerPermittedIdentifiers=["org.redhouse.mobile.lab.observations"])
            with (app / "Info.plist").open("wb") as file:
                plistlib.dump(info, file)
            (app / "RedHouseLab").write_bytes(b"synthetic-app")
            (app / "redhouse-lab-ca.der").write_bytes(self.ca.read_bytes())
            with self.assertRaises(ValueError):
                MODULE.verify_artifact(app, manifest)
            info["CFBundleIdentifier"] = "org.redhouse.mobile.lab"
            with (app / "Info.plist").open("wb") as file:
                plistlib.dump(info, file)
            self.assertEqual(MODULE.verify_artifact(app, manifest)["executable_sha256"],
                             MODULE.sha256(app / "RedHouseLab"))
            (app / "redhouse-lab-ca.der").write_bytes(b"different-ca")
            with self.assertRaises(ValueError):
                MODULE.verify_artifact(app, manifest)

    def test_normal_artifact_rejects_lab_ca(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps(MODULE.identity(self.normal())))
            app = root / "RedHouse.app"; app.mkdir()
            info = dict(CFBundleIdentifier="org.redhouse.mobile", CFBundleExecutable="RedHouse",
                        RedHouseVariant="normal", RedHouseGateway="https://34.18.186.116",
                        RedHouseLabCASHA256="",
                        BGTaskSchedulerPermittedIdentifiers=["org.redhouse.mobile.observations"])
            with (app / "Info.plist").open("wb") as file:
                plistlib.dump(info, file)
            (app / "RedHouse").write_bytes(b"synthetic-app")
            (app / "redhouse-lab-ca.der").write_bytes(self.ca.read_bytes())
            with self.assertRaises(ValueError):
                MODULE.verify_artifact(app, manifest)


if __name__ == "__main__":
    unittest.main()
