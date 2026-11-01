#!/usr/bin/env python3
"""Points the app's own links and its update checker at this project instead of Azahar.

Needs the project address as owner/name, from the BRISA_REPO environment variable (the workflow
sets it from the repository it runs in). Without it nothing is changed, so local test runs still
work, and a message says so.

Links to Azahar's wiki, blog and contributors page are kept on purpose: they are documentation and
credit for work this project is built on.
"""
import os
import re
import sys
from pathlib import Path

LINK_KEYS = {
    "support_link": "{base}/issues",
    "website_link": "{base}",
    "github_link": "{base}",
    "stable_channel_update_link": "{base}/releases",
    "prerelease_channel_update_link": "{base}/releases",
}
OLD_UPDATE_PATH = '"/repos/azahar-emu/azahar"'

# The "Discord" button on the About screen opened Azahar's Discord server. It now opens this
# project's issues page, so it gets a help icon (Material "help outline") in place of the logo.
HELP_ICON = """<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:fillColor="#FF000000"
        android:pathData="M11,18h2v-2h-2v2zM12,2C6.48,2 2,6.48 2,12s4.48,10 10,10 10,-4.48 10,-10S17.52,2 12,2zM12,20c-4.41,0 -8,-3.59 -8,-8s3.59,-8 8,-8 8,3.59 8,8 -3.59,8 -8,8zM12,6c-2.21,0 -4,1.79 -4,4h2c0,-1.1 0.9,-2 2,-2s2,0.9 2,2c0,2 -3,1.75 -3,5h2c0,-2.25 3,-2.5 3,-5 0,-2.21 -1.79,-4 -4,-4z" />
</vector>
"""


def main(root: str) -> None:
    repo = os.environ.get("BRISA_REPO", "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        print("== rebrand_links.py: BRISA_REPO is not set (owner/name), links left as they are")
        return

    base = f"https://github.com/{repo}"
    app = Path(root) / "src" / "android" / "app" / "src" / "main"

    strings_path = app / "res" / "values" / "strings.xml"
    text = strings_path.read_text(encoding="utf-8")
    changed = 0
    for key, template in LINK_KEYS.items():
        pattern = re.compile(rf'(<string name="{key}"[^>]*>)[^<]*(</string>)')
        text, count = pattern.subn(lambda m: m.group(1) + template.format(base=base) + m.group(2), text)
        if count != 1:
            sys.exit(f"rebrand_links.py: expected one '{key}' string, found {count}")
        changed += count
    strings_path.write_text(text, encoding="utf-8")

    checker = app / "java" / "org" / "citra" / "citra_emu" / "features" / "updatechecker" / "UpdateChecker.kt"
    code = checker.read_text(encoding="utf-8")
    if OLD_UPDATE_PATH not in code:
        sys.exit("rebrand_links.py: update checker path not found, upstream layout changed")
    checker.write_text(code.replace(OLD_UPDATE_PATH, f'"/repos/{repo}"', 1), encoding="utf-8")

    icon = app / "res" / "drawable" / "ic_discord.xml"
    if not icon.exists():
        sys.exit("rebrand_links.py: ic_discord.xml not found, upstream layout changed")
    icon.write_text(HELP_ICON, encoding="utf-8")

    print(f"== links and update checker now point to {base} ({changed} links)")


if __name__ == "__main__":
    main(sys.argv[1])
