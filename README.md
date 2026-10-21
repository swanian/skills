# skills

个人 Agent Skills 集合，一个目录对应一个技能。每个技能包含 `SKILL.md`（触发条件与工作流），必要时附 `references/` 细节文档。

## 技能列表

### [win11-reinstall](win11-reinstall/SKILL.md) — Windows 11 干净重装

一套不依赖本机脚本的五阶段方法论，目标是在保留数据的前提下彻底重装 Windows 11：

1. **预检** — 机型 / BIOS、磁盘控制器模式（NVMe vs Intel VMD）、分区布局、BitLocker、SKU、网卡型号、SSH 密钥、Secure Boot
2. **备份** — P0/P1/P2 分级，先外置再本地暂存，导出软件清单、驱动库、WiFi 配置
3. **安装介质** — 官方 ISO，Rufus 按 GPT / UEFI 写入，网卡驱动提前离线备好
4. **安装执行** — 依据自己的预检快照选分区，绝不按索引或示例值操作
5. **恢复** — 先装驱动再开 Windows Update，随后激活、装软件、核对数据盘完整

技能内置的硬性约束：

- 动手前必须与使用者确认**备份清单**和**软件恢复清单**，内置模板只是待确认的默认值
- 分区、SKU、BitLocker 恢复密钥、离线驱动"死结"均有明确红线
- 附带 2026-10-15 在 Lenovo ThinkBook 14 G7+ IAH (21TK) 上的实测记录，仅作样例，不可照抄

触发词：重装系统 / 重做系统 / 全新安装 Windows 11 / 制作 Win11 安装 U 盘 / Windows 11 clean install。

## 目录结构

```text
skills/
└── win11-reinstall/
    ├── SKILL.md
    └── references/
        ├── 01-preflight.md
        ├── 02-backup.md
        ├── 03-install-media.md
        ├── 04-drivers.md
        ├── 05-restore.md
        ├── 06-risks.md
        └── 07-bios.md
```

## 使用方式

1. 克隆仓库：

   ```bash
   git clone https://github.com/swannian/skills.git
   ```

2. 把需要的技能目录放入所用 agent 客户端的 skills 目录，或直接将 `SKILL.md` 提供给 agent 加载。

3. 技能中的机型、分区、软件清单等示例值只对应作者当年那台机器，执行前请按 `references/01-preflight.md` 自行采集事实。

> 仓库文档不含序列号、密码或密钥。真正执行重装前，请自行核对备份范围与分区信息。
