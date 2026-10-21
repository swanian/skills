# 阶段二：镜像与安装介质

配套 SKILL.md Stage 2。

> 本文件中的机型、容量、版本号均为**示例**。介质与 SKU 的选择取决于 `references/01-preflight.md` 的事实 5 与事实 6。

官方唯一入口：<https://www.microsoft.com/zh-cn/software-download/windows11>（页面标注「Windows 11 2026 更新 | 版本 26H2」）。

**红线**：不用任何第三方 Ghost/精简/激活镜像。多数预装 Windows 的机器使用**绑主板的 OEM 数字许可证**（Step 0 事实 5 可确认），官方介质联网即可自动激活，无需任何激活工具。

## 四条官方途径

| 途径 | 产物 | 适用场景 |
| --- | --- | --- |
| ① 媒体创建工具 | `MediaCreationTool.exe` | 一步完成下载+写盘，最省事；不愿配置 Rufus 或 U 盘不太合适时用它兜底 |
| ② 直接下载 ISO | 约 5 GB `.iso` | 用 Rufus 写盘、留档复用；**本次选定**，与 SKU 精确匹配 |
| ③ 安装助手 | 就地升级 | 只能升级，**不能干净安装** |
| ④ 云下载重置 | 无需介质 | 手边没有 ≥8 GB U 盘时兜底 |

## ISO 下载接口实测（2026-10-15）

**结论：媒体创建工具有永久直链，ISO 没有。**

| 项 | 媒体创建工具 | ISO 映像 |
| --- | --- | --- |
| 链接性质 | **固定直链**，长期有效 | **会话动态生成**，有效期 **24 小时** |
| 能否绕过页面 | 能 | **不能**——接口拒绝外部调用 |
| 点不动的主因 | 浏览器/网络拦截 | 未先完成「选版本 → 选语言」两步，按钮不会激活 |

调用 `software-download-connector/api/GetProductDownloadLinksBySku`，带 `skuId` / `releaseId` / `geo` / `locale` 各种组合的 GET 全部返回 **400**，POST 返回 **405**。接口只接受带完整浏览器会话的请求，脚本取不到链接，**不存在可粘贴的 ISO 永久直链**。

> 因此自动化脚本无法直接取到 ISO 链接；需要在浏览器中完成「选版本 → 选语言」两步后下载。

## Rufus 路线设置

ISO 约 5 GB，文件名随所选版本与语言而定（形如 `Win11_<版本>_<语言>_x64.iso`）。可暂存到本地另一分区留出余量，**但若它与待重装的系统盘同属一块物理磁盘，装前须把 ISO 一并挪到外部介质**。

Rufus 须设 **GPT / UEFI（非 CSM 或 BIOS）/ NTFS**，切勿选「Windows To Go」。Arm64 镜像不适用 Intel/AMD 机型——按 Step 0 事实 1 的 CPU 选择。

## 介质与驱动清单

**驱动项请替换为 Step 0 事实 6 里你自己查到的网卡与机型**，下面仅为示例。
| --- | --- | --- |
| U 盘 | ≥ 8 GB，内容会被清空 | 用官方 Media Creation Tool 制作，或官方 ISO + Rufus 写入 |
| 无线驱动 | Intel Wi-Fi 7 BE200 驱动包 | **必下**：装完能否联网的前提 |
| 有线驱动 | Intel Ethernet I219-V 驱动包 | **必下**：无线失效时的兜底联网路径 |
| 音频驱动 | 联想音频包（Realtek + Dolby + Elevoc） | **必下**：B 类 8 项靠它一次性补齐 |
| 显卡驱动 | Intel Arc 130T（联想 21TK 定制版优先） | Windows Update 会推通用版；用定制版则需阻止 WU 覆盖 |
| 厂商驱动 | Lenovo Vantage / 热键 / 电源管理 | 联网后装 Vantage 自动补齐 |

## 三条环境提醒

- **虚拟化软件的兼容性**：机器若装有 VMware Workstation / VirtualBox 且已启用基于虚拟化的安全性（VBS），改开 Hyper-V 会让它们跑在 WHPX 后端，可能影响性能与嵌套虚拟化。**做嵌套虚拟化相关工作的务必先实测**，没有强需求就保持 Hyper-V 关闭。VBS 状态可查：

```powershell
(Get-CimInstance Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard).VirtualizationBasedSecurityStatus
```

- **企业授权**：机器上若装有企业 VPN、VDI 客户端、设备管控等企业组件（如 iNode、Horizon Client、企业 IM），**先向 IT 确认能否提供专业版授权与重装所需的审批流程**，不要自行下载安装包绕过管控——这类软件往往本身就应当由 IT 分发。
- **若要上专业版**：先用「家庭版（仅限中国）」装好并自动激活，再走 设置 → 系统 → 激活 → 升级你的 Windows 版本 → 打开商店（有 25 位 Pro 密钥则直接「更改产品密钥」）。升级在线完成不重装，Pro 许可证会绑主板+微软账号，此后重装可直接用「专业中文版本」ISO 自动激活。**不要跳过先激活家庭版这一步**；中国区 CoreCountrySpecific 在商店是否有 Pro 升级入口需自验，若无则只能走 25 位密钥。
