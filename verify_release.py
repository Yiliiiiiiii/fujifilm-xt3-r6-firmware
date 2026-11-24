#!/usr/bin/env python3
"""Verify Fujifilm X-T3 Hardened R6 release ZIP archives and extracted binaries.

Zero third-party dependencies (Python 3 standard library only).

Usage:
    python verify_release.py <path_to_file_or_directory> [...]
"""

import hashlib
import struct
import sys
import zipfile
from pathlib import Path

EXPECTED = {
    "XT3_Hardened_R6_SD_FastBoot_Test.zip": (
        10_250_555,
        "d8b2918031db248cdadbf84cafde9b1f10bafe1134e5e2b4ad2768139405f5db",
    ),
    "XT3_Hardened_R6_Firmware_DAT.zip": (
        16_747_891,
        "04904052926e16c90f339ff132d315ed55225d9d2ff4509fe07b881f14e5542c",
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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_blob(name: str, data: bytes) -> bool:
    exp_size, exp_sha = EXPECTED[name]
    actual_size = len(data)
    actual_sha = sha256_bytes(data)
    ok = (actual_size == exp_size) and (actual_sha == exp_sha)

    extra = ""
    if name == "FWUP0019.DAT" and actual_size >= 0x210:
        csum = struct.unpack_from("<I", data, 0x20C)[0]
        if csum != EXPECTED_DAT_MAIN_CSUM:
            ok = False
        extra = f"  main_csum@0x20C=0x{csum:08x}"

    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name:38s}  {actual_size:10,d} B  sha256={actual_sha}{extra}")
    if not ok:
        print(f"       expected: {exp_size:10,d} B  sha256={exp_sha}")
    return ok


def verify_path(path: Path) -> tuple[int, int]:
    checked = 0
    failed = 0
    targets = sorted(path.iterdir()) if path.is_dir() else [path]
    for item in targets:
        if not item.is_file():
            continue
        if item.name not in EXPECTED:
            continue
        data = item.read_bytes()
        checked += 1
        if not verify_blob(item.name, data):
            failed += 1
        if item.suffix.lower() == ".zip":
            with zipfile.ZipFile(item, "r") as zf:
                for member in zf.namelist():
                    if member in EXPECTED:
                        checked += 1
                        if not verify_blob(member, zf.read(member)):
                            failed += 1
    return checked, failed


def main(argv: list[str]) -> int:
    paths = [Path(a) for a in argv[1:]] if len(argv) > 1 else [Path(".")]
    total_checked = 0
    total_failed = 0
    for p in paths:
        if not p.exists():
            print(f"[ERROR] Not found: {p}")
            total_failed += 1
            continue
        c, f = verify_path(p)
        total_checked += c
        total_failed += f

    if total_checked == 0:
        print("No known R6 release files found in the specified path(s).")
        print("Expected filenames:", ", ".join(EXPECTED.keys()))
        return 1

    print(f"\nSummary: {total_checked} file(s) checked, {total_failed} failure(s).")
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
