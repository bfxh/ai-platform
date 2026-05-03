# Skills MCP 配置

本配置文件定义了 \python\MCP_Core\skills 中可用的 Skills 技能。

## 配置格式

每个 Skill 通过 `mcp_skill_server` 统一入口加载，路径指向 `\python\MCP_Core\skills\{skill_name}\skill.py`

## 已验证可用的 Skills (30个)

### GitHub 集成类
| Skill | 路径 | 功能 |
|-------|------|------|
| github_api_manager | `\python\MCP_Core\skills\github_api_manager\skill.py` | GitHub API 管理 |
| github_repo_manager | `\python\MCP_Core\skills\github_repo_manager\skill.py` | 仓库批量管理 |
| github_opensource | `\python\MCP_Core\skills\github_opensource\skill.py` | 开源项目支持 |
| github_nlp_search | `\python\MCP_Core\skills\github_nlp_search\skill.py` | NLP 智能搜索 |
| github_project_search | `\python\MCP_Core\skills\github_project_search\skill.py` | 项目搜索 |
| github_extended | `\python\MCP_Core\skills\github_extended\skill.py` | GitHub 扩展 |
| github_api_tester | `\python\MCP_Core\skills\github_api_tester\skill.py` | API 测试 |
| github_branch_analyzer | `\python\MCP_Core\skills\github_branch_analyzer\skill.py` | 分支分析 |
| github_data_analytics | `\python\MCP_Core\skills\github_data_analytics\skill.py` | 数据分析 |
| github_skill_discovery | `\python\MCP_Core\skills\github_skill_discovery\skill.py` | 技能发现 |
| github_skill_fuser | `\python\MCP_Core\skills\github_skill_fuser\skill.py` | 技能融合 |

### 开发效率类
| Skill | 路径 | 功能 |
|-------|------|------|
| auto_tester | `\python\MCP_Core\skills\auto_tester\skill.py` | 自动测试 |
| automated_testing | `\python\MCP_Core\skills\automated_testing\skill.py` | 自动化测试 |
| automated_workflow | `\python\MCP_Core\skills\automated_workflow\skill.py` | 自动化工作流 |
| project_doc_generator | `\python\MCP_Core\skills\project_doc_generator\skill.py` | 文档生成 |
| skill_reviewer | `\python\MCP_Core\skills\skill_reviewer\skill.py` | 代码审查 |
| continuous_integration | `\python\MCP_Core\skills\continuous_integration\skill.py` | 持续集成 |

### 系统管理类
| Skill | 路径 | 功能 |
|-------|------|------|
| system_optimizer | `\python\MCP_Core\skills\system_optimizer\skill.py` | 系统优化 |
| background_process_manager | `\python\MCP_Core\skills\background_process_manager\skill.py` | 后台进程 |
| software_location_manager | `\python\MCP_Core\skills\software_location_manager\skill.py` | 软件定位 |
| software_scanner | `\python\MCP_Core\skills\software_scanner\skill.py` | 软件扫描 |
| mempalace | `\python\MCP_Core\skills\mempalace\skill.py` | 记忆宫殿 |
| ask | `\python\MCP_Core\skills\ask\skill.py` | Agent Skill Kit |
| blender_mcp | `\python\MCP_Core\skills\blender_mcp\skill.py` | Blender 自然语言控制 |
| n8n_workflow | `\python\MCP_Core\skills\n8n_workflow\skill.py` | n8n 工作流自动化 |
| narsil_mcp | `\python\MCP_Core\skills\narsil_mcp\skill.py` | 代码分析工具 |

### 网络工具类
| Skill | 路径 | 功能 |
|-------|------|------|
| network_bypass | `\python\MCP_Core\skills\network_bypass\skill.py` | 网络突破 |
| ai_toolkit_manager | `\python\MCP_Core\skills\ai_toolkit_manager\skill.py` | AI 工具管理 |
| ai_toolkit_linkage | `\python\MCP_Core\skills\ai_toolkit_linkage\skill.py` | 工具联动 |
| ai_toolkit_ecosystem | `\python\MCP_Core\skills\ai_toolkit_ecosystem\skill.py` | 工具生态 |

## 加载方式

### 方式1: 通过 mcp_skill_server 统一加载
```python
# \python\MCP_Core\mcp_skill_server.py
# 支持动态加载所有 skills
```

### 方式2: 直接 MCP 配置引用
```json
{
  "mcpServers": {
    "system_optimizer": {
      "command": "python",
      "args": ["/python/MCP_Core/skills/system_optimizer/skill.py", "mcp"]
    }
  }
}
```

## 验证状态
- 创建时间: 2026-04-19
- Skills 总数: 30+
- 状态: 已验证结构正确
