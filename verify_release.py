#!/usr/bin/env python3
"""Verify the Hardened R9 delta patch and locally generated camera files.

Zero third-party dependencies (Python 3 standard library only).

Usage:
    python verify_release.py <path_to_file_or_directory> [...]
"""

import hashlib
import struct
import sys
from pathlib import Path

EXPECTED = {
    "r9_stock511.x3p": (
        98_320,
        "7ddb1949e3bbf2f561134213e886fd6d93153562f274420842a547776f42b5c0",
    ),
    "ffinit.bin": (
        40_808,
        "1b83b4547eac786b9ab062b6e0bb56438f06cae58d479ac1246ff7633b76414f",
    ),
    "ffboot.bin": (
        30_937_088,
        "27c5e6596bfdaeaec7c6a129da32a99662908138c5c2d8f3fdbbeaf517ceac2a",
    ),
    "FWUP0019.DAT": (
        50_136_252,
        "d4e8950d61915d7716c2b408783b35d7e831084f70e8f1507dd9793cfb90cfb9",
    ),
}

EXPECTED_DAT_MAIN_CSUM = 0xAD0EAD23


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
        print("No known R9 patch or output files found in the specified path(s).")
        print("Expected filenames:", ", ".join(EXPECTED.keys()))
        return 1

    print(f"\nSummary: {checked} file(s) checked, {failed} failure(s).")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
