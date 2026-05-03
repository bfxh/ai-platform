#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Code Tudou 桥接器

功能：
- 桥接 Claude Code Tudou 与我们的 MCP 工具
- 让 Claude Code 可以调用我们的工具
- 让我们的 AI 可以调用 Claude Code 的工具
- 统一工具接口

用法：
    python claude_code_bridge.py call <tool> <action> [params]  # 调用工具
    python claude_code_bridge.py list                           # 列出可用工具
    python claude_code_bridge.py status                         # 查看状态
    python claude_code_bridge.py analyze <file>                 # 分析代码
    python claude_code_bridge.py edit <file> <changes>          # 编辑代码

MCP调用：
    {"tool": "claude_code_bridge", "action": "call", "params": {...}}
"""

import json
import sys
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

# ============================================================
# 配置
# ============================================================
AI_PATH = Path("/python")
MCP_PATH = AI_PATH / "MCP"
CLAUDE_CODE_PATH = Path("D:/嗷嗷的")

# Claude Code 工具映射
CLAUDE_CODE_TOOLS = {
    "bash": {
        "name": "BashTool",
        "description": "执行终端命令",
        "path": CLAUDE_CODE_PATH / "SRC/tools/BashTool",
    },
    "file_edit": {
        "name": "FileEditTool",
        "description": "精准编辑文件",
        "path": CLAUDE_CODE_PATH / "SRC/tools/FileEditTool",
    },
    "file_read": {
        "name": "FileReadTool",
        "description": "读取文件内容",
        "path": CLAUDE_CODE_PATH / "SRC/tools/FileReadTool",
    },
    "file_write": {
        "name": "FileWriteTool",
        "description": "写入文件",
        "path": CLAUDE_CODE_PATH / "SRC/tools/FileWriteTool",
    },
    "glob": {
        "name": "GlobTool",
        "description": "文件搜索",
        "path": CLAUDE_CODE_PATH / "SRC/tools/GlobTool",
    },
    "grep": {
        "name": "GrepTool",
        "description": "代码搜索",
        "path": CLAUDE_CODE_PATH / "SRC/tools/GrepTool",
    },
    "web_search": {
        "name": "WebSearchTool",
        "description": "网络搜索",
        "path": CLAUDE_CODE_PATH / "SRC/tools/WebSearchTool",
    },
    "web_fetch": {
        "name": "WebFetchTool",
        "description": "网页抓取",
        "path": CLAUDE_CODE_PATH / "SRC/tools/WebFetchTool",
    },
    "lsp": {
        "name": "LSPTool",
        "description": "LSP 代码分析",
        "path": CLAUDE_CODE_PATH / "SRC/tools/LSPTool",
    },
}

# 我们的 MCP 工具映射
OUR_MCP_TOOLS = {
    "desktop_auto": {
        "name": "desktop_automation",
        "description": "桌面自动化",
        "cmd": ["python", str(MCP_PATH / "da.py"), "mcp"],
    },
    "vision": {
        "name": "vision_pro",
        "description": "视觉分析",
        "cmd": ["python", str(MCP_PATH / "vision_pro.py"), "mcp"],
    },
    "screen": {
        "name": "screen_eye",
        "description": "屏幕截图",
        "cmd": ["python", str(MCP_PATH / "screen_eye.py"), "mcp"],
    },
    "network": {
        "name": "net_pro",
        "description": "网络工具",
        "cmd": ["python", str(MCP_PATH / "net_pro.py"), "mcp"],
    },
    "github": {
        "name": "github_auto_commit",
        "description": "GitHub 工具",
        "cmd": ["python", str(MCP_PATH / "github_auto_commit.py"), "mcp"],
    },
    "download": {
        "name": "aria2_mcp",
        "description": "下载管理",
        "cmd": ["python", str(MCP_PATH / "aria2_mcp.py"), "mcp"],
    },
    "software": {
        "name": "local_software",
        "description": "软件管理",
        "cmd": ["python", str(MCP_PATH / "local_software.py"), "mcp"],
    },
    "translate": {
        "name": "auto_translate",
        "description": "自动翻译",
        "cmd": ["python", str(MCP_PATH / "auto_translate.py"), "mcp"],
    },
}

# ============================================================
# 桥接器
# ============================================================
class ClaudeCodeBridge:
    """Claude Code 桥接器"""
    
    def __init__(self):
        self.claude_code_process = None
        self.mcp_processes = {}
    
    def list_tools(self) -> Dict:
        """列出所有可用工具"""
        return {
            "success": True,
            "claude_code_tools": [
                {
                    "id": key,
                    "name": tool["name"],
                    "description": tool["description"]
                }
                for key, tool in CLAUDE_CODE_TOOLS.items()
            ],
            "our_mcp_tools": [
                {
                    "id": key,
                    "name": tool["name"],
                    "description": tool["description"]
                }
                for key, tool in OUR_MCP_TOOLS.items()
            ]
        }
    
    def call_our_tool(self, tool_name: str, action: str, params: Dict) -> Dict:
        """调用我们的 MCP 工具"""
        if tool_name not in OUR_MCP_TOOLS:
            return {"success": False, "error": f"未知工具: {tool_name}"}
        
        tool = OUR_MCP_TOOLS[tool_name]
        
        try:
            # 构建 MCP 请求
            request = {
                "tool": tool["name"],
                "action": action,
                "params": params
            }
            
            # 启动进程（如果未运行）
            if tool_name not in self.mcp_processes or \
               self.mcp_processes[tool_name].poll() is not None:
                self.mcp_processes[tool_name] = subprocess.Popen(
                    tool["cmd"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            
            process = self.mcp_processes[tool_name]
            
            # 发送请求
            request_json = json.dumps(request) + "\n"
            process.stdin.write(request_json)
            process.stdin.flush()
            
            # 读取响应
            response_line = process.stdout.readline()
            response = json.loads(response_line)
            
            return response
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def call_claude_code_tool(self, tool_name: str, params: Dict) -> Dict:
        """调用 Claude Code 工具（通过 bun/node）"""
        if tool_name not in CLAUDE_CODE_TOOLS:
            return {"success": False, "error": f"未知工具: {tool_name}"}
        
        tool = CLAUDE_CODE_TOOLS[tool_name]
        
        try:
            # 构建调用脚本
            script = f"""
