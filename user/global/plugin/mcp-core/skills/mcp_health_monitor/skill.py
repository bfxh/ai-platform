import os
import json
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

class MCPHealthMonitor:
    def __init__(self):
        self.ai_path = Path("/python")
        self.mcp_path = self.ai_path / "MCP"
        self.config_file = self.ai_path / "MCP" / "mcp-config.json"
        self.reports_dir = self.ai_path / "reports"
        self.results = []
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def load_mcp_config(self):
        if not self.config_file.exists():
            print(f"❌ MCP 配置文件不存在: {self.config_file}")
            return {}
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            try:
                config = json.load(f)
                return config.get('mcpServers', {})
            except json.JSONDecodeError:
                print(f"❌ MCP 配置文件格式错误: {self.config_file}")
                return {}
    
    def test_blender_mcp(self, mcp_info):
        try:
            script = """
import bpy
print(f"Blender version: {bpy.app.version_string}")
print("✅ Blender MCP 正常")
"""
            test_file = self.ai_path / "temp" / "test_blender.py"
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text(script)
            
            result = subprocess.run(
                ["python", str(mcp_info['path']), "test"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if "Blender version" in result.stdout:
                return True, result.stdout.strip()
            else:
                return False, f"Blender 测试失败: {result.stderr[:100]}"
        except Exception as e:
            return False, f"测试异常: {str(e)}"
    
    def test_github_mcp(self, mcp_info):
        try:
            script = """
import requests
try:
    response = requests.get('https://api.github.com', timeout=5)
    if response.status_code == 200:
        print("✅ GitHub API 可访问")
    else:
        print(f"❌ GitHub API 响应: {response.status_code}")
except Exception as e:
    print(f"❌ GitHub 测试失败: {str(e)}")
"""
            test_file = self.ai_path / "temp" / "test_github.py"
            test_file.write_text(script)
            
            result = subprocess.run(
                ["python", str(test_file)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if "✅" in result.stdout:
                return True, result.stdout.strip()
            else:
                return False, result.stderr.strip()
        except Exception as e:
            return False, f"测试异常: {str(e)}"
    
    def test_generic_mcp(self, mcp_info):
        try:
            result = subprocess.run(
                ["python", str(mcp_info['path']), "test"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return True, "✅ 通用 MCP 测试通过"
            else:
                return False, f"❌ 测试失败: {result.stderr[:100]}"
        except Exception as e:
            return False, f"测试异常: {str(e)}"
    
    def test_mcp(self, name, mcp_info):
        print(f"🔍 测试 MCP: {name}")
        
        category = mcp_info.get('category', 'Unknown')
        status = "❌"
        message = "未测试"
        
        try:
            if 'blender' in name.lower():
                success, message = self.test_blender_mcp(mcp_info)
            elif 'github' in name.lower():
                success, message = self.test_github_mcp(mcp_info)
            else:
                success, message = self.test_generic_mcp(mcp_info)
            
            if success:
                status = "✅"
        except Exception as e:
            message = f"执行异常: {str(e)}"
        
        self.results.append({
            "name": name,
            "category": category,
            "status": status,
            "message": message,
            "path": mcp_info.get('path', 'Unknown'),
            "last_validated": mcp_info.get('last_validated', 'Unknown')
        })
    
    def generate_report(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f"mcp_health_{timestamp}.md"
        
        report = []
        report.append("# MCP 健康度监控报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        report.append("## 健康状态概览")
        total = len(self.results)
        healthy = sum(1 for r in self.results if r['status'] == "✅")
        unhealthy = total - healthy
        report.append(f"- 总 MCP 数: {total}")
        report.append(f"- 健康: {healthy} ✅")
        report.append(f"- 异常: {unhealthy} ❌")
        report.append("")
        
        report.append("## 详细状态")
        report.append("| MCP 名称 | 分类 | 状态 | 消息 | 路径 | 最后验证 |")
        report.append("|----------|------|------|------|------|----------|")
        
        for result in self.results:
            report.append(f"| {result['name']} | {result['category']} | {result['status']} | {result['message']} | {result['path']} | {result['last_validated']} |")
        
        report_content = "\n".join(report)
        report_file.write_text(report_content, encoding='utf-8')
        
        return str(report_file)
    
    def run(self):
        print("🚀 开始 MCP 健康度检查...")
        print("=" * 60)
        
        mcp_servers = self.load_mcp_config()
        
        if not mcp_servers:
            print("❌ 没有找到 MCP 服务器配置")
            return
        
        for name, mcp_info in mcp_servers.items():
            if mcp_info.get('status') == 'active':
                self.test_mcp(name, mcp_info)
        
        report_path = self.generate_report()
        print(f"\n📊 报告已生成: {report_path}")
        print("=" * 60)


if __name__ == "__main__":
    monitor = MCPHealthMonitor()
    monitor.run()
