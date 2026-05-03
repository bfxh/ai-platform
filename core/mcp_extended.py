#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP扩展工具集 - 增强版Model Context Protocol工具
支持: 文件操作、代码分析、数据处理、网络请求、系统命令等
"""

import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

sys.path.insert(0, r"\python\core")
sys.path.insert(0, r"\python\tools")


# ============ 文件操作工具 ============


class FileTools:
    """文件操作工具集"""

    @staticmethod
    def read(path: str, offset: int = 0, limit: int = None) -> str:
        """读取文件内容"""
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                if offset > 0:
                    f.seek(offset)
                content = f.read()
                if limit:
                    content = content[:limit]
                return content
        except Exception as e:
            return f"[错误] 读取失败: {e}"

    @staticmethod
    def read_binary(path: str) -> str:
        """读取二进制文件并转为base64"""
        try:
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            return f"[错误] 读取失败: {e}"

    @staticmethod
    def write(path: str, content: str, append: bool = False) -> str:
        """写入文件"""
        try:
            mode = "a" if append else "w"
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, mode, encoding="utf-8") as f:
                f.write(content)
            return f"[成功] 已{'追加' if append else '写入'}: {path}"
        except Exception as e:
            return f"[错误] 写入失败: {e}"

    @staticmethod
    def edit(path: str, old: str, new: str, count: int = 0) -> str:
        """编辑文件内容"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            if old not in content:
                return "[错误] 未找到要替换的内容"

            new_content = content.replace(old, new, count if count > 0 else -1)

            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return f"[成功] 已编辑: {path}"
        except Exception as e:
            return f"[错误] 编辑失败: {e}"

    @staticmethod
    def delete(path: str) -> str:
        """删除文件"""
        try:
            Path(path).unlink()
            return f"[成功] 已删除: {path}"
        except Exception as e:
            return f"[错误] 删除失败: {e}"

    @staticmethod
    def move(src: str, dst: str) -> str:
        """移动文件"""
        try:
            Path(src).rename(dst)
            return f"[成功] 已移动: {src} -> {dst}"
        except Exception as e:
            return f"[错误] 移动失败: {e}"

    @staticmethod
    def copy(src: str, dst: str) -> str:
        """复制文件"""
        try:
            import shutil

            Path(dst).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            return f"[成功] 已复制: {src} -> {dst}"
        except Exception as e:
            return f"[错误] 复制失败: {e}"

    @staticmethod
    def list_dir(path: str = ".", recursive: bool = False) -> str:
        """列出目录内容"""
        try:
            result = []
            p = Path(path)

            if recursive:
                for item in p.rglob("*"):
                    rel_path = item.relative_to(p)
                    icon = "📁" if item.is_dir() else "📄"
                    result.append(f"{icon} {rel_path}")
            else:
                for item in p.iterdir():
                    icon = "📁" if item.is_dir() else "📄"
                    size = item.stat().st_size if item.is_file() else "-"
                    result.append(f"{icon} {item.name:30} {size:>10} bytes")

            return "\n".join(result) if result else "(空目录)"
        except Exception as e:
            return f"[错误] 列出失败: {e}"

    @staticmethod
    def find(pattern: str, path: str = ".", file_type: str = "both") -> str:
        """查找文件"""
        try:
            result = []
            p = Path(path)

            for item in p.rglob(pattern):
                if file_type == "file" and item.is_dir():
                    continue
                if file_type == "dir" and item.is_file():
                    continue
                result.append(str(item))

            return "\n".join(result[:100]) if result else "(未找到)"
        except Exception as e:
            return f"[错误] 查找失败: {e}"

    @staticmethod
    def grep(pattern: str, path: str = ".", file_pattern: str = "*") -> str:
        """搜索文件内容"""
        try:
            result = []
            p = Path(path)

            for file_path in p.rglob(file_pattern):
                if file_path.is_file():
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            for i, line in enumerate(f, 1):
                                if pattern in line:
                                    result.append(f"{file_path}:{i}: {line.strip()}")
                                    if len(result) >= 50:
                                        break
                    except Exception:
                        pass

                if len(result) >= 50:
                    break

            return "\n".join(result) if result else "(未找到)"
        except Exception as e:
            return f"[错误] 搜索失败: {e}"

    @staticmethod
    def info(path: str) -> str:
        """获取文件信息"""
        try:
            p = Path(path)
            stat = p.stat()

            info = {
                "路径": str(p.absolute()),
                "类型": "目录" if p.is_dir() else "文件",
                "大小": f"{stat.st_size} bytes",
                "创建时间": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "修改时间": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "访问时间": datetime.fromtimestamp(stat.st_atime).isoformat(),
            }

            if p.is_file():
                info["扩展名"] = p.suffix
                info["MD5"] = FileTools._md5(path)

            return json.dumps(info, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"[错误] 获取信息失败: {e}"

    @staticmethod
    def _md5(path: str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)
        return h.hexdigest()


# ============ 代码分析工具 ============


class CodeTools:
    """代码分析工具集"""

    @staticmethod
    def analyze(path: str) -> str:
        """分析代码文件"""
        try:
            content = FileTools.read(path)
            if content.startswith("[错误]"):
                return content

            lines = content.split("\n")
            ext = Path(path).suffix.lower()

            analysis = {
                "文件": path,
                "行数": len(lines),
                "字符数": len(content),
                "空行": len([l for l in lines if not l.strip()]),
                "注释行": CodeTools._count_comments(content, ext),
                "函数/类": CodeTools._count_functions(content, ext),
            }

            return json.dumps(analysis, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"[错误] 分析失败: {e}"

    @staticmethod
    def _count_comments(content: str, ext: str) -> int:
        """统计注释行"""
        lines = content.split("\n")
        count = 0

        if ext in [".py"]:
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                    count += 1
        elif ext in [".js", ".ts", ".java", ".c", ".cpp"]:
            in_block = False
            for line in lines:
                stripped = line.strip()
                if "/*" in stripped:
                    in_block = True
                if in_block or stripped.startswith("//"):
                    count += 1
                if "*/" in stripped:
                    in_block = False

        return count

    @staticmethod
    def _count_functions(content: str, ext: str) -> Dict:
        """统计函数和类"""
        result = {"函数": 0, "类": 0}

        if ext == ".py":
            result["函数"] = len(re.findall(r"^def\s+\w+", content, re.MULTILINE))
            result["类"] = len(re.findall(r"^class\s+\w+", content, re.MULTILINE))
        elif ext in [".js", ".ts"]:
            result["函数"] = len(re.findall(r"function\s+\w+|\w+\s*=\s*\([^)]*\)\s*=>", content))
            result["类"] = len(re.findall(r"class\s+\w+", content))

        return result

    @staticmethod
    def extract_functions(path: str) -> str:
        """提取函数定义"""
        try:
            content = FileTools.read(path)
            ext = Path(path).suffix.lower()

            functions = []

            if ext == ".py":
                # 匹配函数定义
                pattern = r"^(def|class)\s+(\w+)\s*\([^)]*\):"
                for match in re.finditer(pattern, content, re.MULTILINE):
                    functions.append(match.group(0))

            return "\n".join(functions) if functions else "(未找到函数)"
        except Exception as e:
            return f"[错误] 提取失败: {e}"

    @staticmethod
    def format_code(path: str) -> str:
        """格式化代码"""
        try:
            ext = Path(path).suffix.lower()

            if ext == ".py":
                result = subprocess.run(["python", "-m", "black", path], capture_output=True, text=True)
                if result.returncode == 0:
                    return f"[成功] 已格式化: {path}"
                else:
                    return f"[警告] 格式化可能失败: {result.stderr}"
            else:
                return f"[错误] 不支持的文件类型: {ext}"
        except Exception as e:
            return f"[错误] 格式化失败: {e}"

    @staticmethod
    def lint(path: str) -> str:
        """代码检查"""
        try:
            ext = Path(path).suffix.lower()

            if ext == ".py":
                result = subprocess.run(["python", "-m", "pylint", path], capture_output=True, text=True)
                return result.stdout or "[成功] 无问题"
            else:
                return f"[错误] 不支持的文件类型: {ext}"
        except Exception as e:
            return f"[错误] 检查失败: {e}"


# ============ 数据处理工具 ============


class DataTools:
    """数据处理工具集"""

    @staticmethod
    def json_parse(text: str) -> str:
        """解析JSON"""
        try:
            data = json.loads(text)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"[错误] 解析失败: {e}"

    @staticmethod
    def json_format(path: str) -> str:
        """格式化JSON文件"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return f"[成功] 已格式化: {path}"
        except Exception as e:
            return f"[错误] 格式化失败: {e}"

    @staticmethod
    def csv_to_json(csv_path: str) -> str:
        """CSV转JSON"""
        try:
            import csv

            data = []
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)

            json_path = csv_path.replace(".csv", ".json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return f"[成功] 已转换: {json_path}"
        except Exception as e:
            return f"[错误] 转换失败: {e}"

    @staticmethod
    def count_lines(path: str) -> str:
        """统计行数"""
        try:
            result = subprocess.run(["findstr", "/R", "/N", "^", path], capture_output=True, text=True, shell=False)
            lines = len(result.stdout.strip().split("\n"))
            return f"总行数: {lines}"
        except Exception as e:
            return f"[错误] 统计失败: {e}"


# ============ 网络工具 ============


class NetworkTools:
    """网络工具集"""

    @staticmethod
    def fetch(url: str, method: str = "GET", headers: Dict = None, data: str = None) -> str:
        """HTTP请求"""
        try:
            req = urllib.request.Request(
                url, data=data.encode("utf-8") if data else None, headers=headers or {}, method=method
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read().decode("utf-8")
        except Exception as e:
            return f"[错误] 请求失败: {e}"

    @staticmethod
    def download(url: str, output: str = None) -> str:
        """下载文件"""
        try:
            if not output:
                output = Path(url).name or "download"

            urllib.request.urlretrieve(url, output)
            return f"[成功] 已下载: {output}"
        except Exception as e:
            return f"[错误] 下载失败: {e}"

    @staticmethod
    def ping(host: str) -> str:
        """Ping测试"""
        try:
            result = subprocess.run(["ping", "-n", "4", host], capture_output=True, text=True)
            return result.stdout
        except Exception as e:
            return f"[错误] Ping失败: {e}"


# ============ 系统工具 ============


class SystemTools:
    """系统工具集"""

    _BLOCKED = {'rm', 'del', 'format', 'rmdir', 'rd', 'erase', 'cipher', 'diskpart',
                'net', 'netsh', 'reg', 'regedit', 'wscript', 'cscript', 'mshta',
                'certutil', 'bitsadmin', 'ftp', 'shutdown', 'taskkill'}

    @staticmethod
    def exec(command: str, timeout: int = 60) -> str:
        """执行命令"""
        try:
            first_token = command.split()[0].lower() if command.split() else ""
            base_name = os.path.basename(first_token)
            name, _ = os.path.splitext(base_name)
            if name in SystemTools._BLOCKED:
                return f"[错误] 危险命令已被阻止: {name}"
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr] {result.stderr}"
            return output or "(无输出)"
        except subprocess.TimeoutExpired:
            return "[错误] 命令超时"
        except Exception as e:
            return f"[错误] 执行失败: {e}"

    @staticmethod
    def env(var: str = None) -> str:
        """查看环境变量"""
        if var:
            return os.getenv(var, "(未设置)")
        else:
            return json.dumps(dict(os.environ), ensure_ascii=False, indent=2)

    @staticmethod
    def which(command: str) -> str:
        """查找命令路径"""
        try:
            result = subprocess.run(["where", command], capture_output=True, text=True)
            return result.stdout.strip() or "(未找到)"
        except Exception as e:
            return f"[错误] 查找失败: {e}"

    @staticmethod
    def disk_usage(path: str = ".") -> str:
        """磁盘使用情况"""
        try:
            import shutil

            total, used, free = shutil.disk_usage(path)
            return json.dumps(
                {
                    "总空间": f"{total // (2**30)} GB",
                    "已使用": f"{used // (2**30)} GB",
                    "可用": f"{free // (2**30)} GB",
                    "使用率": f"{used/total*100:.1f}%",
                },
                ensure_ascii=False,
                indent=2,
            )
        except Exception as e:
            return f"[错误] 获取失败: {e}"


# ============ MCP工具总入口 ============


class MCPExtended:
    """
    MCP扩展工具总入口

    用法:
        mcp = MCPExtended()

        # 文件操作
        mcp.file("read", "path/to/file")
        mcp.file("write", "path", content="...")

        # 代码分析
        mcp.code("analyze", "path/to/code.py")

        # 数据处理
        mcp.data("json_parse", '{"key": "value"}')

        # 网络请求
        mcp.network("fetch", "https://api.example.com")

        # 系统命令
        mcp.system("exec", "dir")
    """

    def __init__(self):
        self.file_tools = FileTools()
        self.code_tools = CodeTools()
        self.data_tools = DataTools()
        self.network_tools = NetworkTools()
        self.system_tools = SystemTools()

    def file(self, action: str, *args, **kwargs) -> str:
        """文件操作"""
        method = getattr(self.file_tools, action, None)
        if method:
            return method(*args, **kwargs)
        return f"[错误] 未知的文件操作: {action}"

    def code(self, action: str, *args, **kwargs) -> str:
        """代码操作"""
        method = getattr(self.code_tools, action, None)
        if method:
            return method(*args, **kwargs)
        return f"[错误] 未知的代码操作: {action}"

    def data(self, action: str, *args, **kwargs) -> str:
        """数据操作"""
        method = getattr(self.data_tools, action, None)
        if method:
            return method(*args, **kwargs)
        return f"[错误] 未知的数据操作: {action}"

    def network(self, action: str, *args, **kwargs) -> str:
        """网络操作"""
        method = getattr(self.network_tools, action, None)
        if method:
            return method(*args, **kwargs)
        return f"[错误] 未知的网络操作: {action}"

    def system(self, action: str, *args, **kwargs) -> str:
        """系统操作"""
        method = getattr(self.system_tools, action, None)
        if method:
            return method(*args, **kwargs)
        return f"[错误] 未知的系统操作: {action}"

    def help(self) -> str:
        """显示帮助"""
        return """
MCP扩展工具集

文件操作 (mcp.file):
  - read(path, offset=0, limit=None)     读取文件
  - read_binary(path)                    读取二进制文件
  - write(path, content, append=False)   写入文件
  - edit(path, old, new, count=0)        编辑文件
  - delete(path)                         删除文件
  - move(src, dst)                       移动文件
  - copy(src, dst)                       复制文件
  - list_dir(path=".", recursive=False)  列出目录
  - find(pattern, path=".")              查找文件
  - grep(pattern, path=".")              搜索内容
  - info(path)                           文件信息

代码分析 (mcp.code):
  - analyze(path)                        分析代码
  - extract_functions(path)              提取函数
  - format_code(path)                    格式化代码
  - lint(path)                           代码检查

数据处理 (mcp.data):
  - json_parse(text)                     解析JSON
  - json_format(path)                    格式化JSON文件
  - csv_to_json(csv_path)                CSV转JSON
  - count_lines(path)                    统计行数

网络工具 (mcp.network):
  - fetch(url, method="GET")             HTTP请求
  - download(url, output=None)           下载文件
  - ping(host)                           Ping测试

系统工具 (mcp.system):
  - exec(command, timeout=60)            执行命令
  - env(var=None)                        查看环境变量
  - which(command)                       查找命令
  - disk_usage(path=".")                 磁盘使用
"""


# 全局实例
mcp_ext = MCPExtended()


# 便捷函数
def file(action: str, *args, **kwargs) -> str:
    return mcp_ext.file(action, *args, **kwargs)


def code(action: str, *args, **kwargs) -> str:
    return mcp_ext.code(action, *args, **kwargs)


def data(action: str, *args, **kwargs) -> str:
    return mcp_ext.data(action, *args, **kwargs)


def network(action: str, *args, **kwargs) -> str:
    return mcp_ext.network(action, *args, **kwargs)


def system(action: str, *args, **kwargs) -> str:
    return mcp_ext.system(action, *args, **kwargs)


if __name__ == "__main__":
    print(mcp_ext.help())
