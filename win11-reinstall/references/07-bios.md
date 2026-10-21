# BIOS 操作与启动键（F1 / F12 / 安全启动）

示例机型（按键与菜单布局随厂商而异，请以自己机器开机 LOGO 上的提示为准）：联想 ThinkBook 14 G7+ IAH (21TK)，BIOS R6CN24WW。

## 两个按键的用途

| 按键 | 时机 | 作用 |
| --- | --- | --- |
| **F1** | 开机出现 Lenovo logo 时连按 | 进入 **BIOS Setup（BIOS 设置）**——改启动模式、开关 Secure Boot 这类**持久配置**都在这里 |
| **F12** | 同上 | 打开**一次性启动菜单（Boot Menu）**，只选出「本次」从哪个设备启动，**不改** BIOS 持久配置 |
| Enter | 同上（F1/F12 无响应时的兜底） | 进入 **Startup Interrupt Menu**，从中可再进 BIOS 或启动菜单 |

使用要点：

- **日常「从 U 盘启动」优先用 F12**——它只影响本次，不动 BIOS 持久设置，是风险最低的做法。
- 只有在需要改 BIOS 持久配置（Secure Boot、启动顺序等）时才用 **F1**。
- 若按键被吞、毫无反应，多半是 **Fast Boot（快速启动）** 导致：先用任意方式进 BIOS 关掉 Fast Boot，或改用 **Enter** 兜底菜单。

## 安全启动（Secure Boot）

### 安装前到底要不要关？

**官方原版介质不需要关闭。** Windows 11 正式版 ISO / 媒体创建工具产出的介质由微软签名，受 PK/KEK 信任，Secure Boot 开着即可正常安装。主动关掉它只会平白引入「装完忘开」的风险——示例机器上一轮重装就踩过这个坑（装完忘了恢复）。

仅在以下情况才考虑临时关闭：

- 需要启动未签名 / 带第三方 shim 的 Live USB、PE、硬件诊断工具
- Rufus 写入的介质用了不被信任的引导方式，确实无法从 U 盘启动

一旦关闭，**安装结束后必须回来重新启用并验证**。

### 示例教训（2026-10-16 实测）

| 检查项 | 示例机器结果 |
| --- | --- |
| 注册表 `UEFISecureBootEnabled` | **0（关闭）** |
| `Confirm-SecureBootUEFI` | 管理员 PowerShell 才返回 True/False，普通会话报「访问被拒绝」 |

示例机器上一轮重装后安全启动一直没恢复，**直到复查才发现**——正因为容易忘，它被写进了 Stage 5 的必做步骤。

### 开关路径与验证

BIOS 路径：**F1 进 Setup → Security（安全）→ Secure Boot → 设为 Enabled → F10 保存退出**。不同 BIOS 版本菜单措辞可能略有差异，以屏幕上实际显示为准。

Windows 内验证（任选其一）：

```powershell
# 方法一：注册表（普通权限即可，0=关 / 1=开）
(Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\SecureBoot\State' -Name UEFISecureBootEnabled).UEFISecureBootEnabled

# 方法二：固件查询（需管理员 PowerShell，返回 True 表示已启用）
Confirm-SecureBootUEFI
```

也可在 `msinfo32` 中查看「安全启动状态：启用 / 关闭」。

### 长期不恢复的后果

安全特性受限、偏离「官方原版」原则；部分依赖 Secure Boot 的合规与加固场景会直接报错。此项在 `references/06-risks.md` 登记为历史风险（示例机器实际发生过）。

## 与五个阶段的关系

| 阶段 | BIOS 相关动作 |
| --- | --- |
| Stage 3 前置 | 记录当前 Secure Boot 状态；确认 F1/F12 可唤出（不行先关 Fast Boot 或用 Enter） |
| Stage 4 安装 | 用 **F12** 选 `UEFI: USB 设备` 启动 |
| Stage 5 恢复 | 用 **F1** 回来把 Secure Boot 开回去，并用上面命令验证为 `1` / `True` |
