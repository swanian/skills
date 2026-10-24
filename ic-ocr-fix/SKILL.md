---
name: "ic-ocr-fix"
description: "纠正IC验证项目代码中的OCR文字识别错误。当用户指出截图识别的代码有误、或发现数字/字母混淆、编辑器伪影符号等OCR误差时调用此skill。适用于SystemVerilog/TCL/Verilog等IC验证语言。"
---

# IC OCR Error Fixer - IC验证项目OCR错误纠正器

## 功能概述

专门用于检测和纠正从截图中识别IC验证代码时产生的**文字识别（OCR）误差**。覆盖SystemVerilog、TCL、Verilog等IC验证常用语言的典型错误模式。

## 触发条件

- 用户明确指出某行代码有"识别错误"或"OCR问题"
- 发现代码中出现不符合语法的字符组合（如 `run lus`, `l0us` 等）
- 代码中混入编辑器UI伪影（`>`, `>>-`, `>-` 等）
- 数字和字母混淆导致语义错误

---

## 错误分类与修正规则

### 类型1: 数字↔字母混淆（高频错误）

**特征**: OCR将数字误识别为字母，或反之

#### 常见混淆模式

| 错误模式 | 正确内容 | 出现场景 | 示例 |
|----------|----------|----------|------|
| `l` (小写L) | `1` (数字1) | 时间单位前缀 | `run lus` → `run 1us` |
| `l0` | `10` | 时间单位前缀 | `run l0us` → `run 10us` |
| `O` (大写O) | `0` (数字0) | 十六进制/地址 | `hO` → `h0`, `0xO` → `0x0` |
| `I` (大写i) | `1` (数字1) | 端口号/索引 | `port I` → `port 1` |
| `S` | `5` | 数值常量 | `value S` → `value 5` |
| `Z` | `2` | 位宽/数量 | `bit Z` → `bit 2` |

#### 检测方法

**上下文语法检查**:
```tcl
# 错误: run lus (lus不是合法的时间单位)
# 正确: run 1us, run 10us, run 100us
# 合法时间单位: us, ns, ps, fs, ms, s

# 错误: set delay l0ns
# 正确: set delay 10ns
```

**正则表达式匹配**:
- 查找 `run <含字母>us` → 应为 `run [0-9]+us`（注意排除合法命令 `run status`）
- 查找 `[a-zA-Z]0us` (排除 `10us`) → 应为 `[0-9]+0us`
- 查找 `0x[OoIiSsZz]` → 十六进制数中不应有字母O/I/S/Z

#### 自动修正规则

```
IF 字母出现在数字应出现的位置 AND 上下文要求数字
THEN 替换为对应的数字:
  - 小写 'l' 或大写 'I' 在行首/数字位 → '1'
  - 大写 'O' 在十六进制/地址中 → '0'
  - 大写 'S' 在数值常量中 → '5'
  - 大写 'Z' 在数值常量中 → '2'
```

---

### 类型2: 编辑器UI伪影符号

**特征**: 截图时捕获到编辑器的折叠标记、diff指示器等非代码内容

#### 常见伪影类型

| 符号 | 来源 | 出现位置 | 典型示例 |
|------|------|----------|----------|
| `>` | diff视图/折叠标记 | 行首(函数/类定义) | `>function new(...)` |
| `>>-` | 代码折叠指示器 | 行首(函数体/宏) | `>>-super.new(...)` |
| `>-` | 变量声明标记 | 行首(rand变量) | `>-rand uvm_reg_field` |
| `*` | 文件修改标记 | 标题栏 | `[filename.sv]*` |
| `+` | 新增行标记(diff) | 行首 | `+this.cfg = ...` |
| `-` | 删除行标记(diff) | 行首 | `-old_code` |

#### SystemVerilog特定检测规则

**关键字前不应有特殊符号**:
```systemverilog
# 错误示例:
>function void build_phase(uvm_phase phase);
>>-super.build_phase(phase);
>-rand bit [31:0] data;
>>-`uvm_object_utils_begin(my_class)

