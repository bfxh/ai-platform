#!/usr/bin/env python3
"""
/python 统一入口 - AI工具集
根据参数分发到对应的 MCP 工具
"""

import sys
import os
import json
import importlib.util
from pathlib import Path

MCP_CONFIG = Path("/python/storage/mcp/mcp-config.json")

def load_mcp_config():
    try:
        with open(MCP_CONFIG, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def list_tools():
    config = load_mcp_config()
    servers = config.get('mcpServers', {})
    print("Available MCP Tools:")
    print("-" * 60)
    for name, info in servers.items():
        status = info.get('status', 'unknown')
        desc = info.get('description', '')
        cat = info.get('category', '')
        print(f"  [{cat}] {name}: {desc}")
    print(f"\nTotal: {len(servers)} tools")

def run_tool(tool_name, *args):
    config = load_mcp_config()
    servers = config.get('mcpServers', {})
    
    if tool_name not in servers:
        print(f"[ERROR] Tool not found: {tool_name}")
        print(f"Available: {', '.join(servers.keys())}")
        return 1
    
    server = servers[tool_name]
    script_path = server.get('path', '')
    
    if not script_path or not os.path.exists(script_path):
        print(f"[ERROR] Script not found: {script_path}")
        return 1
    
    print(f"[AI] Running {tool_name}: {script_path}")
    os.execv(sys.executable, [sys.executable, script_path] + list(args))

def main():
    if len(sys.argv) < 2:
        print("/python Toolkit - Unified Entry Point")
        print()
        print("Usage:")
        print("  python ai.py list              - List all available tools")
        print("  python ai.py <tool_name> [args] - Run a specific tool")
        print()
        list_tools()
        return 0
    
    command = sys.argv[1]
    
    if command in ('list', 'ls'):
        list_tools()
        return 0
    
    run_tool(command, *sys.argv[2:])

if __name__ == "__main__":
    sys.exit(main())
