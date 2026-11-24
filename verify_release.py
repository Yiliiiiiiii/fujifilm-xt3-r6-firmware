#!/usr/bin/env python3
"""Verify the Hardened R6 delta patch and locally generated camera files.

Zero third-party dependencies (Python 3 standard library only).

Usage:
    python verify_release.py <path_to_file_or_directory> [...]
"""

import hashlib
import struct
import sys
from pathlib import Path

EXPECTED = {
    "r6_stock511.x3p": (
        95_988,
        "be90b7ee572992be6434d783cd8fee33d84ee35a2a77ed133e4d401229a877d1",
    ),
    "ffinit.bin": (
        40_808,
        "a218eca392f6d1a645ff1e8388dada4325a9b0a8bb30a3ffc75d7429b8085983",
    ),
    "ffboot.bin": (
        30_937_088,
        "d4bc67e9ca10f25e45c60845be8d7e22ad0264bb8cb0f1186a9f3695a589225b",
    ),
    "FWUP0019.DAT": (
        50_136_252,
        "59658c432421b60d986d1815d50a685d078ebc5222647ea140572d0f979f08a0",
    ),
}

EXPECTED_DAT_MAIN_CSUM = 0xAD1E4ED5


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
        print("No known R6 patch or output files found in the specified path(s).")
        print("Expected filenames:", ", ".join(EXPECTED.keys()))
        return 1

    print(f"\nSummary: {checked} file(s) checked, {failed} failure(s).")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
