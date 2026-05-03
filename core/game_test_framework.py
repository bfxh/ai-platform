#!/usr/bin/env python3
"""
通用游戏测试框架
以玩家视角执行完整测试流程：启动 → 主菜单 → 进入游戏 → 操控 → 玩法 → 退出
"""

import ctypes
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import pyautogui

    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.3
except ImportError:
    pyautogui = None

try:
    from PIL import Image
except ImportError:
    Image = None


class GameTestFramework:
    def __init__(self, project_name: str, base_dir: str = None):
        if base_dir is None:
            base_dir = os.environ.get("AI_BASE_DIR", str(Path(__file__).resolve().parent.parent))
        self.project_name = project_name
        self.base_dir = Path(base_dir)
        self.screenshot_dir = self.base_dir / "projects" / project_name / "screenshots"
        self.reports_dir = self.base_dir / "projects" / project_name / "reports"
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self.results: List[dict] = []
        self.process: Optional[subprocess.Popen] = None
        self.start_time = time.time()
        self.user32 = ctypes.windll.user32

        self.game_hwnd: Optional[int] = None
        self.game_rect = {"x": 0, "y": 0, "w": 0, "h": 0}
        self.launcher_hwnd: Optional[int] = None

    def _timestamp(self) -> str:
        return datetime.now().strftime("%H%M%S")

    def _elapsed(self) -> float:
        return round(time.time() - self.start_time, 1)

    def screenshot(self, phase: str, step: str = "") -> Optional[str]:
        if pyautogui is None:
            return None
        ts = self._timestamp()
        name = f"{self.project_name}_{phase}_{step}_{ts}.png" if step else f"{self.project_name}_{phase}_{ts}.png"
        path = self.screenshot_dir / name
        try:
            img = pyautogui.screenshot()
            img.save(str(path))
            print(f"  📸 {name}")
            return str(path)
        except Exception as e:
            print(f"  ⚠ 截图失败: {e}")
            return None

    def record(self, phase: str, status: str, duration: float = 0, note: str = ""):
        entry = {
            "phase": phase,
            "status": status,
            "duration": round(duration, 1),
            "note": note,
            "elapsed": self._elapsed(),
        }
        self.results.append(entry)
        icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠"
        print(f"  {icon} [{phase}] {status} ({duration:.1f}s) {note}")

    def find_window(self, title_keyword: str) -> Optional[int]:
        result = []

        def callback(hwnd, _):
            length = self.user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                self.user32.GetWindowTextW(hwnd, buf, length + 1)
                if title_keyword.lower() in buf.value.lower():
                    result.append(hwnd)
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        self.user32.EnumWindows(WNDENUMPROC(callback), 0)
        return result[0] if result else None

    def get_window_rect(self, hwnd: int) -> dict:
        rect = ctypes.wintypes.RECT()
        self.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        return {
            "x": rect.left,
            "y": rect.top,
            "w": rect.right - rect.left,
            "h": rect.bottom - rect.top,
        }

    def activate_window(self, hwnd: int) -> bool:
        try:
            self.user32.SetForegroundWindow(hwnd)
            self.user32.ShowWindow(hwnd, 9)
            time.sleep(0.3)
            return True
        except Exception:
            return False

    def ensure_game_active(self):
        if self.game_hwnd:
            self.activate_window(self.game_hwnd)

    def detect_popups(self) -> dict:
        """检测常见弹窗并自动处理"""
        popup_keywords = [
            {"title": "Error", "type": "error"},
            {"title": "错误", "type": "error"},
            {"title": "JVM", "type": "jvm"},
            {"title": "Java", "type": "jvm"},
            {"title": "TLauncher", "type": "launcher"},
            {"title": "HMCL", "type": "launcher"},
            {"title": "许可", "type": "license"},
            {"title": "License", "type": "license"},
            {"title": "警告", "type": "warning"},
            {"title": "Warning", "type": "warning"},
        ]

        for popup in popup_keywords:
            hwnd = self.find_window(popup["title"])
            if hwnd:
                rect = self.get_window_rect(hwnd)
                self.activate_window(hwnd)
                self.screenshot("popup", popup["type"])

                # 自动点击确定按钮（通常在弹窗右下角）
                ok_x = rect["x"] + rect["w"] - 100
                ok_y = rect["y"] + rect["h"] - 60
                self.click_at(ok_x, ok_y)
                time.sleep(2)

                return {"found": True, "type": popup["type"], "hwnd": hwnd}
        return {"found": False}

    def wait_for_window(self, title_keyword: str, timeout: float = 120) -> Optional[int]:
        start = time.time()
        while time.time() - start < timeout:
            # 检查是否有弹窗
            popup = self.detect_popups()
            if popup["found"]:
                print(f"  ⚠ 检测到弹窗: {popup['type']}，已自动处理")
                # 处理完弹窗后继续等待目标窗口
                continue

            hwnd = self.find_window(title_keyword)
            if hwnd:
                return hwnd
            time.sleep(1)
        return None

    def wait_for_window_stable(self, timeout: float = 10, interval: float = 1.0) -> bool:
        if pyautogui is None:
            time.sleep(timeout)
            return True
        start = time.time()
        last_img = None
        stable_count = 0
        while time.time() - start < timeout:
            # 检查是否有弹窗
            popup = self.detect_popups()
            if popup["found"]:
                print(f"  ⚠ 检测到弹窗: {popup['type']}，已自动处理")
                # 处理完弹窗后重新开始稳定检测
                stable_count = 0
                time.sleep(2)
                continue
            try:
                current = pyautogui.screenshot()
                if last_img is not None and Image is not None:
                    diff = sum(
                        abs(a - b) for a, b in zip(list(last_img.getdata())[:1000], list(current.getdata())[:1000])
                    )
                    if diff < 5000:
                        stable_count += 1
                        if stable_count >= 3:
                            return True
                    else:
                        stable_count = 0
                last_img = current
            except Exception:
                pass
            time.sleep(interval)
        return False

    def click_at(self, x: int, y: int, clicks: int = 1):
        if pyautogui:
            self.ensure_game_active()
            pyautogui.click(x, y, clicks=clicks)
            time.sleep(0.5)

    def click_center(self, offset_x: int = 0, offset_y: int = 0):
        if pyautogui:
            self.ensure_game_active()
            cx = self.game_rect["x"] + self.game_rect["w"] // 2 + offset_x
            cy = self.game_rect["y"] + self.game_rect["h"] // 2 + offset_y
            pyautogui.click(cx, cy)
            time.sleep(0.5)

    def click_win_rel(self, rel_x: float, rel_y: float):
        if pyautogui:
            self.ensure_game_active()
            abs_x = self.game_rect["x"] + int(self.game_rect["w"] * rel_x)
            abs_y = self.game_rect["y"] + int(self.game_rect["h"] * rel_y)
            pyautogui.click(abs_x, abs_y)
            time.sleep(0.5)

    def press_key(self, key: str, duration: float = 0.1):
        if pyautogui:
            pyautogui.keyDown(key)
            time.sleep(duration)
            pyautogui.keyUp(key)
            time.sleep(0.2)

    def hold_key(self, key: str, duration: float = 2.0):
        if pyautogui:
            pyautogui.keyDown(key)
            time.sleep(duration)
            pyautogui.keyUp(key)
            time.sleep(0.3)

    def type_text(self, text: str, interval: float = 0.05):
        if pyautogui:
            pyautogui.write(text, interval=interval)
            time.sleep(0.5)

    # ============================================================
    # 阶段一：启动
    # ============================================================
    def launch_game(
        self,
        cmd: List[str],
        window_title: str,
        launcher_title: str = None,
        launcher_button_pos: Tuple[int, int] = None,
        timeout: float = 120,
        cwd: str = None,
    ) -> dict:
        print(f"\n{'='*50}")
        print(f"  阶段一：启动游戏")
        print(f"{'='*50}")
        start = time.time()

        try:
            self.process = subprocess.Popen(cmd, cwd=cwd)
            print(f"  进程已启动 PID={self.process.pid}")
        except Exception as e:
            self.record("launch", "FAIL", 0, f"启动失败: {e}")
            return {"status": "FAIL", "error": str(e)}

        if launcher_title:
            print(f"  等待启动器窗口: {launcher_title}")
            self.launcher_hwnd = self.wait_for_window(launcher_title, timeout=30)
            if self.launcher_hwnd:
                self.activate_window(self.launcher_hwnd)
                lrect = self.get_window_rect(self.launcher_hwnd)
                self.screenshot("launch", "launcher")
                time.sleep(2)
                if launcher_button_pos:
                    abs_x = lrect["x"] + launcher_button_pos[0]
                    abs_y = lrect["y"] + launcher_button_pos[1]
                    print(f"  点击启动器按钮: ({abs_x}, {abs_y})")
                    self.activate_window(self.launcher_hwnd)
                    self.click_at(abs_x, abs_y)
                    time.sleep(3)
            else:
                print(f"  ⚠ 未找到启动器窗口")

        print(f"  等待游戏窗口: {window_title}")
        self.game_hwnd = self.wait_for_window(window_title, timeout=timeout)

        duration = time.time() - start
        if self.game_hwnd:
            self.activate_window(self.game_hwnd)
            self.game_rect = self.get_window_rect(self.game_hwnd)
            print(
                f"  游戏窗口: {self.game_rect['w']}x{self.game_rect['h']} at ({self.game_rect['x']}, {self.game_rect['y']})"
            )
            self.screenshot("launch", "game_window")
            self.record("launch", "PASS", duration, f"窗口 {self.game_rect['w']}x{self.game_rect['h']}")
            return {"status": "PASS", "hwnd": self.game_hwnd, "duration": duration, "rect": self.game_rect}
        else:
            if self.process and self.process.poll() is not None:
                self.record("launch", "FAIL", duration, f"进程已退出 code={self.process.returncode}")
            else:
                self.record("launch", "FAIL", duration, "窗口未出现")
            return {"status": "FAIL", "duration": duration}

    # ============================================================
    # 阶段二：主菜单导航
    # ============================================================
    def navigate_menu(
        self,
        menu_actions: List[dict],
        wait_stable: float = 10,
    ) -> dict:
        print(f"\n{'='*50}")
        print(f"  阶段二：主菜单导航")
        print(f"{'='*50}")
        start = time.time()

        self.ensure_game_active()
        self.wait_for_window_stable(timeout=wait_stable)
        self.screenshot("menu", "initial")

        for i, action in enumerate(menu_actions):
            action_type = action.get("type", "click")
            desc = action.get("desc", f"步骤{i+1}")

            if action_type == "click":
                self.ensure_game_active()
                x, y = action.get("x", 0), action.get("y", 0)
                if x == 0 and y == 0:
                    self.click_center(action.get("ox", 0), action.get("oy", 0))
                else:
                    self.click_at(x, y)
                print(f"  点击: {desc}")
            elif action_type == "win_rel":
                self.ensure_game_active()
                rx = action.get("rx", 0.5)
                ry = action.get("ry", 0.5)
                self.click_win_rel(rx, ry)
                print(f"  窗口相对点击: ({rx:.2f}, {ry:.2f})")
            elif action_type == "key":
                self.ensure_game_active()
                key = action.get("key", "")
                duration = action.get("duration", 0.1)
                self.press_key(key, duration)
                print(f"  按键: {desc} ({key})")
            elif action_type == "hold":
                self.ensure_game_active()
                key = action.get("key", "")
                duration = action.get("duration", 2.0)
                self.hold_key(key, duration)
                print(f"  长按: {desc} ({key} {duration}s)")
            elif action_type == "type":
                self.ensure_game_active()
                text = action.get("text", "")
                self.type_text(text)
                print(f"  输入: {desc} ({text})")
            elif action_type == "wait":
                wait_time = action.get("time", 2)
                time.sleep(wait_time)
                print(f"  等待: {desc} ({wait_time}s)")

            time.sleep(action.get("delay", 1.5))
            self.screenshot("menu", f"step{i+1}")

        duration = time.time() - start
        self.record("menu", "PASS", duration)
        return {"status": "PASS", "duration": duration}

    # ============================================================
    # 阶段三：等待游戏加载
    # ============================================================
    def wait_for_game_load(
        self,
        log_path: str = None,
        log_keywords: List[str] = None,
        timeout: float = 120,
        check_interval: float = 5,
    ) -> dict:
        print(f"\n{'='*50}")
        print(f"  阶段三：等待游戏加载")
        print(f"{'='*50}")
        start = time.time()

        loaded = False
        stable_count = 0
        while time.time() - start < timeout:
            if self.process and self.process.poll() is not None:
                self.record("load", "FAIL", time.time() - start, "进程已退出")
                return {"status": "FAIL"}

            if log_path:
                log = Path(log_path)
                if log.exists():
                    try:
                        content = log.read_text(encoding="utf-8", errors="replace")
                        # 更准确的加载完成标志
                        load_complete_keywords = [
                            "Preparing spawn area",
                            "Done (",
                            "Saving chunks",
                        ]
                        if log_keywords:
                            load_complete_keywords.extend(log_keywords)

                        if any(kw in content for kw in load_complete_keywords):
                            # 找到了加载完成标志，再等待画面稳定
                            if self.wait_for_window_stable(timeout=5, interval=1.0):
                                loaded = True
                                break

                        if "Stopping!" in content or "FATAL" in content:
                            self.record("load", "FAIL", time.time() - start, "日志检测到崩溃")
                            return {"status": "FAIL"}
                    except Exception:
                        pass

            # 画面稳定检测（作为备用）
            if self.wait_for_window_stable(timeout=check_interval, interval=1.0):
                stable_count += 1
                if stable_count >= 2:
                    loaded = True
                    break
            else:
                stable_count = 0

            time.sleep(check_interval)

        duration = time.time() - start
        if loaded:
            self.screenshot("load", "complete")
            self.record("load", "PASS", duration)
            return {"status": "PASS", "duration": duration}
        else:
            self.record("load", "FAIL", duration, "加载超时")
            return {"status": "FAIL", "duration": duration}

    # ============================================================
    # 阶段四：基础操控测试
    # ============================================================
    def test_movement(self, directions: List[dict] = None) -> dict:
        print(f"\n{'='*50}")
        print(f"  阶段四：基础操控测试")
        print(f"{'='*50}")
        start = time.time()
        self.ensure_game_active()

        if directions is None:
            directions = [
                {"key": "w", "desc": "前进", "duration": 2.0},
                {"key": "s", "desc": "后退", "duration": 2.0},
                {"key": "a", "desc": "左移", "duration": 2.0},
                {"key": "d", "desc": "右移", "duration": 2.0},
            ]

        passed = 0
        for d in directions:
            key = d["key"]
            desc = d["desc"]
            duration = d.get("duration", 2.0)
            self.ensure_game_active()
            self.screenshot("move", f"{desc}_before")
            self.hold_key(key, duration)
            self.screenshot("move", f"{desc}_after")
            passed += 1
            print(f"  移动测试: {desc} ({key})")

        self.ensure_game_active()
        self.screenshot("move", "jump_before")
        self.press_key("space", 0.1)
        time.sleep(0.5)
        self.screenshot("move", "jump_after")
        passed += 1
        print(f"  跳跃测试: space")

        duration = time.time() - start
        self.record("movement", "PASS", duration, f"{passed}项测试完成")
        return {"status": "PASS", "passed": passed, "duration": duration}

    # ============================================================
    # 阶段五：玩法测试
    # ============================================================
    def test_gameplay(self, actions: List[dict]) -> dict:
        print(f"\n{'='*50}")
        print(f"  阶段五：玩法测试")
        print(f"{'='*50}")
        start = time.time()

        passed = 0
        failed = 0
        for i, action in enumerate(actions):
            desc = action.get("desc", f"玩法{i+1}")
            action_type = action.get("type", "click")
            print(f"  玩法测试: {desc}")

            try:
                self.ensure_game_active()
                if action_type == "click":
                    self.click_at(action.get("x", 0), action.get("y", 0))
                elif action_type == "win_rel":
                    rx = action.get("rx", 0.5)
                    ry = action.get("ry", 0.5)
                    self.click_win_rel(rx, ry)
                elif action_type == "key":
                    self.press_key(action.get("key", ""), action.get("duration", 0.1))
                elif action_type == "hold":
                    self.hold_key(action.get("key", ""), action.get("duration", 2.0))
                elif action_type == "type":
                    self.type_text(action.get("text", ""))
                elif action_type == "wait":
                    time.sleep(action.get("time", 2))

                time.sleep(action.get("delay", 1.5))
                self.screenshot("gameplay", f"step{i+1}")
                passed += 1
            except Exception as e:
                print(f"  ❌ 失败: {e}")
                self.screenshot("gameplay", f"step{i+1}_fail")
                failed += 1

        duration = time.time() - start
        status = "PASS" if failed == 0 else "PARTIAL" if passed > 0 else "FAIL"
        self.record("gameplay", status, duration, f"通过{passed} 失败{failed}")
        return {"status": status, "passed": passed, "failed": failed, "duration": duration}

    # ============================================================
    # 阶段六：稳定性验证
    # ============================================================
    def test_stability(self, duration_seconds: float = 60, check_interval: float = 10) -> dict:
        print(f"\n{'='*50}")
        print(f"  阶段六：稳定性验证 ({duration_seconds}s)")
        print(f"{'='*50}")
        start = time.time()
        errors = 0
        checks = 0

        while time.time() - start < duration_seconds:
            if self.process and self.process.poll() is not None:
                self.record("stability", "FAIL", time.time() - start, "进程崩溃")
                return {"status": "FAIL", "errors": errors}
            checks += 1
            time.sleep(check_interval)

        elapsed = time.time() - start
        self.screenshot("stability", "final")
        self.record("stability", "PASS", elapsed, f"{checks}次检查")
        return {"status": "PASS", "checks": checks, "errors": errors}

    # ============================================================
    # 阶段七：退出
    # ============================================================
    def exit_game(self, method: str = "key", key: str = "escape") -> dict:
        print(f"\n{'='*50}")
        print(f"  阶段七：退出游戏")
        print(f"{'='*50}")
        start = time.time()

        if method == "key":
            self.press_key(key)
            time.sleep(2)
            self.screenshot("exit", "menu")
        elif method == "kill":
            if self.process:
                self.process.terminate()

        if self.process:
            try:
                self.process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()

        duration = time.time() - start
        self.screenshot("exit", "done")
        self.record("exit", "PASS", duration)
        return {"status": "PASS", "duration": duration}

    # ============================================================
    # 生成报告
    # ============================================================
    def generate_report(self) -> str:
        print(f"\n{'='*50}")
        print(f"  生成测试报告")
        print(f"{'='*50}")

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f"report_{ts}.json"

        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        partial = sum(1 for r in self.results if r["status"] == "PARTIAL")

        overall = "PASS" if failed == 0 else "FAIL" if passed == 0 else "PARTIAL"

        report = {
            "project": self.project_name,
            "timestamp": datetime.now().isoformat(),
            "overall": overall,
            "summary": {"total": total, "passed": passed, "failed": failed, "partial": partial},
            "results": self.results,
        }

        report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        print(f"\n  📋 测试报告: {report_file}")
        print(f"  总体结果: {overall}")
        print(f"  通过: {passed}  失败: {failed}  部分: {partial}")
        return str(report_file)
