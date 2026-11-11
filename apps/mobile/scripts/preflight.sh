#!/bin/sh
set -u
printf 'Java:\n'
java -version 2>&1
printf '\nAndroid SDK: %s\n' "${ANDROID_SDK_ROOT:-not configured}"
printf '\niOS toolchain:\n'
xcodebuild -version 2>&1
xcrun simctl list devices booted 2>&1
