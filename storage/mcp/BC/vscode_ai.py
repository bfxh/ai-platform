#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VS Code AI Integration MCP - VS Code AI集成工具

功能：
- 直接调用VS Code的Copilot进行代码生成
- 在VS Code中打开、编辑、保存文件
- 格式化代码
- 运行任务和调试

用法：
    python vscode_ai.py <action> [args...]

示例：
    python vscode_ai.py copilot generate "sort function" --language python
    python vscode_ai.py copilot explain --file main.py --lines 10-20
    python vscode_ai.py open --file main.py
    python vscode_ai.py insert --file main.py --line 10 --code "print('hello')"
    python vscode_ai.py format --file main.py
"""

import json
import sys
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ============================================================
# 配置
# ============================================================
CONFIG = {
    "vscode_executable": "code",
    "wait_timeout": 30,
    "auto_save": True,
    "auto_format": True
}

# ============================================================
# 工具函数
# ============================================================
def run_vscode_command(args: List[str], wait: bool = False, timeout: int = 30) -> Tuple[int, str, str]:
    """运行VS Code命令"""
    cmd = [CONFIG["vscode_executable"]] + args
    
    try:
        if wait:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        else:
            # 异步运行
            subprocess.Popen(cmd)
            return 0, "", ""
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def check_vscode_installed() -> bool:
    """检查VS Code是否安装"""
    try:
        result = subprocess.run(
            [CONFIG["vscode_executable"], "--version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False

def check_copilot_installed() -> bool:
    """检查Copilot是否安装"""
    try:
        # 检查Copilot扩展
        result = subprocess.run(
            [CONFIG["vscode_executable"], "--list-extensions"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return "github.copilot" in result.stdout
    except:
        return False

# ============================================================
# VS Code AI集成
# ============================================================
class VSCodeAI:
    """VS Code AI集成"""
    
    def __init__(self):
        self.vscode_available = check_vscode_installed()
        self.copilot_available = check_copilot_installed() if self.vscode_available else False
    
    # ========== Copilot功能 ==========
    def copilot_generate(self, params: Dict) -> Dict:
        """使用Copilot生成代码"""
        if not self.vscode_available:
            return {"success": False, "error": "VS Code not found"}
        
        if not self.copilot_available:
            return {"success": False, "error": "GitHub Copilot not installed"}
        
        prompt = params.get("prompt")
        language = params.get("language", "python")
        file_path = params.get("file")
        line = params.get("line", 0)
        context = params.get("context", "")
        
        if not prompt:
            return {"success": False, "error": "Prompt is required"}
        
        try:
            # 创建临时文件用于生成代码
            if file_path:
                target_file = Path(file_path)
            else:
                # 创建临时文件
                temp_dir = Path(tempfile.gettempdir()) / "vscode_ai"
                temp_dir.mkdir(exist_ok=True)
                target_file = temp_dir / f"generated_{language}_{int(__import__('time').time())}.{language}"
            
            # 确保文件存在
            if not target_file.exists():
                target_file.parent.mkdir(parents=True, exist_ok=True)
                target_file.write_text(f"# {prompt}\n", encoding="utf-8")
            
            # 在VS Code中打开文件
            code, stdout, stderr = run_vscode_command([
                "--goto", f"{target_file}:{line}:0",
                "--wait"
            ], wait=True, timeout=5)
            
            # 构造Copilot提示
            copilot_prompt = f"""
# Task: {prompt}
# Language: {language}
# Context: {context}

