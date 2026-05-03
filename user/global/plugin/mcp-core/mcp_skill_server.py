#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Skill Server - 将所有技能能力暴露给 TRAE
这是 TRAE 通过 MCP 协调用地技能的统一入口

工具列表（TRAE 直接调用）：
- nl_route: 然由到 Skill
- kb_search: 搜索知识
- kb_add: 添加到知识库
- kb_auto_extract: 从文动提取知
- skill_list: 列出有可 Skill
- skill_run: 运指 Skill
- github_search: 搜索 GitHub 项目
- github_install_skill:  GitHub 安新 Skill
- memory_read: 读取持久记忆
- memory_write: 写入持久记忆
"""

import json
import re
import sys
import os
import sqlite3
import subprocess
import urllib.request
import urllib.parse
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent))

#  导入核心模块 
try:
    from nl_router import nl_route, nl_suggest, nl_list_skills, NLRouter
    NL_AVAILABLE = True
except ImportError:
    NL_AVAILABLE = False

try:
    from knowledge_base import (
        KnowledgeBase, get_kb, kb_add, kb_search,
        kb_stats, kb_auto_extract, kb_summary, bootstrap_knowledge
    )
    KB_AVAILABLE = True
except ImportError:
    KB_AVAILABLE = False


#  径常 
AI_ROOT = Path("/python")
MCP_CORE = Path("/python/MCP_Core")
WB_SKILLS = Path("{USERPROFILE}/.workbuddy/skills")
MEMORY_DIR = Path("{USERPROFILE}/WorkBuddy/20260410084126/.workbuddy/memory")
MEMORY_MD = Path("{USERPROFILE}/.workbuddy/memory/MEMORY.md")
KB_PATH = Path("/python/MCP_Core/data/knowledge_base.db")


#  MCP 工具实现 

def tool_nl_route(query: str) -> Dict:
    """然由：输入句话，返回调用哪 Skill 以及参数"""
    if not NL_AVAILABLE:
        return {"error": "nl_router 模块加载"}
    return nl_route(query)


def tool_kb_search(query: str, top_k: int = 10) -> Dict:
    """搜索知识库，返回相关知识条目"""
    if not KB_AVAILABLE:
        return {"error": "knowledge_base 模块加载"}
    return kb_search(query)


def tool_kb_add(title: str, content: str, category: str = "general", importance: int = 5) -> Dict:
    """向知识库添加新知"""
    if not KB_AVAILABLE:
        return {"error": "knowledge_base 模块加载"}
    return kb_add(title, content, category=category, importance=importance)


def tool_kb_auto_extract(text: str) -> Dict:
    """从文动提取并保存知识（路径IP、配等）"""
    if not KB_AVAILABLE:
        return {"error": "knowledge_base 模块加载"}
    return kb_auto_extract(text)


def tool_skill_list() -> Dict:
    """列出有可 Skill（MCP Core + WorkBuddy"""
    skills = {
        "mcp_core_skills": [],
        "workbuddy_skills": [],
        "internal_skills": [
            "software_scanner",
            "project_doc_generator",
            "auto_tester",
            "network_bypass",
            "github_branch_analyzer",
            "github_skill_fuser",
        ],
    }

    # MCP Core Skills
    if MCP_CORE.exists():
        skills_dir = MCP_CORE / "skills"
        if skills_dir.exists():
            for d in skills_dir.iterdir():
                if d.is_dir() and not d.name.startswith("_"):
                    skill_file = d / "skill.py"
                    readme = d / "README.md"
                    desc = ""
                    if readme.exists():
                        try:
                            desc = readme.read_text(encoding="utf-8")[:100]
                        except Exception:
                            pass
                    skills["mcp_core_skills"].append({
                        "name": d.name,
                        "has_skill_py": skill_file.exists(),
                        "description": desc,
                    })

    # WorkBuddy Skills（只列前 50 ，太多了
    if WB_SKILLS.exists():
        wb_list = sorted([d.name for d in WB_SKILLS.iterdir() if d.is_dir()])
        skills["workbuddy_skills"] = wb_list[:50]
        skills["workbuddy_total"] = len(wb_list)

    return {"success": True, **skills}


def tool_software_search(name: str = "") -> Dict:
    """搜索件库（知识库 software_inventory """
    if not name:
        return {"error": "要提供软件名"}

    conn = sqlite3.connect(str(KB_PATH))
    try:
        rows = conn.execute("""
            SELECT name, path, category, size_mb
            FROM software_inventory
            WHERE name LIKE ? OR path LIKE ?
            ORDER BY size_mb DESC
            LIMIT 20
        """, (f"%{name}%", f"%{name}%")).fetchall()
    finally:
        conn.close()

    results = [
        {"name": r[0], "path": r[1], "category": r[2], "size_mb": r[3]}
        for r in rows
    ]

    return {
        "query": name,
        "found": len(results),
        "results": results,
    }


def tool_project_search(name: str = "") -> Dict:
    """搜索项目录（知识 project_inventory """
    if not name:
        return {"error": "要提供项名称"}

    conn = sqlite3.connect(str(KB_PATH))
    try:
        rows = conn.execute("""
            SELECT name, path, category
            FROM project_inventory
            WHERE name LIKE ? OR path LIKE ?
            LIMIT 20
        """, (f"%{name}%", f"%{name}%")).fetchall()
    finally:
        conn.close()

    results = [{"name": r[0], "path": r[1], "category": r[2]} for r in rows]

    return {
        "query": name,
        "found": len(results),
        "results": results,
    }


def tool_skill_run(skill_name: str, params: Dict = None) -> Dict:
    """直接运指 Skill"""
    if params is None:
        params = {}

    # 特殊能（内置处理，不依赖 skill.py
    INTERNAL_SKILLS = {
        "software_scanner": lambda p: _run_software_scanner(),
        "project_doc_generator": lambda p: _run_project_doc(p.get("project_path", "")),
        "auto_tester": lambda p: _run_auto_tester(p.get("mode", "all"), p.get("project", "")),
        "network_bypass": lambda p: tool_network_bypass(**p),
        "github_branch_analyzer": lambda p: tool_branch_analyze(p.get("repo_url", ""), p.get("action", "analyze")),
        "github_skill_fuser": lambda p: tool_skill_fuse(p.get("repo_url", ""), p.get("action", "install"), p.get("skill_name")),
    }

    if skill_name in INTERNAL_SKILLS:
        try:
            result = INTERNAL_SKILLS[skill_name](params)
            return {"success": True, "skill": skill_name, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    skill_path = MCP_CORE / "skills" / skill_name / "skill.py"

    if not skill_path.exists():
        return {
            "success": False,
            "error": f"Skill '{skill_name}' 不存在于 {skill_path}",
            "suggestion": "使用 github_search 工具查找并安装这 Skill",
        }

    try:
        cmd = [
            "python", str(skill_path),
        ]
        # 传参
        for k, v in params.items():
            if v:
                cmd.extend([f"--{k}", str(v)])

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60,
            encoding="utf-8"
        )

        if result.returncode == 0:
            try:
                return json.loads(result.stdout)
            except:
                return {"success": True, "output": result.stdout[-3000:]}
        else:
            return {"success": False, "error": result.stderr[-1000:]}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Skill 执超时（60秒）"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _run_software_scanner() -> Dict:
    """运软件扫描器"""
    import sys
    scanner_path = str(MCP_CORE / "skills" / "software_scanner")
    sys.path.insert(0, scanner_path)
    import skill as scanner_mod

    data = scanner_mod.scan_all()
    scanner_mod.write_to_knowledge_base(data)

    # 同时写入知识库中的软件条
    conn = sqlite3.connect(str(KB_PATH))
    conn.close()

    return {
        "exe_count": data["exe_count"],
        "project_count": data["project_count"],
        "scan_time": data["scan_time"],
    }


def _run_project_doc(project_path: str) -> Dict:
    """运项文档生成"""
    if not project_path:
        return {"error": "要提 project_path 参数"}

    import sys
    sys.path.insert(0, str(MCP_CORE / "skills" / "project_doc_generator"))
    import project_doc_generator as pdg

    result = pdg.generate_project_doc(project_path)
    if "error" not in result:
        doc_path = pdg.save_project_doc(project_path, result["document"])
        result["doc_path"] = doc_path

    return result


def _run_auto_tester(mode: str = "all", project: str = "") -> Dict:
    """运自动化测试"""
    import sys
    sys.path.insert(0, str(MCP_CORE / "skills" / "auto_tester"))
    import auto_tester as tester

    all_results = []

    if mode in ["software", "all"]:
        software_results = tester.test_all_software()
        all_results.extend(software_results)

    if mode in ["project", "all"]:
        for proj_key in tester.PROJECT_TEST_CONFIG:
            print(f"测试: {proj_key}...")
            all_results.append(tester.test_project(proj_key))

    # 保存历史
    tester.save_test_history(all_results)

    # 写知识库
    for result in all_results:
        tester.write_result_to_kb(result)

    passed = sum(1 for r in all_results if r.get("status") == "passed")
    failed = sum(1 for r in all_results if r.get("status") == "failed")

    return {
        "total": len(all_results),
        "passed": passed,
        "failed": failed,
        "results": all_results,
    }



def tool_network_bypass(action: str, url: str = None, dest: str = None, **kwargs) -> Dict:
    import sys
    sys.path.insert(0, str(MCP_CORE / 'skills' / 'network_bypass'))
    import skill as nb
    if action == 'probe-github':
        gh = nb.GitHubDownloader()
        return gh.probe_github()
    elif action == 'clone':
        gh = nb.GitHubDownloader()
        return gh.clone_repo(url, dest)
    elif action == 'analyze':
        gh = nb.GitHubDownloader()
        return gh.analyze_repo(url)
    elif action == 'download':
        d = nb.Downloader()
        return d.download_file(url, dest)
    else:
        return {'error': 'Unknown action: ' + action}

def tool_branch_analyze(repo_url: str, action: str = 'analyze') -> Dict:
    import sys
    sys.path.insert(0, str(MCP_CORE / 'skills' / 'github_branch_analyzer'))
    import skill as ba
    analyzer = ba.BranchAnalyzer()
    if action == 'analyze':
        return analyzer.analyze(repo_url)
    elif action == 'tree':
        m = re.match(r'https?://github.com/([^/]+)/([^/.]+)', repo_url)
        if not m:
            return {'error': 'Invalid URL'}
        gh = ba.GitHubBranchAnalyzer()
        return {'tree': gh.generate_branch_tree(m.group(1), m.group(2))}
    else:
        return {'error': 'Unknown action: ' + action}

def tool_skill_fuse(repo_url: str, action: str = 'install', skill_name: str = None) -> Dict:
    import sys
    sys.path.insert(0, str(MCP_CORE / 'skills' / 'github_skill_fuser'))
    import skill as sf
    fuser = sf.SkillFuser()
    if action == 'search-similar':
        return {'results': fuser.search_similar(repo_url)}
    elif action == 'analyze':
        return fuser.analyze_repo(repo_url)
    elif action == 'install':
        return fuser.install_skill(repo_url, skill_name=skill_name)
    else:
        return {'error': 'Unknown action: ' + action}

def tool_github_search(query: str, language: str = "", limit: int = 10) -> Dict:
    """
    搜索 GitHub 项目（用于发现可安为 Skill 的项
    使用 GitHub API（无 token，但有率限制
    """
    try:
        q = urllib.parse.quote(f"{query} in:name,description")
        if language:
            q += f"+language:{language}"
        
        url = f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page={limit}"
        
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "TRAE-AI-Agent/1.0")
        req.add_header("Accept", "application/vnd.github.v3+json")
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        
        repos = []
        for item in data.get("items", []):
            repos.append({
                "name": item["full_name"],
                "description": item.get("description", ""),
                "stars": item["stargazers_count"],
                "url": item["html_url"],
                "clone_url": item["clone_url"],
                "language": item.get("language", ""),
                "topics": item.get("topics", []),
            })
        
        return {
            "success": True,
            "query": query,
            "total_count": data.get("total_count", 0),
            "results": repos,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "fallback": "GitHub API 请求失败，可能需 token 或网络问",
        }


def tool_github_install_skill(repo_url: str, skill_name: str = "") -> Dict:
    """
     GitHub 克隆并安装为 MCP Skill
    动放 \python\MCP_Core\skills\ 录下
    """
    try:
        if not skill_name:
            skill_name = repo_url.rstrip("/").split("/")[-1]
            skill_name = skill_name.replace("-", "_").lower()
        
        target_dir = MCP_CORE / "skills" / skill_name
        
        if target_dir.exists():
            return {
                "success": False,
                "error": f"Skill '{skill_name}' 已存在于 {target_dir}",
            }
        
        # 克隆
        result = subprocess.run(
            ["git", "clone", repo_url, str(target_dir)],
            capture_output=True, text=True, timeout=60, encoding="utf-8"
        )
        
        if result.returncode != 0:
            return {"success": False, "error": result.stderr}
        
        # 查是否有 requirements.txt
        req_file = target_dir / "requirements.txt"
        if req_file.exists():
            pip_result = subprocess.run(
                ["python", "-m", "pip", "install", "-r", str(req_file), "-q"],
                capture_output=True, text=True, timeout=120, encoding="utf-8"
            )
            if pip_result.returncode != 0:
                return {
                    "success": True,
                    "warning": f"安完成但依赖安失: {pip_result.stderr[:200]}",
                    "skill_path": str(target_dir),
                }
        
        # 记录到知识库
        if KB_AVAILABLE:
            kb_add(
                title=f"已安装Skill: {skill_name}",
                content=f"来源: {repo_url}\n: {target_dir}",
                category="skill",
                importance=7,
            )
        
        return {
            "success": True,
            "skill_name": skill_name,
            "skill_path": str(target_dir),
            "message": f"Skill '{skill_name}' 安成",
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "克隆超时60秒）"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_memory_read(date: str = "") -> Dict:
    """读取持久记忆（MEMORY.md 或指定日期的日志"""
    if not date:
        #  MEMORY.md
        mem_file = MEMORY_MD
        if not mem_file.exists():
            # 尝试 workbuddy 
            mem_file = MEMORY_DIR / "MEMORY.md"
    else:
        mem_file = MEMORY_DIR / f"{date}.md"
    
    if not mem_file.exists():
        return {"success": False, "error": f"记忆文件不存: {mem_file}"}
    
    try:
        content = mem_file.read_text(encoding="utf-8")
        return {"success": True, "content": content, "path": str(mem_file)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_memory_write(content: str, date: str = "", append: bool = True) -> Dict:
    """写入持久记忆"""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    mem_file = MEMORY_DIR / f"{date}.md"
    
    try:
        if append and mem_file.exists():
            existing = mem_file.read_text(encoding="utf-8")
            new_content = existing + "\n" + content
        else:
            new_content = content
        
        mem_file.write_text(new_content, encoding="utf-8")
        return {"success": True, "path": str(mem_file), "date": date}
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_system_check() -> Dict:
    """系统状查：知识库路由Skill """
    status = {
        "nl_router": NL_AVAILABLE,
        "knowledge_base": KB_AVAILABLE,
        "mcp_core_exists": MCP_CORE.exists(),
        "workbuddy_skills_exists": WB_SKILLS.exists(),
        "memory_dir_exists": MEMORY_DIR.exists(),
    }
    
    if MCP_CORE.exists():
        skills_dir = MCP_CORE / "skills"
        if skills_dir.exists():
            skill_count = sum(1 for d in skills_dir.iterdir() if d.is_dir() and not d.name.startswith("_"))
            status["mcp_core_skill_count"] = skill_count
    
    if WB_SKILLS.exists():
        wb_count = sum(1 for d in WB_SKILLS.iterdir() if d.is_dir())
        status["workbuddy_skill_count"] = wb_count
    
    if KB_AVAILABLE:
        kb = get_kb()
        kb_status = kb.stats()
        status["knowledge_base_count"] = kb_status.get("total", 0)
    
    return {"success": True, "status": status}


# ================================================================
# 新增: Session Memory + File Protector 工具
# ================================================================

def tool_session_list(limit: int = 20) -> Dict:
    """列出最近的会话记录"""
    try:
        from core.infra_adapter import get_adapter
        adapter = get_adapter()
        sessions = adapter.list_recent_sessions(limit=limit)
        stats = adapter.get_session_stats()
        return {"success": True, "sessions": sessions, "stats": stats}
    except Exception as e:
        return {"success": False, "error": f"Session Memory 不可用: {e}"}


def tool_session_read(session_id: str = "") -> Dict:
    """读取指定会话或当前会话的上下文"""
    try:
        from core.infra_adapter import get_adapter
        adapter = get_adapter()
        if session_id and adapter._memory:
            ctx = adapter._memory.get_context(session_id)
        else:
            ctx = adapter.get_session_context()
        if ctx and ctx.get("available"):
            return {"success": True, **ctx}
        return {"success": False, "error": "会话不存在或未初始化"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_session_write(content: str, category: str = "mcp_tool") -> Dict:
    """写入当前会话记忆"""
    try:
        from core.infra_adapter import get_adapter
        adapter = get_adapter()
        if adapter._memory and adapter._session_id:
            adapter._memory.add_message(adapter._session_id, "user", content)
            return {"success": True, "session_id": adapter._session_id}
        return {"success": False, "error": "会话未初始化"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_file_protect(file_path: str) -> Dict:
    """将文件添加到保护列表（修改前自动备份）"""
    try:
        from core.infra_adapter import get_adapter
        adapter = get_adapter()
        if adapter.protect_file(file_path):
            return {"success": True, "file": file_path, "message": "文件已加入保护列表"}
        return {"success": False, "error": "File Protector 不可用"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_file_backup_before(file_path: str) -> Dict:
    """在修改文件前手动触发备份到 CC/2_old"""
    try:
        from core.infra_adapter import get_adapter
        adapter = get_adapter()
        if adapter.backup_before_modify(file_path):
            return {"success": True, "file": file_path, "message": "已备份到 CC/2_old"}
        return {"success": True, "file": file_path, "message": "文件未受保护或不存在，跳过备份"}
    except Exception as e:
        return {"success": False, "error": str(e)}


#  MCP 协处理（stdio 模式）─
TOOLS = {
    "nl_route": {
        "description": "然由到 Skill。输入用户的然指令，返回应该调用的 Skill 和提取的参数",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "用户的自然指令"}
            },
            "required": ["query"]
        }
    },
    "kb_search": {
        "description": "搜索知识库，获取已录的路径配、决策等信息",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键"},
                "top_k": {"type": "integer", "description": "返回条数", "default": 10}
            },
            "required": ["query"]
        }
    },
    "kb_add": {
        "description": "向知识库添加新知识（径配、决策偏好等",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"},
                "category": {"type": "string", "enum": ["path", "config", "decision", "pref", "project", "skill", "error", "general"]},
                "importance": {"type": "integer", "minimum": 1, "maximum": 10}
            },
            "required": ["title", "content"]
        }
    },
    "kb_auto_extract": {
        "description": "从一段文动提取并保存知识（路径IP、配等）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "要提取知识的文本"}
            },
            "required": ["text"]
        }
    },
    "skill_list": {
        "description": "列出有可 Skill（MCP Core  + WorkBuddy 能）",
        "inputSchema": {"type": "object", "properties": {}}
    },
    "skill_run": {
        "description": "运指定的 MCP Core Skill（含内置处理：software_scanner, project_doc_generator, auto_tester",
        "inputSchema": {
            "type": "object",
            "properties": {
                "skill_name": {"type": "string", "description": "Skill 名称"},
                "params": {"type": "object", "description": "调用参数"}
            },
            "required": ["skill_name"]
        }
    },
    "software_search": {
        "description": "搜索已扫描的件库（从知识 software_inventory 表查",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "件名称关"}
            },
            "required": ["name"]
        }
    },
    "project_search": {
        "description": "搜索已扫描的项目录（从知识库 project_inventory 表查",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "项目名称关键"}
            },
            "required": ["name"]
        }
    },
    "github_search": {
        "description": "搜索 GitHub 上的源项，用于发现可安为 Skill 的工",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "language": {"type": "string", "description": "编程过滤"},
                "limit": {"type": "integer", "default": 10}
            },
            "required": ["query"]
        }
    },
    "github_install_skill": {
        "description": " GitHub 克隆项目并安装为 Skill",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_url": {"type": "string", "description": "GitHub 仓库 URL"},
                "skill_name": {"type": "string", "description": "安后 Skill 名称（可选）"}
            },
            "required": ["repo_url"]
        }
    },
    "memory_read": {
        "description": "读取持久记忆（MEMORY.md 或指定日期的工作日志",
        "inputSchema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "日期 YYYY-MM-DD，空则 MEMORY.md"}
            }
        }
    },
    "memory_write": {
        "description": "写入持久记忆（自动按日期存储",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "date": {"type": "string"},
                "append": {"type": "boolean", "default": True}
            },
            "required": ["content"]
        }
    },
    "system_check": {
        "description": "查整 AI 系统的状态（知识库路由引擎Skill 录）",
        "inputSchema": {"type": "object", "properties": {}}
    },
    "session_list": {
        "description": "列出最近的会话记录（新 Session Memory 系统）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "返回条数，默认 20"}
            }
        }
    },
    "session_read": {
        "description": "读取指定会话的完整上下文和消息历史",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "会话 ID，空则读取当前"}
            }
        }
    },
    "session_write": {
        "description": "写入消息到当前会话记忆",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "消息内容"},
                "category": {"type": "string", "description": "分类标签"}
            },
            "required": ["content"]
        }
    },
    "file_protect": {
        "description": "将文件标记为受保护（修改前自动备份到 CC 缓存）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "相对于项目根的文件路径"}
            },
            "required": ["file_path"]
        }
    },
    "file_backup_before": {
        "description": "修改文件前手动触发备份到 CC/2_old",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "相对于项目根的文件路径"}
            },
            "required": ["file_path"]
        }
    },
}

TOOL_HANDLERS = {
    "nl_route": lambda args: tool_nl_route(args["query"]),
    "kb_search": lambda args: tool_kb_search(args["query"], args.get("top_k", 10)),
    "kb_add": lambda args: tool_kb_add(args["title"], args["content"], args.get("category", "general"), args.get("importance", 5)),
    "kb_auto_extract": lambda args: tool_kb_auto_extract(args["text"]),
    "skill_list": lambda args: tool_skill_list(),
    "skill_run": lambda args: tool_skill_run(args["skill_name"], args.get("params", {})),
    "software_search": lambda args: tool_software_search(args.get("name", "")),
    "project_search": lambda args: tool_project_search(args.get("name", "")),
    "github_search": lambda args: tool_github_search(args["query"], args.get("language", ""), args.get("limit", 10)),
    "github_install_skill": lambda args: tool_github_install_skill(args["repo_url"], args.get("skill_name", "")),
    "memory_read": lambda args: tool_memory_read(args.get("date", "")),
    "memory_write": lambda args: tool_memory_write(args["content"], args.get("date", ""), args.get("append", True)),
    "system_check": lambda args: tool_system_check(),
    "session_list": lambda args: tool_session_list(args.get("limit", 20)),
    "session_read": lambda args: tool_session_read(args.get("session_id", "")),
    "session_write": lambda args: tool_session_write(args["content"], args.get("category", "mcp_tool")),
    "file_protect": lambda args: tool_file_protect(args["file_path"]),
    "file_backup_before": lambda args: tool_file_backup_before(args["file_path"]),
}


def handle_mcp_message(msg: Dict) -> Optional[Dict]:
    """处理 MCP 协消息"""
    method = msg.get("method", "")
    msg_id = msg.get("id")
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "mcp-core-skills",
                    "version": "3.0.0",
                    "description": "AI工作区核心技能服务器 - 知识++Skill管理+GitHub搜索",
                }
            }
        }
    
    elif method == "tools/list":
        tools_list = []
        for name, defn in TOOLS.items():
            tools_list.append({
                "name": name,
                "description": defn["description"],
                "inputSchema": defn["inputSchema"],
            })
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": tools_list}
        }
    
    elif method == "tools/call":
        tool_name = msg.get("params", {}).get("name", "")
        tool_args = msg.get("params", {}).get("arguments", {})
        
        if tool_name not in TOOL_HANDLERS:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Tool not found: {tool_name}"}
            }
        
        try:
            result = TOOL_HANDLERS[tool_name](tool_args)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]
                }
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32603,
                    "message": str(e),
                    "data": traceback.format_exc()
                }
            }
    
    elif method == "notifications/initialized":
        # 初化完成通知，执行启动任
        if KB_AVAILABLE:
            try:
                bootstrap_knowledge()
            except Exception:
                pass
        return None
    
    return None


def run_server():
    """ stdio 模式运 MCP 服务"""
    sys.stderr.write("[mcp-core-skills] 动中...\n")
    sys.stderr.flush()
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            line = line.strip()
            if not line:
                continue
            
            msg = json.loads(line)
            response = handle_mcp_message(msg)
            
            if response is not None:
                output = json.dumps(response, ensure_ascii=False)
                sys.stdout.write(output + "\n")
                sys.stdout.flush()
                
        except json.JSONDecodeError:
            pass
        except KeyboardInterrupt:
            break
        except Exception as e:
            sys.stderr.write(f"[mcp-core-skills] 错: {e}\n")
            sys.stderr.flush()
    
    sys.stderr.write("[mcp-core-skills] 已停\n")
    sys.stderr.flush()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # 测试模式
        print("=== MCP Skill Server 测试 ===\n")
        
        print("1. 系统:")
        result = tool_system_check()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        print("\n2. 然由测:")
        if NL_AVAILABLE:
            result = tool_nl_route("搜索 GitHub 上好用的 AI 代理框架")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
        print("\n3. 知识库测:")
        if KB_AVAILABLE:
            bootstrap_knowledge()
            result = tool_kb_search("MCP")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
        print("\n4. Skill 列表:")
        result = tool_skill_list()
        print(f"MCP Core Skills: {len(result.get('mcp_core_skills', []))}")
        print(f"WorkBuddy Skills: {result.get('workbuddy_total', 0)}")
    else:
        run_server()
