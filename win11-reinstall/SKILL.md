---
name: win11-reinstall
description: This skill should be used when planning, preparing, or executing a clean reinstallation of Windows 11 — building a pre-flight machine snapshot, choosing the correct edition/SKU, preparing official install media, preserving data and credentials, performing a partition-safe custom install, and restoring software. Before acting it must confirm with the user both the **backup list** and the **software install list**, treating the bundled versions only as templates to be confirmed. Triggers include 重装系统 / 重做系统 / 全新安装 Windows 11 / 制作 Win11 安装 U 盘 / 备份分级 / 恢复软件清单 / Windows 11 clean install / reinstall Windows 11.
agent_created: true
---

# Windows 11 全新安装（干净重装）

## Overview

A self-contained five-stage methodology for wiping and reinstalling Windows 11 without losing data. It depends on **no local files** — every machine-specific fact is discovered at runtime with commands given below and in `references/01-preflight.md`.

Use only the target machine's live pre-flight results. Any examples are illustrative and must never replace those results.

## Mandatory Intake — Confirm Two Lists Before Acting

The lists bundled with this skill come from one person's machine. Treat them as **defaults to confirm, never as assumptions**. Ask the user the following two questions **in a single round**, before any destructive or time-consuming step.

### Q1 — What must be backed up?

Present the tiering template in `references/02-backup.md` as a starting point, then ask for additions and removals.

