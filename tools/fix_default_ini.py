#!/usr/bin/env python3
"""Fixes a startup crash caused by Azahar's own Android default config.

At startup the Android app checks that every setting key is declared in jni/default_ini.h (or
listed as omitted). When a key is added upstream without being declared there, the app aborts
right after the user picks the data folder with "Missing declaration for key '...'".

This script finds the keys that are missing and adds them to the omitted list, which makes the
check pass while the settings keep their built-in defaults. It does nothing when no key is
missing, so it is safe to run on versions where upstream already fixed the problem.
"""
import re
import sys
from pathlib import Path


def key_blocks(cmake_text: str):
    """Yields (position, keys) for every `foreach(KEY IN ITEMS ...)` block."""
    for match in re.finditer(r"foreach\(KEY IN ITEMS(.*?)\n\s*\)", cmake_text, re.S):
        body = re.sub(r"#[^\n]*", "", match.group(1))
        yield match.start(), re.findall(r'"([A-Za-z0-9_]+)"', body)


def main(root: str) -> None:
    root_path = Path(root)
    cmake_path = root_path / "CMakeModules" / "GenerateSettingKeys.cmake"
    ini_path = root_path / "src" / "android" / "app" / "src" / "main" / "jni" / "default_ini.h"

    cmake_text = cmake_path.read_text(encoding="utf-8")
    ini_text = ini_path.read_text(encoding="utf-8")

    qt_start = cmake_text.index("if (ENABLE_QT)")
    android_start = cmake_text.index("# Android exclusive setting keys")
    libretro_start = cmake_text.index("# Libretro exclusive setting keys")

    # Keys that exist in an Android build: the shared group and the Android-only group.
    android_keys = []
    for position, keys in key_blocks(cmake_text):
        if position < qt_start or android_start < position < libretro_start:
            android_keys.extend(keys)
    if not android_keys:
        sys.exit("fix_default_ini.py: could not read the key list, upstream layout changed")

    declared = set(re.findall(r"DECLARE_KEY\((\w+)\)", ini_text))
    marker = "android_config_omitted_keys = {\n"
    if marker not in ini_text:
        sys.exit("fix_default_ini.py: omitted keys list not found, upstream layout changed")
    omitted_block = ini_text.split(marker, 1)[1].split("};", 1)[0]
    omitted = set(re.findall(r"Settings::Keys::(\w+)", omitted_block))

    missing = [k for k in dict.fromkeys(android_keys) if k not in declared and k not in omitted]
    if not missing:
        print("== default_ini.h is already complete, nothing to fix")
        return

    if len(missing) > 10:
        sys.exit(f"fix_default_ini.py: {len(missing)} keys look missing, upstream layout changed")

    lines = "".join(f"    Settings::Keys::{k}, // added by Brisa3DS: missing upstream\n" for k in missing)
    ini_path.write_text(ini_text.replace(marker, marker + lines, 1), encoding="utf-8")
    print(f"== default_ini.h fixed, keys added to the omitted list: {', '.join(missing)}")


if __name__ == "__main__":
    main(sys.argv[1])
