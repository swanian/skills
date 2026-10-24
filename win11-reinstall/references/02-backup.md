# 阶段一：备份

**原则：同盘不算备份。** 系统盘与数据盘若在同一块物理磁盘上，备份到另一个分区只是镜像，磁盘一旦出问题两者一起完蛋。

本阶段不依赖任何本地脚本，所有命令均可直接复制执行。先准备好一个备份目录变量：

```powershell
$BackupDir = "D:\_PreinstallBackup\$(Get-Date -Format yyyyMMdd_HHmm)"
New-Item -ItemType Directory -Path $BackupDir -Force
$ExternalDir = "E:\ReinstallBackup"      # 改成你的 U 盘/移动硬盘路径
```

> ⚠️ **动手前先问使用者**：下面的 P0/P1/P2 分级只是**模板**。必须让使用者确认「哪些要备份」，并拿到**具体路径**（`D:\Projects` 这种，而不是「项目文件」）。明确告知：**没列进清单的内容不会被保护**。

## 优先级

| 级别 | 对象 | 处置 |
| --- | --- | --- |
| P0 | `.workbuddy`（memory、skills）、`Documents`、各项目盘中不可替代的数据 | **先外备**，不依赖本地其他分区 |
| P0 | `~/.ssh`、`~/.gitconfig`、浏览器配置文件目录 | 外备；有私钥必须带上（见 Step 0 事实 7） |
| P1 | `.vscode`、`.codex` / `.cursor` / `.comate` 等工具侧配置 | 改导出清单而非整体复制；会自动重建的部分可跳过 |
| P2 | `Downloads` | 不整体备份，按需挑选 |

`.vscode` 这类体积大但可重建的目录，建议只导出扩展清单：

```powershell
code --list-extensions > vscode-extensions.txt
```

## 大目录：选择性备份（不要整体拷贝）

**"备份某个目录"不等于"整体拷贝这个目录"。** 大目录里绝大多数是缓存、日志、运行时数据——装完毫无用处，整体拷贝还极慢。应当**只取有价值的子路径**，这一粒度必须在问询阶段与使用者**逐项确认**。

| 目录 | 要备份的子路径 | 跳过 | 原因 |
| --- | --- | --- | --- |
| `.workbuddy` | `memory`、`skills` | 其余（缓存、会话数据等） | 整体备份太耗时；真正不可替代的只有记忆与自定义技能 |
| 企业微信 / WeCom | **聊天记录** | 程序缓存、缩略图等 | 聊天记录是唯一不可替代的部分，其余可重建（记录目录位置随版本而异，需在使用者机器上确认） |
| `.vscode` | 扩展清单 `code --list-extensions` | 整个目录（2 GB+） | 扩展可重装，一份清单足够 |
| 浏览器 profile | 书签、密码、扩展数据 | `Cache`、`Code Cache` | 缓存体积大且无价值 |
| 项目目录 | 源码、配置、文档 | `node_modules`、`__pycache__`、构建产物 | 依赖可重新安装 |

**判断口诀**：问「这个子目录删掉后能不能自动重建 / 重新下载？」——**能，就不备份**。

## 落地顺序（不可颠倒）

1. **先外备 P0 小数据**到 U 盘或网盘。
2. **再大批量备份到本地暂存目录**——这只是同盘副本，应对软件重装后配置丢失，**不能替代第 1 步**。
3. **确认云盘同步完成**，托盘无上传队列再继续。
4. **把 `$BackupDir` 整体复制到外部介质**——这一步才让备份真正生效。

```powershell
robocopy $BackupDir $ExternalDir /E /Z /R:2 /W:2 /NP /LOG:$BackupDir\copy-external.log
```

## 导出命令清单

```powershell
# 软件清单（winget 可识别条目 + 注册表全量，两者互为补充）
winget export -o "$BackupDir\winget-packages.json" --accept-source-agreements
winget list > "$BackupDir\winget-list.txt"
Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*,
                 HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\* |
    Select-Object DisplayName,DisplayVersion,Publisher |
    Sort-Object DisplayName | Out-File "$BackupDir\installed-software.txt"

# 开发/网络配置
code --list-extensions > "$BackupDir\vscode-extensions.txt"
netsh wlan export profile key=clear folder="$BackupDir\wifi-profiles"    # 含明文密钥，妥善保管
Get-ChildItem env: | Out-File "$BackupDir\env-vars.txt"
Get-NetIPConfiguration | Out-File "$BackupDir\network.txt"
git config --global --list > "$BackupDir\git-config.txt"

# 分区快照（安装前最后一次核对容量）
Get-Partition | Select-Object DiskNumber,PartitionNumber,DriveLetter,Size,Type | Out-File "$BackupDir\disk-layout.txt"
Get-Volume | Where-Object DriveLetter | Select-Object DriveLetter,FileSystemLabel,Size,SizeRemaining | Out-File -Append "$BackupDir\disk-layout.txt"

# 凭据
Copy-Item "$env:USERPROFILE\.ssh" "$BackupDir\p0-config\.ssh" -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item "$env:USERPROFILE\.gitconfig" "$BackupDir\p0-config\" -Force -ErrorAction SilentlyContinue
```

## 备份后必须做的两件事

1. **核对产物**：关键文件/目录不能为空 —— `installed-software.txt`、`disk-layout.txt`、`winget-packages.json`、`p0-config\`、**`Drivers\`**（驱动库，见 `references/04-drivers.md`，用于破解「没驱动→没网→没驱动」死结）。
2. **拔盘存放**：外部介质拔下来单独放。留在机器上的 U 盘，等于没备份。

> PowerShell 提示：`$HOME` 是只读自动变量，直接赋值会抛 `UnauthorizedAccessException`。写脚本时用 `$env:USERPROFILE` 或自定义变量。

> 恢复方式说明：重装后**不使用** `winget import` 批量安装，改为按 `references/05-restore.md` 下载安装包手动安装。`winget-packages.json` 因此降级为**核对清单**，用于装完后核查有无遗漏软件。
