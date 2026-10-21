# 阶段五之一：驱动

> **以下设备名单是一台 Lenovo ThinkBook 14 G7+ IAH (21TK) 的实测样例，仅供参照。** 请按 `references/01-preflight.md` 事实 6 普查你自己机器的设备，切勿照抄厂商与型号。

**方法**：绝大多数驱动不用手动装。真正需要自己处理的按「A 类装完自动补齐 / B 类厂商专属必须手动装 / C 类随应用软件自动带回」三分法归类。

下表为**示例机器**的实测统计：第三方驱动设备共 **61 个**（摘要逐项列出 58 项，另有 3 项 Intel 同族设备未单列）：

| 类别 | 数量 | 处置 |
| --- | --- | --- |
| A 自动补齐 | 32（摘要） | 安装介质 driver store 自带 + Windows Update 补 WHQL |
| B 联想专属，必须手动装 | 21 | 不在 WU 分发范围，只能从联想官网取 |
| C 装应用时自动带回 | 5 | VMware VMnet1/8/VMCI（3）、iNode 虚拟网卡（1）、TAP-Windows V9（1） |

## A 类：自动补齐，不用管（32 项）

安装介质自带 driver store，联网后 Windows Update 再补 WHQL 驱动。

| 厂商 / 组 | 设备（实测） | 数量 |
| --- | --- | --- |
| Intel 芯片组 | SMBus 7722、SPI 7723、HECI、Management Engine Interface/WMI、Serial IO GPIO(INTC105E)/I2C(7778/777A/777B)、PPM Provisioning、TXT、Dynamic Tuning、Innovation Platform Framework、Integrated Sensor Solution、ISS HID | 21 |
| Intel 显卡 | Arc(TM) 130T GPU (16GB)、Display Audio ×3、AI Boost (NPU) | 5 |
| Intel 网络 | Wi-Fi 7 BE200 320MHz、Ethernet I219-V、无线 Bluetooth | 3 |
| 其他 | BayHubTech SD 读卡器（1）、Realtek Integrated Camera（1）、标准 NVMe 控制器（1，微软 inbox，仅作核对） | 3 |

> **唯一例外风险**：Wi-Fi BE200 与有线 I219-V 是「装完能否联网」的前提，一旦没识别 Windows Update 什么都拉不到；**必须预下载到 U 盘**。

## B 类：必须手动装（联想专属，21 项）

不在 Windows Update 分发范围内，只能从联想官网取。

| 厂商 | 设备（实测驱动版本） | 处理 |
| --- | --- | --- |
| Lenovo（7 项） | ACPI-Compliant Virtual Power Controller `15.11.300.14`、Fn and function keys `2.1.2602.8`、Virtual Bus `2.0.0.135`、Process Management `3.1.0.41`、Universal Device Client Device `26.8.0.29` + Plugins `26.9.0.20`、Integrated Monitor `1.70.1.17` | 联想官网按机型下载；装 Lenovo Vantage 后可自动补齐大部分 |
| Realtek 音频（4 项） | High Definition Audio(SST) `6.0.9879.1`、Audio Effects Component、Audio Universal Service、DMFT - IR（红外摄像头，Windows Hello 人脸识别用） | **必须装联想音频驱动包**，否则杜比/Elevoc 效果链不生效 |
| Dolby（2 项） | DolbyAPO Software Device (HSA) `3.30803.830`、DolbyAPO SWC Device `3.30809.881` | 随联想音频包一起装，无独立分发 |
| Elevoc（2 项） | Elevoc Audio Effects Component `5.0.5.258` ×2 | 同上 |
| 英特尔智音（5 项） | 智音技术总线 / 数字麦克风 / USB 音频 / OED / 检测验证 `20.40.12248.0` | 联想音频包内含 |
| Sunia（1 项） | SPB Peripheral Driver - LTCN0001 `1.0.7.6` | 官网按机型下载 |

**B 类核心**：联想音频驱动包一次性补齐 Realtek（4）+ Dolby（2）+ Elevoc（2）+ 英特尔智音（5）= **13 项**，否则杜比/Elevoc 效果链不生效；其余靠装 Lenovo Vantage 自动补齐。

## C 类：装应用时自动带回（5 项，不用管）

| 设备 | 来源 |
| --- | --- |
| VMware VMnet1 / VMnet8 / VMCI Host Device（Broadcom 25.0.0.1） | 装 VMware Workstation 时带回 |
| iNode VPN Virtual NIC `1.0.0.0` | 装 iNode 客户端时带回 |
| TAP-Windows Adapter V9 `9.27.0.0` | 随对应 VPN / 代理软件带回 |

## 驱动导出 / 回装（Stage 1 必做，不是可选项）

**为什么必做**：重装后若网卡驱动没被识别，机器上不了网；上不了网，Windows Update 一个驱动都拉不到——形成「没驱动 → 没网 → 没驱动」的死结，后续步骤全部卡死。所以网卡驱动必须在重装前就放在**能离线拿到**的地方。

导出的是**当前系统里已被验证可用**的驱动包（.inf + .sys），比事后去官网翻型号更可靠。装前导出（管理员），装后再一次性灌回去：

```powershell
$BackupDir = "D:\_PreinstallBackup\$(Get-Date -Format yyyyMMdd_HHmm)"    # 换成你自己的备份目录
pnputil /export-driver * "$BackupDir\Drivers"                            # 装前
pnputil /add-driver "$BackupDir\Drivers\*.inf" /subdirs /install         # 装后
```

**落点说明**：导出到 **D: 数据盘即可**——它不随 C 盘被格式化，重装后立刻可读。这里的威胁模型与备份数据不同：驱动备份防的是「C 盘被清空」这一件事，D 盘与 C 盘是否同属一块物理磁盘**并不影响**它。因此**不像数据备份那样强求外置**；顺手再拷一份到 U 盘 `Drivers\` 更稳妥。

导出的是驱动包而非安装包，**联网后仍建议补厂商官方最新版**（尤其音频/热键这类厂商定制件）。

**必下三项（按你自己普查出的型号替换），解压到 U 盘 `Drivers\`**：① 无线网卡驱动 ② 有线网卡驱动 ③ 厂商音频/热键驱动包。显卡通常由 Windows Update 推送即可；若坚持用厂商定制版，则需阻止 WU 覆盖。

## 驱动来源

| 来源 | 入口 |
| --- | --- |
| 厂商官方支持站 | 用 Step 0 事实 1 查到的机型与序列号检索，如 Lenovo <https://pcsupport.lenovo.com/> |
| Intel 下载中心 | <https://www.intel.com/content/www/us/en/download-center/home.html> |