# 正确示例:
function void build_phase(uvm_phase phase);
  super.build_phase(phase);
  rand bit [31:0] data;
  `uvm_object_utils_begin(my_class)
```

**宏调用前不应有折叠标记**:
```systemverilog
# 错误:
>>-`uvm_component_utils(apb_env)
>>-`uvm_info(get_type_name(), "msg", UVM_LOW)

# 正确:
`uvm_component_utils(apb_env)
`uvm_info(get_type_name(), "msg", UVM_LOW)
```

#### 修正流程

```
步骤1: 定位 → 搜索文件中所有 {>, >>-, >-, +, -} 的异常出现
步骤2: 分类 → 区分是diff标记还是代码中的合法运算符
步骤3: 移除 → 删除行首的伪影符号，保留实际代码
步骤4: 调整 → 补偿缩进（移除符号后可能需要添加空格）
步骤5: 验证 → 确保修正后符合SV/TCL语法规范
```

**缩进补偿表**:

| 移除的符号 | 需要补充的空格 | 说明 |
|-----------|---------------|------|
| `>` | 0空格 | 直接删除即可 |
| `>>-` | 2空格 | 保持原有缩进级别 |
| `>-` | 2空格 | 变量声明的标准缩进 |

---

### 类型3: TCL脚本特定错误

**特征**: TCL命令或参数被OCR破坏

#### 常见错误模式

| 错误类型 | 示例 | 正确形式 | 说明 |
|----------|------|----------|------|
| **命令拼写错误** | `ral:w r sys_reg` | `ral::wr sys_reg` | 冒号→字母w |
| **参数分隔符** | `set a${b}` | `set a ${b}` | 空格丢失 |
| **变量引用** | `$data` | `$data` 或 `${data}` | 可能正确需上下文判断 |
| **注释符** | `#svincr_pkt_num` | `#sv_incr_pkt_num` | 下划线丢失 |
| **路径分隔** | `source$PRJROOT/file` | `source $PRJROOT/file` | 空格丢失 |

#### RAL相关命令检查

```tcl
# 常见的RAL命令模式（必须准确）:
ral::wr <reg_name> <value>      # 写寄存器
ral::rd <reg_name>              # 读寄存器
ral::check <block_name>         # 检查寄存器块
ral::poll <reg_name> <field>    # 轮询寄存器字段
ral_source <file.ralf>          # 加载RALF文件

# OCR易错点:
- :: (双冒号) 易被识别为 : (单冒号) 或 w 或 W
- _ (下划线) 易被丢失或变为空格
- $ (美元符) 后的空格易丢失
```

#### 时间控制命令检查

```tcl
# 标准仿真时间命令:
run <time><unit>               # 运行指定时间
@<time>                         # 等待到指定时间
wait <signal>                   # 等待信号

# 单位必须是: us, ns, ps, fs, ms, s
# 数字必须是: 整数或浮点数

# 错误检测:
run lus     # ❌ lus不是有效时间 → 应为 1us
run l0us    # ❌ l0不是数字 → 应为 10us
run .5ns    # ✅ 浮点数可以
run 100ns   # ✅ 整数标准格式
```

---

### 类型4: SystemVerilog关键字/标识符错误

**特征**: SV保留字或用户定义标识符被破坏

#### 关键字完整性检查

**类/函数/任务定义**:
```systemverilog
# 必须完整的关键字序列:
class <name> extends <parent>;       # 类定义
function <type> <name>(<args>);       # 函数定义
task <name>(<args>);                  # 任务定义
virtual function/task <name>;         # 虚方法
extern function/task <name>;           # 外部声明

# OCR常见错误:
>class ...                            # 多余的 >
funct ion                             # 空格插入
virtualfunction                       # 缺少空格
```

**UVM宏完整性**:
```systemverilog
# 必须完整的UVM宏:
`uvm_component_utils(<class>)
`uvm_object_utils(<class>)
`uvm_component_utils_begin(<class>)
`uvm_field_<type>(<var>, UVM_ALL_ON)
`uvm_info(<id>, <msg>, <verbosity>)
`uvm_error(<id>, <msg>)
`uvm_fatal(<id>, <msg>)