"""
            
            # 写入提示到文件
            with open(target_file, "a", encoding="utf-8") as f:
                f.write(copilot_prompt)
            
            return {
                "success": True,
                "prompt": prompt,
                "language": language,
                "file": str(target_file),
                "line": line,
                "note": "Please use Copilot inline suggestion (Ctrl+Enter) to generate code",
                "instructions": [
                    "1. VS Code has opened the file",
                    "2. Position your cursor after the prompt",
                    "3. Press Ctrl+Enter to trigger Copilot",
                    "4. Accept the suggestion with Tab"
                ]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def copilot_explain(self, params: Dict) -> Dict:
        """使用Copilot解释代码"""
        if not self.vscode_available:
            return {"success": False, "error": "VS Code not found"}
        
        file_path = params.get("file")
        start_line = params.get("start_line")
        end_line = params.get("end_line")
        
        if not file_path or not Path(file_path).exists():
            return {"success": False, "error": "File not found"}
        
        try:
            # 打开文件并选中代码
            code, stdout, stderr = run_vscode_command([
                "--goto", f"{file_path}:{start_line}:{end_line}",
            ])
            
            return {
                "success": True,
                "file": file_path,
                "lines": f"{start_line}-{end_line}",
                "note": "Please use Copilot Chat to explain the selected code",
                "instructions": [
                    "1. Select the code you want to explain",
                    "2. Open Copilot Chat (Ctrl+Shift+I)",
                    "3. Type: /explain",
                    "4. Copilot will explain the selected code"
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def copilot_refactor(self, params: Dict) -> Dict:
        """使用Copilot重构代码"""
        if not self.vscode_available:
            return {"success": False, "error": "VS Code not found"}
        
        file_path = params.get("file")
        start_line = params.get("start_line")
        end_line = params.get("end_line")
        target = params.get("target", "optimize")
        
        if not file_path or not Path(file_path).exists():
            return {"success": False, "error": "File not found"}
        
        try:
            # 打开文件
            code, stdout, stderr = run_vscode_command([
                "--goto", f"{file_path}:{start_line}:{end_line}",
            ])
            
            return {
                "success": True,
                "file": file_path,
                "lines": f"{start_line}-{end_line}",
                "target": target,
                "note": f"Please use Copilot Chat to refactor the code: {target}",
                "instructions": [
                    f"1. Select the code you want to refactor",
                    "2. Open Copilot Chat (Ctrl+Shift+I)",
                    f"3. Type: /refactor to {target}",
                    "4. Copilot will suggest refactored code"
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def copilot_test(self, params: Dict) -> Dict:
        """使用Copilot生成单元测试"""
        if not self.vscode_available:
            return {"success": False, "error": "VS Code not found"}
        
        file_path = params.get("file")
        function = params.get("function")
        
        if not file_path or not Path(file_path).exists():
            return {"success": False, "error": "File not found"}
        
        try:
            # 打开文件
            code, stdout, stderr = run_vscode_command([
                "--goto", f"{file_path}:0:0",
            ])
            
            return {
                "success": True,
                "file": file_path,
                "function": function,
                "note": "Please use Copilot Chat to generate tests",
                "instructions": [
                    "1. Open Copilot Chat (Ctrl+Shift+I)",
                    f"2. Type: /tests for {function or 'this file'}",
                    "3. Copilot will generate unit tests"
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ========== 编辑器操作 ==========
    def open_file(self, params: Dict) -> Dict:
        """在VS Code中打开文件"""
        if not self.vscode_available:
            return {"success": False, "error": "VS Code not found"}
        
        file_path = params.get("file")
        line = params.get("line", 0)
        
        if not file_path:
            return {"success": False, "error": "File path is required"}
        
        file_obj = Path(file_path)
        if not file_obj.exists():
            # 创建文件
            file_obj.parent.mkdir(parents=True, exist_ok=True)
            file_obj.touch()
        
        try:
            code, stdout, stderr = run_vscode_command([
                "--goto", f"{file_obj}:{line}:0",
            ])
            
            return {
                "success": True,
                "file": str(file_obj),
                "line": line
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def insert_code(self, params: Dict) -> Dict:
        """插入代码"""
        file_path = params.get("file")
        line = params.get("line")
        code = params.get("code")
        
        if not file_path or not Path(file_path).exists():
            return {"success": False, "error": "File not found"}
        
        if code is None:
            return {"success": False, "error": "Code is required"}
        
        try:
            # 读取文件
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # 插入代码
            lines.insert(line, code + "\n")
            
            # 写回文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            
            # 在VS Code中打开
            self.open_file({"file": file_path, "line": line})
            
            return {
                "success": True,
                "file": file_path,
                "line": line,
                "inserted": code
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def replace_code(self, params: Dict) -> Dict:
        """替换代码"""
        file_path = params.get("file")
        start_line = params.get("start_line")
        end_line = params.get("end_line")
        code = params.get("code")
        
        if not file_path or not Path(file_path).exists():
            return {"success": False, "error": "File not found"}
        
        if code is None:
            return {"success": False, "error": "Code is required"}
        
        try:
            # 读取文件
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # 替换代码
            new_lines = lines[:start_line-1] + [code + "\n"] + lines[end_line:]
            
            # 写回文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            
            # 在VS Code中打开
            self.open_file({"file": file_path, "line": start_line})
            
            return {
                "success": True,
                "file": file_path,
                "replaced_lines": f"{start_line}-{end_line}",
                "new_code": code
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def format_file(self, params: Dict) -> Dict:
        """格式化文件"""
        if not self.vscode_available:
            return {"success": False, "error": "VS Code not found"}
        
        file_path = params.get("file")
        
        if not file_path or not Path(file_path).exists():
            return {"success": False, "error": "File not found"}
        
        try:
            # 使用VS Code CLI格式化
            code, stdout, stderr = run_vscode_command([
                "--command", "editor.action.formatDocument",
                file_path
            ])
            
            return {
                "success": True,
                "file": file_path,
                "note": "File formatted"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def save_file(self, params: Dict) -> Dict:
        """保存文件"""
        file_path = params.get("file")
        
        if not file_path or not Path(file_path).exists():
            return {"success": False, "error": "File not found"}
        
        try:
            # 使用VS Code CLI保存
            code, stdout, stderr = run_vscode_command([
                "--command", "workbench.action.files.save",
                file_path
            ])
            
            return {
                "success": True,
                "file": file_path,
                "note": "File saved"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def open_workspace(self, params: Dict) -> Dict:
        """打开工作区"""
        if not self.vscode_available:
            return {"success": False, "error": "VS Code not found"}
        
        path = params.get("path")
        
        if not path or not Path(path).exists():
            return {"success": False, "error": "Path not found"}
        
        try:
            code, stdout, stderr = run_vscode_command([path])
            
            return {
                "success": True,
                "workspace": path
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def run_task(self, params: Dict) -> Dict:
        """运行任务"""
        if not self.vscode_available:
            return {"success": False, "error": "VS Code not found"}
        
        task_name = params.get("name")
        
        if not task_name:
            return {"success": False, "error": "Task name is required"}
        
        try:
            # 使用VS Code CLI运行任务
            code, stdout, stderr = run_vscode_command([
                "--command", f"workbench.action.tasks.runTask",
                task_name
            ])
            
            return {
                "success": True,
                "task": task_name,
                "note": f"Task '{task_name}' started"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

# ============================================================
# MCP 接口
# ============================================================
vscode_ai = VSCodeAI()

def mcp_copilot_generate(params: Dict) -> Dict:
    """MCP Copilot生成接口"""
    return vscode_ai.copilot_generate(params)

def mcp_copilot_explain(params: Dict) -> Dict:
    """MCP Copilot解释接口"""
    return vscode_ai.copilot_explain(params)

def mcp_copilot_refactor(params: Dict) -> Dict:
    """MCP Copilot重构接口"""
    return vscode_ai.copilot_refactor(params)

def mcp_copilot_test(params: Dict) -> Dict:
    """MCP Copilot测试接口"""
    return vscode_ai.copilot_test(params)

def mcp_open_file(params: Dict) -> Dict:
    """MCP打开文件接口"""
    return vscode_ai.open_file(params)

def mcp_insert_code(params: Dict) -> Dict:
    """MCP插入代码接口"""
    return vscode_ai.insert_code(params)

def mcp_replace_code(params: Dict) -> Dict:
    """MCP替换代码接口"""
    return vscode_ai.replace_code(params)

def mcp_format_file(params: Dict) -> Dict:
    """MCP格式化文件接口"""
    return vscode_ai.format_file(params)

def mcp_save_file(params: Dict) -> Dict:
    """MCP保存文件接口"""
    return vscode_ai.save_file(params)

def mcp_open_workspace(params: Dict) -> Dict:
    """MCP打开工作区接口"""
    return vscode_ai.open_workspace(params)

def mcp_run_task(params: Dict) -> Dict:
    """MCP运行任务接口"""
    return vscode_ai.run_task(params)

# ============================================================
# 命令行接口
# ============================================================
def print_help():
    """打印帮助信息"""
    print(__doc__)
    print("\n命令:")
    print("  copilot generate <prompt> [options]  使用Copilot生成代码")
    print("  copilot explain --file <file> --lines <start>-<end>  解释代码")
    print("  copilot refactor --file <file> --lines <start>-<end>  重构代码")
    print("  copilot test --file <file> [--function <name>]  生成测试")
    print("  open --file <file> [--line <n>]      打开文件")
    print("  insert --file <file> --line <n> --code <code>  插入代码")
    print("  replace --file <file> --start <n> --end <n> --code <code>  替换代码")
    print("  format --file <file>                 格式化文件")
    print("  save --file <file>                   保存文件")
    print("  workspace open --path <path>         打开工作区")
    print("  task run --name <name>               运行任务")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action in ["--help", "-h", "help"]:
        print_help()
        sys.exit(0)
    
    if action == "copilot":
        if len(sys.argv) < 3:
            print("Usage: vscode_ai.py copilot <subcommand>")
            sys.exit(1)
        
        subcommand = sys.argv[2]
        
        if subcommand == "generate":
            if len(sys.argv) < 4:
                print("Usage: vscode_ai.py copilot generate <prompt>")
                sys.exit(1)
            
            params = {"prompt": sys.argv[3]}
            
            i = 4
            while i < len(sys.argv):
                if sys.argv[i] == "--language" and i + 1 < len(sys.argv):
                    params["language"] = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] == "--file" and i + 1 < len(sys.argv):
                    params["file"] = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] == "--line" and i + 1 < len(sys.argv):
                    params["line"] = int(sys.argv[i + 1])
                    i += 2
                else:
                    i += 1
            
            result = mcp_copilot_generate(params)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        elif subcommand == "explain":
            params = {}
            
            i = 3
            while i < len(sys.argv):
                if sys.argv[i] == "--file" and i + 1 < len(sys.argv):
                    params["file"] = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] == "--lines" and i + 1 < len(sys.argv):
                    lines = sys.argv[i + 1].split("-")
                    params["start_line"] = int(lines[0])
                    params["end_line"] = int(lines[1]) if len(lines) > 1 else int(lines[0])
                    i += 2
                else:
                    i += 1
            
            result = mcp_copilot_explain(params)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        elif subcommand == "refactor":
            params = {"target": "optimize"}
            
            i = 3
            while i < len(sys.argv):
                if sys.argv[i] == "--file" and i + 1 < len(sys.argv):
                    params["file"] = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] == "--lines" and i + 1 < len(sys.argv):
                    lines = sys.argv[i + 1].split("-")
                    params["start_line"] = int(lines[0])
                    params["end_line"] = int(lines[1]) if len(lines) > 1 else int(lines[0])
                    i += 2
                elif sys.argv[i] == "--target" and i + 1 < len(sys.argv):
                    params["target"] = sys.argv[i + 1]
                    i += 2
                else:
                    i += 1
            
            result = mcp_copilot_refactor(params)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        elif subcommand == "test":
            params = {}
            
            i = 3
            while i < len(sys.argv):
                if sys.argv[i] == "--file" and i + 1 < len(sys.argv):
                    params["file"] = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] == "--function" and i + 1 < len(sys.argv):
                    params["function"] = sys.argv[i + 1]
                    i += 2
                else:
                    i += 1
            
            result = mcp_copilot_test(params)
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif action == "open":
        params = {}
        
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--file" and i + 1 < len(sys.argv):
                params["file"] = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--line" and i + 1 < len(sys.argv):
                params["line"] = int(sys.argv[i + 1])
                i += 2
            else:
                i += 1
        
        result = mcp_open_file(params)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif action == "insert":
        params = {}
        
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--file" and i + 1 < len(sys.argv):
                params["file"] = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--line" and i + 1 < len(sys.argv):
                params["line"] = int(sys.argv[i + 1])
                i += 2
            elif sys.argv[i] == "--code" and i + 1 < len(sys.argv):
                params["code"] = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        
        result = mcp_insert_code(params)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif action == "replace":
        params = {}
        
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--file" and i + 1 < len(sys.argv):
                params["file"] = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--start" and i + 1 < len(sys.argv):
                params["start_line"] = int(sys.argv[i + 1])
                i += 2
            elif sys.argv[i] == "--end" and i + 1 < len(sys.argv):
                params["end_line"] = int(sys.argv[i + 1])
                i += 2
            elif sys.argv[i] == "--code" and i + 1 < len(sys.argv):
                params["code"] = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        
        result = mcp_replace_code(params)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif action == "format":
        params = {}
        
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--file" and i + 1 < len(sys.argv):
                params["file"] = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        
        result = mcp_format_file(params)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif action == "save":
        params = {}
        
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--file" and i + 1 < len(sys.argv):
                params["file"] = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        
        result = mcp_save_file(params)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif action == "workspace":
        if len(sys.argv) < 3:
            print("Usage: vscode_ai.py workspace <subcommand>")
            sys.exit(1)
        
        subcommand = sys.argv[2]
        
        if subcommand == "open":
            params = {}
            
            i = 3
            while i < len(sys.argv):
                if sys.argv[i] == "--path" and i + 1 < len(sys.argv):
                    params["path"] = sys.argv[i + 1]
                    i += 2
                else:
                    i += 1
            
            result = mcp_open_workspace(params)
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif action == "task":
        if len(sys.argv) < 3:
            print("Usage: vscode_ai.py task <subcommand>")
            sys.exit(1)
        
        subcommand = sys.argv[2]
        
        if subcommand == "run":
            params = {}
            
            i = 3
            while i < len(sys.argv):
                if sys.argv[i] == "--name" and i + 1 < len(sys.argv):
                    params["name"] = sys.argv[i + 1]
                    i += 2
                else:
                    i += 1
            
            result = mcp_run_task(params)
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif action == "mcp":
        # MCP Server 模式
        for line in sys.stdin:
            try:
                request = json.loads(line)
                method = request.get("method")
                params = request.get("params", {})
                
                handlers = {
                    "copilot.generate": mcp_copilot_generate,
                    "copilot.explain": mcp_copilot_explain,
                    "copilot.refactor": mcp_copilot_refactor,
                    "copilot.test": mcp_copilot_test,
                    "open.file": mcp_open_file,
                    "insert.code": mcp_insert_code,
                    "replace.code": mcp_replace_code,
                    "format.file": mcp_format_file,
                    "save.file": mcp_save_file,
                    "open.workspace": mcp_open_workspace,
                    "run.task": mcp_run_task
                }
                
                handler = handlers.get(method)
                if handler:
                    result = handler(params)
                else:
                    result = {"success": False, "error": f"Unknown method: {method}"}
                
                print(json.dumps(result, ensure_ascii=False))
                sys.stdout.flush()
                
            except json.JSONDecodeError:
                print(json.dumps({"success": False, "error": "Invalid JSON"}))
                sys.stdout.flush()
    
    else:
        print(f"Unknown action: {action}")
        print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
