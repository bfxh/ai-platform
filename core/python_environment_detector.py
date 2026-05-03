#!/usr/bin/env python3
"""
/python 自动 Python 环境检测器
自动检测并使用系统中可用的 Python 环境
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


class PythonEnvironmentDetector:
    """Python 环境检测器"""

    def __init__(self):
        self.python_paths = []
        self.detected_python = None
        self.search_paths = [
            "%SOFTWARE_DIR%\\AI\\StepFun\\resources\\app.asar.unpacked\\tools\\win\\python-3.11.9\\python.exe",
            "%SOFTWARE_DIR%\\AI\\StepFun\\tools\\win\\python",
            "C:\\Python",
            "C:\\Python39",
            "C:\\Python310",
            "C:\\Python311",
            "C:\\Program Files\\Python",
            "%USERPROFILE%\\AppData\\Local\\Programs\\Python",
        ]

    def detect(self) -> Optional[str]:
        """检测可用的 Python 环境"""
        print("=" * 60)
        print("自动 Python 环境检测")
        print("=" * 60)
        print()

        # 首先检查已知的路径
        print("[1/3] 检查已知 Python 路径...")
        for path in self.search_paths:
            if os.path.exists(path):
                print(f"    ✓ 发现: {path}")
                self.python_paths.append(path)

                # 尝试测试这个 Python
                if self._test_python(path):
                    self.detected_python = path
                    print(f"    ✓ Python 可用: {path}")
                    print()
                    break
            elif os.path.isdir(path):
                # 如果是目录，查找其中的 python.exe
                python_exe = os.path.join(path, "python.exe")
                if os.path.exists(python_exe):
                    print(f"    ✓ 发现: {python_exe}")
                    self.python_paths.append(python_exe)

                    if self._test_python(python_exe):
                        self.detected_python = python_exe
                        print(f"    ✓ Python 可用: {python_exe}")
                        print()
                        break

        # 如果没找到，尝试系统 PATH
        if not self.detected_python:
            print("[2/3] 检查系统 PATH...")
            try:
                result = subprocess.run(["where", "python"], capture_output=True, text=True, timeout=5)

                if result.returncode == 0:
                    paths = result.stdout.strip().split("\n")
                    for path in paths:
                        path = path.strip()
                        if path and os.path.exists(path):
                            print(f"    ✓ 发现: {path}")
                            self.python_paths.append(path)

                            if self._test_python(path):
                                self.detected_python = path
                                print(f"    ✓ Python 可用: {path}")
                                print()
                                break
            except Exception as e:
                print(f"    ✗ 错误: {e}")

        # 最后尝试使用 uv
        if not self.detected_python:
            print("[3/3] 检查 uv 工具...")
            uv_path = "%USERPROFILE%\\.trae-cn\\tools\\uv\\latest\\uv.exe"
            if os.path.exists(uv_path):
                print(f"    ✓ 发现 uv: {uv_path}")
                # uv 可以用来运行 Python
                self.detected_python = uv_path
                print(f"    ✓ uv 可用: {uv_path}")
                print()

        # 打印结果
        print("=" * 60)
        if self.detected_python:
            print(f"✓ 检测到可用的 Python: {self.detected_python}")
            version = self._get_python_version(self.detected_python)
            if version:
                print(f"  版本: {version}")
        else:
            print("✗ 未检测到可用的 Python 环境")
        print("=" * 60)
        print()

        return self.detected_python

    def _test_python(self, python_path: str) -> bool:
        """测试 Python 是否可用"""
        try:
            result = subprocess.run([python_path, "--version"], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False

    def _get_python_version(self, python_path: str) -> Optional[str]:
        """获取 Python 版本"""
        try:
            result = subprocess.run([python_path, "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except:
            return None

    def get_python_command(self) -> str:
        """获取 Python 命令"""
        if self.detected_python:
            return self.detected_python
        return "python"

    def get_all_detected(self) -> List[str]:
        """获取所有检测到的 Python 环境"""
        return self.python_paths


def main():
    """测试函数"""
    detector = PythonEnvironmentDetector()
    python_path = detector.detect()

    if python_path:
        print(f"[成功] Python 路径: {python_path}")
        print(f"[成功] Python 命令: {detector.get_python_command()}")
    else:
        print("[失败] 未检测到可用的 Python 环境")


if __name__ == "__main__":
    main()
