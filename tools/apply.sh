#!/bin/bash
# Applies the Brisa3DS changes on top of an Azahar source tree.
# Usage: tools/apply.sh /path/to/azahar
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="$(cd "${1:?usage: apply.sh /path/to/azahar [abi]}" && pwd)"
ABI="${2:-arm64-v8a}"

if [ ! -f "$TARGET/src/android/app/build.gradle.kts" ]; then
    echo "error: $TARGET does not look like an Azahar source tree" >&2
    exit 1
fi

cd "$TARGET"

for p in "$HERE"/patches/*.patch; do
    echo "== checking $(basename "$p")"
    if ! patch -p1 --dry-run < "$p" > /dev/null; then
        echo "error: $(basename "$p") no longer applies to this Azahar version." >&2
        echo "Upstream changed the files it touches. Build with upstream_ref set to an older" >&2
        echo "commit or tag, or send this log to get the patch updated." >&2
        exit 1
    fi
    patch -p1 < "$p"
done

cp -r "$HERE"/overlay/. .
python3 "$HERE"/tools/rename.py "$TARGET"
python3 "$HERE"/tools/fix_default_ini.py "$TARGET"
python3 "$HERE"/tools/rebrand_links.py "$TARGET"
python3 "$HERE"/tools/add_home_entry.py "$TARGET"
if [[ "$ABI" == *armeabi-v7a* ]]; then
    python3 "$HERE"/tools/fix_32bit.py "$TARGET"
fi
echo "== Brisa3DS changes applied"