# OCR易错点:
- 反引号 ` 丢失或变为 '
- 双引号 " 变为单引号 ' 或消失
- 逗号 , 后的空格丢失
- 参数括号 () 不匹配
```

#### 数据类型检查

```systemverilog
# 标准数据类型（必须准确）:
logic [n-1:0]        # 逻辑向量
bit [n-1:0]          # 位向量
int/integer          # 整数
real                 # 实数
string               # 字符串
enum {A, B, C}       # 枚举
struct { ... }       # 结构体

# OCR错误示例:
log ic               # ❌ 应为 logic
int eger             # ❌ 应为 integer
bi t                 # ❌ 应为 bit
logic[31: 0]         # ⚠️ 可能正确，但通常写作 logic [31:0]
```

---

### 类型5: 格式与结构破坏

**特征**: 代码的整体结构被OCR打乱

#### 常见结构错误

| 错误类型 | 表现 | 修正方法 |
|----------|------|----------|
| **换行丢失** | 多行合并为一行 | 根据语法恢复换行 |
| **多余换行** | 一行拆成多行 | 合并逻辑相关的行 |
| **缩进混乱** | 层级关系不清 | 根据 begin/end / {} 恢复缩进 |
| **括号不匹配** | (), [], {} 数量不对 | 补全缺失的括号 |
| **分号丢失** | 语句结束符缺失 | 在语句末尾补 ; |

#### SystemVerilog特定断行错误（高频）

**特征**: OCR将长字符串或表达式错误地拆分成多行，导致编译失败

##### 错误模式1: UVM消息字符串断行

```systemverilog
# ❌ 错误: 字符串中间被换行符截断
`uvm_info(get_type_name(), "end_of_elaboration_phase(): end_of_elaboration_phase() finished
", UVM_HIGH);

# ✅ 正确: 完整字符串在一行内
`uvm_info(get_type_name(), "end_of_elaboration_phase(): end_of_elaboration_phase() finished", UVM_HIGH);
```

**检测方法**: 查找以 `"` 开头但未在同一行闭合的字符串，且下一行以 `", UVM_` 或 `", UVM_NONE)` 结尾

---

##### 错误模式2: $sformatf() 格式化参数断行

```systemverilog
# ❌ 错误: 格式化字符串和参数被拆分到多行
`uvm_info(get_type_name(), $sformatf("\n\nSimulation *FAILED* at%15t  (%0d fatals, %0d
errors, %0d warnings) \n",
    $realtime, count_fatal, count_err, count_warning), UVM_NONE);

# ✅ 正确: 格式化参数完整在一行
`uvm_info(get_type_name(), $sformatf("\n\nSimulation *FAILED* at%15t  (%0d fatals, %0d errors, %0d warnings) \n",
    $realtime, count_fatal, count_err, count_warning), UVM_NONE);
```

**检测方法**: `$sformatf(` 后面的字符串跨越多行，或格式化说明符 `%0d` 被拆分

---

##### 错误模式3: 表达式/函数调用断行

```systemverilog
# ❌ 错误1: 单词被断开
//      `uvm_error(get_type_name(), "Simulation timeout, please find out why it stall
ed.");

# ✅ 正确1: 单词完整
//      `uvm_error(get_type_name(), "Simulation timeout, please find out why it stalled.");


# ❌ 错误2: 比较运算符和操作数被拆分
//if (!$cast(seq,factory.create_object_by_name("base_vseq",get_full_name(),"seq")) || seq==
null) begin

# ✅ 正确2: 表达式完整
//if (!$cast(seq,factory.create_object_by_name("base_vseq",get_full_name(),"seq")) || seq==null) begin


# ❌ 错误3: 函数调用跨行
//uvm_config_db #(uvm_object_wrapper)::set(this, "env.vsqr.main_phase", "default_sequence",
base_vseq::type_id::get());

