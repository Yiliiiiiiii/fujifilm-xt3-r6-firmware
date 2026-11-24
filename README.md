# Fujifilm X-T3 Hardened R6 Patcher (based on Stock 5.11)

> ⚠️ **免责声明与版权合规说明 / DISCLAIMER & COPYRIGHT NOTICE**
>
> - 本仓库与 Release **不包含任何富士胶片（FUJIFILM）原厂固件二进制文件**，仅提供约 **94 KB** 的纯 XOR 差分补丁（`r6_stock511.x3p`）与零依赖 Python 本地合成脚本（`build_r6.py`）。用户需自行前往富士官网下载官方原厂 X-T3 5.11 固件 `FWUP0019.DAT`，在自己电脑上本地还原全部测试包与固件文件。
> - 本项目为非官方社区研究与个人折腾产物，与 FUJIFILM Corporation 没有任何关联。刷写第三方修改固件存在**机身变砖、数据丢失及失去官方保修**的风险。**强烈建议先使用零刷机的 SD 快启动测试包在自己机身上体验验证**，并在任何刷写前做好个人设置备份与满电保障。使用本项目产生的一切风险由使用者自行承担。
>
> *No proprietary Fujifilm firmware binaries are hosted in this repository or its Releases. Only a 94 KB pure XOR-delta patch (`r6_stock511.x3p`) and a zero-dependency Python 3 local builder (`build_r6.py`) are distributed. Download official Fujifilm X-T3 5.11 `FWUP0019.DAT` directly from Fujifilm's website and build locally. Use strictly at your own risk.*

---

## 一、三步本地一键合成（Windows / macOS / Linux 通用，零依赖）

只需要 **Python 3**（无需安装任何第三方库）：

### 第 1 步：从富士官网下载官方原厂 X-T3 5.11 固件
前往富士官方支持页面下载 **X-T3 Ver.5.11** 固件 `FWUP0019.DAT`：
- 官方页面：https://www.fujifilm-x.com/global/support/download/firmware/cameras/x-t3/
- 核对输入文件大小：`50,136,252 B`，SHA-256：`9f2c75fd8a16a1d71b9218f6dbd3144b1f11820bcecd3a9608c8cda9f25f95a3`（脚本会自动校验）。

