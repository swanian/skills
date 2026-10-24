# 附录B: 自动检测正则表达式库

> 本文件为 ic-ocr-fix 的参考材料，由 SKILL.md 按需引用，勿直接全文加载。

## 附录B: 自动检测正则表达式库

### B1: 可直接使用的检测模式

以下正则表达式可用于批量扫描文件，快速定位潜在的OCR错误。

#### 类型1: 数字↔字母混淆检测

```regex
# P0: 时间单位前的混淆字符 (字母出现在数字位)
/\brun\s+[0-9]*[lIOoSsZz][0-9]*\s*(us|ns|ps|fs|ms)\b/  # run lus, run l0us, run 1Ous
# 注意: 勿用 /run [a-zA-Z]+us/ — 会误报合法命令 "run status"

# P0: 数字0前缀的混淆 (l0, O0, I0等)
/\b[a-zA-Z]0(us|ns|ps|fs|ms)\b/i   # l0us, O0ns, I0ps 等
/\b[a-zA-Z]0\d+(us|ns|ps|fs|ms)\b/i # l010us 等
# 注意: 勿用 /\b[a-zA-Z]0[unspms]/i — [unspms] 是单字符集合而非单位列表

# P1: 十六进制数中的非法字母 (O/I/l 不是合法hex数字，S/Z 亦不合法)
/0[xX][0-9a-fA-F]*[OoIiIlSsZz][0-9a-fA-F]*/  # 0xO123, 0xlF00, 0xABZ 等
/'[hH][0-9a-fA-F]*[OoIiIlSsZz][0-9a-fA-F]*/  # 'hOFF, 'hl00, 'h1SZ 等

# P2: 纯数字上下文中的字母 (排除合法时间单位 us/ns/ps/fs/ms)
/\b\d+[a-zA-Z]\b(?!\w)(?!(us|ns|ps|fs|ms)\b)/  # 123a, 456b (排除合法标识符)
/[a-zA-Z]\d+\b(?=[^\w]|$)/      # a123, b456 (行尾或标点前)
```

#### 类型2: 编辑器伪影检测

```regex
# P0: SV关键字前的伪影符号
/^>[^>].*\b(class|function|task|module|package|interface)\b/m
/^>>-.*\b(super|end|begin|else|join)\b/m
/^>-.*\b(rand|int|logic|bit|string|real|enum)\b/m

# P1: UVM宏前的伪影
/^>>-.*`uvm_/m
/^>-.*`uvm_/m
/^>`uvm_/m

# P2: 通用行首伪影 (需人工确认)
/^>[^> ]/m                      # 单>后非空格
/^>>-/m                          # 折叠标记
/^>-/m                           # 变量标记
```

#### 类型3: TCL/RAL命令错误检测

```regex
# P0: RAL单冒号错误 (应为双冒号)
/\bral:[wrds]\b/i               # ral:w r, ral:r d 等
/\bral_source\b/i                # 缺少双冒号

# P1: TCL命令拼写错误
/\brun\s+[a-z]us/i              # run命令时间单位
/\bral\s*:\s*:\s*(?!check)/i     # ral:: 后跟非标准命令

