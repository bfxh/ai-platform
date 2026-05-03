# Tasks

- [x] Task 1: 创建项目结构和配置系统
  - [x] 1.1 创建 core/ 目录和 __init__.py
  - [x] 1.2 创建 config.yaml 默认配置模板
  - [x] 1.3 创建 core/config.py 配置加载器（支持自动扫描本机工具）
  - [x] 1.4 创建 core/scanner.py 项目扫描与引擎检测模块（从engine_converter.py提取analyze_project）
  - [x] 1.5 验证: `python -c "from core.config import Config; c = Config.load(); print(c.blender_path)"` 正常输出

- [x] Task 2: 拆分核心转换逻辑
  - [x] 2.1 创建 core/godot_builder.py（提取GodotSceneBuilder/GodotMaterialBuilder/GodotProjectInitializer）
  - [x] 2.2 创建 core/blender_bridge.py（提取Blender调用逻辑+烘焙管线）
  - [x] 2.3 创建 core/converters.py（提取7个转换器类，统一继承BaseConverter）
  - [x] 2.4 创建 core/cli.py（提取CLI入口+MCP服务注册）
  - [x] 2.5 验证: 模块导入测试通过

- [x] Task 3: 烘焙管线模板化
  - [x] 3.1 创建 bake_templates/ 目录
  - [x] 3.2 创建 bake_templates/default_cyan_metallic.py（蓝青金属默认方案）
  - [x] 3.3 创建 bake_templates/warm_metallic.py（暖色金属方案）
  - [x] 3.4 创建 bake_templates/preserve_original.py（保留原始材质方案）
  - [x] 3.5 修改 core/blender_bridge.py 支持模板加载和参数注入
  - [x] 3.6 验证: 模板加载和format注入成功

- [x] Task 4: 转换矩阵外部化
  - [x] 4.1 创建 conversion_matrix.yaml（从engine_converter_extended.py提取）
  - [x] 4.2 修改 engine_converter_extended.py 从yaml加载矩阵
  - [x] 4.3 验证: total_conversion_paths 输出1610

- [x] Task 5: 错误恢复机制
  - [x] 5.1 创建 core/state.py 转换状态管理（保存/恢复/清理）
  - [x] 5.2 修改 core/converters.py 在每个步骤完成后保存状态
  - [x] 5.3 修改 drag_convert.py 启动时检查是否有未完成的转换
  - [x] 5.4 验证: ConvertState 10项测试全部通过

- [x] Task 6: 重构拖拽工具和UI
  - [x] 6.1 重写 drag_convert.py 使用core模块API（删除270行内嵌BLENDER_SCRIPT）
  - [x] 6.2 重写 engine_converter_ui.py 使用core模块API（新增材质方案切换）
  - [x] 6.3 更新 拖拽转换.bat 和 启动转换器.bat
  - [x] 6.4 验证: 语法检查通过，core模块导入成功

- [x] Task 7: 端到端测试
  - [x] 7.1 OBJ → Godot（484KB GLB，有烘焙贴图）✅
  - [x] 7.2 STL → Godot（136.5KB GLB）✅
  - [x] 7.3 FBX → Godot（preserve_original方案，9.8KB）✅
  - [x] 7.4 GLB → Godot（427.8KB，含烘焙贴图）✅
  - [x] 7.5 换机器场景：删除config.yaml后自动扫描生成 ✅

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 2]
- [Task 5] depends on [Task 2]
- [Task 6] depends on [Task 2, Task 3, Task 5]
- [Task 7] depends on [Task 6]
- [Task 4] 独立，可与Task 2并行
