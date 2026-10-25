# skills

个人 Agent Skills 集合，一个目录一个技能。每个技能包含 `SKILL.md`（触发条件与工作流），必要时附 `references/` 细节文档。

## 技能

| 技能 | 说明 |
| --- | --- |
| [win11-reinstall](win11-reinstall/) | Windows 11 干净重装：预检、备份、安装介质、驱动、恢复。 |
| [screenshot-to-files](screenshot-to-files/) | 从截图重建目录与文件，写入代码内容并维护 PROGRESS.md。 |
| [ic-ocr-fix](ic-ocr-fix/) | 纠正截图识别代码的 OCR 误差：数字字母混淆、编辑器伪影、断行。 |
| [ocr-code-cleaner](ocr-code-cleaner/) | 清理 OCR 生成代码中的非代码内容，输出完整性与清理报告。 |

## 使用

```bash
git clone https://github.com/swannian/skills.git
```

将技能目录放入所用 agent 的 skills 目录即可。文档中的设备与软件信息仅作示例；公开分享前请检查设备指纹、个人信息、凭据和第三方材料。

> 当前文档未发现明文序列号、密码或密钥；这不代表所有设备信息都已匿名化。