# ✅ 正确3: 函数调用完整
//uvm_config_db #(uvm_object_wrapper)::set(this, "env.vsqr.main_phase", "default_sequence", base_vseq::type_id::get());
```

**检测方法**: 
- 连续字母被 `\n` 断开（如 `stall\ned.`）
- 运算符 `==`, `!=` 后紧跟换行
- 函数参数列表中 `,` 后紧跟换行但下一行不是参数而是延续上一行的内容

---

## 修正工作流

### 步骤1: 接收错误报告

**触发方式**:
- 用户直接指出: "第X行有OCR错误"
- 用户选中代码并提问: "这里对吗？"
- 自我发现异常时主动检查

**信息收集**:
```
□ 哪个文件？
□ 哪一行（或哪些行）？
□ 用户认为的正确内容是什么？（如果有）
□ 错误的表现形式是什么？
```

### 步骤2: 分析错误类型

**诊断决策树**:
```
是否包含非法字符(>, >>-, >-)?
├── 是 → 类型2: 编辑器伪影
└── 否 → 是否有数字/字母混淆?
    ├── 是 → 类型1: 数字↔字母混淆
    └── 否 → 是否是TCL脚本?
        ├── 是 → 类型3: TCL特定错误
        └── 否 → 是否是SV关键字/结构问题?
            ├── 是 → 类型4: SV关键字错误
            └── 否 → 是否有字符串/表达式断行? (高频OCR错误)
                ├── 字符串中间有换行符 → 类型5a: UVM消息字符串断行
                ├── $sformatf参数跨行 → 类型5b: 格式化参数断行
                ├── 单词被\n断开(stall\ned.) → 类型5c: 单词断行
                ├── 运算符后换行(==\nnull) → 类型5d: 表达式断行
                └── 其他结构问题 → 类型5: 通用格式破坏
```

### 步骤3: 执行修正

**通用修正原则**: 最小改动 · 保持原意 · 符合语法 · 记录变更

**铁律: 只修有依据的错误，禁止推导补全**

```
依据优先级（从高到低）:
1. 原图像素 — 用 tools/crop.py 裁剪目标行放大核对，这是最高置信来源
2. 语法规则 — 语言规范明确判定为非法
3. 上下文一致性 — 同文件同类结构的写法
4. 工程常识 — 仅在以上三条均无法判定时使用，且必须报告

