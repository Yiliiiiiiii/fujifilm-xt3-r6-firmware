# Fujifilm X-T3 Hardened R9 Patcher (based on Stock 5.11)

**中文** | [English](README_EN.md)

> ⚠️ **免责声明与版权合规说明 / DISCLAIMER & COPYRIGHT NOTICE**
>
> - 本仓库与 Release **不包含任何富士胶片（FUJIFILM）原厂固件二进制文件**，仅提供约 **96 KB** 的纯 XOR 差分补丁（`r9_stock511.x3p`）与零依赖 Python 本地合成脚本（`build_r9.py`）。用户需自行前往富士官网下载官方原厂 X-T3 5.11 固件 `FWUP0019.DAT`，在自己电脑上本地还原全部测试包与固件文件。
> - 本项目为非官方社区研究与个人折腾产物，与 FUJIFILM Corporation 没有任何关联。刷写第三方修改固件存在**机身变砖、数据丢失及失去官方保修**的风险。**强烈建议先使用零刷机的 SD 快启动测试包在自己机身上体验验证**，并在任何刷写前做好个人设置备份与满电保障。使用本项目产生的一切风险由使用者自行承担。
>
> *No proprietary Fujifilm firmware binaries are hosted in this repository or its Releases. Only a 96 KB pure XOR-delta patch (`r9_stock511.x3p`) and a zero-dependency Python 3 local builder (`build_r9.py`) are distributed. Download official Fujifilm X-T3 5.11 `FWUP0019.DAT` directly from Fujifilm's website and build locally. Use strictly at your own risk.*

---

## 一、三步本地一键合成（Windows / macOS / Linux 通用，零依赖）

只需要 **Python 3**（无需安装任何第三方库）：

### 第 1 步：从富士官网下载官方原厂 X-T3 5.11 固件
前往富士官方支持页面下载 **X-T3 Ver.5.11** 固件 `FWUP0019.DAT`：
- 官方页面：https://www.fujifilm-x.com/global/support/download/firmware/cameras/x-t3/
- 核对输入文件大小：`50,136,252 B`，SHA-256：`9f2c75fd8a16a1d71b9218f6dbd3144b1f11820bcecd3a9608c8cda9f25f95a3`（脚本会自动校验）。

