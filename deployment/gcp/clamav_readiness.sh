#!/bin/sh
# Read-only check; mount the signature directory read-only for external use.
set -eu
set -f
export LC_ALL=C
database_dir=${CLAMAV_DATABASE_DIR:-/var/lib/clamav}
max_age=${CLAMD_SIGNATURE_MAX_AGE_SECONDS:-172800}
case "$max_age" in ''|0*|*[!0-9]*) echo 'degraded: invalid policy'; exit 1;; esac
if [ "${#max_age}" -gt 6 ]; then echo 'degraded: invalid policy'; exit 1; fi
if [ "$max_age" -lt 3600 ] || [ "$max_age" -gt 604800 ]; then
    echo 'degraded: invalid policy'; exit 1
fi
if [ -f "$database_dir/daily.cld" ] && [ ! -e "$database_dir/daily.cvd" ]; then
    database=$database_dir/daily.cld
elif [ -f "$database_dir/daily.cvd" ] && [ ! -e "$database_dir/daily.cld" ]; then
    database=$database_dir/daily.cvd
else
    echo 'degraded: database unavailable'; exit 1
fi
stat1=$(stat -c '%d:%i:%s:%Y:%Z' "$database" 2>/dev/null) || { echo 'degraded: database unavailable'; exit 1; }
size1=$(dd if="$database" bs=512 count=1 2>/dev/null | wc -c)
header1=$(dd if="$database" bs=512 count=1 2>/dev/null) || { echo 'degraded: database unavailable'; exit 1; }
version1=$(timeout 5 sh -c "printf 'VERSION\\n' | timeout 4 nc -w 3 localhost 3310 2>/dev/null | head -c 257") || { echo 'degraded: scanner unavailable'; exit 1; }
size2=$(dd if="$database" bs=512 count=1 2>/dev/null | wc -c)
header2=$(dd if="$database" bs=512 count=1 2>/dev/null) || { echo 'degraded: update in progress'; exit 1; }
version2=$(timeout 5 sh -c "printf 'VERSION\\n' | timeout 4 nc -w 3 localhost 3310 2>/dev/null | head -c 257") || { echo 'degraded: scanner unavailable'; exit 1; }
stat2=$(stat -c '%d:%i:%s:%Y:%Z' "$database" 2>/dev/null) || { echo 'degraded: update in progress'; exit 1; }
if [ "$database" = "$database_dir/daily.cld" ]; then other=$database_dir/daily.cvd; else other=$database_dir/daily.cld; fi
if [ -e "$other" ] || [ "$stat1" != "$stat2" ] || [ "$header1" != "$header2" ] || [ "$version1" != "$version2" ]; then
    echo 'degraded: update in progress'; exit 1
fi
if [ -z "$version1" ] || [ "${#version1}" -gt 256 ]; then echo 'degraded: scanner unavailable'; exit 1; fi
if [ "$size1" -ne 512 ] || [ "$size2" -ne 512 ]; then echo 'degraded: invalid database header'; exit 1; fi
fields=$(printf '%s\n' "$header1" | awk -F: '$1 == "ClamAV-VDB" && NF == 9 {print $3 " " $9}')
set -- $fields
if [ "$#" -ne 2 ]; then echo 'degraded: invalid database header'; exit 1; fi
disk_version=$1
built_at=$(printf '%s' "$2" | tr -d ' ')
case "$disk_version:$built_at" in *[!0-9:]*|:*|*:) echo 'degraded: invalid database header'; exit 1;; esac
case "$built_at" in 0*) echo 'degraded: invalid database header'; exit 1;; esac
if [ "${#disk_version}" -gt 12 ] || [ "${#built_at}" -gt 10 ]; then echo 'degraded: invalid database header'; exit 1; fi
valid_version=$(printf '%s\n' "$version1" | awk '/^ClamAV [A-Za-z0-9.+_-]+\/[0-9]+\/(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) [ 0-9][0-9] [0-9][0-9]:[0-9][0-9]:[0-9][0-9] [0-9][0-9][0-9][0-9]$/ {print "yes"}')
if [ "$valid_version" != yes ]; then echo 'degraded: invalid scanner version'; exit 1; fi
loaded_version=$(printf '%s\n' "$version1" | cut -d/ -f2)
case "$loaded_version" in ''|*[!0-9]*) echo 'degraded: invalid scanner version'; exit 1;; esac
if [ "$loaded_version" != "$disk_version" ]; then echo 'degraded: version mismatch'; exit 1; fi
now=$(date -u +%s)
case "$now" in ''|0*|*[!0-9]*) echo 'degraded: invalid clock'; exit 1;; esac
if [ "${#now}" -gt 10 ]; then echo 'degraded: invalid clock'; exit 1; fi
if [ "$built_at" -gt "$((now + 300))" ] || [ "$built_at" -lt "$((now - max_age))" ]; then
    echo 'degraded: signature age'; exit 1
fi
echo 'healthy: signatures current'
