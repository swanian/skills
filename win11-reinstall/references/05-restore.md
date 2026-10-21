# 阶段五之二：装后恢复（下载安装包 → 手动安装）

配套 SKILL.md Stage 5。**恢复方式：不使用 `winget import` 批量安装，改为先把安装包下载下来，再由用户逐个运行安装。**

> ⚠️ **恢复前必须先问使用者**：软件清单体现的是**作者的软件偏好**，不是给所有人的推荐。使用前应当作「待办清单模板」交给使用者增删确认；与版本号无关的下载入口部分可直接复用。
>
> 提问时把清单拆成两栏——「现在就能下到安装包的」与「需要账号或 IT 审批的」，后者需提前协调。另外要记下**明确排除项**，避免之后被误装。

## 方式变更说明

| 对比   | winget 批量导入                                                 | 下载安装包（现行）                                |
| ---- | ----------------------------------------------------------- | ---------------------------------------- |
| 触发方式 | `winget import -i winget-packages.json`                     | 下载exe/msi → 用户双击安装                       |
| 优点   | 一键、无人值守                                                     | 版本可控、可离线重装、介质可复用；覆盖 winget 源没有或 ID 失效的软件 |
| 缺点   | ID 随版本增删易中断；企业/受限软件（iNode、VMware Workstation、LightWAN）根本走不通 | 失去一键批量，耗时更长；需自行校验安装包完整性                  |

`winget-packages.json` / `winget-list.txt` 仍保留，用途从「恢复脚本」降级为**核对清单**：装完对照一遍，确保没有遗漏（见 `references/02-backup.md`）。

## 系统层（按顺序，先做）

驱动优先，因为后续一切都依赖联网：

1. **驱动**：设备管理器查未知设备 → 优先补无线/有线 → 装 Arc 显卡 → 运行 Lenovo Vantage 补齐。
2. **激活**：设置 → 系统 → 激活，确认「已激活（数字许可证）」；未激活则用激活疑难解答并登录原微软账号。
3. **更新**：Windows Update 拉到 26300.9711 或更高。
4. **D 盘**：确认 `D:\` 数据完好后再继续。

## 已验证直链（2026-10-16 实测 HTTP 200）

下载后由用户自行安装。版本号会随上游更新失效，失效处理见下一节。

| 软件                  | 直接下载链接                                                                                                         | 备注                                        |
| ------------------- | -------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| Git 2.56.0.2        | `https://github.com/git-for-windows/git/releases/download/v2.56.0.windows.2/Git-2.56.0.2-64-bit.exe`           | x64 安装包                                   |
| GitHub CLI 2.102.0  | `https://github.com/cli/cli/releases/download/v2.102.0/gh_2.102.0_windows_amd64.msi`                           | `.msi`，非 exe                              |
| Python 3.14.8       | `https://www.python.org/ftp/python/3.14.8/python-3.14.8-amd64.exe`                                             | 约 33.4 MB                                 |
| VS Code             | `https://code.visualstudio.com/sha/download?build=stable&os=win32-x64-user`                                    | **稳定重定向，始终最新**（实测 243 MB User 版）          |
| Cursor              | `https://www.cursor.com/api/download?platform=win32-x64-user&releaseTrack=latest`                              | 官网 API；旧域 `downloader.cursor.sh` 已 502 失效 |
| WinSCP 6.7          | `https://winscp.net/download/WinSCP-6.7-Setup.exe/download`                                                    | 约 13 MB                                   |
| PDFgear 3.0.0       | `https://downloadfiles.pdfgear.com/releases/windows/pdfgear_setup_v3.0.0.exe`                                  | 约 132 MB                                  |
| FlClash 0.9.0       | `https://github.com/chen08209/FlClash/releases/download/v0.9.0/FlClash-0.9.0-windows-amd64-setup.exe`          | 代理客户端                                     |
| Horizon Client 2406 | `https://download3.omnissa.com/software/CART25FQ2_WIN_2406/VMware-Horizon-Client-2406-8.13.0-9986028157.exe`   | 8.13.0，**永久许可建议上限版**                      |
| Horizon Client 2606 | `https://download3.omnissa.com/software/CART27FQ2_WIN_2606/Omnissa-Horizon-Client-2606-8.19.0-32215845441.exe` | 8.19.0 最新公开版，免注册                          |
| LightWAN 6.1.38     | `https://lightwan.com/download/windows`                                                                        | 重定向到带签名的 COS 直链，约 38 MB                   |