### 第 2 步：下载本仓库的差分补丁工具包
前往右侧 **[Releases](https://github.com/Yiliiiiiiii/fujifilm-xt3-r6-firmware/releases)** 下载最新版 **`v1.1.0-r9`** 补丁包（仅 **~110 KB**），或直接克隆本仓库：

```bash
git clone https://github.com/Yiliiiiiiii/fujifilm-xt3-r6-firmware.git
cd fujifilm-xt3-r6-firmware
```

### 第 3 步：一键本地生成并自动校验 SHA-256

```bash
# 同时生成「零刷机 SD 快启动测试包」+「正式刷机包 FWUP0019.DAT」（约 12 秒）
python build_r9.py /path/to/official_511_FWUP0019.DAT -o out_r9

# 如果只想先体验零刷机 SD 快启动测试包（约 2 秒完成）
python build_r9.py /path/to/official_511_FWUP0019.DAT -o out_r9 --sd-only
```

生成完成后会在 `out_r9/` 下得到并自动校验以下文件（100% 逐字节匹配已验证的 Hardened R9 哈希）：

| 本地生成路径 | 用途 | 字节数 | 锁定 SHA-256 |
| --- | --- | ---: | --- |
| `out_r9/sd_fastboot/ffinit.bin` | **零刷机 SD 快启动测试包**（与 `ffboot.bin` 配对） | `40,808` | `1b83b4547eac786b9ab062b6e0bb56438f06cae58d479ac1246ff7633b76414f` |
| `out_r9/sd_fastboot/ffboot.bin` | **零刷机 SD 快启动测试包**（纯内存运行，拔卡即回原厂） | `30,937,088` | `27c5e6596bfdaeaec7c6a129da32a99662908138c5c2d8f3fdbbeaf517ceac2a` |
| `out_r9/firmware_dat/FWUP0019.DAT` | **Hardened R9 正式固件包**（主校验和 `@0x20C = 0xad0ead23`） | `50,136,252` | `d4e8950d61915d7716c2b408783b35d7e831084f70e8f1507dd9793cfb90cfb9` |

> 将文件复制到 SD 卡后，可随时运行 `python verify_release.py E:\`（替换为你的 SD 卡盘符）二次核对卡内文件完整性。

---

## 二、Hardened R9 相比 R6 的重点修复（均已实机验证）

- **R7 — Q 菜单半档高光/阴影原生矢量图标 + Liveview 取景白平衡所见即所得**：
  - 新增 6 组 `80×48` 原生 GVFF 矢量图标（`0xFF00200E..0xFF002013`），彻底修复 Q 菜单 16 宫格下半档高光/阴影（`+3.5 / +2.5 / +1.5 / +0.5 / -0.5 / -1.5`）空白问题。
  - 打通 Liveview 取景 AE/AWB 分发、ISP 显示选择器及实时优先增益缩放，WA/AA 取景画面与成片所见即所得，多帧零 IIR 漂移。
- **R8 — 修复 WA/AA 半按锁白平衡回退日光 & 保留单机出厂 EEPROM 白平衡校准**：
  - 修复 S1 半按锁定白平衡（`0x0115E048` / `0x01E52804`）未包含 WA/AA 导致成片偏冷/回退日光预设的问题。
  - 恢复原厂单机 EEPROM 增益表读取（`0x011B1FE0` / `0x011B201C`），避免不同机身个体白平衡基准漂移；实机 RAF 验证 Auto / WA / AA 与算法理论值 `0-LSB` 吻合。
- **R9 — 修复 Classic Neg. (NC) 与 Eterna Bleach Bypass (EB) 曲线库选错导致成片偏暗 1 档及 DR100 H/S 失效**：
  - 修复静态取景配置（40 个 `0x01F5BD34 == 0` 配置）误选 X-T4 无 2x/4x 提亮的 1x Bank 1 曲线库，导致 NC / EB 在 **DR200 偏暗 `-1.00 EV`**、**DR400 偏暗 `-1.80 EV`**、**DR100 高光/阴影微调失效**的问题。
  - 补齐 Bank 2 缺失的全部 8 个 **D 范围优先级（DRP）** 曲线（消除 `+1.00 EV` 过曝）、补齐 `gcls=2/4` 选择项与 DRP 分段点 `27`，并修复关闭曝光预览/自然实时取景下 NC/EB 丢失半档 H/S 的问题。
  - 与原生 X-T4 Bank 0（`0x02084E40`）达成 **`1,200/1,200` 逐点 0-LSB 完全一致**；**F-Log / HLG 及视频模式零负面影响**，NN / RA 与全部原厂胶片零回归。

---

## 三、相比原厂 X-T3 5.11 的核心新增功能汇总

| 功能模块 | Hardened R9 实现内容 |
| --- | --- |
| **新增 4 款后期胶片模拟**（共 20 款可用） | 新增 **Classic Neg. (NC)**、**ETERNA Bleach Bypass (EB/BB)**、**Nostalgic Neg. (NN)**、**REALA ACE (RA)**；完整接入主菜单、Q 菜单、胶片包围、C1–C7、EXIF MakerNote 及机内 RAW 转换；NC/EB 全 DR100/200/400/DRP 曲线与原生 X-T4 Bank 0 0-LSB 对齐，RA 含 3D D3 LUT 与 DMA 合并更新，NN 含完整 40 点曲线与 76B 扩展色彩记录 |
| **双优先自动白平衡（WA / AA）** | 移植 X-T4 **白色优先（WA）** / **氛围优先（AA）** 双优先比值算法（保留单机出厂 EEPROM 校准）、Liveview 实时取景所见即所得与静态捕获环；支持独立 R/B 白平衡漂移、S1 半按 & AE-L/AWB-L、35 语言菜单与 20 组原生 GVFF 图标、**全部 6 路取景 HUD**、**全部 6 路回放 INFO 图标**、MakerNote `0x1002` 与 RAF 字段写入、**机内 RAW 转换手选及“反映拍摄条件”自动闭环** |
| **全系列静态胶片 0.5 档高光 / 阴影** | 原厂全部静态胶片 + 新增 4 款移植胶片（底层全 23 个静态胶片枚举）全部解锁 **−2 ~ +4 共 13 档（含 `±0.5 / ±1.5 / +2.5 / +3.5`）**；原厂胶片采用 124 B 常驻 50/50 实时混合算法（对比原厂 X-T4 误差 `≤ 1 LSB`）；完整打通主菜单、**Q 菜单 26/26 原生矢量图标渲染**、C1–C7、EXIF `0x1040`/`0x1041`、PTP、**全部 4 路回放 INFO 页 `±0.5` 显示**与**机内 RAW“反映拍摄条件”向 0 对称归整** |
| **彩色铬蓝** | **Color Chrome FX Blue**（关 / 弱 / 强，与原厂色彩效果形成 3×3 正交组合，支持 C1–C7 保存与菜单复位） |

### 明确未列入范围与安全隔离边界
- **未包含功能**：清晰度（Clarity）、F-Log View Assist / F-Log2、黑白第二色轴（暖冷调）、HDR / 多重曝光、X-T4 式的 C1–C7 自动覆盖更新（保留 X-T3 原生手动保存机制）。
- **刻意隔离设计**：**视频模式（Movie）** 严格隔离 WA/AA 与静态 0.5 档，F-Log/HLG 直接走原厂路径，保持原厂视频稳定性；**机内 RAW 手动菜单**高光/阴影列表保持原厂整数项不混入半档。

---

## 四、色彩与算法来源透明度说明（哪些是 100% 原厂迁移，哪些是拟合）

### 1. 新增 4 款胶片模拟：3 款全链路 100% 原厂无损迁移，仅 RA 的 3D LUT 做了高精度网格拟合

| 胶片模拟 | 18B 3×3 色彩矩阵 & 8B 参数 | 辅助色相块 | 色调 / 伽马曲线（含半档） | D3 3D LUT（核心色彩表） | 彩色铬 / 彩色铬蓝 (3×3) |
| --- | --- | --- | --- | --- | --- |
| **Classic Neg. (NC)** | **100% 原厂迁移**<br>（X-T4 / X-S20 逐字节一致） | **100% 原厂迁移** | **100% 原厂迁移**<br>（与 X-T4 Bank 0 `0-LSB` 一致） | **100% 一致（原生关闭）**<br>（原厂 X-T4/X-S20/GFX 在 NC 下均不启用） | FX Blue 弱/强 **100% 原厂迁移**；关时沿用 X-T3 原厂彩色铬 |
| **ETERNA Bleach Bypass (EB)** | **100% 原厂迁移**<br>（X-T4 / X-S20 逐字节一致） | **100% 原厂迁移** | **100% 原厂迁移**<br>（与 X-T4 Bank 0 `0-LSB` 一致） | **100% 无损迁移**<br>（X-T4 / GFX100S / GFX50SII 原厂 `16³` 表，`0-LSB` 精确还原） | 同上 |
| **Nostalgic Neg. (NN)** | **100% 原厂迁移**<br>（取自同传感器 X-Trans IV 的 **X-S20**） | **100% 原厂迁移** | **100% 原厂迁移**<br>（原厂 40 点半档曲线表） | **100% 无损迁移**<br>（GFX100S / GFX50SII 原厂 `16³` 表，`0-LSB` 精确还原） | 同上 |
| **REALA ACE (RA)** | **100% 原厂迁移**<br>（取自同传感器 X-Trans IV 的 **X-S20 3.30**） | **100% 原厂迁移** | **100% 原厂迁移**<br>（X-S20 原厂 DR100/200/400/DRP 半档曲线） | **最小二乘网格拟合**<br>（X-S20 原厂 `17³` → X-T3 硬件 `16³`） | **9/9 100% 原厂迁移**<br>（含“关/关”下 RA 原厂色彩塑形行，取自 X-S20） |

- **关于 REALA ACE (RA) 的 D3 3D LUT 网格拟合说明**：
  - REALA ACE 仅存在于第五代处理器（X-Processor 5，如 X-S20）固件中，其硬件 3D LUT 为 **`17×17×17`** 网格；而 X-T3（X-Processor 4）硬件 ISP 寄存器固定只接收 **`16×16×16`**（32 KB）网格，物理上无法直接写入 `17³` 原表。
  - 本固件对 X-S20 原厂 `17³` 表在全域 RGB 空间采用**高斯求积最小二乘优化**求解最优 `16³` 节点，并强制锚定全部 **8 个色域顶点与完整中性灰轴（`R=G=B` 零偏色）**。
  - 在 `373,248` 个独立 12-bit（`0..4095`）RGB 采样点上对比 X-S20 原厂 `17³` 三线性输出：**平均误差仅 `1.72 / 4095`（`0.042%`，约 8-bit 下 `0.11` 级，肉眼不可分辨）**，P95 误差 `6.86 / 4095`（`0.17%`），P99 误差 `17.38 / 4095`（`0.42%`），极端高饱和拐点峰值 `119.08 / 4095`（`2.9%`）。
- **关于原厂 19 款老胶片的 0.5 档高光 / 阴影**：
  - 新增 4 款胶片（NC / EB / NN / RA）直接使用原厂 4 锚点/权重插值引擎（`0-LSB`）；原厂 19 款胶片采用相邻整数档 `(a + b + 1) >> 1` 50/50 实时混合，对比原生 X-T4 全 16 组 × 6 档 DR × 6 半档共 `23,040` 个控制点，**最大偏差 `≤ 1 LSB`（`92.7%` 零误差、零直流偏置）**。

### 2. 新增双优先自动白平衡（WA 白色优先 / AA 氛围优先）来源说明
- **算法来源：原生 Fujifilm X-T4 原厂双优先比值算法（`0-LSB` 无损提取，零近似）**。
  - 从官方 X-T4 固件白平衡优先核心函数精确提取全部色温坐标（`coord ∈ [120..174]`，区间外饱和与 X-T4 一致）对应的**既约精确有理数分子/分母比值表**（`566 B`，置于 `0x0150C400`），通过 X-T3 CPU 原生 ARMv7-A `UDIV` 指令按精确比例缩放 R/B 增益。
- **单机出厂白平衡校准保留（不破坏个体机身色准）**：
  - 优先缩放直接叠加在 **X-T3 原生 Auto AWB 结果**之上，**完整保留原厂单机出厂 EEPROM 白平衡校准表入口**（`0x011B1FE0` / `0x011B201C` → `0x01841800`），绝不用静态 X-T4 标定表覆盖你机身的出厂个体校准。
  - 同一套精确比值同时驱动 **Liveview 实时取景（多帧零 IIR 漂移）**、**静态拍摄 / S1 半按与 AWB-L 锁定**、**RAF 双增益元数据（`0xF013`/`0xF014`）**及 **X-T4 规范 MakerNote `0x1002`（`0x0001` / `0x0002`）**，实机拍摄 RAF 核对与理论值 **0-LSB 完全吻合**。

---

## 五、上机使用指南（强烈建议先走方式 A 零刷机体验）

### 方式 A（强烈推荐）：SD 快启动测试包（零刷机、纯内存运行）
此方式**完全不改写机身闪存**，最适合零风险先在自己机身上体验全部 R9 功能：

1. 先用官方 **FUJIFILM X RAW Studio** 或 **X Acquire** 通过 USB 备份你的个人机身设置。
2. 准备一张 **MBR + FAT32** 格式的干净 SD 卡（插在**卡槽 1**，**卡槽 2 留空**，拔掉 USB 线；若使用 64GB 及以上 SDXC 大卡，需先在电脑上划分一个 `≤ 32 GB` 的 FAT32 分区，因为 X-T3 Boot ROM 不支持从 exFAT 引导），确保根目录**没有**旧的 `FWUP0019.DAT` 或其它引导文件。
3. 将本地生成的 `out_r9/sd_fastboot/ffinit.bin` 与 `out_r9/sd_fastboot/ffboot.bin` **配对复制到 SD 卡根目录**（切勿改名），并运行 `python verify_release.py <SD卡路径>` 核对哈希。
4. 插卡后，**按住「后指令拨盘（按下）+ `Fn1`」不松手，同时将电源开关拨至 `ON`**，约 **3 秒**即从 SD 卡加载 Hardened R9 进入取景画面（加载进入画面后即可松手）。
5. 如需恢复原厂系统：**正常关机**，拔出 SD 卡或删除根目录的 `ffinit.bin`、`ffboot.bin`，重新正常开机即 100% 回到机身原厂固件。

### 方式 B（高风险）：正式刷写机身固件 `FWUP0019.DAT`
仅建议在**已完成方式 A 零刷机实测**、且明确理解刷机风险的前提下操作：

1. **刷前必备**：使用**满电原装电池**；提前做好个人机身设置与 C1–C7 备份；准备好官方原厂 5.11 恢复方案。
2. 将本地生成的 `out_r9/firmware_dat/FWUP0019.DAT` 复制到干净 SD 卡（**卡槽 1**）根目录——**切勿改名**（X-T3 固件更新器只精确识别 `FWUP0019.DAT`，诸如 `FWUP0019 (1).DAT` 等改名均无法识别），确保无其它 `.DAT` 文件，并对卡内文件再次运行 `verify_release.py` 核对哈希。
3. **按住 `DISP/BACK` 键不放的同时拨动电源开关至 `ON`**，进入官方固件更新界面。
4. **关于原厂 5.11 同版本提示**：若机身当前已经是原厂 `5.11`，原版更新程序通常会拒绝 `5.11 → 5.11` 同版本直接刷写（需从低于 5.11 版本升级，或配合相应同版本合法引导流程）。
5. 写入过程中**绝对不要关机、拔电池、拔卡或操作按键**，直至机身提示升级完成并正常关机重启。

---

## 六、技术验证记录与致谢
- 详细 R4 → R9 演进说明与 12 轴离线独立验收摘要见：[docs/CHANGELOG_AND_VERIFICATION.md](docs/CHANGELOG_AND_VERIFICATION.md)。
- `build_r9.py` 内置的纯 Python FFLZ 编解码器参考开源项目 [tiredboffin/fffw](https://github.com/tiredboffin/fffw)（MIT License）。
