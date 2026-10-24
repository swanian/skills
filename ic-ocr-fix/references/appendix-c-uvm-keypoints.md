# 附录C: UVM框架OCR关键点

> 本文件为 ic-ocr-fix 的参考材料，由 SKILL.md 按需引用，勿直接全文加载。

## 附录C: UVM框架OCR关键点

### C1: Factory机制关键字
```
type_id::create()       # 注意: type_id 不是 type id
set_type_override()     # 注意: set_type 不是 set type
`uvm_component_utils()  # 注意: 反引号不能丢，下划线不能少
```

### C2: Phase命名规范
```
build_phase / connect_phase / end_of_elaboration_phase
start_of_simulation_phase / run_phase / reset_phase
configure_phase / main_phase / shutdown_phase
check_phase / report_phase / final_phase
```
**OCR易错**: `build phase` → `build_phase` · `run phase` → `run_phase` · `main phase` → `main_phase`

### C3: TLM接口命名模式
```
uvm_<blocking|nonblocking>_<put|get|peek|transport>_<port|imp|export> #(T)
uvm_analysis_port #(T)   # 最常用，井号不能丢
```
**OCR易错**: `analysis port` → `analysis_port` · `#(T)` 不能写成 `(T)`

### C4: Config DB语法
```
uvm_config_db #(type)::set/get(null/this, "path", "field", value);
```
**OCR易错**: `uvm config db` → `uvm_config_db` · `#(type)::set` 不是 `::set`

### C5: UVM宏完整性
```
`uvm_info / `uvm_error / `uvm_warning / `uvm_fatal    # 信息宏
`uvm_field_int / `uvm_field_object / `uvm_field_string  # 字段宏
`uvm_component_utils / `uvm_object_utils               # 注册宏
```
**OCR易错**: 反引号 `` ` `` 丢失 · `uvm_info` 中间不能有空格 → `` `uvm_info ``

---