> Horizon Client 两版二选一即可：VDI 是永久许可用 2406，订阅制用 2606。

## 无公开直链 / 需账号

| 软件                     | 获取方式                                             | 关注点                                                            |
| ---------------------- | ------------------------------------------------ | -------------------------------------------------------------- |
| iNode 智能客户端            | 优先从企业内部渠道获取（如企业微信微盘）；若需走 H3C 官网，则要账号 + 验证码且无法脚本化 | 企业管控软件，须由 IT 分发                                                |
| VMware Workstation Pro | Broadcom 官网，需注册账号 + 出口合规审核（可能数周）                 | 已对个人与商业使用免费，但下载仍需登录；旧 `softwareupdate.vmware.com` 公开 CDS 路径已失效 |
| Office 家庭版 2024        | 登录微软账号 → account.microsoft.com → 服务与订阅 → 安装      | 无公开直链，必须走账号                                                    |
| 企业微信 WeCom             | `https://work.weixin.qq.com/` 下载页                | 官网下载，装后需扫码激活                                                   |
| WorkBuddy              | `https://www.workbuddy.cn/`                      | 官网下载；winget 源无条目                                               |
| Hermes                 | 官网下载                                             | 仅需填入 API Key 即可使用                                              |
| 豆包 Doubao              | `https://www.doubao.com/`                        | 官网下载                                                           |
| Comate                 | `https://comate.baidu.com/`                      | 官网下载                                                           |
| 360Zip                 | 官网下载                                             | —                                                              |

## 版本失效时如何取最新版

- **GitHub 托管**（Git / GitHub CLI / FlClash）：用 API 取最新资产，避免在 skill 里硬编码会过期的版本号。

```powershell
$d = Invoke-RestMethod https://api.github.com/repos/<owner>/<repo>/releases/latest
$d.assets | Where-Object { $_.name -like '*windows*amd64*' -or $_.name -like '*64-bit.exe' } |
    Select-Object name, browser_download_url
```

常用仓库：`git-for-windows/git`、`cli/cli`、`chen08209/FlClash`。

- **VS Code / Cursor**：上表中的链接是**稳定重定向**，始终指向最新稳定版，长期有效，无需改版本号。
- **Python**：新补丁版发布后，把 URL 里的 `3.14.8` 换成目标版本即可，格式固定为 `https://www.python.org/ftp/python/<版本>/python-<版本>-amd64.exe`。
- **Omnissa / WinSCP / PDFgear / LightWAN**：版本号会变，失效时回到官方下载页重新取链接。

## 下载完整性校验建议

手动下载的安装包建议在 PowerShell 里确认是可执行文件并核对 SHA256（与官网公布值比对）：

```powershell
Get-AuthenticodeSignature ".\xxx.exe" | Select-Object Status, StatusMessage   # 期望 Valid / VMware, Inc. 等真实发行者
Get-FileHash ".\xxx.exe" -Algorithm SHA256 | Format-List
```

## 建议安装顺序

1. **运行时 / 开发工具**：Git → GitHub CLI → Python 3.14 → VS Code → Cursor
2. **日常软件**：企业微信 → WinSCP → PDFgear → 360Zip → 豆包 / Comate
3. **企业 / 网络组件**：iNode → VMware Horizon Client → LightWAN → FlClash（代理）
4. **必须手动且需账号的**：Office 家庭版 2024（微软账号）→ VMware Workstation（**授权需重新输入**）
5. **VS Code 扩展**：按导出清单逐条重装，或登录开启 Settings Sync

> 代理类软件建议**优先恢复**——若有工具依赖需要经代理才能访问的资源，它不通会让后续一连串工具都不可用。

## 明确排除（不装）

LocalSend、天禧AI、联想百应 / 联想应用商店 / 超级互联。

由于已无自动化批量安装，装完后务必对照备份阶段导出的 `installed-software.txt`（注册表软件清单）与 `winget-list.txt` 复核一遍，避免遗漏。

## 企业侧与网络（需预留协调时间）

以下重装后**可能需 IT 重新授权**，建议提前确认安装包与配置来源：

| 软件                    | 关注点                                              |
| --------------------- | ------------------------------------------------ |
| iNode 智能客户端           | **从企业微信微盘获取安装包**（勿自行从第三方下载）；企业 VPN，可能受控制中心下发策略约束 |
| VMware Horizon Client | 需重配连接服务器地址                                       |
| LightWAN              | 用途需确认，先问 IT 是否仍需安装                               |
| FlClash 代理            | 需重配；部分依赖代理链路的工具会随之不可用                            |
