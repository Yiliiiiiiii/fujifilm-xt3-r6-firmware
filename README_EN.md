# Fujifilm X-T3 Hardened R9 Patcher (based on Stock 5.11)

[中文](README.md) | **English**

> ⚠️ **DISCLAIMER & COPYRIGHT NOTICE**
>
> - **No proprietary Fujifilm firmware binaries are hosted in this repository or its Releases.** Only a **~96 KB** pure XOR-delta patch (`r9_stock511.x3p`) and a zero-dependency Python 3 local builder (`build_r9.py`) are distributed. Users must download the official Fujifilm X-T3 5.11 `FWUP0019.DAT` directly from Fujifilm's website and reconstruct all camera files locally.
> - This is an unofficial community research project with no affiliation with FUJIFILM Corporation. Flashing modified firmware carries risks of **bricking the camera, data loss, and voiding warranty**. **We strongly recommend trying the zero-flash SD Fast-Boot Test Package first** (runs purely in RAM without touching camera flash), backing up all personal settings, and ensuring a fully charged battery before any flash. Use strictly at your own risk.

---

## 1. Local 3-Step Build (Windows / macOS / Linux, Zero Dependencies)

Requires **Python 3** only (standard library only, no third-party packages):

### Step 1: Download Official Fujifilm X-T3 Firmware 5.11
Download the official **X-T3 Ver.5.11** `FWUP0019.DAT` from Fujifilm's support page:
- Official page: https://www.fujifilm-x.com/global/support/download/firmware/cameras/x-t3/
- Expected input size: `50,136,252 B`, SHA-256: `9f2c75fd8a16a1d71b9218f6dbd3144b1f11820bcecd3a9608c8cda9f25f95a3` (verified automatically by the script).

