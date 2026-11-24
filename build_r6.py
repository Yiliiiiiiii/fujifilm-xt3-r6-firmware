#!/usr/bin/env python3
"""Build Fujifilm X-T3 Hardened R6 firmware & SD Fast-Boot Test Package locally
from Fujifilm's official X-T3 Stock 5.11 firmware (FWUP0019.DAT).

Zero third-party dependencies (Python 3 standard library only; works on Windows,
macOS, and Linux). No proprietary Fujifilm firmware binaries are stored in this
repository — the user supplies their own official Stock 5.11 FWUP0019.DAT
downloaded from Fujifilm's website, and this script applies the pure XOR-delta
patch (r6_stock511.x3p) and verifies every output file against pinned SHA-256s.

FFLZ codec follows tiredboffin/fffw (MIT License).

Usage:
    python build_r6.py <path/to/stock_511_FWUP0019.DAT> [-o out_r6] [--sd-only] [--dat-only]
"""

from __future__ import annotations

import argparse
import hashlib
import lzma
import re
import struct
import sys
import time
from pathlib import Path

INVERT = bytes(255 - i for i in range(256))

STOCK_511_SIZE = 50_136_252
STOCK_511_SHA256 = "9f2c75fd8a16a1d71b9218f6dbd3144b1f11820bcecd3a9608c8cda9f25f95a3"

PATCH_MAGIC = b"X3R6P001"
PATCH_DEFAULT_NAME = "r6_stock511.x3p"
PATCH_SHA256 = "be90b7ee572992be6434d783cd8fee33d84ee35a2a77ed133e4d401229a877d1"

