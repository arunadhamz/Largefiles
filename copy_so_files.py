#!/usr/bin/env python3
"""
copy_so_files.py
----------------
Recursively finds all *.so files under LiBs/ folder and copies them
to a flat Lib_shared_obj/ folder.

- If a file already exists in the target, compares using MD5 checksum.
- If changed, asks user confirmation before overwriting (unless -f flag is used).
- Usage:
    python copy_so_files.py              # interactive mode
    python copy_so_files.py -f           # force mode (no confirmation)
    python copy_so_files.py --src /custom/LiBs --dst /custom/Lib_shared_obj
    python copy_so_files.py -f --src /path/LiBs --dst /path/Lib_shared_obj
"""

import os
import sys
import shutil
import hashlib
import zlib
import argparse
from pathlib import Path


# ─────────────────────────────────────────────
#  Checksum helpers
# ─────────────────────────────────────────────

def md5_checksum(filepath: Path) -> str:
    """Return MD5 hex digest of a file."""
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def crc32_checksum(filepath: Path) -> str:
    """Return CRC32 hex string of a file."""
    crc = 0
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            crc = zlib.crc32(chunk, crc)
    return format(crc & 0xFFFFFFFF, "08x")


def files_are_same(src: Path, dst: Path) -> bool:
    """Return True if src and dst have identical MD5 AND CRC32."""
    return md5_checksum(src) == md5_checksum(dst) and \
           crc32_checksum(src) == crc32_checksum(dst)


# ─────────────────────────────────────────────
#  Core logic
# ─────────────────────────────────────────────

def find_so_files(src_root: Path) -> list[Path]:
    """Recursively find all *.so files under src_root."""
    return sorted(src_root.rglob("*.so"))


def ask_user(filename: str, src: Path, dst: Path) -> bool:
    """Prompt user to confirm overwrite. Returns True if user agrees."""
    print(f"\n  [CHANGED] {filename}")
    print(f"    Source : {src}")
    print(f"    Target : {dst}")
    print(f"    MD5  (src) : {md5_checksum(src)}")
    print(f"    MD5  (dst) : {md5_checksum(dst)}")
    print(f"    CRC32(src) : {crc32_checksum(src)}")
    print(f"    CRC32(dst) : {crc32_checksum(dst)}")
    while True:
        ans = input("  Overwrite? [y/n/a(yes-to-all)/q(quit)] : ").strip().lower()
        if ans in ("y", "yes"):
            return "yes"
        elif ans in ("n", "no"):
            return "no"
        elif ans in ("a", "all"):
            return "all"
        elif ans in ("q", "quit"):
            return "quit"
        else:
            print("  Please enter y / n / a / q")


def copy_files(src_root: Path, dst_root: Path, force: bool):
    """Main copy routine."""

    # Validate source
    if not src_root.exists():
        print(f"[ERROR] Source folder not found: {src_root}")
        sys.exit(1)

    # Create destination if needed
    dst_root.mkdir(parents=True, exist_ok=True)

    so_files = find_so_files(src_root)

    if not so_files:
        print(f"[INFO] No *.so files found under: {src_root}")
        sys.exit(0)

    print(f"\n{'='*60}")
    print(f"  Source      : {src_root}")
    print(f"  Destination : {dst_root}")
    print(f"  Total .so   : {len(so_files)}")
    print(f"  Mode        : {'FORCE (no confirmation)' if force else 'Interactive'}")
    print(f"{'='*60}\n")

    stats = {"copied": 0, "skipped": 0, "new": 0, "errors": 0}
    yes_to_all = force  # if -f flag, treat as yes-to-all from start

    for src_file in so_files:
        filename  = src_file.name
        dst_file  = dst_root / filename

        # ── Duplicate filename check (two different paths, same filename) ──
        if dst_file.exists() and dst_file.resolve() != src_file.resolve():
            if files_are_same(src_file, dst_file):
                print(f"  [OK - SAME]  {filename}")
                stats["skipped"] += 1
                continue

            # Files differ
            if yes_to_all:
                decision = "yes"
            else:
                decision = ask_user(filename, src_file, dst_file)

            if decision == "all":
                yes_to_all = True
                decision   = "yes"

            if decision == "quit":
                print("\n[ABORT] User quit. Partial copy done.")
                break

            if decision == "yes":
                try:
                    shutil.copy2(src_file, dst_file)
                    print(f"  [OVERWRITE]  {filename}")
                    stats["copied"] += 1
                except Exception as e:
                    print(f"  [ERROR]      {filename} → {e}")
                    stats["errors"] += 1
            else:
                print(f"  [SKIP]       {filename}")
                stats["skipped"] += 1

        elif not dst_file.exists():
            # New file — always copy
            try:
                shutil.copy2(src_file, dst_file)
                print(f"  [NEW]        {filename}")
                stats["new"] += 1
            except Exception as e:
                print(f"  [ERROR]      {filename} → {e}")
                stats["errors"] += 1
        else:
            # dst_file exists and is same path (shouldn't normally happen)
            print(f"  [SKIP-SAME]  {filename}")
            stats["skipped"] += 1

    # ── Summary ──
    print(f"\n{'='*60}")
    print(f"  Done!")
    print(f"  New files copied   : {stats['new']}")
    print(f"  Overwritten        : {stats['copied']}")
    print(f"  Skipped (no change): {stats['skipped']}")
    print(f"  Errors             : {stats['errors']}")
    print(f"{'='*60}\n")


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Copy *.so files from nested LiBs/ folder to a flat Lib_shared_obj/ folder."
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Force copy all .so files without asking confirmation for changed files."
    )
    parser.add_argument(
        "--src",
        default="LiBs",
        help="Source root folder (default: LiBs)"
    )
    parser.add_argument(
        "--dst",
        default="Lib_shared_obj",
        help="Destination folder (default: Lib_shared_obj)"
    )

    args = parser.parse_args()

    src_root = Path(args.src).resolve()
    dst_root = Path(args.dst).resolve()

    copy_files(src_root, dst_root, force=args.force)


if __name__ == "__main__":
    main()