禁止事项:
- 禁止按"看起来应该是什么"补全截图未覆盖的内容
- 截图缺页/模糊导致的缺失，一律留 [OCR-GAP] 或 FIXME 标记，交人工补拍
- 禁止为了让代码"能编译"而添加任何截图中不存在的语句
```

历史教训: 曾有 subagent 对缺屏区域按语义推导补全 35 行，产出看似完整实则
编造的代码，仅靠抽查分页边界才发现。**宁缺勿编。**

**批量模式时机（快模式）**: 处理批量转写产物时，ic-ocr-fix 的作用对象是**提取后的文本**，
不是截图：先对落盘文本做一遍纯文本规则扫描（关键字速查表、正则库、引号/括号/
begin-end 结构校验），一次性完成所有文本规则可判定的修正；仅对文本规则无法判定的
个别疑难字符（l/1、O/0 等）才裁原图放大回查。禁止为"验证"逐行回读截图——
那会抵消并行转写带来的速度收益。

**疑难字符回查原图**:

```bash
# 对可疑行（如 l/1/I、O/0 混淆）裁剪原图放大
python tools/crop.py <截图png> tmp_crop <band数> <scale倍率>
# 再用 Read 查看裁剪结果，直接看像素判定，不要靠正则猜
```

### 步骤4: 验证修正结果

**正则命中 ≠ 错误**。以下规则在合法代码上必然命中，只能作为候选清单，
必须逐条结合上下文确认，禁止直接批量替换:

| 规则 | 合法代码中的形态 |
|---|---|
| `\w\s{2,}\w` | 列对齐声明 `apb_env_cfg                cfg;` |
| `\w\s+\(` | `foo (x)` 合法调用 |
| 字母后跟数字 | 合法标识符 `sig1`、`x8720000` |
| 行尾开括号 | 合法的跨行函数调用 |

可靠的结构校验（推荐优先使用）:

```
□ 逐行统计 " 引号奇偶 — 奇数行 = 字符串被换行截断（需排除注释行）
□ 统计 ( [ { 与 ) ] } 深度 — 末态非 0 = 括号未闭合
□ 统计 begin/end 数量差 — 非 0 = 块结构不完整
□ 语法规范？ □ 无新错误？ □ 缩进一致？
```

### 步骤5: 报告修正内容

```
✅ 已修正 [文件路径]#L[行号]  [类型N]  [错误→正确]  [原因]
⛔ 未修正 [文件路径]#L[行号]  [原因: 截图缺页/模糊，已留 [OCR-GAP]]
```

---

## 快速参考卡片

### 高频错误速查表（TOP 10）

| 优先级 | 错误模式 | 正确形式 | 触发词 |
|--------|----------|----------|--------|
| 🔴 P0 | `run lus/l0us` | `run 1us/10us` | 时间命令 |
| 🔴 P0 | `>function/class` | `function/class` | SV定义 |
| 🟠 P1 | `>>-super/end` | `  super/end` | 函数体 |
| 🟠 P1 | `>-rand/int/logic` | `  rand/int/logic` | 变量声明 |
| 🟠 P1 | `ral:w r/d` | `ral::wr/rd` | RAL命令 |
| 🟡 P2 | `` `uvm_xxx `` 前有 `>>-` | `` `uvm_xxx `` | UVM宏 |
| 🟡 P2 | `#comment` 下划线丢失 | `#correct_comment` | TCL注释 |
| 🟢 P3 | `"finished\n"` 字符串断行 | `"finished"` | UVM消息 |
| 🟢 P3 | `stall\ned.` 单词断行 | `stalled.` | 任意位置 |
| 🟢 P3 | `==\nnull` 表达式断行 | `==null` | SV条件表达式 |

### SV关键字速查（前不能有 `>` `>>-` `>-`）
```
class, function, task, module, package, interface, rand, typedef,
virtual, extern, static, local, protected, pure, const, ref
```

### TCL/RAL命令速查（必须精确匹配）
```
ral::wr, ral::rd, ral::check, ral::poll, ral_source
set, get, proc, if, foreach, source, incr, run <时间><单位>
```

---

## 最佳实践

### 主动检查时机
- **写入新文件后**: 快速扫描
- **发现一处错误后**: 同一文件可能有多处同类错误
- **高风险模式**: `run` 命令(TCL)、`>` 符号(SV)、`ral::` 命令(RAL)

### 批量修正策略
```
统计位置 → 确认一致性 → 批量修正 → 统一报告
```
报告模板: `✅ [文件路径] 修正N处 [类型]  L[行1] [旧→新] ...`

---

*此 Skill 专注于IC验证项目的OCR错误纠正，强调准确性、最小改动原则和语言规范性。*

---


---

## 参考资料（按需加载）

以下文件包含详细规则库，遇到对应场景时用 Read 工具加载，不要一次性全文读入：

| 文件 | 内容 | 何时加载 |
|------|------|----------|
| `references/appendix-a-filetypes.md` | RALF / Makefile / Filelist / Verdi 配置专项规则 | 处理这四类文件时 |
| `references/appendix-b-regex-library.md` | 检测正则库 + PowerShell 扫描脚本 | 批量扫描定位疑点时 |
| `references/appendix-c-uvm-keypoints.md` | UVM Factory/Phase/TLM/ConfigDB/宏 关键点 | 校验 UVM 代码时 |
| `references/appendix-d-preventive-scan.md` | 写入前预检流程 + 高风险文件特征识别 | 大批量写入前 |
*此 Skill 专注于IC验证项目的OCR错误纠正，覆盖5大错误类型、正则检测库、多文件类型专项规则和预防性扫描机制。*
