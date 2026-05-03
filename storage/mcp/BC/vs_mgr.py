#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VS Manager - MCP Server (stdio JSON-RPC)

 AI 直接调用 Visual Studio / VSCode 的所有功能
 MCP stdio 协，也兼命令模式

MCP Tools:
  vs_open        打开 VS  VSCode
  vs_info        IDE 境信
  vs_build       编译解决方 (MSBuild)
  vs_rebuild     重新编译
  vs_clean       清理编译输出
  vs_ext_list    列出 VSCode 扩展
  vs_ext_install 安扩
  vs_ext_uninstall 卸载扩展
  vs_diff        VSCode 对比文件
  vs_open_file   打开文件到指定
  vs_open_folder 打开文件
  vs_check       境
  vs_kill        关闭有实
"""

import sys
import os
import subprocess
import json
import shutil
import time
import io
from pathlib import Path
from datetime import datetime

# ============================================================
# 径配
# ============================================================
VS_PATH = Path(r"%SOFTWARE_DIR%\KF\BC\VS")
VS_DEVENV = VS_PATH / "Common7" / "IDE" / "devenv.exe"
VS_MSVC = VS_PATH / "VC" / "Tools" / "MSVC"
VS_MSBUILD = VS_PATH / "MSBuild" / "Current" / "Bin" / "MSBuild.exe"

VSCODE_PATH = Path(r"F:\件\编程\vs code\Microsoft VS Code")
VSCODE_EXE = VSCODE_PATH / "Code.exe"
VSCODE_CLI = VSCODE_PATH / "bin" / "code.cmd"
VSCODE_EXTENSIONS = Path(os.environ.get("USERPROFILE", "{USERPROFILE}")) / ".vscode" / "extensions"

DEFAULT_CONFIG = "Release"
DEFAULT_PLATFORM = "x64"


def _run(cmd, cwd=None, capture=True, timeout=120, shell=False):
    try:
        if capture:
            r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout, shell=shell)
            return r.returncode, r.stdout, r.stderr
        else:
            r = subprocess.run(cmd, cwd=cwd, timeout=timeout, shell=shell)
            return r.returncode, "", ""
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except FileNotFoundError:
        return -1, "", f"not found: {cmd[0] if cmd else '?'}"


def _find_msbuild():
    candidates = [
        VS_MSBUILD,
        VS_PATH / "MSBuild" / "Current" / "Bin" / "amd64" / "MSBuild.exe",
        VS_PATH / "MSBuild" / "Current" / "Bin" / "MSBuild.exe",
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    vw = VS_PATH / "Common7" / "Tools" / "vswhere.exe"
    if vw.exists():
        rc, out, _ = _run([str(vw), "-latest", "-requires", "Microsoft.Component.MSBuild",
                           "-find", "MSBuild\\**\\Bin\\MSBuild.exe"])
        if rc == 0 and out.strip():
            return out.strip()
    return None


def _find_sln(dir_path):
    p = Path(dir_path)
    if p.is_file() and p.suffix == ".sln":
        return str(p)
    if p.is_dir():
        slns = list(p.glob("*.sln"))
        if slns:
            for s in slns:
                if "Test" not in s.name:
                    return str(s)
            return str(slns[0])
    return None


# ============================================================
# Tool 实现（返回文结果
# ============================================================

def tool_open(params):
    target = params.get("target", "code")
    target = target.lower()

    if target in ("vs", "visualstudio", "devenv"):
        if not VS_DEVENV.exists():
            return f"VS devenv 不存: {VS_DEVENV}"
        subprocess.Popen([str(VS_DEVENV)])
        return f"已打 Visual Studio ({VS_DEVENV})"

    elif target in ("code", "vscode"):
        if not VSCODE_EXE.exists():
            return f"VSCode 不存: {VSCODE_EXE}"
        subprocess.Popen([str(VSCODE_EXE)])
        return f"已打 VSCode ({VSCODE_EXE})"

    else:
        p = Path(target)
        if p.exists():
            if VSCODE_EXE.exists():
                subprocess.Popen([str(VSCODE_EXE), str(p)])
                return f"已在 VSCode 打开: {p}"
            elif VS_DEVENV.exists():
                subprocess.Popen([str(VS_DEVENV), str(p)])
                return f"已在 VS 打开: {p}"
        return f"知目: {target} (: vs, code, 或文件路)"


def tool_info(params):
    lines = []
    lines.append("=== Visual Studio / VSCode 境信 ===")

    lines.append("\n[Visual Studio]")
    lines.append(f"  : {VS_PATH}")
    lines.append(f"  devenv: {'存在' if VS_DEVENV.exists() else '缺失'}")
    if VS_DEVENV.exists():
        lines.append(f"  大小: {VS_DEVENV.stat().st_size/1024/1024:.1f}MB")

    if VS_MSVC.exists():
        versions = sorted([d.name for d in VS_MSVC.iterdir() if d.is_dir()])
        lines.append(f"  MSVC: {', '.join(versions)}")
    else:
        lines.append("  MSVC: 找到")

    msbuild = _find_msbuild()
    lines.append(f"  MSBuild: {msbuild if msbuild else '找到'}")

    lines.append("\n[VSCode]")
    lines.append(f"  : {VSCODE_PATH}")
    lines.append(f"  Code.exe: {'存在' if VSCODE_EXE.exists() else '缺失'}")
    if VSCODE_CLI.exists():
        rc, out, _ = _run([str(VSCODE_CLI), "--version"])
        if rc == 0:
            vl = out.strip().split("\n")
            lines.append(f"  版本: {vl[0] if vl else ''}")
            lines.append(f"  提交: {vl[1] if len(vl) > 1 else ''}")
            lines.append(f"  架构: {vl[2] if len(vl) > 2 else ''}")

    if VSCODE_EXTENSIONS.exists():
        ext_count = len(list(VSCODE_EXTENSIONS.iterdir()))
        lines.append(f"  扩展: {ext_count} ")

    return "\n".join(lines)


def tool_build(params):
    sln_path = params.get("sln_path", "")
    config = params.get("config") or DEFAULT_CONFIG
    platform = params.get("platform") or DEFAULT_PLATFORM
    rebuild = params.get("rebuild", False)

    if not sln_path:
        return "错: 要提 sln_path (解决方路径或项目)"

    sln = _find_sln(sln_path)
    if not sln:
        return f"找到解决方: {sln_path}"

    msbuild = _find_msbuild()
    if not msbuild:
        return "找到 MSBuild.exe"

    cmd = [msbuild, sln, f"/p:Configuration={config}", f"/p:Platform={platform}",
           "/m", "/v:minimal", "/t:Rebuild" if rebuild else "/t:Build"]

    start = time.time()
    rc, out, err = _run(cmd, timeout=300)
    elapsed = time.time() - start

    if rc == 0:
        warnings = out.count("warning")
        result = f"[OK] 编译成功 ({elapsed:.1f}s, {warnings} warnings)\n{sln}"
        # 提取输出
        for line in out.split("\n"):
            if ".dll" in line.lower() or ".exe" in line.lower():
                result += f"\n  {line.strip()}"
        return result
    else:
        error_lines = [l.strip() for l in (out + err).split("\n") if "error" in l.lower()]
        return f"[FAIL] 编译失败 ({elapsed:.1f}s)\n" + "\n".join(error_lines[-15:])


def tool_clean(params):
    sln_path = params.get("sln_path", "")
    config = params.get("config") or DEFAULT_CONFIG
    platform = params.get("platform") or DEFAULT_PLATFORM

    if not sln_path:
        return "错: 要提 sln_path"
    sln = _find_sln(sln_path)
    if not sln:
        return f"找到解决方: {sln_path}"
    msbuild = _find_msbuild()
    if not msbuild:
        return "找到 MSBuild.exe"

    rc, out, err = _run([msbuild, sln, f"/p:Configuration={config}",
                         f"/p:Platform={platform}", "/t:Clean", "/v:minimal"],
                        timeout=120)
    return f"[OK] 已清: {Path(sln).name}" if rc == 0 else f"[FAIL] 清理失败\n{err}"


def tool_ext_list(params):
    if not VSCODE_CLI.exists():
        return "VSCode CLI 不存"
    rc, out, _ = _run([str(VSCODE_CLI), "--list-extensions", "--show-versions"])
    if rc == 0:
        exts = [e.strip() for e in out.strip().split("\n") if e.strip()]
        return f"已安 {len(exts)} 扩展:\n" + "\n".join(f"  {e}" for e in sorted(exts))
    return "获取扩展列表失败"


def tool_ext_install(params):
    ext_id = params.get("ext_id", "")
    if not ext_id:
        return "错: 要提 ext_id"
    rc, out, err = _run([str(VSCODE_CLI), "--install-extension", ext_id, "--force"],
                       timeout=120)
    if rc == 0:
        return f"[OK] 已安: {ext_id}"
    return f"[FAIL] 安失: {ext_id}\n{err}"


def tool_ext_uninstall(params):
    ext_id = params.get("ext_id", "")
    if not ext_id:
        return "错: 要提 ext_id"
    rc, out, err = _run([str(VSCODE_CLI), "--uninstall-extension", ext_id],
                       timeout=60)
    if rc == 0:
        return f"[OK] 已卸: {ext_id}"
    return f"[FAIL] 卸载失败: {ext_id}\n{err}"


def tool_diff(params):
    file1 = params.get("file1", "")
    file2 = params.get("file2", "")
    if not file1 or not file2:
        return "错: 要提 file1  file2"
    if not Path(file1).exists():
        return f"文件不存: {file1}"
    if not Path(file2).exists():
        return f"文件不存: {file2}"
    if not VSCODE_EXE.exists():
        return "VSCode 不存"
    subprocess.Popen([str(VSCODE_EXE), "--diff", file1, file2])
    return f"已打对比: {file1} vs {file2}"


def tool_open_file(params):
    path = params.get("path", "")
    line = params.get("line")
    if not path:
        return "错: 要提 path"
    p = Path(path)
    if not p.exists():
        return f"文件不存: {path}"
    if not VSCODE_EXE.exists():
        return "VSCode 不存"
    cmd = [str(VSCODE_EXE), "-g", str(p)]
    if line:
        cmd.append(f":{line}")
    subprocess.Popen(cmd)
    return f"已打: {p}" + (f" ( {line})" if line else "")


def tool_open_folder(params):
    path = params.get("path", "")
    if not path:
        return "错: 要提 path"
    p = Path(path)
    if not p.exists():
        return f"径不存在: {path}"
    if not VSCODE_EXE.exists():
        return "VSCode 不存"
    subprocess.Popen([str(VSCODE_EXE), str(p)])
    return f"已打文件: {p}"


def tool_check(params):
    lines = ["=== IDE 境 ==="]

    vs_ok = VS_DEVENV.exists()
    lines.append(f"\n[Visual Studio] {'OK' if vs_ok else 'MISSING'}")
    if vs_ok:
        lines.append(f"  devenv: {VS_DEVENV}")

    msvc_versions = []
    if VS_MSVC.exists():
        msvc_versions = sorted([d.name for d in VS_MSVC.iterdir() if d.is_dir()])
    lines.append(f"[MSVC] {len(msvc_versions)} 版本 ({', '.join(msvc_versions) if msvc_versions else ''})")

    msbuild = _find_msbuild()
    lines.append(f"[MSBuild] {'OK' if msbuild else 'MISSING'}")
    if msbuild:
        lines.append(f"  {msbuild}")

    vsc_ok = VSCODE_EXE.exists()
    lines.append(f"\n[VSCode] {'OK' if vsc_ok else 'MISSING'}")
    if vsc_ok:
        lines.append(f"  Code.exe: {VSCODE_EXE}")

    ext_ok = VSCODE_EXTENSIONS.exists()
    ext_count = len(list(VSCODE_EXTENSIONS.iterdir())) if ext_ok else 0
    lines.append(f"[扩展] {ext_count} ")

    lines.append("\n[运状态]")
    for name in ["devenv.exe", "Code.exe"]:
        rc, out, _ = _run(["tasklist", "/FI", f"IMAGENAME eq {name}", "/FO", "CSV", "/NH"])
        if name in out:
            for line in out.strip().split("\n"):
                if name in line:
                    parts = line.split('","')
                    pid = parts[1].strip('"') if len(parts) > 1 else "?"
                    mem = parts[4].strip('"').replace(",", "").replace(" K", "") if len(parts) > 4 else "?"
                    lines.append(f"  {name}: PID={pid}, 内存={mem} KB")
        else:
            lines.append(f"  {name}: 运")

    return "\n".join(lines)


def tool_kill(params):
    results = []
    for name in ["devenv.exe", "Code.exe"]:
        rc, _, _ = _run(["taskkill", "/F", "/IM", name], capture=False)
        results.append(f"  {name}: {'已关' if rc == 0 else '无运行实'}")
    return "已关 IDE 实例:\n" + "\n".join(results)


# ============================================================
# Tool 注册
# ============================================================

TOOLS = {
    "vs_open": {
        "name": "vs_open",
        "description": "打开 Visual Studio  VSCode IDE。target='vs' 打开VS, target='code' 打开VSCode, target='' 用VSCode打开文件/文件",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "vs / code / 文件/文件夹路", "default": "code"}
            }
        },
        "handler": tool_open
    },
    "vs_info": {
        "name": "vs_info",
        "description": "获取 Visual Studio  VSCode 的完整环境信（版、路径MSVC工具链MSBuild、扩展数量等",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": tool_info
    },
    "vs_build": {
        "name": "vs_build",
        "description": " MSBuild 编译 .sln 解决方自动查找目录中 .sln 文件。config: Debug/Release, platform: x64/x86/Win32, rebuild: true=重新编译",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sln_path": {"type": "string", "description": ".sln 文件径或包含 .sln 的目"},
                "config": {"type": "string", "description": "编译配置: Debug / Release", "default": "Release"},
                "platform": {"type": "string", "description": "标平: x64 / x86 / Win32", "default": "x64"},
                "rebuild": {"type": "boolean", "description": "否重新编译（默量编译", "default": False}
            },
            "required": ["sln_path"]
        },
        "handler": tool_build
    },
    "vs_clean": {
        "name": "vs_clean",
        "description": "清理解决方的编译输出（bin/obj 等）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sln_path": {"type": "string", "description": ".sln 文件径或"},
                "config": {"type": "string", "default": "Release"},
                "platform": {"type": "string", "default": "x64"}
            },
            "required": ["sln_path"]
        },
        "handler": tool_clean
    },
    "vs_ext_list": {
        "name": "vs_ext_list",
        "description": "列出 VSCode 已安装的有扩展及版本",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": tool_ext_list
    },
    "vs_ext_install": {
        "name": "vs_ext_install",
        "description": "安 VSCode 扩展， 'ms-python.python'  'ms-vscode.cpptools'",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ext_id": {"type": "string", "description": "扩展ID,  ms-python.python"}
            },
            "required": ["ext_id"]
        },
        "handler": tool_ext_install
    },
    "vs_ext_uninstall": {
        "name": "vs_ext_uninstall",
        "description": "卸载 VSCode 扩展",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ext_id": {"type": "string", "description": "扩展ID"}
            },
            "required": ["ext_id"]
        },
        "handler": tool_ext_uninstall
    },
    "vs_diff": {
        "name": "vs_diff",
        "description": " VSCode 打开双文件比视图",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file1": {"type": "string", "description": "文件1"},
                "file2": {"type": "string", "description": "文件2"}
            },
            "required": ["file1", "file2"]
        },
        "handler": tool_diff
    },
    "vs_open_file": {
        "name": "vs_open_file",
        "description": " VSCode 打开文件并跳到指定号",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件"},
                "line": {"type": "integer", "description": "跳转到的行号（可选）"}
            },
            "required": ["path"]
        },
        "handler": tool_open_file
    },
    "vs_open_folder": {
        "name": "vs_open_folder",
        "description": " VSCode 打开文件夹作为工作区",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件夹路"}
            },
            "required": ["path"]
        },
        "handler": tool_open_folder
    },
    "vs_check": {
        "name": "vs_check",
        "description": " VS/VSCode 境状态MSVC工具链MSBuild、运行进程等",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": tool_check
    },
    "vs_kill": {
        "name": "vs_kill",
        "description": "强制关闭 Visual Studio  VSCode 实例",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": tool_kill
    },
}


# ============================================================
# MCP stdio 协实现
# ============================================================

def _send(msg):
    """发 JSON-RPC 消息 stdout"""
    json.dump(msg, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    sys.stdout.flush()


def _read_line():
    """ stdin 读取"""
    line = sys.stdin.readline()
    if not line:
        sys.exit(0)
    return line.strip()


def handle_request(req):
    """处理 JSON-RPC 请求"""
    method = req.get("method", "")
    req_id = req.get("id")
    params = req.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": False}
                },
                "serverInfo": {
                    "name": "vs-manager",
                    "version": "1.0.0"
                }
            }
        }

    elif method == "notifications/initialized":
        return None  # 无需回

    elif method == "tools/list":
        tool_list = []
        for tid, t in TOOLS.items():
            tool_list.append({
                "name": t["name"],
                "description": t["description"],
                "inputSchema": t["inputSchema"]
            })
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": tool_list}
        }

    elif method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        tool = TOOLS.get(tool_name)
        if not tool:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"知工: {tool_name}"}
            }

        try:
            result_text = tool["handler"](arguments)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": result_text}]
                }
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32603, "message": str(e)}
            }

    elif method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}

    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"知方: {method}"}
        }


def mcp_loop():
    """MCP stdio 主循"""
    # 发 server 信息
    _send({
        "jsonrpc": "2.0",
        "method": "notifications/message",
        "params": {
            "level": "info",
            "data": "VS Manager MCP Server started. 12 tools available."
        }
    })

    while True:
        try:
            line = _read_line()
            if not line:
                break
            req = json.loads(line)
            resp = handle_request(req)
            if resp is not None:
                _send(resp)
        except json.JSONDecodeError:
            pass
        except Exception:
            break


# ============================================================
# 命令行模式（兼 ai.py 调用
# ============================================================

def cli_main():
    if len(sys.argv) < 2:
        tools_desc = "\n".join(f"  {t['name']:20s} {t['description'][:50]}" for t in TOOLS.values())
        print(f"""VS Manager - VS/VSCode 控制

