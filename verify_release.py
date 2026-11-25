#!/usr/bin/env python3
"""Verify the Hardened R10 delta patch and locally generated camera files.

Zero third-party dependencies (Python 3 standard library only).

Usage:
    python verify_release.py <path_to_file_or_directory> [...]
"""

import hashlib
import struct
import sys
from pathlib import Path

EXPECTED = {
    "r10_stock511.x3p": (
        98_340,
        "557746385bebcc8b0b5b431f9b8ed6b1491c309b929b109bd7ea0fee886f2cb6",
    ),
    "ffinit.bin": (
        40_808,
        "8005819e62143153ececeecfadc04772c2c3170b04963c34ca065bc66bfdd787",
    ),
    "ffboot.bin": (
        30_937_088,
        "72a29e1d702085f1fd2d1f125c61ed7dc6d8e06e816eaa627500b6a27ff513e9",
    ),
    "FWUP0019.DAT": (
        50_136_252,
        "20095acc5f4a7edc4ca8b22ead12d656f33f8bfe6b7525301a6a703dc94d8047",
    ),
}

EXPECTED_DAT_MAIN_CSUM = 0xAD0E6C5C


def verify_file(item: Path) -> bool:
    exp_size, exp_sha = EXPECTED[item.name]
    data = item.read_bytes()
    actual_size = len(data)
    actual_sha = hashlib.sha256(data).hexdigest()
    ok = (actual_size == exp_size) and (actual_sha == exp_sha)

    extra = ""
    if item.name == "FWUP0019.DAT" and actual_size >= 0x210:
        csum = struct.unpack_from("<I", data, 0x20C)[0]
        if csum != EXPECTED_DAT_MAIN_CSUM:
            ok = False
        extra = f"  main_csum@0x20C=0x{csum:08x}"

    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {str(item):45s}  {actual_size:10,d} B  sha256={actual_sha}{extra}")
    if not ok:
        print(f"       expected: {exp_size:10,d} B  sha256={exp_sha}")
    return ok


def main(argv: list[str]) -> int:
    roots = [Path(a) for a in argv[1:]] if len(argv) > 1 else [Path(".")]
    checked = 0
    failed = 0
    for root in roots:
        if not root.exists():
            print(f"[ERROR] Not found: {root}")
            failed += 1
            continue
        items = sorted(root.rglob("*")) if root.is_dir() else [root]
        for item in items:
            if item.is_file() and item.name in EXPECTED:
                checked += 1
                if not verify_file(item):
                    failed += 1

    if checked == 0:
        print("No known R10 patch or output files found in the specified path(s).")
        print("Expected filenames:", ", ".join(EXPECTED.keys()))
        return 1

    print(f"\nSummary: {checked} file(s) checked, {failed} failure(s).")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