const {{ {tool['name']} }} = require('{tool['path'].as_posix()}/{tool['name']}.js');
const result = {tool['name']}.call({json.dumps(params)});
console.log(JSON.stringify(result));
"""
            
            # 执行
            result = subprocess.run(
                ["bun", "-e", script],
                capture_output=True,
                text=True,
                cwd=str(CLAUDE_CODE_PATH)
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return {"success": False, "error": result.stderr}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def analyze_code(self, file_path: str) -> Dict:
        """分析代码"""
        try:
            # 1. 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 2. 检测语言
            ext = Path(file_path).suffix
            language = self._detect_language(ext)
            
            # 3. 基础分析
            lines = content.split('\n')
            analysis = {
                "file": file_path,
                "language": language,
                "total_lines": len(lines),
                "code_lines": len([l for l in lines if l.strip() and not l.strip().startswith('#')]),
                "comment_lines": len([l for l in lines if l.strip().startswith('#') or '//' in l]),
                "blank_lines": len([l for l in lines if not l.strip()]),
            }
            
            return {"success": True, "analysis": analysis}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _detect_language(self, ext: str) -> str:
        """检测编程语言"""
        lang_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript React',
            '.jsx': 'JavaScript React',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.h': 'C/C++ Header',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
        }
        return lang_map.get(ext, 'Unknown')
    
    def edit_file(self, file_path: str, changes: List[Dict]) -> Dict:
        """编辑文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # 应用更改
            for change in changes:
                old_text = change.get("old", "")
                new_text = change.get("new", "")
                content = content.replace(old_text, new_text, 1)
            
            # 保存
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "file": file_path,
                "changes_applied": len(changes)
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            "success": True,
            "claude_code_path": str(CLAUDE_CODE_PATH),
            "claude_code_exists": CLAUDE_CODE_PATH.exists(),
            "mcp_tools_count": len(OUR_MCP_TOOLS),
            "running_processes": len([p for p in self.mcp_processes.values() if p.poll() is None])
        }

