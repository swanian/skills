# 阶段五之一：驱动

配套 SKILL.md Stage 5。按 `references/01-preflight.md` 事实 1 和事实 6，使用目标机器的实际型号与设备信息选择驱动；不要照搬其他机器的设备清单或驱动版本。

## 驱动分类

| 类别 | 常见来源 | 处理 |
| --- | --- | --- |
| A：系统可自动安装 | Windows 安装介质与 Windows Update | 联网后检查设备管理器；确认关键设备正常工作 |
| B：整机厂专属 | 整机厂官方支持站 | 按机器型号获取热键、电源管理、音频等定制驱动 |
| C：随应用安装 | VPN、虚拟机或外设软件安装包 | 安装对应应用后检查是否已添加所需设备驱动 |

网卡是离线恢复的关键：重装后如果没有可用网络，Windows Update 就无法获取其他驱动。安装前先从当前系统导出驱动，并按实际网卡型号准备厂商安装包，至少保存一份到 U 盘。

## 导出与回装

导出当前系统已经使用的驱动包（管理员 PowerShell）：

```powershell
$BackupDir = "D:\_PreinstallBackup\$(Get-Date -Format yyyyMMdd_HHmm)"  # 换成自己的备份目录
pnputil /export-driver * "$BackupDir\Drivers"
```

重装后回装：

```powershell
pnputil /add-driver "$BackupDir\Drivers\*.inf" /subdirs /install
```

驱动库导出不代替外部数据备份。确认保存位置在重装时不会被格式化，并额外准备与实际网卡型号匹配的离线安装包。

## 下载来源

| 来源 | 入口 |
| --- | --- |
| 整机厂官方支持站 | 使用 Step 0 记录的机型；需要序列号时，仅在厂商官方页面输入 |
| Intel 下载中心 | <https://www.intel.com/content/www/us/en/download-center/home.html> |

安装前核对操作系统版本、硬件型号与驱动兼容性。第三方驱动下载站不作为来源。