### Step 2: Download This Delta Patcher
Download the latest **`v1.1.0-r9`** patcher bundle (**~113 KB**) from **[Releases](https://github.com/Yiliiiiiiii/fujifilm-xt3-r6-firmware/releases)**, or clone this repository:

```bash
git clone https://github.com/Yiliiiiiiii/fujifilm-xt3-r6-firmware.git
cd fujifilm-xt3-r6-firmware
```

### Step 3: Build Locally and Auto-Verify SHA-256

```bash
# Build both the zero-flash SD Fast-Boot Package AND FWUP0019.DAT (~12s)
python build_r9.py /path/to/official_511_FWUP0019.DAT -o out_r9

# Or build ONLY the zero-flash SD Fast-Boot Package (~2s)
python build_r9.py /path/to/official_511_FWUP0019.DAT -o out_r9 --sd-only
```

All generated files under `out_r9/` are automatically verified bit-for-bit against the pinned Hardened R9 hashes:

| Local Output Path | Purpose | Bytes | Pinned SHA-256 |
| --- | --- | ---: | --- |
| `out_r9/sd_fastboot/ffinit.bin` | **Zero-flash SD Fast-Boot Package** (paired with `ffboot.bin`) | `40,808` | `1b83b4547eac786b9ab062b6e0bb56438f06cae58d479ac1246ff7633b76414f` |
| `out_r9/sd_fastboot/ffboot.bin` | **Zero-flash SD Fast-Boot Package** (RAM-only; remove card to return to stock) | `30,937,088` | `27c5e6596bfdaeaec7c6a129da32a99662908138c5c2d8f3fdbbeaf517ceac2a` |
| `out_r9/firmware_dat/FWUP0019.DAT` | **Hardened R9 Firmware Image** (main checksum `@0x20C = 0xad0ead23`) | `50,136,252` | `d4e8950d61915d7716c2b408783b35d7e831084f70e8f1507dd9793cfb90cfb9` |

> After copying files to your SD card, you can run `python verify_release.py E:\` (replace with your SD card path) to re-verify file integrity on the card.

---

## 2. Key Fixes in Hardened R9 vs. R6 (All Hardware-Verified on X-T3)

- **R7 — Native Q-Menu Half-Step GVFF Vector Icons + Liveview WYSIWYG WA/AA**:
  - Added 6 native `80×48` GVFF vector icons (`0xFF00200E..0xFF002013`), fixing blank Q-menu 16-tile cells for half-step Highlight/Shadow values (`+3.5 / +2.5 / +1.5 / +0.5 / -0.5 / -1.5`).
  - Wired Liveview AE/AWB gain dispatch, ISP display selector, and real-time priority gain scaling so WA/AA Liveview matches the captured photo with zero multi-frame IIR drift.
- **R8 — Fixed S1 Half-Press AWB Lock Fallback & Restored Per-Body Factory EEPROM Calibration**:
  - Fixed S1 half-press AWB Lock sync/init (`0x0115E048` / `0x01E52804`) so WA/AA retain locked live gains instead of zeroing out and falling back to the Daylight preset.
  - Restored stock per-body factory EEPROM gain-table getters (`0x011B1FE0` / `0x011B201C`), preserving individual camera WB calibration; verified `0-LSB` exact match on real X-T3 Auto / WA / AA RAF captures.
- **R9 — Fixed Classic Neg. (NC) & Eterna Bleach Bypass (EB) `-1 EV` / `-1.8 EV` Underexposure & DR100 H/S Bug**:
  - Fixed `0x0150A02C` (`moveq r0, #1 -> #2`) where all 40 Still Liveview sensor configs (`0x01F5BD34 == 0`) erroneously selected X-T4's 1x Bank 1 (lacking 2x/4x DR lift and DR100 IDs), which caused **`-1.00 EV` underexposure at DR200**, **`-1.80 EV` at DR400**, and **non-functional Highlight/Shadow adjustments at DR100** on NC and EB.
  - Replaced Bank 2's incomplete 35-entry pointer table with O(1) direct indexing across all 168 Stock X-T3 curves (restoring all 8 missing **D-Range Priority (DRP)** curves to eliminate `+1.00 EV` overexposure), restored `gcls=2/4` selector entries and DRP split index `27`, and fixed Natural Live View / Preview Exposure OFF (`aux[+0xA5] == 0`) half-step retention.
  - Verified **`1,200/1,200` exact `0-LSB` parity** against native X-T4 Bank 0 (`0x02084E40`). **F-Log / HLG and Movie mode remain safely isolated with zero regression**, and NN / RA / all stock film simulations are bit-identical.

---

## 3. Feature Summary (Relative to Stock X-T3 5.11)

| Feature Module | Hardened R9 Implementation |
| --- | --- |
| **4 Added Film Simulations** (20 total) | Adds **Classic Neg. (NC)**, **ETERNA Bleach Bypass (EB/BB)**, **Nostalgic Neg. (NN)**, and **REALA ACE (RA)** across Shooting Menu, Q Menu, Film Simulation Bracketing, C1–C7, EXIF MakerNote, and In-Camera RAW Conversion. NC/EB achieve `0-LSB` X-T4 Bank 0 curve parity across DR100/200/400/DRP; RA includes 3D D3 LUT with Movie DMA refresh; NN includes complete 40-point curves and extended color parameters. |
| **Dual-Priority Auto White Balance (WA / AA)** | Ports X-T4 **White Priority (WA)** and **Ambience Priority (AA)** exact ratio scaling (preserving each body's factory EEPROM calibration), Liveview WYSIWYG, and still capture ring. Includes independent R/B shift, S1 & AE-L/AWB-L, 35-language captions, 20 native GVFF icons, **all 6 Liveview HUD screens**, **all 6 Playback Info screens**, MakerNote `0x1002` + RAF dual-gain tags, and **In-Camera RAW Conversion manual selection & Reflect Shooting Cond.** |
| **All-Film 0.5-Step Highlight / Shadow Tone** | Unlocks **−2 to +4 in 0.5-step increments (13 steps, including `±0.5 / ±1.5 / +2.5 / +3.5`)** across all 23 internal still film enums (19 stock + 4 ported). Stock films use a 124 B resident 50/50 real-time blender (`≤ 1 LSB` vs. X-T4). Integrated with Main Menu, **26/26 native Q-Menu GVFF icons**, C1–C7, EXIF `0x1040`/`0x1041`, PTP, **all 4 Playback Info screens (`±0.5`)**, and **In-Camera RAW Reflect Shooting Cond. round-toward-zero**. |
| **Color Chrome FX Blue** | **Off / Weak / Strong**, orthogonal 3×3 combination with native Color Chrome Effect, with C1–C7 persistence and Shooting Menu Reset support. |

### Out of Scope & Deliberate Isolation Boundaries
- **Not included**: Clarity, F-Log View Assist / F-Log2, Monochromatic Color (Warm/Cool), HDR / Multiple Exposure, and X-T4 auto-update C1–C7 behavior (retains X-T3's native manual save workflow).
- **Deliberately isolated**: **Movie mode** strictly isolates WA/AA and static 0.5-step H/S, and F-Log/HLG bypass directly to Stock `0x01D74AA0` to preserve stock video stability. **In-Camera RAW manual H/S menus** remain stock integer steps.

---

## 4. Color & Algorithm Provenance (Exact Factory Ports vs. Fitted Tables)

### 1. The 4 Ported Film Simulations: 3 Full-Pipeline 100% Lossless Ports; Only RA's D3 3D LUT Is Grid-Fitted

| Film Simulation | 18B 3×3 Color Matrix & 8B Params | Aux Hue Block | Tone / Gamma Curves (incl. 0.5-step) | D3 3D LUT (Core Color LUT) | Color Chrome / FX Blue (3×3) |
| --- | --- | --- | --- | --- | --- |
| **Classic Neg. (NC)** | **100% Exact Port**<br>(byte-identical to X-T4 / X-S20) | **100% Exact Port** | **100% Exact Port**<br>(`0-LSB` vs. X-T4 Bank 0) | **100% Exact (Natively Off)**<br>(X-T4 / X-S20 / GFX do not enable D3 LUT for NC) | FX Blue Weak/Strong **100% Exact Port**; stock X-T3 Color Chrome when FX Blue Off |
| **ETERNA Bleach Bypass (EB)** | **100% Exact Port**<br>(byte-identical to X-T4 / X-S20) | **100% Exact Port** | **100% Exact Port**<br>(`0-LSB` vs. X-T4 Bank 0) | **100% Lossless Port**<br>(X-T4 / GFX100S / GFX50SII factory `16³` table, `0-LSB` exact) | Same as above |
| **Nostalgic Neg. (NN)** | **100% Exact Port**<br>(from same-sensor X-Trans IV **X-S20**) | **100% Exact Port** | **100% Exact Port**<br>(factory 40-point half-step curves) | **100% Lossless Port**<br>(GFX100S / GFX50SII factory `16³` table, `0-LSB` exact) | Same as above |
| **REALA ACE (RA)** | **100% Exact Port**<br>(from same-sensor X-Trans IV **X-S20 3.30**) | **100% Exact Port** | **100% Exact Port**<br>(X-S20 DR100/200/400/DRP half-step curves) | **Least-Squares Grid Fit**<br>(X-S20 factory `17³` → X-T3 hardware `16³`) | **9/9 100% Exact Port**<br>(incl. Off/Off native RA color-shaping row from X-S20) |

- **Why only REALA ACE's D3 3D LUT is grid-fitted**:
  - REALA ACE only exists on X-Processor 5 cameras (e.g. X-S20), which use a **`17×17×17`** hardware 3D LUT grid, whereas X-T3's X-Processor 4 ISP hardware strictly expects a **`16×16×16`** (32 KB) grid.
  - Rather than naive resampling, X-S20's factory `17³` LUT is fitted onto the `16³` grid via **exact Gauss-quadrature uniform RGB least squares**, with all **8 gamut corners and the entire neutral gray axis (`R=G=B`, zero tint) hard-anchored**.
  - Evaluated across `373,248` independent 12-bit (`0..4095`) RGB inputs against X-S20's `17³` trilinear reference: **mean error `1.72 / 4095` (`0.042%`, ~`0.11` levels in 8-bit — visually indistinguishable)**, P95 `6.86 / 4095` (`0.17%`), P99 `17.38 / 4095` (`0.42%`), peak at extreme gamut edges `119.08 / 4095` (`2.9%`).
- **0.5-Step Curves on the 19 Stock Film Simulations**:
  - The 4 ported films (NC / EB / NN / RA) use native 4-anchor weighted interpolation (`0-LSB`). The 19 stock films use `(a + b + 1) >> 1` 50/50 midpoint blending between adjacent integer curves; across `23,040` control points vs. native X-T4, **max deviation is `≤ 1 LSB` (`92.7%` zero-error, zero DC bias)**.

### 2. Dual-Priority Auto White Balance (WA / AA) Provenance
- **Source: Native Fujifilm X-T4 priority gain-ratio algorithm (`0-LSB` exact extraction, no approximation)**.
  - Extracts the exact reduced rational ratios `(red_num/red_den, blue_num/blue_den)` across all color-temperature coordinates (`coord ∈ [120..174]`, saturated outside identically to X-T4) into a `566 B` resident table (`0x0150C400`), evaluated with X-T3's native ARMv7-A `UDIV` instruction.
- **Per-Body Factory EEPROM Calibration Preserved**:
  - Priority scaling is applied on top of **X-T3's own Auto AWB result**, keeping the stock per-body EEPROM calibration table getters (`0x011B1FE0` / `0x011B201C` → `0x01841800`) completely intact instead of overwriting them with a static X-T4 table.
  - The same exact ratio table drives **Liveview WYSIWYG (zero multi-frame IIR drift)**, **Still capture / S1 & AWB-L Lock**, **RAF dual-gain metadata (`0xF013`/`0xF014`)**, and **X-T4-compliant MakerNote `0x1002` (`0x0001` / `0x0002`)**, verified `0-LSB` exact on real X-T3 RAF captures.

---

## 5. On-Camera Usage Guide (Start with Method A!)

### Method A (Strongly Recommended): Zero-Flash SD Fast-Boot Test Package
This method **never writes to camera flash** and is the safest way to test every Hardened R9 feature on your own X-T3:

1. Back up your camera settings first using official **FUJIFILM X RAW Studio** or **X Acquire** via USB.
2. Prepare a clean **MBR + FAT32** SD card in **Slot 1** (**Slot 2 empty**, USB unplugged; for 64 GB+ SDXC cards, create a `≤ 32 GB` FAT32 partition because X-T3's Boot ROM cannot boot from exFAT). Ensure there is **no** `FWUP0019.DAT` or other boot files in the root directory.
3. Copy the locally built `out_r9/sd_fastboot/ffinit.bin` and `out_r9/sd_fastboot/ffboot.bin` **together** to the SD card root (do not rename) and run `python verify_release.py <SD_card_path>`.
4. Insert the card, **press and hold Rear Command Dial (click in) + `Fn1` while switching power `ON`**; Hardened R9 boots into Liveview in ~3 seconds (you may release the buttons once Liveview appears).
5. To return to stock firmware: **power off normally**, remove the SD card (or delete `ffinit.bin` & `ffboot.bin`), and power on normally — 100% stock X-T3.

### Method B (High Risk): Permanent Flash via `FWUP0019.DAT`
Only proceed after testing Method A and understanding the risks:

1. Use a **fully charged genuine battery**, back up all settings/C1–C7, and keep official Stock 5.11 ready.
2. Copy `out_r9/firmware_dat/FWUP0019.DAT` to the root of a clean SD card (**Slot 1**). **Keep the exact filename `FWUP0019.DAT`** (X-T3 ignores renamed files like `FWUP0019 (1).DAT`), ensure no other `.DAT` files exist, and run `verify_release.py`.
3. **Hold `DISP/BACK` while switching power `ON`** to open Fujifilm's firmware updater.
4. **Same-version 5.11 note**: If your camera is already running Stock `5.11`, Fujifilm's updater normally blocks a `5.11 → 5.11` same-version flash (requires upgrading from an earlier version or using an appropriate same-version workflow).
5. **Never power off, remove the battery/card, or press buttons** while flashing until the camera confirms completion.

---

## 6. Verification Records & Credits
- Detailed R4 → R9 changelog and 12-axis independent offline acceptance report (`FINAL_ACCEPTANCE_R9_PASSED`): [docs/CHANGELOG_AND_VERIFICATION.md](docs/CHANGELOG_AND_VERIFICATION.md).
- Pure-Python FFLZ codec inside `build_r9.py` follows [tiredboffin/fffw](https://github.com/tiredboffin/fffw) (MIT License).
