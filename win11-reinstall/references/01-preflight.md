# Step 0：装机前普查（八项事实 + 取数命令）

**在目标机器上运行这些命令，把结果抄到纸上或存到外部介质。** 此后所有决策都以这里记录的值为准，而不是以本 skill 里的示例为准。

下列步骤要求你现场读取目标机器的数据；不要根据其他设备的记录推断。

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

- `LicenseStatus = 1` 表示当前显示为已许可。`OEM_DM` 常见于固件嵌入的 OEM 密钥；不要仅凭该字段推断可用版本或保证重装后自动激活。
- 记录当前 Windows 版本，并选择与许可相符的官方安装介质。区域版 SKU 和下载选项可能不同；不要选择“最接近”的版本，也不要假设多版本 ISO 一定包含当前许可对应的版本。
- 若安装程序提供「我没有产品密钥」选项，可跳过输入步骤；联网后通常会自动激活，但具体结果取决于许可、版本和设备状态。参阅 [Microsoft 重装说明](https://support.microsoft.com/en-us/windows/deployment/install-upgrade/reinstall-windows-with-the-installation-media)（核对日期：2026-10-24）。

| 下载页下拉项 | 对应 SKU | 注意 |
| --- | --- | --- |
| 多版本 ISO | 页面列出的多个版本 | 确认包含与当前许可匹配的版本 |
| 区域版 ISO | 页面列出的区域版本 | 仅在它与当前许可匹配时选择 |
| 其他版本 | 页面列出的其他版本 | 不要假设当前许可涵盖该版本 |

## 事实 6 — 网卡型号（决定预下载哪些驱动）

```powershell
Get-NetAdapter | Select-Object Name,InterfaceDescription,Status,LinkSpeed
```

把无线和有线网卡的型号抄下来，去芯片厂商或整机厂官方支持站下载对应离线驱动，放进 U 盘 `Drivers\`。**这是「装完能不能联网」的前提。**

## 事实 7 — SSH 私钥与 Git 身份（⚠️ 不要照搬别人的结论）

```powershell
Get-ChildItem $env:USERPROFILE\.ssh -Force -ErrorAction SilentlyContinue
git config --global --list
```

- 如果 `.ssh` 里有 `id_ed25519`/`id_rsa`，将私钥纳入 P0 备份；丢失后需要重新给相关服务器配置公钥。
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

## 记录模板

把命令结果记录在你自己的安全位置；不要把序列号、恢复密钥、私钥或账号信息贴进共享 skill、公开仓库或聊天记录。
