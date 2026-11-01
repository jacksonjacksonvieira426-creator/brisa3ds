#!/usr/bin/env python3
"""Adds the "Performance profile" entry to the app's home settings list."""
import sys
from pathlib import Path

ENTRY = '''            HomeSetting(
                R.string.brisa_profile_title,
                R.string.brisa_profile_description,
                R.drawable.ic_stats,
                { DeviceProfile.showProfileDialog(mainActivity) }
            ),
'''
ANCHOR = '''            HomeSetting(
                R.string.share_log,'''
IMPORT_ANCHOR = "import org.citra.citra_emu.utils.GameHelper\n"


def main(root: str) -> None:
    path = (
        Path(root) / "src/android/app/src/main/java/org/citra/citra_emu/fragments/HomeSettingsFragment.kt"
    )
    text = path.read_text(encoding="utf-8")
    if text.count(ANCHOR) != 1 or IMPORT_ANCHOR not in text:
        sys.exit("add_home_entry.py: home settings list not found, upstream layout changed")
    text = text.replace(ANCHOR, ENTRY + ANCHOR, 1)
    text = text.replace(
        IMPORT_ANCHOR, "import org.citra.citra_emu.utils.DeviceProfile\n" + IMPORT_ANCHOR, 1
    )
    path.write_text(text, encoding="utf-8")
    print("== home settings: performance profile entry added")


if __name__ == "__main__":
    main(sys.argv[1])
