#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能工作流 - 结合记忆和上下文

功能：
- 自动检索相关记忆
- 根据用户偏好调整工作流
- 智能推荐工具和工作流
- 自动应用基因记忆
- 上下文感知执行

用法：
    python smart_workflow.py run <workflow> [context]    # 运行智能工作流
    python smart_workflow.py suggest <task>              # 推荐工作流
    python smart_workflow.py genes                       # 应用基因记忆
    python smart_workflow.py context                     # 显示当前上下文

MCP调用：
    {"tool": "smart_workflow", "action": "run", "params": {"workflow": "...", "context": "..."}}
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# ============================================================
# 配置
# ============================================================
AI_PATH = Path("/python")
MCP_PATH = AI_PATH / "MCP"

# ============================================================
# 智能工作流
# ============================================================
class SmartWorkflow:
    """智能工作流"""
    
    def __init__(self):
        self.context = {}
        self.memories = []
    
    def get_relevant_memories(self, user_input: str) -> List[Dict]:
        """获取相关记忆"""
        # 调用 ai_memory 获取相关记忆
        import subprocess
        result = subprocess.run(
            ["python", str(MCP_PATH / "ai_memory.py"), "mcp"],
            input=json.dumps({
                "action": "relevant",
                "params": {"context": user_input, "limit": 5}
            }),
            capture_output=True,
            text=True
        )
        
        try:
            response = json.loads(result.stdout.strip().split('\n')[0])
            return response.get("memories", [])
        except:
            return []
    
    def get_genes(self) -> Dict:
        """获取基因记忆"""
        import subprocess
        result = subprocess.run(
            ["python", str(MCP_PATH / "ai_memory.py"), "genes"],
            capture_output=True,
            text=True
        )
        
        try:
            # 解析输出
            genes = {}
            for line in result.stdout.split('\n'):
                if ':' in line and not line.startswith('='):
                    parts = line.strip().split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        genes[key] = value
            return genes
        except:
            return {}
    
    def suggest_workflow(self, task: str) -> Dict:
        """推荐工作流"""
        # 根据任务和记忆推荐工作流
        memories = self.get_relevant_memories(task)
        genes = self.get_genes()
        
        # 分析任务类型
        task_lower = task.lower()
        
        suggestions = []
        
        # 游戏开发
        if any(word in task_lower for word in ["游戏", "game", "godot", "unity"]):
            suggestions.append({
                "name": "game_development",
                "description": "游戏开发工作流",
                "priority": "high" if genes.get("game_engine") == "Godot优先" else "medium"
            })
        
        # MCP 开发
        if any(word in task_lower for word in ["mcp", "技能", "工具"]):
            suggestions.append({
                "name": "mcp_development",
                "description": "MCP技能开发工作流",
                "priority": "high"
            })
        
        # GitHub 相关
        if any(word in task_lower for word in ["github", "git", "下载"]):
            suggestions.append({
                "name": "github_workflow",
                "description": "GitHub工作流",
                "priority": "high" if genes.get("github_sync") == "自动同步" else "medium"
            })
        
        # 代码开发
        if any(word in task_lower for word in ["代码", "编程", "开发"]):
            suggestions.append({
                "name": "code_development",
                "description": "代码开发工作流",
                "priority": "high"
            })
        
        # 按优先级排序
        suggestions.sort(key=lambda x: x["priority"], reverse=True)
        
        return {
            "success": True,
            "task": task,
            "genes_applied": genes,
            "relevant_memories": len(memories),
            "suggestions": suggestions
        }
    
    def run_with_context(self, workflow_name: str, user_context: str) -> Dict:
        """结合上下文运行工作流"""
        # 获取相关记忆
        memories = self.get_relevant_memories(user_context)
        genes = self.get_genes()
        
        # 构建增强的上下文
        enhanced_context = {
            "user_input": user_context,
            "genes": genes,
            "relevant_memories": memories,
            "timestamp": datetime.now().isoformat()
        }
        
        # 保存上下文
        self._save_context(enhanced_context)
        
        # 运行工作流
        import subprocess
        result = subprocess.run(
            ["python", str(MCP_PATH / "unified_workflow.py"), "run", workflow_name],
            capture_output=True,
            text=True
        )
        
        return {
            "success": result.returncode == 0,
            "workflow": workflow_name,
            "context": enhanced_context,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }
    
    def _save_context(self, context: Dict):
        """保存上下文"""
        context_file = AI_PATH / "Memory" / "current_context.json"
        context_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(context, f, ensure_ascii=False, indent=2)
    
    def get_current_context(self) -> Dict:
        """获取当前上下文"""
        context_file = AI_PATH / "Memory" / "current_context.json"
        
        if context_file.exists():
            with open(context_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            "genes": self.get_genes(),
            "message": "没有活动的上下文"
        }

# ============================================================
# MCP 接口
# ============================================================
class MCPInterface:
    """MCP 接口"""
    
    def __init__(self):
        self.workflow = SmartWorkflow()
    
    def handle(self, request: Dict) -> Dict:
        """处理 MCP 请求"""
        action = request.get("action")
        params = request.get("params", {})
        
        if action == "suggest":
            return self.workflow.suggest_workflow(params.get("task"))
        
        elif action == "run":
            return self.workflow.run_with_context(
                workflow_name=params.get("workflow"),
                user_context=params.get("context", "")
            )
        
        elif action == "genes":
            return {"success": True, "genes": self.workflow.get_genes()}
        
        elif action == "context":
            return {"success": True, **self.workflow.get_current_context()}
        
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
    workflow = SmartWorkflow()
    
    if cmd == "suggest":
        if len(sys.argv) < 3:
            print("用法: smart_workflow.py suggest <task>")
            return
        
        task = sys.argv[2]
        result = workflow.suggest_workflow(task)
        
        if result.get("success"):
            print(f"任务: {result['task']}")
            print(f"基因记忆: {result['genes_applied']}")
            print(f"相关记忆: {result['relevant_memories']} 条")
            print("\n推荐工作流:")
            for i, sug in enumerate(result["suggestions"], 1):
                print(f"  {i}. {sug['name']} ({sug['priority']})")
                print(f"     {sug['description']}")
    
    elif cmd == "genes":
        genes = workflow.get_genes()
        print("基因记忆（核心偏好）:")
        for key, value in genes.items():
            print(f"  {key}: {value}")
    
    elif cmd == "context":
        context = workflow.get_current_context()
        print("当前上下文:")
        print(json.dumps(context, ensure_ascii=False, indent=2))
    
    elif cmd == "mcp":
        # MCP 服务器模式
        print("智能工作流 MCP 已启动")
        
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
