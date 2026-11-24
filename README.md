# Fujifilm X-T3 Hardened R6 Custom Firmware (based on Stock 5.11)

> ⚠️ **免责声明 / IMPORTANT DISCLAIMER**
>
> 本项目为非官方社区研究与个人折腾产物，与 FUJIFILM Corporation 没有任何关联。刷写第三方修改固件存在**机身变砖、数据丢失及失去官方保修**的风险。**强烈建议先使用零刷机的 SD 快启动测试包在自己机身上充分体验验证**，并在任何刷写前做好原厂设置备份与满电供电保障。使用本项目产生的一切风险与后果由使用者自行承担。
>
> *Unofficial community firmware modification for Fujifilm X-T3 (based on Stock 5.11). Not affiliated with FUJIFILM. Flashing carries bricking risk — ALWAYS test with the zero-flash SD Fast-Boot Test Package first and back up your camera settings before flashing. Use strictly at your own risk.*

---

## 一、下载 Release 成品包 / Download

请前往本仓库右侧 **[Releases](https://github.com/Yiliiiiiiii/fujifilm-xt3-r6-firmware/releases)** 页面下载最新 **`v1.0.0-r6`** 附件：

| 发布附件 | 用途 | 大小 | SHA-256 |
| --- | --- | ---: | --- |
| `XT3_Hardened_R6_SD_FastBoot_Test.zip` | **零刷机 SD 快启动测试包**（含配对 `ffinit.bin` + `ffboot.bin`，纯内存运行，拔卡即恢复原厂） | 10.25 MB | `d8b2918031db248cdadbf84cafde9b1f10bafe1134e5e2b4ad2768139405f5db` |
| `XT3_Hardened_R6_Firmware_DAT.zip` | **Hardened R6 固件包**（含 `FWUP0019.DAT`，主校验和 `@0x20C = 0xad1e4ed5`） | 16.75 MB | `04904052926e16c90f339ff132d315ed55225d9d2ff4509fe07b881f14e5542c` |
| `SHA256SUMS.txt` | 压缩包与解压后全部二进制文件 SHA-256 校验清单 | — | 见仓库根目录 [SHA256SUMS.txt](SHA256SUMS.txt) |

---

## 二、相比原厂 X-T3 5.11 的核心新增功能

| 功能模块 | Hardened R6 实现内容 |
| --- | --- |
| **新增 4 款后期胶片模拟**（共 20 款可用） | 新增 **Classic Neg. (NC)**、**ETERNA Bleach Bypass (BB)**、**Nostalgic Neg. (NN)**、**REALA ACE (RA)**；完整接入主菜单、Q 菜单、胶片包围、C1–C7、EXIF MakerNote 及机内 RAW 转换（RA 含 3D D3 LUT 与 DMA 合并更新，NN 含完整 40 点曲线与 76B 扩展色彩记录） |
| **双优先自动白平衡（WA / AA）** | 移植 X-T4 **白色优先（WA）** / **氛围优先（AA）** 双优先比值算法与静态捕获环；支持独立 R/B 白平衡漂移、AE-L/AWB-L、35 语言菜单与 14 组原生图标、**全部 6 路取景 HUD**、**全部 6 路回放 INFO 图标**、MakerNote `0x1002` 与 RAF 字段写入、**机内 RAW 转换手选及“反映拍摄条件”自动闭环** |
| **全系列静态胶片 0.5 档高光 / 阴影** | 原厂全部静态胶片 + 新增 4 款移植胶片（底层全 23 个静态胶片枚举）全部解锁 **−2 ~ +4 共 13 档（含 `±0.5 / ±1.5 / +2.5 / +3.5`）**；原厂胶片采用 124 B 常驻 50/50 实时混合算法（对比原厂 X-T4 误差 `≤ 1 LSB`）；完整打通主菜单、Q 菜单、C1–C7、EXIF `0x1040`/`0x1041`、PTP、**全部 4 路回放 INFO 页 `±0.5` 显示**与**机内 RAW“反映拍摄条件”向 0 对称归整** |
| **彩色铬蓝 + 大颗粒** | **Color Chrome FX Blue**（关 / 弱 / 强，与原厂色彩效果形成 3×3 正交组合，支持 C1–C7 保存与菜单复位）；**大颗粒效果**（强/弱 × 大/小 共 5 态） |
| **C1–C7 独立白平衡漂移** | 彻底终结 X-T3 原厂 C1–C7 共用同一组白平衡漂移的痛点，每个自定义槽位独立保存、恢复与复制 R/B 偏移；完整兼容富士官方 USB 备份与恢复（`X RAW Studio` / `X Acquire`） |

### 明确未列入范围与安全隔离边界
- **未包含功能**：清晰度（Clarity）、F-Log View Assist / F-Log2、黑白第二色轴（暖冷调）、HDR / 多重曝光、X-T4 式的 C1–C7 自动覆盖更新（保留 X-T3 原生手动保存机制）。
- **刻意隔离设计**：**视频模式（Movie）** 严格隔离 WA/AA 与静态 0.5 档，保持原厂视频稳定性；**机内 RAW 手动菜单**高光/阴影列表保持原厂整数项不混入半档。

---

## 三、使用指南（强烈建议先走步骤 1 零刷机体验）

### 准备：校验文件完整性
下载 Release 文件后，运行仓库自带的零依赖校验脚本（同时校验 ZIP 与解压后的文件）：

```bash
python verify_release.py /path/to/downloaded_files
```

解压后二进制文件必须严格匹配以下字节数与 SHA-256：

| 文件名 | 字节数 | SHA-256 |
| --- | ---: | --- |
| `ffinit.bin` | `40,808` | `a218eca392f6d1a645ff1e8388dada4325a9b0a8bb30a3ffc75d7429b8085983` |
| `ffboot.bin` | `30,937,088` | `d4bc67e9ca10f25e45c60845be8d7e22ad0264bb8cb0f1186a9f3695a589225b` |
| `FWUP0019.DAT` | `50,136,252` | `59658c432421b60d986d1815d50a685d078ebc5222647ea140572d0f979f08a0` |

---

### 步骤 1（推荐）：SD 快启动测试包（零刷机、纯内存运行）
此方式**完全不改写机身闪存**，非常适合先在自己机身上体验全部 R6 功能：

1. 先用官方 **FUJIFILM X RAW Studio** 或 **X Acquire** 通过 USB 备份你的机身设置。
2. 准备一张干净的 FAT32 / exFAT SD 卡（插在**卡槽 1**），确保根目录**没有**旧的 `FWUP0019.DAT` 或其它引导文件。
3. 将 `XT3_Hardened_R6_SD_FastBoot_Test.zip` 解压出的**配对文件** `ffinit.bin` 和 `ffboot.bin` 同时复制到 SD 卡根目录，并在卡上再次核对 SHA-256。
4. 插卡后**直接正常拨动电源开关至 `ON`**（无需按任何组合键），约 **3 秒**即从 SD 卡加载 Hardened R6 进入取景画面。
5. 如需恢复原厂固件：**正常关机**，拔出 SD 卡或删除根目录的 `ffinit.bin`、`ffboot.bin`，重新开机即 100% 回到机身原厂系统。

---

### 步骤 2（高风险）：正式刷写机身固件 `FWUP0019.DAT`
仅建议在**已完成步骤 1 零刷机实测**、且明确理解刷机风险的前提下操作：

1. **刷前必备**：
   - 使用**满电原装电池**；
   - 已用官方软件做好个人机身设置与 C1–C7 备份；
   - 提前准备好官方原厂 5.11 恢复材料。
2. 将 `XT3_Hardened_R6_Firmware_DAT.zip` 解压得到的 `FWUP0019.DAT` 复制到干净 SD 卡（**卡槽 1**）根目录，确认根目录无其它 `.DAT` 文件，并对卡内文件再次运行 `verify_release.py` 校验哈希。
3. **按住 `DISP/BACK` 键不放的同时拨动电源开关至 `ON`**，进入官方固件更新确认页面。
4. **关于原厂 5.11 同版本提示**：若你的机身当前已经是原厂 `5.11`，原版更新程序可能会阻止 `5.11 → 5.11` 同版本直接刷写（需从低于 5.11 的版本升级，或搭配对应版本的合法更新引导流程）。
5. 写入过程中**绝对不要关机、拔电池、拔卡或操作按键**，直至机身提示升级完成并正常关机重启。

---

## 四、技术验证记录

详细 R4 → R5 → R6 演进说明、补丁归因与 10 轴离线独立验收摘要请参阅：[docs/CHANGELOG_AND_VERIFICATION.md](docs/CHANGELOG_AND_VERIFICATION.md)。