EXPECTED_OUTPUTS = {
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
EXPECTED_FULL_SD_SHA256 = "1995aba5bebe71fcf78496a1190ca89c3e155557a2f128a22f94ded95c403c54"

SEG0_OFFSET, SEG0_CAPACITY = 0x260274, 0x2E0000
SEG1_OFFSET, SEG1_CAPACITY = 0x540274, 0x480000
FULL_RAM_SIZE = 63_696_896

FAST_TABLE, FAST_END = 0x3E10, 0x4000
INIT_FIELDS = 0x4784
MIN_RUN, PAGE, FIRST, STRIDE = 0x10000, 0x1000, 0x1000, 16


def sha256(data: bytes | bytearray) -> str:
    return hashlib.sha256(data).hexdigest()


def unpack_fflz(image: bytes, offset: int) -> bytes:
    """Decode one Fujifilm FFLZ (method 4) compressed firmware segment."""
    size, packed_size, pages, page_size, alignment = struct.unpack_from("<5I", image, offset)
    if not (0 < packed_size < size < 128 * 1024 * 1024):
        raise ValueError(f"Invalid FFLZ header at {offset:#x}")
    if pages != (packed_size + 16383) // 16384 or page_size != 16384 or alignment != 4:
        raise ValueError(f"Unexpected FFLZ geometry at {offset:#x}")
    pos, end = offset + 20, offset + packed_size
    out = bytearray()
    while pos < end:
        token = image[pos]
        pos += 1
        if token & 0x80:
            second = image[pos]
            pos += 1
            count = second & 0x0F
            dist = ((token & 0x7F) << 4) | (second >> 4)
            start = len(out) - dist
            out.extend(out[start : start + count])
        else:
            out.extend(image[pos : pos + token])
            pos += token
    if 0 < size - len(out) <= 127 and packed_size % 16384 == 0:
        out.extend(bytes(size - len(out)))
    if pos != end or len(out) != size:
        raise ValueError(f"FFLZ unpack size mismatch at {offset:#x}: {len(out)} != {size}")
    return bytes(out)


def pack_fflz(data: bytes) -> bytes:
    """Bit-exact Fujifilm FFLZ (method 4) packer matching tiredboffin/fffw."""
    HEADER_SIZE = 20
    PAGE_SIZE = 16384
    MAX_LIT = 127
    n = len(data)
    out = bytearray(HEADER_SIZE)
    lit = bytearray()
    held = bytearray()
    held_start = 0
    held_out = 0
    written_tokens = 0

    def write_held() -> None:
        if held:
            out.extend(held)
            held.clear()

    def emit(token: bytes, out_len: int) -> None:
        nonlocal held_start, held_out, written_tokens
        write_held()
        held_start = written_tokens + HEADER_SIZE
        held.extend(token)
        held_out = out_len
        written_tokens += len(token)

    def page_free() -> int:
        return PAGE_SIZE - (written_tokens + HEADER_SIZE) % PAGE_SIZE

    def write_lit(length: int) -> None:
        flush_all = length == 0
        if flush_all:
            length = len(lit)
        emit(bytes([length]) + bytes(lit[:length]), length)
        if flush_all:
            lit.clear()
        else:
            del lit[:length]

    def flush_lit() -> bool:
        if not lit:
            return False
        free = page_free()
        ll = len(lit)
        if free == ll + 2:
            if ll == MAX_LIT:
                write_lit(free - 3)
            return True
        if free < ll + 1:
            write_lit(free - 1)
            if ll == MAX_LIT:
                return True
        write_lit(0)
        return False

    pos = 0
    rfind = data.rfind
    while pos < n:
        win_start = pos - 2047 if pos > 2047 else 0
        max_l = 15 if pos + 15 <= n else n - pos
        mlen = 0
        mpos = 0
        if max_l >= 3 and pos > win_start:
            hit3 = rfind(data[pos : pos + 3], win_start, pos)
            if hit3 != -1:
                best_l = 3
                best_idx = hit3
                for L in range(4, max_l + 1):
                    h = rfind(data[pos : pos + L], win_start, pos)
                    if h == -1:
                        break
                    best_l = L
                    best_idx = h
                mlen = best_l
                mpos = pos - best_idx

        if mlen < 3:
            lit.append(data[pos])
            if len(lit) == MAX_LIT:
                flush_lit()
            pos += 1
        else:
            if flush_lit():
                lit.append(data[pos])
                pos += 1
            else:
                free = page_free()
                unmatched = 2 if free == 3 else (1 if free == 4 else 0)
                if unmatched:
                    src = pos - mpos
                    lit.extend(data[src : src + unmatched])
                    flush_lit()
                ml = mlen - unmatched
                emit(bytes([0x80 | ((mpos >> 4) & 0x7F), ((mpos & 0x0F) << 4) | (ml & 0x0F)]), ml)
                pos += mlen

    if lit:
        if flush_lit():
            write_lit(0)

    if (
        held
        and held_start % PAGE_SIZE == 0
        and (held[0] & 0x80) != 0
        and held_out == 2
        and data[n - 2 : n] == b"\x00\x00"
    ):
        written_tokens -= len(held)
        held.clear()
    else:
        write_held()

    packed_size = written_tokens + HEADER_SIZE
    num_pages = (packed_size + PAGE_SIZE - 1) // PAGE_SIZE
    struct.pack_into("<5I", out, 0, n, packed_size, num_pages, PAGE_SIZE, 4)
    return bytes(out)


def apply_xor_section(base: bytes, section: bytes) -> bytes:
    """Apply one sparse XOR-delta section onto base bytes."""
    target_len, num_runs = struct.unpack_from("<2I", section, 0)
    out = bytearray(base[:target_len])
    if len(out) < target_len:
        out.extend(bytes(target_len - len(out)))
    p = 8
    cur = 0
    for _ in range(num_runs):
        delta_off, length = struct.unpack_from("<2I", section, p)
        p += 8
        cur += delta_off
        end = cur + length
        x = section[p : p + length]
        p += length
        for i in range(length):
            out[cur + i] ^= x[i]
        cur = end
    if p != len(section):
        raise ValueError("Corrupt XOR-delta section length")
    return bytes(out)


def load_patch(patch_path: Path) -> tuple[bytes, bytes, bytes, bytes, bytes]:
    raw = patch_path.read_bytes()
    actual_sha = sha256(raw)
    if actual_sha != PATCH_SHA256:
        raise ValueError(
            f"Patch SHA-256 mismatch for {patch_path}:\n"
            f"  got:      {actual_sha}\n"
            f"  expected: {PATCH_SHA256}"
        )
    if raw[:8] != PATCH_MAGIC:
        raise ValueError("Invalid patch magic header")
    payload = lzma.decompress(raw[8:])
    sections = []
    p = 0
    for _ in range(5):
        (sz,) = struct.unpack_from("<I", payload, p)
        p += 4
        sections.append(payload[p : p + sz])
        p += sz
    if p != len(payload):
        raise ValueError("Trailing bytes in patch payload")
    return tuple(sections)  # type: ignore[return-value]


def dat_main_checksum(image: bytes, raw: bytes) -> int:
    size = struct.unpack_from("<I", raw, 0x248)[0]
    if size <= 0 or 0x274 + size > len(image):
        raise ValueError("Invalid DAT payload size field at 0x248")
    return (~sum(image[0x274 : 0x274 + size])) & 0xFFFFFFFF


def fast_boot_segments(img: bytes) -> list[tuple[int, int]]:
    gaps = []
    for m in re.finditer(rb"\x00{%d,}" % MIN_RUN, img):
        a = (m.start() + PAGE - 1) & ~(PAGE - 1)
        b = m.end() & ~(PAGE - 1)
        if b - a >= MIN_RUN:
            gaps.append((a, b))
    segs = []
    at = 0
    for a, b in gaps:
        segs.append((at, a))
        at = b
    if at < len(img):
        segs.append((at, len(img)))
    segs = [s for s in segs if s[1] > s[0]]
    return [(0, FIRST), (FIRST, segs[0][1])] + segs[1:]


def verify_and_write(path: Path, name: str, data: bytes) -> None:
    exp_size, exp_sha = EXPECTED_OUTPUTS[name]
    got_sha = sha256(data)
    if len(data) != exp_size or got_sha != exp_sha:
        raise RuntimeError(
            f"Output verification FAILED for {name}!\n"
            f"  got:      {len(data):,} B  {got_sha}\n"
            f"  expected: {exp_size:,} B  {exp_sha}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    print(f"  [PASS] {path}  ({len(data):,} B, sha256={got_sha})")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Locally reconstruct Fujifilm X-T3 Hardened R6 firmware & SD Fast-Boot Test Package from official Stock 5.11 FWUP0019.DAT."
    )
    parser.add_argument("stock_dat", type=Path, help="Path to official Fujifilm X-T3 5.11 FWUP0019.DAT")
    parser.add_argument(
        "-p",
        "--patch",
        type=Path,
        default=Path(__file__).resolve().parent / PATCH_DEFAULT_NAME,
        help=f"Path to delta patch file (default: {PATCH_DEFAULT_NAME} beside this script)",
    )
    parser.add_argument("-o", "--out", type=Path, default=Path("out_r6"), help="Output directory (default: out_r6)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--sd-only", action="store_true", help="Build only the zero-flash SD Fast-Boot Test Package (~2s)")
    mode.add_argument("--dat-only", action="store_true", help="Build only FWUP0019.DAT (~12s)")
    args = parser.parse_args(argv[1:])

    t0 = time.time()
    print("[1/4] Verifying official X-T3 Stock 5.11 FWUP0019.DAT and delta patch...")
    if not args.stock_dat.is_file():
        print(f"[ERROR] Stock 5.11 DAT not found: {args.stock_dat}", file=sys.stderr)
        return 1
    stock_raw = args.stock_dat.read_bytes()
    stock_sha = sha256(stock_raw)
    if len(stock_raw) != STOCK_511_SIZE or stock_sha != STOCK_511_SHA256:
        print(
            "[ERROR] Input file is NOT official Fujifilm X-T3 Firmware 5.11 (FWUP0019.DAT)!\n"
            f"  got:      {len(stock_raw):,} B  {stock_sha}\n"
            f"  expected: {STOCK_511_SIZE:,} B  {STOCK_511_SHA256}\n"
            "  Download official 5.11 from Fujifilm's X-T3 support page.",
            file=sys.stderr,
        )
        return 1
    print(f"  [OK] Stock 5.11 verified ({len(stock_raw):,} B)")

    sec_outer, sec_seg0, sec_seg1, sec_sd, sec_init = load_patch(args.patch)
    print(f"  [OK] Patch {args.patch.name} verified ({args.patch.stat().st_size:,} B)")

    print("[2/4] Unpacking Stock 5.11 segments and applying R6 deltas...")
    stock_img = stock_raw.translate(INVERT)
    stock_seg0 = unpack_fflz(stock_img, SEG0_OFFSET)
    stock_seg1 = unpack_fflz(stock_img, SEG1_OFFSET)

    r6_outer = apply_xor_section(stock_img, sec_outer)
    r6_seg0 = apply_xor_section(stock_seg0, sec_seg0)
    r6_seg1 = apply_xor_section(stock_seg1, sec_seg1)
    seg0_base = struct.unpack_from("<I", r6_seg0, 4)[0]
    seg1_base = struct.unpack_from("<I", r6_seg1, 4)[0]

    if not args.dat_only:
        print("[3/4] Building zero-flash SD Fast-Boot Test Package (ffinit.bin + ffboot.bin)...")
        ram = bytearray(FULL_RAM_SIZE)
        for dst, src, sz in (
            (0x00000000, 0x00020274, 0x00020000),
            (0x00020000, 0x00040274, 0x00020000),
            (0x00040000, 0x00060274, 0x00020000),
            (0x001E0000, 0x01800274, 0x00580000),
            (0x007E0000, 0x01DC0274, 0x000C0000),
            (0x00D20000, 0x00140274, 0x00000400),
            (0x00D20400, 0x00160274, 0x0002C000),
            (0x00E20400, 0x001E0274, 0x0002C000),
            (0x033B1000, 0x009C0274, 0x0090E000),
        ):
            ram[dst : dst + sz] = r6_outer[src : src + sz]
        ram[seg0_base : seg0_base + len(r6_seg0)] = r6_seg0
        ram[seg1_base : seg1_base + len(r6_seg1)] = r6_seg1

        full_sd = apply_xor_section(bytes(ram), sec_sd)
        if sha256(full_sd) != EXPECTED_FULL_SD_SHA256:
            raise RuntimeError("Reconstructed full SD image SHA-256 mismatch")

        segs = fast_boot_segments(full_sd)
        ffboot = b"".join(full_sd[a:b] for a, b in segs)

        base_init = bytearray(EXPECTED_OUTPUTS["ffinit.bin"][0])
        base_init[0x0000:0x1AC0] = stock_img[0x00A74:0x02534]
        base_init[0x47A4:0x4FA4] = stock_img[0x00274:0x00A74]
        base_init[0x4FA4:0x9F68] = stock_img[0x02534:0x074F8]
        ffinit = apply_xor_section(bytes(base_init), sec_init)

        # Cross-check fast-loader table & rolling checksum inside ffinit against ffboot
        table = b"".join(struct.pack("<2I", a, b - a) for a, b in segs) + struct.pack("<2I", len(full_sd), 0)
        rolling = 0
        for i in range(0, len(ffboot), 4 * STRIDE):
            rolling = (struct.unpack_from("<I", ffboot, i)[0] + (((rolling << 1) | (rolling >> 31)) & 0xFFFFFFFF)) & 0xFFFFFFFF
        if ffinit[FAST_TABLE : FAST_TABLE + len(table)] != table:
            raise RuntimeError("Fast-loader extent table mismatch")
        if struct.unpack_from("<2I", ffinit, INIT_FIELDS) != (len(ffboot), rolling):
            raise RuntimeError("Fast-loader header fields mismatch")

        sd_out = args.out / "sd_fastboot"
        verify_and_write(sd_out / "ffinit.bin", "ffinit.bin", ffinit)
        verify_and_write(sd_out / "ffboot.bin", "ffboot.bin", ffboot)

    if not args.sd_only:
        print("[4/4] Compressing FFLZ segments and packing FWUP0019.DAT (~10s)...")
        packed0 = pack_fflz(r6_seg0)
        packed1 = pack_fflz(r6_seg1)
        if len(packed0) >= SEG0_CAPACITY or len(packed1) >= SEG1_CAPACITY:
            raise RuntimeError("Compressed segment exceeded container capacity")

        r6_img = bytearray(r6_outer)
        r6_img[SEG0_OFFSET : SEG0_OFFSET + SEG0_CAPACITY] = packed0 + bytes(SEG0_CAPACITY - len(packed0))
        r6_img[SEG1_OFFSET : SEG1_OFFSET + SEG1_CAPACITY] = packed1 + bytes(SEG1_CAPACITY - len(packed1))

        r6_raw = bytearray(stock_raw)
        r6_raw[0x274:] = bytes(r6_img[0x274:]).translate(INVERT)
        csum = dat_main_checksum(bytes(r6_img), bytes(r6_raw))
        if csum != EXPECTED_DAT_MAIN_CSUM:
            raise RuntimeError(f"Main checksum mismatch: {csum:#x} != {EXPECTED_DAT_MAIN_CSUM:#x}")
        struct.pack_into("<I", r6_raw, 0x20C, csum)

        verify_and_write(args.out / "firmware_dat" / "FWUP0019.DAT", "FWUP0019.DAT", bytes(r6_raw))

    print(f"\nAll requested Hardened R6 outputs built and verified in {time.time() - t0:.2f}s!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
