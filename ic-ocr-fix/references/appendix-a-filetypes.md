# 附录A: 更多文件类型的专项规则

> 本文件为 ic-ocr-fix 的参考材料，由 SKILL.md 按需引用，勿直接全文加载。

## 附录A: 更多文件类型的专项规则

### A1: RALF文件 (`.ralf`) OCR错误处理

**文件特征**: RALF是Synopsys RAL寄存器抽象层的专用格式，用于定义寄存器模型。

#### 常见RALF关键字（必须完整）

```ralf
# 顶层结构关键字:
system <name> { ... }           # 系统定义
block <name> { ... }            # 寄存器块定义
register <name> @ <addr> { ... } # 寄存器定义
field <name> [<bits>] { ... }   # 字段定义

# 属性关键字:
accesses = rw / ro / wo / w1c   # 访问类型
reset = <value>                 # 复位值
size = <bits>                   # 位宽
cover = on/off                  # 覆盖率开关
```

#### OCR易错点

| 错误模式 | 正确形式 | 说明 |
|----------|----------|------|
| `b1ock` | `block` | 数字0→字母O混淆 |
| `regi ster` | `register` | 空格插入 |
| `fi eld` | `field` | 空格插入 |
| `acce sses` | `accesses` | 空格插入 |
| `re set` | `reset` | 空格插入 |
| `@` 符号丢失 | `register NAME @ ADDR` | 地址声明符被忽略 |
| `{` `}` 不匹配 | block/register体 | 括号数量错误 |

#### RALF语法完整性检查

```ralf
# 标准结构模板:
system top_sys {
    // 必须包含 source 引用
    path = "path/to/rtl";

    block sys_reg {
        // 必须包含 @地址
        register ctrl_reg @ 'h100 {
            // 字段必须有 [start:end] 或 [bit]
            field enable [0] {
                access = rw;
                reset = 'h0;
                cover = on;
            }
        }
    }
}

# OCR破坏示例:
# ❌ system top_sys{ (缺少空格)
# ✅ system top_sys {

# ❌ register ctrl_reg h100 { (缺少@)
# ✅ register ctrl_reg @ 'h100 {

# ❌ field enable[0]{ (缺少空格)
# ✅ field enable [0] {
```

#### 特殊字符保护

**十六进制地址格式**:
```ralf
# 标准: @ 'hADDR 或 @ 0xADDR
# OCR易错:
'hl00      → 'h100     # l→1
'hOFF       → 'h0FF     # O→0
0xABC       → 0xABC     # 通常正确
0xABD       → 0xABO?   # O可能混入
```

---

### A2: Makefile/Shell脚本 OCR错误

**文件特征**: 包含大量特殊字符（`$`, `()`, `{}`, Tab等），OCR极易出错。

#### 关键符号保护规则

| 符号 | 用途 | OCR常见错误 | 保护策略 |
|------|------|------------|----------|
| `$()` | 变量引用 | `$()`, `$ ()`, `$()` 丢失 | 确保紧邻无空格 |
| `${VAR}` | 变量引用 | `${ VAR}`, `$VAR` | 保持花括号和内部紧凑 |
| `$(shell cmd)` | Shell命令执行 | `(shell cmd)`, `$( shell)` | 双括号必须成对 |
| `\` | 行续接符 | 丢失或变为 `/` 或 `-` | 行末必须保留 |
| `Tab` | Makefile缩进 | 变为空格（致命错误） | **必须用Tab不能用空格** |
| `#` | 注释符 | 丢失或变为数字 | 行首#必须保留 |
| `:=/?=+=` | 赋值操作符 | `=`, `: =`, `+ =` | 操作符不能有空格 |

#### Makefile特定检查

```makefile
# 目标依赖规则:
target: dependency1 dependency2
<TAB>command1
<TAB>command2

# OCR错误:
# ❌ target:dependency (缺少空格)
# ✅ target: dependency

# ❌ command前用空格代替Tab (Makefile会报错)
# ✅ command前必须是Tab字符

# 变量赋值:
CC = gcc          # 递归展开
CFLAGS := -Wall   # 简单展开
OBJ += main.o     # 追加

# OCR易错:
CC= gcc           # ⚠️ 可能正确但风格不佳
CFLAGS : = -Wall  # ❌ 冒号后有空格
OBJ + = main.o    # ❌ 加号后有空格
```

#### Shell脚本变量引用

```bash
# 正确形式:
${VCS_HOME}/bin/vcs
${UVM_HOME}/src/uvm_pkg.sv
$(dirname $0)

# OCR错误:
$ VCS_HOME/bin/vcs       # 多余空格
${ VCS_HOME}/bin/vcs     # 花括号内空格
$ {UVM_HOME}/src/uvm...  # 分离的$
$( dirname $0)           # 括号内空格
```

---

### A3: Filelist文件 (`.f`) OCR错误

**文件特征**: 编译器使用的文件列表，每行一个文件路径，支持注释和条件编译。

#### 标准格式规范

```f
# 注释行以#开头
-f sub_file.f           # 包含其他filelist
+incdir+/path/to/include # 包含目录
-fileline               # 显示行号选项
-timescale=1ns/100ps    # 时间精度

/path/to/file1.sv
/path/to/file2.sv
$path_env/file3.v
```

#### OCR易错模式

| 错误模式 | 正确形式 | 影响 |
|----------|----------|------|
| `-f` → `- f` | `-f sub.f` | 编译器无法识别include指令 |
| `+incdir+` → `+ incdir +` | `+incdir+/path` | include路径失效 |
| 路径分隔符 `/` → `\` | Unix路径 | Windows/Unix不兼容 |
| 文件扩展名 `.sv` → `.s v` | `file.sv` | 文件找不到 |
| 注释符 `#` 丢失 | `# comment` | 注释变代码导致编译错误 |

#### 路径格式检查

```f
# 绝对路径:
/home/user/project/env/apb_env.sv
d:/project/code/env/apb_env.sv

# 相对路径:
./env/apb_env.sv
../common/uvm_pkg.sv

# 环境变量路径:
$PRJ_ROOT/env/apb_env.sv
${PROJECT_DIR}/env/apb_env.sv

# OCR错误:
/home/user/project/env/apb env.sv  # 路径中空格
d:\project\code\env\apb_env.sv     # 反斜杠(Unix下错误)
./env/apb_env sv                  # 扩展名分离
$ PRJ ROOT/env/apb_env.sv         # 环境变量名空格
```

---

### A4: Verdi/调试配置文件

**文件特征**: 波形查看器配置，包含信号名、时间参数等。

#### 常见配置项

```tcl
# Verdi FSDB dump命令:
$fsdbDumpvars(0, top);           # Dump顶层所有信号
$fsdbDumpvars(1, top.u_agent);   # Dump指定实例
$fsdbDumpfile("wave.fsdb");      # 设置输出文件名

# 时间控制:
$fsdbDumpon;                     # 开始记录
$fsdbDumpoff;                    # 停止记录
```

#### OCR敏感点

- 函数名必须精确: `$fsdbDumpvars` 不能写成 `$fsdb Dumpvars`
- 参数中的层次路径: `top.u_agent.driver` 点号不能丢
- 文件名引号: `"wave.fsdb"` 双引号必须成对

---
