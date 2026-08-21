"""
Build the archives published on the Releases page.

Anyone who does not want to run Python can download these instead of cloning.
The archives are not tracked in git, because a zip cannot be delta compressed
and every rebuild would add a full copy to history forever. They live as release
assets, which are stored outside the repository.

Usage:  python package.py

Produces dist/:
    acme-collections-data.zip     the data set plus the data dictionary
    ANSWER_KEY.md                 defect catalog and true propensity coefficients
    acme-collections-data-2.zip   a second, independent data set
    ANSWER_KEY-2.md               the matching catalog for that second set

Two data sets are published because they share one underlying propensity model
and differ only in noise, which makes them a ready made train and holdout pair
for A/B work, or simply a second set for anyone who needs one.

Each answer key is a separate file rather than being bundled inside its zip, so
the data can be handed over without the answers. Each key belongs to its own
data set: the record ids in one do not refer to anything in the other.

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

# The first set uses generate.py's own defaults, so the published archive matches
# what anyone gets by cloning and running the script with no arguments.
DATASETS = [
    {"label": "default seed",
     "args": [],
     "data_dir": "data",
     "key_src": "ANSWER_KEY.md",
     "zip_name": "acme-collections-data.zip",
     "key_name": "ANSWER_KEY.md"},
    {"label": 'seed "Data 2"',
     "args": ["--seed", "Data 2", "--out", "data_2",
              "--key", os.path.join("data_2", "ANSWER_KEY.md")],
     "data_dir": "data_2",
     "key_src": os.path.join("data_2", "ANSWER_KEY.md"),
     "zip_name": "acme-collections-data-2.zip",
     "key_name": "ANSWER_KEY-2.md"},
]


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

    for spec in DATASETS:
        print(f"generating: {spec['label']}")
        run(*spec["args"])

    print()
    for spec in DATASETS:
        members = [(os.path.join(BASE_DIR, spec["data_dir"], f), f) for f in CSV_FILES]
        members.append((os.path.join(BASE_DIR, "README.md"), "README.md"))
        size = build_zip(os.path.join(DIST_DIR, spec["zip_name"]), members)
        print(f"  {spec['zip_name']:32} {size / 1e6:6.2f} MB")

        key_out = os.path.join(DIST_DIR, spec["key_name"])
        shutil.copyfile(os.path.join(BASE_DIR, spec["key_src"]), key_out)
        print(f"  {spec['key_name']:32} {os.path.getsize(key_out) / 1e3:6.1f} KB")

    print(f"\nwrote {os.path.relpath(DIST_DIR, BASE_DIR)}/")


if __name__ == "__main__":
    main()
