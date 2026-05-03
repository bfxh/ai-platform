import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

class MCPReactor:
    def __init__(self):
        self.ai_path = Path("/python")
        self.mcp_path = self.ai_path / "MCP"
        self.mcp_config = self.mcp_path / "mcp-config.json"
        self.pipes = []
        self.results = []
    
    def load_mcp_config(self):
        if self.mcp_config.exists():
            with open(self.mcp_config, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def parse_pipe_syntax(self, command):
        steps = []
        current_step = ""
        in_quote = False
        quote_char = None
        
        for char in command:
            if char in ['"', "'"] and not in_quote:
                in_quote = True
                quote_char = char
            elif char == quote_char and in_quote:
                in_quote = False
                quote_char = None
            elif char == "|" and not in_quote:
                if current_step.strip():
                    steps.append(current_step.strip())
                current_step = ""
            else:
                current_step += char
        
        if current_step.strip():
            steps.append(current_step.strip())
        
        return steps
    
    def execute_step(self, step, context=None):
        print(f"\n🔄 执行步骤: {step}")
        
        parts = step.split("->")
        if len(parts) < 2:
            parts = [step]
        
        mcp_name = None
        action = None
        params = {}
        
        step_lower = step.lower()
        
        if "blender" in step_lower or "3d" in step_lower or "模型" in step_lower:
            mcp_name = "blender_mcp"
            if "生成" in step_lower or "create" in step_lower:
                action = "generate_model"
            elif "渲染" in step_lower or "render" in step_lower:
                action = "render"
            else:
                action = "open"
        elif "code" in step_lower or "网页" in step_lower or "web" in step_lower:
            mcp_name = "code_intelligence"
            if "生成" in step_lower or "create" in step_lower:
                action = "generate"
            else:
                action = "analyze"
        elif "browser" in step_lower or "浏览器" in step_lower or "preview" in step_lower:
            mcp_name = "desktop_automation"
            action = "open_url"
            if context and "url" in context:
                params["url"] = context["url"]
        elif "github" in step_lower:
            mcp_name = "github_dl"
            action = "download"
        elif "download" in step_lower or "下载" in step_lower:
            mcp_name = "download_manager"
            action = "download"
        else:
            print(f"  ⚠️ 无法识别的步骤: {step}")
            return None
        
        print(f"  📦 MCP: {mcp_name}")
        print(f"  ⚡ 动作: {action}")
        
        result = {
            "step": step,
            "mcp": mcp_name,
            "action": action,
            "params": params,
            "status": "success",
            "output": None
        }
        
        return result
    
    def run_pipeline(self, command):
        print("🚀 启动 MCP 反应堆模式")
        print(f"📝 原始命令: {command}")
        print("=" * 60)
        
        steps = self.parse_pipe_syntax(command)
        print(f"\n📋 检测到 {len(steps)} 个步骤:")
        for i, step in enumerate(steps):
            print(f"  {i+1}. {step}")
        
        print("\n" + "=" * 60)
        
        context = {}
        
        for i, step in enumerate(steps):
            print(f"\n[{i+1}/{len(steps)}]")
            result = self.execute_step(step, context)
            
            if result:
                self.results.append(result)
                
                if result.get("output"):
                    context[result["mcp"]] = result["output"]
            else:
                print(f"  ❌ 步骤执行失败")
                return False
        
        print("\n" + "=" * 60)
        print("📊 管道执行完成")
        print(f"  成功步骤: {sum(1 for r in self.results if r['status'] == 'success')}/{len(self.results)}")
        
        return True
    
    def generate_report(self):
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_steps": len(self.results),
            "successful": sum(1 for r in self.results if r['status'] == 'success'),
            "failed": sum(1 for r in self.results if r['status'] == 'fail'),
            "steps": self.results
        }
        
        print("\n📋 管道执行报告:")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        
        return report
    
    def list_available_mcps(self):
        config = self.load_mcp_config()
        mcp_servers = config.get("mcpServers", {})
        
        print("\n📦 可用的 MCP 服务器:")
        print("=" * 60)
        
        for name, info in mcp_servers.items():
            category = info.get("category", "Unknown")
            status = info.get("status", "Unknown")
            desc = info.get("description", "无描述")
            print(f"\n🔧 {name}")
            print(f"   分类: {category}")
            print(f"   状态: {status}")
            print(f"   描述: {desc}")


if __name__ == "__main__":
    reactor = MCPReactor()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            reactor.list_available_mcps()
        elif sys.argv[1] == "run" and len(sys.argv) > 2:
            command = " ".join(sys.argv[2:])
            reactor.run_pipeline(command)
            reactor.generate_report()
        else:
            print("用法:")
            print("  python mcp_reactor.py list - 列出可用 MCP")
            print("  python mcp_reactor.py run <pipe_command> - 执行管道命令")
            print("\n示例:")
            print('  python mcp_reactor.py run "Blender生成模型 -> CodeMCP生成网页 -> 打开浏览器"')
    else:
        print("MCP 反应堆模式")
        print("支持 Pipe 语法连接多个 MCP")
        print("\n用法:")
        print("  python mcp_reactor.py list - 列出可用 MCP")
        print("  python mcp_reactor.py run <pipe_command> - 执行管道命令")
