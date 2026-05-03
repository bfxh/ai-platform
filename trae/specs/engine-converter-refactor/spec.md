# 引擎资产转换器重构 Spec

## Why
当前转换器存在6个核心问题：代码臃肿(2234行单文件)、路径硬编码、烘焙流程不稳定、拖拽工具与核心逻辑耦合、缺少错误恢复、没有配置文件。导致维护困难、换机器不能用、转换经常失败。

## What Changes
- **拆分核心模块**: engine_converter.py (2234L) → 5个独立模块，每个<500行
- **引入配置文件**: config.yaml 替代所有硬编码路径
- **统一烘焙管线**: Blender烘焙脚本独立为模板文件，支持自定义材质方案
- **解耦拖拽工具**: drag_convert.py 只做参数解析+调度，核心逻辑走模块API
- **错误恢复机制**: 转换失败时保存中间状态，支持断点续转
- **自动检测本机工具**: 启动时扫描本机已安装的Blender/Godot/UE5，自动配置

## Impact
- Affected code: engine_converter.py, engine_converter_extended.py, engine_converter_ui.py, drag_convert.py
- Affected plugins: engine_converter_plugins/ (4个插件)
- Affected configs: mcp-config.json, 桌面快捷方式

## ADDED Requirements

### Requirement: 模块化拆分
系统 SHALL 将 engine_converter.py 拆分为以下5个模块:
- `core/scanner.py` - 项目扫描与引擎检测
- `core/converters.py` - 转换器基类与7个引擎转换器
- `core/godot_builder.py` - Godot场景/材质/项目构建
- `core/blender_bridge.py` - Blender调用与烘焙管线
- `core/cli.py` - CLI入口与MCP服务注册

#### Scenario: 模块导入成功
- **WHEN** 执行 `from core.scanner import analyze_project`
- **THEN** 模块正常导入，无循环依赖

#### Scenario: 单模块可独立测试
- **WHEN** 单独运行 `python -m core.scanner`
- **THEN** 执行自检测试通过

### Requirement: 配置文件
系统 SHALL 使用 `config.yaml` 管理所有可配置项，不再硬编码路径。

#### Scenario: 首次启动自动生成配置
- **WHEN** config.yaml 不存在时启动工具
- **THEN** 自动扫描本机已安装软件，生成config.yaml

#### Scenario: 换机器后重新配置
- **WHEN** 用户在新机器上运行工具
- **THEN** 提示"检测到新环境，是否重新扫描？"，自动发现本机工具

#### Scenario: 配置项覆盖
- **WHEN** 用户修改config.yaml中的blender_path
- **THEN** 后续所有操作使用新路径，无需改代码

### Requirement: 统一烘焙管线
系统 SHALL 将Blender烘焙脚本从Python字符串模板改为独立.py模板文件，支持材质方案切换。

#### Scenario: 使用默认材质方案
- **WHEN** 拖入一个无材质的OBJ文件
- **THEN** 自动使用"蓝青金属"默认方案烘焙，输出484KB+ GLB

#### Scenario: 使用自定义材质方案
- **WHEN** 用户在config.yaml中指定 material_preset: "warm_metallic"
- **THEN** 使用对应模板烘焙，输出暖色金属效果

#### Scenario: 保留原始材质
- **WHEN** 拖入一个已有贴图的FBX文件
- **THEN** 跳过程序化材质生成，只做格式转换，保留原始贴图

### Requirement: 错误恢复
系统 SHALL 在转换失败时保存中间状态，支持断点续转。

#### Scenario: Blender崩溃后恢复
- **WHEN** Blender烘焙过程中崩溃
- **THEN** 保存已完成的步骤到 .convert_state.json，下次运行时跳过已完成步骤

#### Scenario: Godot导入失败后重试
- **WHEN** Godot headless导入返回非零退出码
- **THEN** 清理.import缓存后重试一次，仍失败则记录到日志

### Requirement: 自动检测本机工具
系统 SHALL 启动时自动扫描本机已安装的3D软件。

#### Scenario: 扫描发现多个版本
- **WHEN** 本机安装了Godot 4.3和4.6.1
- **THEN** 自动选择最新版本，并在config.yaml中记录所有版本

#### Scenario: 找不到必要工具
- **WHEN** 本机没有安装Blender
- **THEN** 提示"Blender未找到，烘焙功能不可用。仅支持GLB/DirectCopy模式"

## MODIFIED Requirements

### Requirement: 拖拽转换工具
原 drag_convert.py 将BLENDER_SCRIPT作为内嵌字符串(约200行Python代码)。
修改为：从 `bake_templates/` 目录加载模板文件，通过参数替换注入变量。

### Requirement: 转换矩阵
原 engine_converter_extended.py 中 get_full_conversion_matrix() 返回硬编码字典。
修改为：从 `conversion_matrix.yaml` 加载，支持用户自定义扩展。

## REMOVED Requirements

### Requirement: 硬编码路径
**Reason**: 换机器就不能用，必须改为配置文件
**Migration**: 所有硬编码路径迁移到 config.yaml

### Requirement: 单文件架构
**Reason**: 2234行单文件无法维护
**Migration**: 拆分为5个模块 + 配置文件 + 模板文件
