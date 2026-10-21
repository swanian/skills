# Step 0：装机前普查（八项事实 + 取数命令）

**在目标机器上运行这些命令，把结果抄到纸上或存到外部介质。** 此后所有决策都以这里记录的值为准，而不是以本 skill 里的示例为准。

> 示例章节里的数值来自作者 2026-10-15 在 Lenovo ThinkBook 14 G7+ IAH (21TK) 上的一次实测重装。它们**只对那台机器成立**。

## 事实 1 — 机型 / BIOS / 序列号

```powershell
Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer,Model
Get-CimInstance Win32_BIOS | Select-Object SMBIOSBIOSVersion,SerialNumber
```

用途：去厂商支持站拉驱动时按键，保修与官方文档定位也靠它。

## 事实 2 — 磁盘控制器模式（决定能否看到硬盘）

```powershell
Get-CimInstance Win32_PnPEntity |
    Where-Object { $_.Name -match 'VMD|RST|RAID|NVMe|SATA' } |
    Select-Object Name,DeviceId
```

也可在「设备管理器 → 存储控制器」下肉眼确认。判据：

| 看到的东西 | 含义 | 后果 |
| --- | --- | --- |
| 「标准 NVM Express 控制器」 | 标准模式 | 安装程序直接认盘，**无需注入驱动** |
| 「Intel Volume Management Device」/ Intel RST | 启用 VMD/RST | 安装程序**看不到硬盘**，必须在「加载驱动程序」环节注入厂商驱动 |

## 事实 3 — 分区布局（最关键，决定丢不丢数据）

```powershell
Get-Disk      | Select-Object Number,FriendlyName,Size,BusType,PartitionStyle | Format-Table -AutoSize
Get-Partition | Select-Object DiskNumber,PartitionNumber,DriveLetter,Size,Type | Sort-Object DiskNumber,PartitionNumber | Format-Table -AutoSize
Get-Volume    | Where-Object DriveLetter | Select-Object DriveLetter,FileSystemLabel,Size,SizeRemaining | Format-Table -AutoSize
```

把下面这张表填完，安装时要对着它看：

| 盘符 | 卷标 | 约合容量 | 角色（系统 / 数据 / 其他） | 动作 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |
|  |  |  |  |  |

规则：**只看容量和卷标，不看分区序号**；只有一个「系统」角色允许删除；标为「数据」的一个都不能碰；EFI（100–260 MB）/ MSR（16 MB）/ WinRE（0.5–1 GB）一律不动。

## 事实 4 — BitLocker / 设备加密

```powershell
manage-bde -status
Get-BitLockerVolume | Select-Object MountPoint,ProtectionStatus,VolumeStatus
```

- `ProtectionStatus = Off` → 无需恢复密钥，可放心格式化。
- `ProtectionStatus = On` → **必须先导出 48 位恢复密钥**，否则重装后卷里的数据永远拿不回来：

```powershell
manage-bde -protectors -get C:      # 抄下「数字密码」那 48 位
```

## 事实 5 — EditionID / SKU / 激活类型

```powershell
(Get-ItemProperty HKLM:\SOFTWARE\Microsoft\Windows\NT\CurrentVersion).EditionID
DISM /Online /Get-CurrentEdition
Get-CimInstance SoftwareLicensingProduct |
    Where-Object PartialProductKey |
    Select-Object Name,LicenseStatus,LicenseFamily,Description
```

- `LicenseStatus = 1` → 已激活；`OEM_DM` 表示绑主板数字许可证，同 SKU 重装后联网自动激活。
- **下载的 ISO 必须精确匹配这里的 EditionID**。多版本 ISO 通常**不含**区域变体，挑最接近的那一项会导致联网激活失败。
- 常见陷阱示例（作者机器 `CoreCountrySpecific`，即「家庭版 中国区变体」）：

| 下载页下拉项 | 对应 SKU | 能否激活作者机器 |
| --- | --- | --- |
| 多版本 ISO | Core / CoreSingleLanguage / Professional 合集 | **不能** —— 不含 CoreCountrySpecific |
| Windows 11 家庭版（仅限中国） | CoreCountrySpecific | **能** |
| Windows 11 专业中文版本 | ProfessionalCountrySpecific | 不能，需另购授权 |

密钥页选「我没有产品密钥」，联网后由数字许可证自动激活。

## 事实 6 — 网卡型号（决定预下载哪些驱动）

```powershell
Get-NetAdapter | Select-Object Name,InterfaceDescription,Status,LinkSpeed
```

把无线和有线两条的型号抄下来（例如 Intel Wi-Fi 7 BE200、Intel Ethernet I219-V），去 Intel 下载中心 / 厂商支持站各下一份离线包放进 U 盘 `Drivers\`。**这是「装完能不能联网」的前提。**

## 事实 7 — SSH 私钥与 Git 身份（⚠️ 不要照搬别人的结论）

```powershell
Get-ChildItem $env:USERPROFILE\.ssh -Force -ErrorAction SilentlyContinue
git config --global --list
```

- **作者那台机器恰好只有 `known_hosts`、没有私钥**，所以当时判定「重装后重新生成即可」。
- **这个结论不能推广。** 若你的 `.ssh` 里有 `id_ed25519`/`id_rsa`，它们必须随 P0 备份，丢了就要重新给所有服务器配公钥。
- 顺手记下 Git 身份，丢了可以两行重建（填你自己的值）：

```bash
git config --global user.name  "<你的名字>"
git config --global user.email "<你的邮箱>"
```

## 事实 8 — 安全启动状态

```powershell
(Get-ItemProperty HKLM:\SYSTEM\CurrentControlSet\Control\SecureBoot\State -Name UEFISecureBootEnabled).UEFISecureBootEnabled   # 0=关 1=开
Confirm-SecureBootUEFI        # 需管理员 PowerShell，返回 True 表示已启用
```

装完后对着这个初始值恢复。详见 `references/07-bios.md`。

---

## 示例：作者机器实测值（**不可照抄**）

| 事实 | 作者机器 | 备注 |
| --- | --- | --- |
| 机型 | Lenovo ThinkBook 14 G7+ IAH (21TK)，BIOS R6CN24WW | 序列号属个人信息，未写入本 skill |
| CPU / GPU / RAM | Core Ultra 5 225H / Intel Arc 130T (16GB) / 31.5 GB | — |
| 磁盘 | 单块 YMTC NVMe 954 GB | 标准 NVMe，**无 VMD** → 无需注入驱动 |
| 分区 | 系统 `Windows-SSD` ~500 GB ／ 数据 `Data` ~451.6 GB | 这两个数字只对这台机器成立 |
| 加密 | 无 BitLocker、无设备加密 | 无需恢复密钥 |
| SKU | `CoreCountrySpecific` | 必须用「家庭版（仅限中国）」单版 ISO |
| 网卡 | Intel Wi-Fi 7 BE200 320MHz ／ Intel I219-V | 两者都预下载了离线包 |
| 凭据 | 无 SSH 私钥；Git 身份另行记录 | **作者机器特例，不代表你的机器** |
| 结果 | Build 26300.9711，数字许可证自动激活，数据盘完好 | — |
| 遗留缺陷 | Safe Boot 装完未恢复（曾为 `UEFISecureBootEnabled=0`） | 记为教训：装完必须回头恢复 |