用法: python vs_mgr.py <action> [args...]

工具列表:
{tools_desc}

命令行快捷方:
  open [vs|code|径]    打开IDE
  info                   境信
  build <sln> [cfg] [plat]  编译
  rebuild <sln> [cfg] [plat]  重编
  clean <sln> [cfg] [plat]   清理
  ext list|install|uninstall  扩展管理
  diff <f1> <f2>        对比文件
  openfile <path> [行]   打开文件
  folder <path>          打开文件
  check                  境
  kill                   关闭""")
        return

    action = sys.argv[1]
    args = sys.argv[2:]

    # 映射 MCP tools
    action_map = {
        "open": ("vs_open", lambda: {"target": args[0] if args else "code"}),
        "info": ("vs_info", lambda: {}),
        "build": ("vs_build", lambda: {
            "sln_path": args[0] if args else "",
            "config": args[1] if len(args) > 1 else None,
            "platform": args[2] if len(args) > 2 else None,
            "rebuild": False
        }),
        "rebuild": ("vs_build", lambda: {
            "sln_path": args[0] if args else "",
            "config": args[1] if len(args) > 1 else None,
            "platform": args[2] if len(args) > 2 else None,
            "rebuild": True
        }),
        "clean": ("vs_clean", lambda: {
            "sln_path": args[0] if args else "",
            "config": args[1] if len(args) > 1 else None,
            "platform": args[2] if len(args) > 2 else None,
        }),
        "ext": ("vs_ext_list", lambda: {}) if (not args or args[0] == "list") else (
            ("vs_ext_install", lambda: {"ext_id": args[1] if len(args) > 1 else ""}) if args[0] == "install" else (
            ("vs_ext_uninstall", lambda: {"ext_id": args[1] if len(args) > 1 else ""}))),
        "diff": ("vs_diff", lambda: {"file1": args[0], "file2": args[1] if len(args) > 1 else ""}),
        "openfile": ("vs_open_file", lambda: {
            "path": args[0] if args else "",
            "line": int(args[1]) if len(args) > 1 and args[1].isdigit() else None
        }),
        "folder": ("vs_open_folder", lambda: {"path": args[0] if args else ""}),
        "check": ("vs_check", lambda: {}),
        "kill": ("vs_kill", lambda: {}),
    }

    if action in action_map:
        tool_name, param_fn = action_map[action]
        tool = TOOLS[tool_name]
        try:
            result = tool["handler"](param_fn())
            print(result)
        except Exception as e:
            print(f"错: {e}")
    else:
        # 直接调用 MCP tool
        if action in TOOLS:
            try:
                result = TOOLS[action]["handler"]({})
                print(result)
            except Exception as e:
                print(f"错: {e}")
        else:
            print(f"知命: {action}")


# ============================================================
# 入口：自动测模
# ============================================================
if __name__ == '__main__':
    # 如果有命令参  CLI 模式
    # 如果没有参数 stdin 管道  MCP stdio 模式
    if len(sys.argv) > 1:
        cli_main()
    else:
        mcp_loop()
