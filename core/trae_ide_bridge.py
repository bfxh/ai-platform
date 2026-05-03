#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRAE IDE Bridge — 语义化 IDE 操作接口，封装 da.py 桌面自动化

将底层键盘模拟 (da.py) 翻译为高层 IDE 语义操作：
- open_ide()      启动/激活 TRAE IDE 窗口
- write_code()    在 IDE 中创建文件并写入代码
- read_file()     从 IDE 中读取文件内容
- run_command()   在 IDE 终端中执行命令
- get_status()    检查 IDE 窗口/进程状态

所有操作调用 da.py 子进程，通过剪贴板传递大段代码（避免中文输入法问题）。

用法:
    from core.trae_ide_bridge import TRAEIDEBridge

    bridge = TRAEIDEBridge()
    bridge.open_ide("D:/projects/myapp")
    bridge.write_code("src/main.py", 'print("hello")')
"""

import os
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

# 导入文件保护（CC 三级缓存 + 安全备份）
try:
    from file_protector import FileProtector, get_protector
    _PROTECTOR_AVAILABLE = True
except ImportError:
    _PROTECTOR_AVAILABLE = False
    FileProtector = None
    get_protector = None


class TRAEIDEBridge:
    """TRAE IDE 桥接控制器 — 封装 da.py 为语义化 IDE 操作"""

    # ================================================================
    # 配置
    # ================================================================
    DEFAULT_IDE_WINDOW_TITLE = "Trae"          # TRAE IDE 窗口标题关键词
    DEFAULT_IDE_PROCESS = "Trae.exe"            # TRAE IDE 进程名
    DEFAULT_DELAY_SHORT = 0.1                    # 短等待 (秒)
    DEFAULT_DELAY_MEDIUM = 0.3                  # 中等待
    DEFAULT_DELAY_LONG = 0.8                    # 长等待
    DEFAULT_STARTUP_TIMEOUT = 30                # IDE 启动超时 (秒)

    def __init__(self, da_path: str = None, python_path: str = None,
                 ide_window_title: str = None, ide_process: str = None,
                 base_dir: str = None):
        """
        Args:
            da_path:          da.py 的绝对路径
            python_path:      Python 解释器路径 (默认: python)
            ide_window_title: TRAE IDE 窗口标题关键词
            ide_process:      TRAE IDE 进程名
            base_dir:         项目根目录（用于计算文件保护路径）
        """
        self.python = python_path or "python"
        self.ide_title = ide_window_title or self.DEFAULT_IDE_WINDOW_TITLE
        self.ide_process = ide_process or self.DEFAULT_IDE_PROCESS

        if da_path is None:
            # 自动探测 da.py 位置
            candidates = [
                Path("/python/storage/mcp/Tools/da.py"),
                Path("/MCP/Tools/da.py"),
            ]
            for c in candidates:
                if c.exists():
                    da_path = str(c)
                    break
            else:
                da_path = "/python/storage/mcp/Tools/da.py"

        self.da_path = da_path
        self._ensure_da_exists()

        # 文件保护器（写代码前自动备份已有文件）
        self._base_dir = base_dir or os.environ.get(
            "AI_BASE_DIR",
            str(Path(da_path).resolve().parent.parent.parent)  # up from storage/mcp/Tools/
        )
        self._protector: Optional[Any] = None
        if _PROTECTOR_AVAILABLE:
            try:
                self._protector = get_protector()
            except Exception:
                pass

    def _ensure_da_exists(self):
        """确认 da.py 存在"""
        if not Path(self.da_path).exists():
            raise FileNotFoundError(
                f"da.py 未找到: {self.da_path}\n"
                f"请确认桌面自动化工具存在，或通过 da_path 参数指定路径。"
            )

    # ================================================================
    # 内部方法
    # ================================================================

    def _call_da(self, action: str, *args) -> str:
        """调用 da.py 执行单个动作

        Args:
            action: da.py 动作名 (如 activate, hotkey, type)
            *args:  动作参数

        Returns:
            da.py 的标准输出字符串
        """
        cmd = [self.python, self.da_path, action] + [str(a) for a in args]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15,
                cwd=os.path.dirname(self.da_path),
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            return "TIMEOUT"
        except Exception as e:
            return f"ERROR: {e}"

    def _call_da_json(self, actions: List[dict]) -> List[str]:
        """通过 macro 批量执行多步操作

        Args:
            actions: [{"action": "activate", "args": ["Trae"]}, ...]

        Returns:
            每步结果列表
        """
        # 将动作列表转为 JSON 并传给 macro
        macro_json = json.dumps(actions, ensure_ascii=False)
        cmd = [self.python, self.da_path, "macro", macro_json]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.path.dirname(self.da_path),
            )
            return result.stdout.strip().split("\n")
        except Exception as e:
            return [f"ERROR: {e}"]

    def _wait_for_window(self, timeout: float = None) -> bool:
        """等待 TRAE IDE 窗口出现"""
        timeout = timeout or self.DEFAULT_STARTUP_TIMEOUT
        result = self._call_da("wait_window", self.ide_title, str(timeout))
        return "found" in result.lower()

    def _clipboard_read(self) -> str:
        """读取剪贴板"""
        result = self._call_da("clip_read")
        # da.py 的 clip_read 直接在 stdout 输出剪贴板内容
        return result

    def _clipboard_write(self, text: str):
        """写入剪贴板"""
        self._call_da("clip_write", text)

    def _is_window_visible(self) -> bool:
        """检查 TRAE IDE 窗口是否可见"""
        result = self._call_da("find_win", self.ide_title)
        return "found" in result.lower() and "no window" not in result.lower()

    def _is_process_running(self) -> bool:
        """检查 TRAE IDE 进程是否在运行"""
        result = self._call_da("processes")
        return self.ide_process.lower() in result.lower()

    def _safe_type(self, text: str, delay_per_char: float = 0.015):
        """安全输入文本 — 短文本逐字输入，长文本优先用剪贴板
        注意：中文输入法环境下，逐字输入可能出错。
              对于多字节字符或长文本，使用剪贴板粘贴。
        """
        if len(text) > 50 or any(ord(c) > 127 for c in text):
            # 长文本或含中文 → 剪贴板粘贴
            self._clipboard_write(text)
            time.sleep(self.DEFAULT_DELAY_SHORT)
            self._call_da("hotkey", "ctrl+v")
        else:
            # 短 ASCII 文本 → 逐字输入
            self._call_da("type", text)

    def _backup_before_write(self, file_path: str):
        """写入前备份已有文件到 CC 缓存（文件保护）"""
        if not self._protector:
            return
        try:
            # 计算文件在工作区中的绝对路径
            abs_path = Path(self._base_dir) / file_path
            if abs_path.exists():
                rel_path = str(abs_path.relative_to(self._base_dir)).replace("\\", "/")
                if self._protector.is_protected(rel_path):
                    self._protector.safe_write(rel_path, abs_path.read_text(encoding="utf-8"))
                    # safe_write 内部会自动备份到 CC/2_old/
        except Exception:
            pass  # 静默失败，不影响主流程

    # ================================================================
    # 公开 API — IDE 操作
    # ================================================================

    def get_status(self) -> Dict[str, Any]:
        """获取 TRAE IDE 当前状态

        Returns:
            {"status": "running"|"not_found"|"error",
             "window": bool, "process": bool, "details": str}
        """
        try:
            has_window = self._is_window_visible()
            has_process = self._is_process_running()

            if has_window and has_process:
                return {
                    "status": "running",
                    "window": True,
                    "process": True,
                    "details": "TRAE IDE 窗口已就绪"
                }
            elif has_process:
                return {
                    "status": "process_only",
                    "window": False,
                    "process": True,
                    "details": "TRAE 进程运行中但窗口不可见（可能在托盘）"
                }
            else:
                return {
                    "status": "not_found",
                    "window": False,
                    "process": False,
                    "details": "TRAE IDE 未运行"
                }
        except Exception as e:
            return {
                "status": "error",
                "window": False,
                "process": False,
                "details": str(e)
            }

    def open_ide(self, project_path: str = None) -> Dict[str, Any]:
        """启动/激活 TRAE IDE

        Args:
            project_path: 可选，要打开的项目目录路径

        Returns:
            {"success": bool, "message": str}
        """
        try:
            # 检查是否已运行
            status = self.get_status()

            if status["status"] == "running":
                # 已运行 → 激活窗口
                self._call_da("activate", self.ide_title)
                time.sleep(self.DEFAULT_DELAY_SHORT)
                return {"success": True, "message": "TRAE IDE 已就绪（激活现有窗口）"}

            elif status["status"] == "process_only":
                # 进程在但窗口不可见 → 尝试恢复
                self._call_da("restore", self.ide_title)
                time.sleep(self.DEFAULT_DELAY_MEDIUM)
                self._call_da("activate", self.ide_title)
                return {"success": True, "message": "TRAE IDE 窗口已恢复"}

            else:
                # 未运行 → 启动
                if project_path:
                    # 用 TRAE 打开项目文件夹
                    self._call_da("open", project_path)
                else:
                    # 直接启动 TRAE IDE
                    self._call_da("start", self.ide_process)

                # 等待窗口出现
                if self._wait_for_window(self.DEFAULT_STARTUP_TIMEOUT):
                    time.sleep(self.DEFAULT_DELAY_LONG)  # 等 IDE 完全加载
                    return {"success": True, "message": f"TRAE IDE 已启动"}
                else:
                    return {
                        "success": False,
                        "message": f"TRAE IDE 启动超时 ({self.DEFAULT_STARTUP_TIMEOUT}s)"
                    }

        except Exception as e:
            return {"success": False, "message": str(e)}

    def write_code(self, file_path: str, content: str) -> Dict[str, Any]:
        """在 TRAE IDE 中创建/写入文件

        通过键盘序列执行:
        1. 备份已有文件到 CC 缓存（写入前保护）
        2. Ctrl+Shift+P → "New File" → 输入文件名 → Enter
        3. 粘贴代码内容
        4. Ctrl+S 保存

        Args:
            file_path: 文件路径 (相对于 IDE 当前工作区)
            content:   要写入的代码内容

        Returns:
            {"success": bool, "file": str, "message": str}
        """
        try:
            # 确保 IDE 窗口就绪
            status = self.get_status()
            if status["status"] == "not_found":
                open_result = self.open_ide()
                if not open_result["success"]:
                    return open_result

            # 写入前备份已有文件到 CC 缓存
            self._backup_before_write(file_path)

            # 1. 聚焦 IDE 窗口
            self._call_da("activate", self.ide_title)
            time.sleep(self.DEFAULT_DELAY_SHORT)

            # 2. 新建文件 (Ctrl+N 在多数 IDE 中是新建文件)
            self._call_da("hotkey", "ctrl+n")
            time.sleep(self.DEFAULT_DELAY_MEDIUM)

            # 3. 输入文件名 (使用剪贴板粘贴避免路径输入问题)
            #    先清空可能存在的默认内容
            self._call_da("hotkey", "ctrl+a")     # 全选
            time.sleep(0.05)
            self._call_da("key", "delete")        # 删除
            time.sleep(0.05)

            # 输入文件路径 (纯 ASCII 可逐字输入)
            self._safe_type(file_path)
            time.sleep(self.DEFAULT_DELAY_SHORT)

            # 4. 确认创建 (Enter)
            self._call_da("key", "enter")
            time.sleep(self.DEFAULT_DELAY_MEDIUM)

            # 5. 粘贴代码内容
            self._clipboard_write(content)
            time.sleep(self.DEFAULT_DELAY_SHORT)
            self._call_da("hotkey", "ctrl+v")
            time.sleep(self.DEFAULT_DELAY_SHORT)

            # 6. 保存文件 (Ctrl+S)
            self._call_da("hotkey", "ctrl+s")
            time.sleep(self.DEFAULT_DELAY_SHORT)

            return {
                "success": True,
                "file": file_path,
                "message": f"已写入 {file_path} ({len(content)} 字符)"
            }
        except Exception as e:
            return {"success": False, "file": file_path, "message": str(e)}

    def read_file(self, file_path: str) -> Dict[str, Any]:
        """从 TRAE IDE 中读取文件内容

        通过 Ctrl+P 打开文件 → Ctrl+A 全选 → Ctrl+C 复制 → 读取剪贴板

        Args:
            file_path: 要读取的文件路径

        Returns:
            {"success": bool, "content": str, "message": str}
        """
        try:
            # 1. 聚焦 IDE
            self._call_da("activate", self.ide_title)
            time.sleep(self.DEFAULT_DELAY_SHORT)

            # 2. Ctrl+P 打开文件搜索
            self._call_da("hotkey", "ctrl+p")
            time.sleep(self.DEFAULT_DELAY_MEDIUM)

            # 3. 输入文件名
            self._safe_type(file_path)
            time.sleep(self.DEFAULT_DELAY_MEDIUM)

            # 4. 确认打开 (Enter)
            self._call_da("key", "enter")
            time.sleep(self.DEFAULT_DELAY_LONG)  # 等待文件加载

            # 5. Ctrl+A 全选
            self._call_da("hotkey", "ctrl+a")
            time.sleep(self.DEFAULT_DELAY_SHORT)

            # 6. Ctrl+C 复制
            self._call_da("hotkey", "ctrl+c")
            time.sleep(self.DEFAULT_DELAY_SHORT)

            # 7. 读取剪贴板
            content = self._clipboard_read()

            return {
                "success": True,
                "content": content,
                "message": f"已读取 {file_path} ({len(content)} 字符)"
            }
        except Exception as e:
            return {"success": False, "content": "", "message": str(e)}

    def run_command(self, command: str) -> Dict[str, Any]:
        """在 TRAE IDE 终端中执行命令

        通过 Ctrl+` 打开终端 → 输入命令 → Enter

        Args:
            command: 要执行的终端命令

        Returns:
            {"success": bool, "output": str, "message": str}
        """
        try:
            # 1. 聚焦 IDE
            self._call_da("activate", self.ide_title)
            time.sleep(self.DEFAULT_DELAY_SHORT)

            # 2. Ctrl+` 切换终端 (VS Code / TRAE 通用快捷键)
            self._call_da("hotkey", "ctrl+`")
            time.sleep(self.DEFAULT_DELAY_MEDIUM)

            # 3. 输入命令 (通过剪贴板粘贴避免特殊字符问题)
            self._clipboard_write(command)
            time.sleep(self.DEFAULT_DELAY_SHORT)
            self._call_da("hotkey", "ctrl+v")
            time.sleep(self.DEFAULT_DELAY_SHORT)

            # 4. 执行命令
            self._call_da("key", "enter")
            time.sleep(self.DEFAULT_DELAY_LONG)  # 等待命令开始执行

            return {
                "success": True,
                "output": "",  # 实际输出需通过 read_output() 获取
                "message": f"已在 IDE 终端执行: {command}"
            }
        except Exception as e:
            return {"success": False, "output": "", "message": str(e)}

    def read_output(self) -> Dict[str, Any]:
        """读取 IDE 终端最近输出

        在终端中 Ctrl+A → Ctrl+C 复制全部内容 → 返回剪贴板

        Returns:
            {"success": bool, "content": str}
        """
        try:
            self._call_da("activate", self.ide_title)
            time.sleep(self.DEFAULT_DELAY_SHORT)

            # 聚焦终端 (Ctrl+`)
            self._call_da("hotkey", "ctrl+`")
            time.sleep(self.DEFAULT_DELAY_SHORT)

            # 全选复制
            self._call_da("hotkey", "ctrl+a")
            time.sleep(0.05)
            self._call_da("hotkey", "ctrl+c")
            time.sleep(self.DEFAULT_DELAY_SHORT)

            content = self._clipboard_read()
            return {
                "success": True,
                "content": content,
                "message": f"已读取终端输出 ({len(content)} 字符)"
            }
        except Exception as e:
            return {"success": False, "content": "", "message": str(e)}

    def focus_ide(self) -> Dict[str, Any]:
        """聚焦 TRAE IDE 窗口 (简单激活)"""
        try:
            self._call_da("activate", self.ide_title)
            return {"success": True, "message": "TRAE IDE 窗口已聚焦"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def save_current_file(self) -> Dict[str, Any]:
        """保存当前编辑的文件"""
        try:
            self._call_da("activate", self.ide_title)
            time.sleep(self.DEFAULT_DELAY_SHORT)
            self._call_da("hotkey", "ctrl+s")
            return {"success": True, "message": "文件已保存"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def select_range(self, start_line: int, end_line: int) -> Dict[str, Any]:
        """选择指定行范围

        Ctrl+G → 输入行号 → Enter → 然后 Shift+向下选择

        Args:
            start_line: 起始行号
            end_line:   结束行号
        """
        try:
            self._call_da("activate", self.ide_title)
            time.sleep(self.DEFAULT_DELAY_SHORT)

            # 跳转到起始行
            self._call_da("hotkey", "ctrl+g")
            time.sleep(self.DEFAULT_DELAY_SHORT)
            self._safe_type(str(start_line))
            time.sleep(0.05)
            self._call_da("key", "enter")
            time.sleep(self.DEFAULT_DELAY_MEDIUM)

            # Shift+向下选择到结束行
            down_count = end_line - start_line
            if down_count > 0:
                self._call_da("key", "home")  # 确保从行首开始
                time.sleep(0.05)
                self._call_da("hold", "shift", "0.3")
                for _ in range(min(down_count, 100)):  # 最多 100 行
                    self._call_da("key", "down")
                    time.sleep(0.02)

            return {"success": True, "message": f"已选择行 {start_line}-{end_line}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def replace_selection(self, new_content: str) -> Dict[str, Any]:
        """替换当前选中的内容 (先粘贴替换)

        注意: 必须先调用 select_range() 再调用此方法
        """
        try:
            self._clipboard_write(new_content)
            time.sleep(self.DEFAULT_DELAY_SHORT)
            self._call_da("hotkey", "ctrl+v")
            return {"success": True, "message": f"已替换选中内容 ({len(new_content)} 字符)"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def close_ide(self) -> Dict[str, Any]:
        """关闭 TRAE IDE (带确认处理)"""
        try:
            self._call_da("activate", self.ide_title)
            time.sleep(self.DEFAULT_DELAY_SHORT)
            # Alt+F4 关闭窗口
            self._call_da("hotkey", "alt+f4")
            time.sleep(self.DEFAULT_DELAY_MEDIUM)
            # 如果有保存确认对话框，按 Enter 确认
            # (如果 IDE 已处理保存，此操作安全)
            self._call_da("key", "enter")
            return {"success": True, "message": "TRAE IDE 已关闭"}
        except Exception as e:
            # Alt+F4 被 da.py 的安全机制阻止，尝试直接关闭
            try:
                self._call_da("close", self.ide_title)
                return {"success": True, "message": "TRAE IDE 已关闭"}
            except Exception:
                return {"success": False, "message": str(e)}


# ================================================================
# 模块级便捷函数
# ================================================================

_bridge_instance = None


def get_bridge() -> TRAEIDEBridge:
    """获取全局 TRAE IDE 桥接实例"""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = TRAEIDEBridge()
    return _bridge_instance


# ================================================================
# 自测试
# ================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("TRAE IDE Bridge — 自测试")
    print("=" * 60)

    bridge = TRAEIDEBridge()

    # 1. 检查状态
    print("\n[1] 检查 TRAE IDE 状态...")
    status = bridge.get_status()
    print(f"  状态: {status['status']}")
    print(f"  窗口: {status['window']}, 进程: {status['process']}")

    # 2. 聚焦/激活 IDE
    print("\n[2] 激活 TRAE IDE...")
    result = bridge.open_ide()
    print(f"  结果: {result}")

    # 3. 写入测试文件
    if status["status"] == "running" or result.get("success"):
        print("\n[3] 写入测试文件...")
        test_content = '''#!/usr/bin/env python3
"""由 TRAE IDE Bridge 自动生成的测试文件"""

def hello():
    print("Hello from TRAE IDE Bridge!")

if __name__ == "__main__":
    hello()
'''
        result = bridge.write_code("bridge_test.py", test_content)
        print(f"  结果: {result}")

        # 4. 读取测试文件
        print("\n[4] 读取测试文件...")
        result = bridge.read_file("bridge_test.py")
        if result["success"]:
            print(f"  内容预览: {result['content'][:200]}")
        else:
            print(f"  失败: {result['message']}")

    print("\n" + "=" * 60)
    print("测试完成")
