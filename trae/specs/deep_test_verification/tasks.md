# GSTACK 深度测试与验证 - 实施计划

## [ ] 任务 1: 创建单元测试目录结构和基础测试文件
- **优先级**: P0
- **依赖**: 无
- **描述**:
  - 创建测试目录结构 `\python\gstack_core\tests\`
  - 创建 conftest.py 基础测试配置
  - 创建测试辅助函数和工具
- **验收标准**: 测试目录结构正确，测试配置可用
- **测试要求**:
  - `programmatic` TR-1.1: 测试目录存在且结构正确
  - `programmatic` TR-1.2: pytest 能发现并运行测试

## [ ] 任务 2: ASK Skill 单元测试
- **优先级**: P0
- **依赖**: 任务 1
- **描述**:
  - 测试 ASK Skill 初始化
  - 测试技能加载功能 (tech_pulse, repo_visualizer, architect)
  - 测试技能执行功能
  - 测试错误处理
- **验收标准**: 所有 ASK Skill 测试通过
- **测试要求**:
  - `programmatic` TR-2.1: ASK Skill 能正确初始化
  - `programmatic` TR-2.2: 能成功加载默认技能
  - `programmatic` TR-2.3: 能正确执行 tech_pulse 技能
  - `programmatic` TR-2.4: 能正确执行 repo_visualizer 技能（传入有效路径）
  - `programmatic` TR-2.5: 能正确执行 architect 技能（传入有效描述）
  - `programmatic` TR-2.6: 错误技能名称返回错误

## [x] 任务 3: Blender MCP 单元测试
- **优先级**: P0
- **依赖**: 任务 1
- **描述**:
  - 测试 Blender MCP 配置加载
  - 测试 HTTP API 响应格式
  - 测试命令解析功能
  - 测试错误处理
- **验收标准**: 所有 Blender MCP 测试通过
- **测试要求**:
  - `programmatic` TR-3.1: 配置正确加载
  - `programmatic` TR-3.2: HTTP API 返回正确格式
  - `programmatic` TR-3.3: 命令解析正确
  - `programmatic` TR-3.4: 未知命令返回错误

## [x] 任务 4: Narsil MCP 单元测试
- **优先级**: P0
- **依赖**: 任务 1
- **描述**:
  - 测试代码分析器初始化
  - 测试符号提取功能
  - 测试导入分析功能
  - 测试复杂度计算功能
  - 测试问题检测功能
- **验收标准**: 所有 Narsil MCP 测试通过
- **测试要求**:
  - `programmatic` TR-4.1: 代码分析器正确初始化
  - `programmatic` TR-4.2: 能正确提取函数和类
  - `programmatic` TR-4.3: 能正确分析导入
  - `programmatic` TR-4.4: 能正确计算复杂度
  - `programmatic` TR-4.5: 能正确检测硬编码路径
  - `programmatic` TR-4.6: 能正确检测空异常处理

## [ ] 任务 5: n8n Workflow 单元测试
- **优先级**: P0
- **依赖**: 任务 1
- **描述**:
  - 测试 n8n 配置加载
  - 测试 Docker 检测功能
  - 测试服务状态检查
  - 测试工作流列表功能
- **验收标准**: 所有 n8n Workflow 测试通过
- **测试要求**:
  - `programmatic` TR-5.1: 配置正确加载
  - `programmatic` TR-5.2: 能正确检测 Docker 安装状态
  - `programmatic` TR-5.3: 能正确检查服务状态
  - `programmatic` TR-5.4: 能正确列出工作流模板

## [ ] 任务 6: GSTACK Commands 集成测试
- **优先级**: P0
- **依赖**: 任务 1
- **描述**:
  - 测试 gstack anchor 命令
  - 测试 gstack log 命令
  - 测试 gstack memo 命令
  - 测试 gstack blender 命令
  - 测试 gstack workflow 命令
  - 测试 gstack narsil 命令
  - 测试 gstack ask 命令
- **验收标准**: 所有 GSTACK 命令测试通过
- **测试要求**:
  - `programmatic` TR-6.1: gstack anchor 返回锚点文本
  - `programmatic` TR-6.2: gstack log 正确记录错误
  - `programmatic` TR-6.3: gstack memo 正确保存记忆
  - `programmatic` TR-6.4: gstack blender 命令参数正确解析
  - `programmatic` TR-6.5: gstack workflow 命令参数正确解析
  - `programmatic` TR-6.6: gstack narsil 命令参数正确解析
  - `programmatic` TR-6.7: gstack ask 命令参数正确解析

## [ ] 任务 7: 安全测试
- **优先级**: P0
- **依赖**: 任务 1
- **描述**:
  - 测试路径注入防护
  - 测试命令注入防护
  - 测试文件权限
  - 测试敏感信息泄露
- **验收标准**: 所有安全测试通过
- **测试要求**:
  - `programmatic` TR-7.1: 路径遍历攻击被拦截
  - `programmatic` TR-7.2: 命令注入被拦截
  - `programmatic` TR-7.3: 配置文件权限正确
  - `programmatic` TR-7.4: 无敏感信息泄露

## [x] 任务 8: 性能测试
- **优先级**: P1
- **依赖**: 任务 1
- **描述**:
  - 测试代码分析性能
  - 测试服务启动时间
  - 测试命令执行时间
- **验收标准**: 所有性能测试通过
- **测试要求**:
  - `programmatic` TR-8.1: 代码分析在 5 秒内完成
  - `programmatic` TR-8.2: 服务状态检查在 1 秒内完成
  - `programmatic` TR-8.3: 命令执行在 1 秒内完成

## [x] 任务 9: 生成测试报告
- **优先级**: P1
- **依赖**: 任务 2-8
- **描述**:
  - 汇总所有测试结果
  - 生成测试覆盖率报告
  - 生成性能基准报告
  - 生成安全问题报告
- **验收标准**: 测试报告完整准确
- **测试要求**:
  - `programmatic` TR-9.1: 测试覆盖率报告生成
  - `programmatic` TR-9.2: 性能基准报告生成
  - `programmatic` TR-9.3: 安全问题报告生成

## 任务依赖关系
```
任务 1 (创建测试基础)
    ↓
任务 2-5 (各模块单元测试) → 并行执行
    ↓
任务 6 (集成测试)
    ↓
任务 7 (安全测试) → 可并行执行
    ↓
任务 8 (性能测试) → 可并行执行
    ↓
任务 9 (生成报告)
```

## 测试文件清单
- `\python\gstack_core\tests\conftest.py` - pytest 配置
- `\python\gstack_core\tests\test_ask_skill.py` - ASK Skill 测试
- `\python\gstack_core\tests\test_blender_mcp.py` - Blender MCP 测试
- `\python\gstack_core\tests\test_narsil_mcp.py` - Narsil MCP 测试
- `\python\gstack_core\tests\test_n8n_workflow.py` - n8n Workflow 测试
- `\python\gstack_core\tests\test_gstack_commands.py` - GSTACK 命令测试
- `\python\gstack_core\tests\test_security.py` - 安全测试
- `\python\gstack_core\tests\test_performance.py` - 性能测试
- `\python\gstack_core\tests\test_report.py` - 测试报告生成