# P2: TCL注释中可能的下划线丢失
/^#\S+\s+.*(?<!_)\s*(field|reg|pkt|cfg|env|agent)/mi
# 注释中包含关键词但前面没有下划线
```

#### 类型4: SystemVerilog关键字完整性检测

```regex
# P0: UVM宏反引号缺失
/(?<!`)uvm_(component|object)_utils\b/i
/(?<!`)uvm_info\s*\(/i
/(?<!`)uvm_error\s*\(/i

# P1: UVM Factory机制
/type_id\s*::\s*create/i        # 空格异常
/uvm_factory\s*::\s*get/i
/set_type_override\s*\(/i

# P2: 类继承关键字
/\bclass\s+\w+\s+extends\s+/i   # extends前后应有空格
/\bvirtual\s+(function|task)\b/i  # virtual与function/task间空格
```

#### 类型5: 格式结构问题检测

```regex
# P0: 缺失分号 (语句末尾)
/^\s*(return|break|continue)\s*[^;{\n]/m  # 控制语句缺分号
/\w\s*=\s*[^=;\n].*$/m                    # 赋值语句可能缺分号

# P1: 括号不匹配提示 (简单检测)
/\(\s*$|\[\s*$|\{\s*$/m             # 开括号在行尾(可能是多行)

# P2: 异常空格
/\w\s{2,}\w/                       # 多个连续空格在单词间
/\w\s+\(/                           # 函数调用前多余空格(可接受但可疑)

# P3: UVM消息字符串断行 (高频)
/"[^"]*\n\s*"[^"]*\)/m             # 字符串中间被换行截断
/"[^"]*(finished|started|execute)\n\s*"/m  # 常见UVM消息动词断行
/`uvm_info\(.*\n.*UVM_HIGH/m       # uvm_info调用跨多行
/`uvm_error\(.*\n.*UVM_NONE/m      # uvm_error调用跨多行

# P4: $sformatf() 格式化参数断行
/\$sformatf\(.*%0*d\s*\n.*\$realtime/m  # 格式化说明符与参数分离
/\(.*fatals.*\n.*errors.*\n.*warnings/m  # 多参数统计信息断行

# P5: 单词被换行符断开 (高频)
/\w{3,}\n\w+\./m                   # 长单词+换行+后缀+句点 (如 stall\ned.)
/\w{3,}\ned\b/m                    # 过去式词尾-ed被断开
/\w{3,}\ning\b/m                   # 现在分词-ing被断开

# P6: 表达式/运算符断行
/==\s*\n\s*\w+/m                   # 等号比较操作数跨行
/!=\s*\n\s*\w+/m                   # 不等号比较操作数跨行
/::\w+\(\)\s*\n\s*\)/m            # 函数调用结尾括号跨行
/,\s*\n\s*[a-z_]+::/m              # 参数列表中函数名跨行
```

---

### B2: 批量扫描脚本使用指南

#### PowerShell快速扫描脚本

```powershell
# 扫描指定目录下的所有SV/TCL文件
# 关键: -match 默认 ^ $ 只匹配整个字符串首尾, 必须加 (?m) 才能按行锚定
Get-ChildItem -Path "./project" -Recurse -Include *.sv,*.tcl,*.v |
ForEach-Object {
    $content = Get-Content $_.FullName -Raw

    # 检查类型1: 时间单位错误
    if ($content -match '\brun\s+[0-9]*[lIOoSsZz][0-9]*\s*(us|ns|ps|fs|ms)\b') {
        Write-Host "WARN $($_.FullName): 潜在的时间单位混淆"
    }

    # 检查类型2: 行首伪影符号 (必须 (?m))
    if ($content -match '(?m)^(?:>>-|>-|>)(?=[A-Za-z_`])') {
        Write-Host "WARN $($_.FullName): 发现行首伪影符号"
    }

    # 检查类型3: RAL命令单冒号错误
    if ($content -match '\bral:[wrds]\b') {
        Write-Host "WARN $($_.FullName): 发现RAL命令冒号错误"
    }

    # 检查类型4: 十六进制含非法字符 (l/O/I 不是合法hex)
    if ($content -match "(?:0[xX]|'[hH])[0-9a-fA-F]*[OoIiIlSsZz][0-9a-fA-F]*") {
        Write-Host "WARN $($_.FullName): 发现十六进制疑似混淆"
    }

    # 检查类型5: 字符串被换行截断 (逐行数引号奇偶)
    for ($i=0; $i -lt $content.Split("`n").Count; $i++) {
        if ($content.Split("`n")[$i].TrimStart().StartsWith('#')) { continue }
        if (($content.Split("`n")[$i].ToCharArray() | Where-Object {$_ -eq '"'}).Count % 2 -eq 1) {
            Write-Host "WARN $($_.FullName):L$($i+1) 字符串疑似被换行截断"
        }
    }
}
```

#### 使用建议

1. **首次扫描**: 对整个项目运行一次全量扫描，建立基线
2. **增量扫描**: 每次写入新文件后，只扫描该文件
3. **定期审查**: 每完成一个子目录后，进行一次全面复查
4. **误报处理**: 正则匹配会有误报，需要人工判断是否真的有错误

---
