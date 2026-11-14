#!/bin/bash
set -euo pipefail

# Validate the host before Gradle can replace generated sources or framework outputs.
python3 "$SRCROOT/verify_build_identity.py" preflight
if [[ "$REDHOUSE_VARIANT" == lab ]]; then
  mkdir -p "$TARGET_BUILD_DIR/$UNLOCALIZED_RESOURCES_FOLDER_PATH"
  cp "$REDHOUSE_LAB_CA_DER" "$TARGET_BUILD_DIR/$UNLOCALIZED_RESOURCES_FOLDER_PATH/redhouse-lab-ca.der"
fi
mobile_root="$(cd "$SRCROOT/.." && pwd)"
variant="$REDHOUSE_VARIANT"
cd "$mobile_root"
./gradlew :composeApp:embedAndSignAppleFrameworkForXcode \
  --console=plain --no-build-cache \
  --project-cache-dir "$mobile_root/composeApp/build/ios-$variant/gradle-state" \
  "-PmobileIosVariant=$variant" "-PmobileGateway=$REDHOUSE_GATEWAY" \
  2>&1 | tee "$TARGET_TEMP_DIR/shared-framework.log"
python3 "$SRCROOT/verify_build_identity.py" framework