### 第 2 步：下载本仓库的差分补丁工具包
前往右侧 **[Releases](https://github.com/Yiliiiiiiii/fujifilm-xt3-r6-firmware/releases)** 下载 `v1.0.0-r6` 补丁包（仅 **~100 KB**），或直接克隆本仓库：

```bash
git clone https://github.com/Yiliiiiiiii/fujifilm-xt3-r6-firmware.git
cd fujifilm-xt3-r6-firmware
```

### 第 3 步：一键本地生成并自动校验 SHA-256

```bash
# 同时生成「零刷机 SD 快启动测试包」+「正式刷机包 FWUP0019.DAT」（约 12 秒）
python build_r6.py /path/to/official_511_FWUP0019.DAT -o out_r6

# 如果只想先体验零刷机 SD 快启动测试包（约 2 秒完成）
python build_r6.py /path/to/official_511_FWUP0019.DAT -o out_r6 --sd-only
```

生成完成后会在 `out_r6/` 下得到并自动校验以下文件（100% 逐字节匹配已验证的 Hardened R6 哈希）：

| 本地生成路径 | 用途 | 字节数 | 锁定 SHA-256 |
| --- | --- | ---: | --- |
| `out_r6/sd_fastboot/ffinit.bin` | **零刷机 SD 快启动测试包**（与 `ffboot.bin` 配对） | `40,808` | `a218eca392f6d1a645ff1e8388dada4325a9b0a8bb30a3ffc75d7429b8085983` |
| `out_r6/sd_fastboot/ffboot.bin` | **零刷机 SD 快启动测试包**（纯内存运行，拔卡即回原厂） | `30,937,088` | `d4bc67e9ca10f25e45c60845be8d7e22ad0264bb8cb0f1186a9f3695a589225b` |
| `out_r6/firmware_dat/FWUP0019.DAT` | **Hardened R6 正式固件包**（主校验和 `@0x20C = 0xad1e4ed5`） | `50,136,252` | `59658c432421b60d986d1815d50a685d078ebc5222647ea140572d0f979f08a0` |

> 将文件复制到 SD 卡后，可随时运行 `python verify_release.py E:\`（替换为你的 SD 卡盘符）二次核对卡内文件完整性。

---

## 二、相比原厂 X-T3 5.11 的核心新增功能

| 功能模块 | Hardened R6 实现内容 |
| --- | --- |
| **新增 4 款后期胶片模拟**（共 20 款可用） | 新增 **Classic Neg. (NC)**、**ETERNA Bleach Bypass (BB)**、**Nostalgic Neg. (NN)**、**REALA ACE (RA)**；完整接入主菜单、Q 菜单、胶片包围、C1–C7、EXIF MakerNote 及机内 RAW 转换（RA 含 3D D3 LUT 与 DMA 合并更新，NN 含完整 40 点曲线与 76B 扩展色彩记录） |
| **双优先自动白平衡（WA / AA）** | 移植 X-T4 **白色优先（WA）** / **氛围优先（AA）** 双优先比值算法与静态捕获环；支持独立 R/B 白平衡漂移、AE-L/AWB-L、35 语言菜单与 14 组原生图标、**全部 6 路取景 HUD**、**全部 6 路回放 INFO 图标**、MakerNote `0x1002` 与 RAF 字段写入、**机内 RAW 转换手选及“反映拍摄条件”自动闭环** |
| **全系列静态胶片 0.5 档高光 / 阴影** | 原厂全部静态胶片 + 新增 4 款移植胶片（底层全 23 个静态胶片枚举）全部解锁 **−2 ~ +4 共 13 档（含 `±0.5 / ±1.5 / +2.5 / +3.5`）**；原厂胶片采用 124 B 常驻 50/50 实时混合算法（对比原厂 X-T4 误差 `≤ 1 LSB`）；完整打通主菜单、Q 菜单、C1–C7、EXIF `0x1040`/`0x1041`、PTP、**全部 4 路回放 INFO 页 `±0.5` 显示**与**机内 RAW“反映拍摄条件”向 0 对称归整** |
| **彩色铬蓝 ** | **Color Chrome FX Blue**（关 / 弱 / 强，与原厂色彩效果形成 3×3 正交组合，支持 C1–C7 保存与菜单复位）； |

### 明确未列入范围与安全隔离边界
- **未包含功能**：清晰度（Clarity）、F-Log View Assist / F-Log2、黑白第二色轴（暖冷调）、HDR / 多重曝光、X-T4 式的 C1–C7 自动覆盖更新（保留 X-T3 原生手动保存机制）。
- **刻意隔离设计**：**视频模式（Movie）** 严格隔离 WA/AA 与静态 0.5 档，保持原厂视频稳定性；**机内 RAW 手动菜单**高光/阴影列表保持原厂整数项不混入半档。

---

## 三、上机使用指南（强烈建议先走方式 A 零刷机体验）

### 方式 A（强烈推荐）：SD 快启动测试包（零刷机、纯内存运行）
此方式**完全不改写机身闪存**，最适合零风险先在自己机身上体验全部 R6 功能：

1. 先用官方 **FUJIFILM X RAW Studio** 或 **X Acquire** 通过 USB 备份你的个人机身设置。
2. 准备一张 **MBR + FAT32** 格式的干净 SD 卡（插在**卡槽 1**，**卡槽 2 留空**，拔掉 USB 线；若使用 64GB 及以上 SDXC 大卡，需先在电脑上划分一个 `≤ 32 GB` 的 FAT32 分区，因为 X-T3 Boot ROM 不支持从 exFAT 引导），确保根目录**没有**旧的 `FWUP0019.DAT` 或其它引导文件。
3. 将本地生成的 `out_r6/sd_fastboot/ffinit.bin` 与 `out_r6/sd_fastboot/ffboot.bin` **配对复制到 SD 卡根目录**（切勿改名），并运行 `python verify_release.py <SD卡路径>` 核对哈希。
4. 插卡后，**按住「后指令拨盘（按下）+ `Fn1`」不松手，同时将电源开关拨至 `ON`**，约 **3 秒**即从 SD 卡加载 Hardened R6 进入取景画面（加载进入画面后即可松手）。
5. 如需恢复原厂系统：**正常关机**，拔出 SD 卡或删除根目录的 `ffinit.bin`、`ffboot.bin`，重新正常开机即 100% 回到机身原厂固件。

### 方式 B（高风险）：正式刷写机身固件 `FWUP0019.DAT`
仅建议在**已完成方式 A 零刷机实测**、且明确理解刷机风险的前提下操作：

1. **刷前必备**：使用**满电原装电池**；提前做好个人机身设置与 C1–C7 备份；准备好官方原厂 5.11 恢复方案。
2. 将本地生成的 `out_r6/firmware_dat/FWUP0019.DAT` 复制到干净 SD 卡（**卡槽 1**）根目录——**切勿改名**（X-T3 固件更新器只精确识别 `FWUP0019.DAT`，诸如 `FWUP0019 (1).DAT` 等改名均无法识别），确保无其它 `.DAT` 文件，并对卡内文件再次运行 `verify_release.py` 核对哈希。
3. **按住 `DISP/BACK` 键不放的同时拨动电源开关至 `ON`**，进入官方固件更新界面。
4. **关于原厂 5.11 同版本提示**：若机身当前已经是原厂 `5.11`，原版更新程序通常会拒绝 `5.11 → 5.11` 同版本直接刷写（需从低于 5.11 版本升级，或配合相应同版本合法引导流程）。
5. 写入过程中**绝对不要关机、拔电池、拔卡或操作按键**，直至机身提示升级完成并正常关机重启。

---

## 四、技术验证记录与致谢
- 详细 R4 → R5 → R6 演进说明与 10 轴离线独立验收摘要见：[docs/CHANGELOG_AND_VERIFICATION.md](docs/CHANGELOG_AND_VERIFICATION.md)。
- `build_r6.py` 内置的纯 Python FFLZ 编解码器参考开源项目 [tiredboffin/fffw](https://github.com/tiredboffin/fffw)（MIT License）。
