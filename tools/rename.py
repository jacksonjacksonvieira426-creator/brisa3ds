#!/usr/bin/env python3
"""Rebrands the Android app from Azahar to Brisa3DS inside an Azahar source tree.

Only user-visible text and the application id are changed. The Kotlin package names, the
license files and the credits to Azahar/Citra are left alone on purpose.
"""
import glob
import os
import sys

NEW_NAME = "Brisa3DS"
NEW_APP_ID = "app.brisa3ds.emu"
OLD_APP_ID = "org.azahar_emu.azahar"

# Lines that must keep mentioning Azahar: credits, the data-migration text, and technical ids.
KEEP_MARKERS = (
    'name="contributors_description"',
    'name="licenses_description"',
    'name="select_which_user_directory_to_use"',
    'name="keep_current_azahar_directory"',
    'name="app_notification_channel_id"',
)


def main(root: str) -> None:
    app = os.path.join(root, "src", "android", "app")

    gradle = os.path.join(app, "build.gradle.kts")
    text = open(gradle, encoding="utf-8").read()
    old = f'applicationId = "{OLD_APP_ID}"'
    if old not in text:
        sys.exit("rename.py: applicationId line not found in build.gradle.kts")
    text = text.replace(old, f'applicationId = "{NEW_APP_ID}"', 1)
    open(gradle, "w", encoding="utf-8").write(text)

    changed = 0
    for path in glob.glob(os.path.join(app, "src", "main", "res", "values*", "strings.xml")):
        lines = open(path, encoding="utf-8").read().split("\n")
        out = []
        for line in lines:
            if "Azahar" in line and not any(m in line for m in KEEP_MARKERS):
                line = line.replace("Azahar", NEW_NAME)
                changed += 1
            out.append(line)
        open(path, "w", encoding="utf-8").write("\n".join(out))

    if changed == 0:
        sys.exit("rename.py: no strings were renamed, upstream layout changed")
    print(f"== renamed to {NEW_NAME}: app id set, {changed} strings updated")


if __name__ == "__main__":
    main(sys.argv[1])