# ============================================================
# MCP 接口
# ============================================================
class MCPInterface:
    """MCP 接口"""
    
    def __init__(self):
        self.bridge = ClaudeCodeBridge()
    
    def handle(self, request: Dict) -> Dict:
        """处理 MCP 请求"""
        action = request.get("action")
        params = request.get("params", {})
        
        if action == "list":
            return self.bridge.list_tools()
        
        elif action == "call_our_tool":
            tool = params.get("tool")
            tool_action = params.get("tool_action", "")
            tool_params = params.get("tool_params", {})
            return self.bridge.call_our_tool(tool, tool_action, tool_params)
        
        elif action == "call_claude_tool":
            tool = params.get("tool")
            tool_params = params.get("tool_params", {})
            return self.bridge.call_claude_code_tool(tool, tool_params)
        
        elif action == "analyze":
            file_path = params.get("file")
            return self.bridge.analyze_code(file_path)
        
        elif action == "edit":
            file_path = params.get("file")
            changes = params.get("changes", [])
            return self.bridge.edit_file(file_path, changes)
        
        elif action == "status":
            return self.bridge.get_status()
        
        else:
            return {"success": False, "error": f"未知操作: {action}"}

# ============================================================
# 命令行接口
# ============================================================
def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1]
    bridge = ClaudeCodeBridge()
    
    if cmd == "list":
        tools = bridge.list_tools()
        
        print("Claude Code 工具:")
        print("-" * 60)
        for tool in tools["claude_code_tools"]:
            print(f"  {tool['id']:<15} - {tool['name']:<20} {tool['description']}")
        
        print("\n我们的 MCP 工具:")
        print("-" * 60)
        for tool in tools["our_mcp_tools"]:
            print(f"  {tool['id']:<15} - {tool['name']:<20} {tool['description']}")
    
    elif cmd == "status":
        status = bridge.get_status()
        
        print("Claude Code 桥接器状态:")
        print("-" * 60)
        print(f"Claude Code 路径: {status['claude_code_path']}")
        print(f"路径存在: {'是' if status['claude_code_exists'] else '否'}")
        print(f"MCP 工具数: {status['mcp_tools_count']}")
        print(f"运行进程数: {status['running_processes']}")
    
    elif cmd == "call":
        if len(sys.argv) < 4:
            print("用法: claude_code_bridge.py call <tool> <action>")
            return
        
        tool = sys.argv[2]
        action = sys.argv[3]
        
        # 解析参数
        params = {}
        if len(sys.argv) > 4:
            for arg in sys.argv[4:]:
                if '=' in arg:
                    key, value = arg.split('=', 1)
                    params[key] = value
        
        # 判断调用哪个工具集
        if tool in OUR_MCP_TOOLS:
            result = bridge.call_our_tool(tool, action, params)
        elif tool in CLAUDE_CODE_TOOLS:
            result = bridge.call_claude_code_tool(tool, params)
        else:
            print(f"未知工具: {tool}")
            return
        
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif cmd == "analyze":
        if len(sys.argv) < 3:
            print("用法: claude_code_bridge.py analyze <file>")
            return
        
        file_path = sys.argv[2]
        result = bridge.analyze_code(file_path)
        
        if result.get("success"):
            analysis = result["analysis"]
            print(f"文件分析: {analysis['file']}")
            print(f"语言: {analysis['language']}")
            print(f"总行数: {analysis['total_lines']}")
            print(f"代码行: {analysis['code_lines']}")
            print(f"注释行: {analysis['comment_lines']}")
            print(f"空行: {analysis['blank_lines']}")
        else:
            print(f"分析失败: {result.get('error')}")
    
    elif cmd == "edit":
        if len(sys.argv) < 4:
            print("用法: claude_code_bridge.py edit <file> <old_text>=<new_text>")
            return
        
        file_path = sys.argv[2]
        change_str = sys.argv[3]
        
        if '=' not in change_str:
            print("格式错误，应为: old_text=new_text")
            return
        
        old_text, new_text = change_str.split('=', 1)
        changes = [{"old": old_text, "new": new_text}]
        
        result = bridge.edit_file(file_path, changes)
        
        if result.get("success"):
            print(f"✓ 已编辑: {result['file']}")
            print(f"  应用了 {result['changes_applied']} 处更改")
        else:
            print(f"✗ 编辑失败: {result.get('error')}")
    
    elif cmd == "mcp":
        # MCP 服务器模式
        print("Claude Code 桥接器 MCP 已启动")
        
        mcp = MCPInterface()
        
        import select
        
        while True:
            if select.select([sys.stdin], [], [], 0.1)[0]:
                line = sys.stdin.readline()
                if not line:
                    break
                
                try:
                    request = json.loads(line)
                    response = mcp.handle(request)
                    print(json.dumps(response, ensure_ascii=False))
                    sys.stdout.flush()
                except json.JSONDecodeError:
                    print(json.dumps({"success": False, "error": "无效的JSON"}))
                    sys.stdout.flush()
    
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)

if __name__ == "__main__":
    main()