- Insist on **concrete paths**, not categories (`D:\NEXAI` rather than "project files").
- Confirm which P0 items also go to external media (default: yes for all P0).
- State plainly: **anything not on the confirmed list will not be protected.**
- Proactively flag items users routinely forget: SSH private keys, browser profiles, WiFi profiles, license keys, and whether cloud sync has actually finished.
- For large directories confirm the **granularity**, not just the top-level item — ask which subpaths to keep, and exclude caches, logs, and anything regenerable. Wholesale copying is slow and mostly copies useless data. Never interpret "back up directory X" as "copy all of X". Real examples of selective backup:
  - `.workbuddy` → only `memory` and `skills` (a full copy is far too slow; those two hold everything irreplaceable)
  - enterprise IM (e.g. WeCom) → only the chat history (location varies by version — confirm on the user's machine)
  - `.vscode` → just the extension list via `code --list-extensions`; the multi-GB directory itself is not worth copying

### Q2 — Which software should be reinstalled?

Present the template in `references/05-restore.md` and ask for confirmations, additions, and removals.

- Make clear the bundled list is **a sample preference list**, not a recommendation for everyone.
- Split the list into "installers that can be fetched now" versus "items needing an account or IT approval", so the user knows what requires advance coordination.
- Re-verify versioned direct links against the vendor page at install time; never trust a stale version number.
- Record any deliberate exclusions so nothing on it gets installed by accident later.

If the user answers "just use the default", restate the full default list explicitly and obtain one confirmation before proceeding. Wherever the user's answer conflicts with the bundled template, **the user's answer wins**.

## Step 0 — Pre-flight Snapshot (do this first, on the target machine)

**Do not touch a single partition until the following eight facts are recorded.** Each has a query command in `references/01-preflight.md`.

| # | Fact | Why it decides everything downstream |
| --- | --- | --- |
| 1 | Model / BIOS / serial | Which vendor drivers to fetch |
| 2 | **Disk controller mode (standard NVMe vs Intel VMD/RST)** | Whether you must inject a driver before the disk appears at all |
| 3 | Partition layout — which is system, which is **data**; their sizes and labels | The single most destructive decision in the whole job |
| 4 | **BitLocker / device encryption status** | If on, the recovery key must be exported or the data is unrecoverable |
| 5 | `EditionID` / SKU and activation type | Which ISO to download; the wrong one fails to activate |
| 6 | Network adapter models | Which drivers to pre-download so you are not stranded offline |
| 7 | **SSH private keys and Git identity** | Credentials that must be backed up, not assumed absent |
| 8 | Secure Boot state | Whether it needs restoring after install |

## Critical Red Lines

1. **Partition selection** — Identify partitions **by capacity and volume label taken from your own Step 0 snapshot, never by index and never from this skill's example**. Delete only the partition you recorded as the system partition; **never delete or format** the one recorded as data; leave EFI (100–260 MB), MSR (16 MB), and WinRE (0.5–1 GB) alone.
2. **Edition must match your license** — Check the installed Windows edition and use installation media for the edition covered by your license. Microsoft says the reinstalled edition must match the digital license; activation is usually automatic after going online, but may require troubleshooting. See [Microsoft's reinstall guidance](https://support.microsoft.com/en-us/windows/deployment/install-upgrade/reinstall-windows-with-the-installation-media) and [activation guidance](https://support.microsoft.com/en-us/windows/activation/activate-windows) (checked 2026-10-24). Edition availability varies by region and media; verify the current official download options before proceeding.
3. **BitLocker before anything else** — If any volume is encrypted, export the recovery key first. Never assume encryption is off; check with `manage-bde -status`.
4. **External backup is mandatory** — Backing up to another partition on the same physical disk is a mirror, not a backup. Export, verify, then copy the artifacts to external media before installing.
5. **Credentials and keys** — Check `~/.ssh` yourself. Back up any private keys you find there, including `id_ed25519` or `id_rsa`.
6. **Official media only** — Never use third-party Ghost / trimmed / pre-activated images.
7. **Mains power throughout** — Power loss mid-install can corrupt the partition table.
8. **Network drivers must exist offline** — There is a deadlock: without a NIC driver there is no network, and without network Windows Update cannot fetch any driver, so every later step stalls. Before installing, put the adapters' drivers in at least one offline location — export the current driver store to the data partition with `pnputil /export-driver`, and/or pre-download the vendor packages to a `Drivers\` folder on the USB stick.

## Workflow

### Stage 1 — Backup

Run external-first, in this order, working from the backup list confirmed during intake — not from the bundled template.

1. Copy P0 data (`.workbuddy` memory+skills, `Documents`, project drives, `~/.ssh`, `.gitconfig`) to external storage or cloud — independent of other local partitions.
2. Then bulk-copy to a local staging folder (same-disk copy, for config convenience only).
3. Confirm cloud sync finishes — no pending uploads before continuing.
4. Copy everything to external media. **This is the step that makes the backup real.**

Essential export commands:

```powershell
winget export -o winget-packages.json --accept-source-agreements          # 软件清单
Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*,
                 HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\* |
    Select-Object DisplayName,DisplayVersion,Publisher |
    Sort-Object DisplayName | Out-File installed-software.txt
code --list-extensions > vscode-extensions.txt                            # VS Code 扩展
netsh wlan export profile key=clear folder=.\wifi-profiles                 # WiFi 配置
Get-ChildItem $env:USERPROFILE\.ssh -ErrorAction SilentlyContinue          # 有私钥就备份
robocopy "$env:USERPROFILE\Documents" "<BackupDir>\Documents" /E /Z /R:2 /W:2

# 驱动库导出（管理员 PowerShell）——不是可选项，见下方「离线死结」
pnputil /export-driver * "<BackupDir>\Drivers"
```

> **离线死结（务必理解）**：重装后若无线/有线网卡驱动没被识别，机器上不了网；而上不了网，Windows Update 一个驱动都拉不到——「没驱动 → 没网 → 没驱动」，后续全部卡死。因此**网卡驱动必须在重装前就已经躺在能离线拿到的地方**。
>
> 两个落点互为冗余，至少做①：
> ① `pnputil /export-driver` 导出到 **D: 数据盘**——它不随 C 盘被格式化，重装后立刻可读，且导出的是**当前系统已验证可用**的驱动，最省事；
> ② 从厂商官网下好对应型号的包放进 **U 盘 `Drivers\`**——独立于本机磁盘，但需自己确认型号。
>
> 注意这里的威胁模型与「数据备份」不同：驱动备份防的是「C 盘被格式化」这一件事，D 盘与 C 盘是否同属一块物理磁盘**不影响**它。所以导出到 D 盘是完全合格的落点，不必像备份数据那样强求外置。

P0/P1/P2 tiering and the full export/verify procedure: `references/02-backup.md`.

### Stage 2 — Media and Driver Preparation

- Microsoft official page only: <https://www.microsoft.com/zh-cn/software-download/windows11>
- Download the ISO whose **SKU matches Step 0 fact 5**. Write it with Rufus set to **GPT / UEFI (not CSM/BIOS) / NTFS**; never select "Windows To Go".
- If no ≥8 GB USB is available, use the Media Creation Tool or cloud download reset as fallback. The installation assistant can only upgrade — it cannot clean install.
- There is **no permanent direct ISO link**: the link is session-generated and valid ~24 h, and the download API rejects external calls, so it cannot be scripted. Expect to complete "select edition → select language" in the browser.
- Pre-download your wireless and wired adapter drivers (fact 6) to a `Drivers\` folder on the USB stick. GPU drivers can generally come from Windows Update.
- Driver sources: the vendor support site by model/serial, and Intel Download Center for Intel parts.

Details, Rufus settings and the media checklist: `references/03-install-media.md`.

### Stage 3 — Pre-install Checks

1. Confirm disk controller mode (fact 2). **If the machine uses Intel VMD/RST, plan to load that driver at the installer's "Load driver" screen**, otherwise the internal disk will not appear at all.
2. Record Secure Boot state and confirm boot keys respond: **F1** enters BIOS Setup (persistent settings), **F12** opens the one-time Boot Menu (this boot only). If neither registers, Fast Boot is likely swallowing the keypress — press **Enter** at the vendor logo for the Startup Interrupt Menu.
3. Disconnect unnecessary external storage; leave only the installer USB.
4. Connect the charger and keep it plugged in.

BIOS keys, Secure Boot policy, and verification commands: `references/07-bios.md`.

### Stage 4 — Install Execution

1. **F12** → **UEFI: <USB device>**.
2. Language → 立即安装.
3. Product key page → **「我没有产品密钥」** (actually in Chinese, since it's a Chinese doc — but keep English). Use local terms.
4. **If an edition list appears, the wrong multi-edition ISO was used** — stop and rebuild media matching fact 5. Never pick an item from that list; none of them matches the board license.
5. Choose **「自定义：仅安装 Windows（高级）」** — never "Upgrade".
6. Apply the partition red line using **your own** Step 0 snapshot.
7. OOBE: Home edition pushes Microsoft account sign-in; prefer accepting it so digital-license activation and cloud restore complete in one pass. `Shift+F10` → `oobe\bypassnro` is unreliable on Home.

### Stage 5 — Post-install Restore

Drivers first, because everything else needs network.

1. **Drivers, offline first — do not open Windows Update yet.** If there is no network, import the driver store exported in Stage 1 (admin PowerShell) and install **wireless first, then wired**: `pnputil /add-driver "<BackupDir>\Drivers\*.inf" /subdirs /install`. If that export is missing, fall back to the `Drivers\` folder on the USB stick. Only once an adapter actually works, continue with Device Manager → unknown devices → GPU → vendor utility (e.g. Lenovo Vantage) → Windows Update. See `references/04-drivers.md`.
2. Settings → System → Activation → confirm activated. If not, run the activation troubleshooter and sign in with the same Microsoft account.
3. Windows Update to the current cumulative.
4. **Verify the data partition is intact before going further.**
5. Install software from downloaded installers, running each manually — see `references/05-restore.md`. Work from the software list confirmed during intake, not from the bundled template.
6. VS Code extensions from the exported list, or enable Settings Sync.
7. Restore Secure Boot in BIOS if it was disabled (fact 8) and verify.
8. Remove `C:\Windows.old` via Settings → System → Storage → Temporary files.

Because there is no bulk unattended install, cross-check the finished machine against `installed-software.txt` so nothing needed is missed.

## Reference Files

| File | Contents |
| --- | --- |
| `references/01-preflight.md` | The eight pre-flight facts with commands to discover each on **your** machine |
| `references/02-backup.md` | P0/P1/P2 tiering, mandatory external-copy ordering, essential export/backup commands, verification procedure |
| `references/03-install-media.md` | Official download paths, Rufus settings, media and driver checklist |
| `references/04-drivers.md` | A/B/C driver triage method and `pnputil` export/import |
| `references/05-restore.md` | Installer-by-download restore method, example download sources, and install order |
| `references/06-risks.md` | Risk register with mitigations and a planning time budget |
| `references/07-bios.md` | Common startup-key functions, Secure Boot guidance, and verification commands |
