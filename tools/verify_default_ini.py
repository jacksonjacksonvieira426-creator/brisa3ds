#!/usr/bin/env python3
"""Checks that every setting key of the Android build is declared in default_ini.h.

This is the same check the app does at startup (and aborts on), done at build time. Run it on a
tree after apply.sh. Exit status 1 lists the keys that would crash the app.
"""
import re
import sys
from pathlib import Path


def main(root: str) -> int:
    base = Path(root)
    cmake = (base / "CMakeModules" / "GenerateSettingKeys.cmake").read_text(encoding="utf-8")
    ini = (base / "src/android/app/src/main/jni/default_ini.h").read_text(encoding="utf-8")

    qt = cmake.index("if (ENABLE_QT)")
    android = cmake.index("# Android exclusive setting keys")
    libretro = cmake.index("# Libretro exclusive setting keys")
    keys = []
    for match in re.finditer(r"foreach\(KEY IN ITEMS(.*?)\n\s*\)", cmake, re.S):
        if match.start() < qt or android < match.start() < libretro:
            body = re.sub(r"#[^\n]*", "", match.group(1))
            keys += re.findall(r'"([A-Za-z0-9_]+)"', body)

    declared = set(re.findall(r"DECLARE_KEY\((\w+)\)", ini))
    omitted_block = ini.split("android_config_omitted_keys = {", 1)[1].split("};", 1)[0]
    omitted = set(re.findall(r"Settings::Keys::(\w+)", omitted_block))
    missing = [k for k in dict.fromkeys(keys) if k not in declared and k not in omitted]

    if missing:
        print(f"FAIL: {len(missing)} keys would abort the app at startup: {', '.join(missing)}")
        return 1
    print(f"OK: all {len(set(keys))} Android setting keys are declared or omitted")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
