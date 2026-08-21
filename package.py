"""
Build the archives published on the Releases page.

Anyone who does not want to run Python can download these instead of cloning.
The archives are not tracked in git, because a zip cannot be delta compressed
and every rebuild would add a full copy to history forever. They live as release
assets, which are stored outside the repository.

Usage:  python package.py

Produces dist/:
    acme-collections-data.zip     the data set plus the data dictionary
    ANSWER_KEY.md                 defect catalog and true propensity coefficients,
                                  kept separate so the data can be handed over
                                  without the answers

The archives are reproducible: file timestamps inside them are pinned, so
rebuilding from the same commit produces byte-identical zips.
"""

import os
import shutil
import subprocess
import sys
import zipfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "dist")

# Pinned so the zip is byte-identical across rebuilds. Matches TODAY in generate.py.
ZIP_TIMESTAMP = (2026, 8, 20, 0, 0, 0)

CSV_FILES = ["clients.csv", "users.csv", "accounts.csv", "payments.csv",
             "payment_arrangements.csv", "notes.csv"]


def run(*args):
    subprocess.run([sys.executable, os.path.join(BASE_DIR, "generate.py"), *args],
                   check=True, cwd=BASE_DIR)


def build_zip(path, members):
    """members: list of (source_path, name_inside_archive)."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for source, name in members:
            info = zipfile.ZipInfo(name, date_time=ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            with open(source, "rb") as fh:
                z.writestr(info, fh.read())
    return os.path.getsize(path)


def main():
    os.makedirs(DIST_DIR, exist_ok=True)

    print("generating the data set")
    run()

    members = [(os.path.join(BASE_DIR, "data", f), f) for f in CSV_FILES]
    members.append((os.path.join(BASE_DIR, "README.md"), "README.md"))

    print()
    name = "acme-collections-data.zip"
    size = build_zip(os.path.join(DIST_DIR, name), members)
    print(f"  {name:32} {size / 1e6:6.2f} MB")

    shutil.copyfile(os.path.join(BASE_DIR, "ANSWER_KEY.md"),
                    os.path.join(DIST_DIR, "ANSWER_KEY.md"))
    print(f"  {'ANSWER_KEY.md':32} {os.path.getsize(os.path.join(DIST_DIR, 'ANSWER_KEY.md')) / 1e3:6.1f} KB")

    print(f"\nwrote {os.path.relpath(DIST_DIR, BASE_DIR)}/")


if __name__ == "__main__":
    main()
