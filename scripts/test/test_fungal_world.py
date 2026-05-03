#!/usr/bin/env python3
"""
真菌起源整合包测试 - 玩家视角完整测试
使用 game_test_framework 自动化：启动→主菜单→创建世界→移动→玩法→退出
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
from game_test_framework import GameTestFramework

MC_DIR = r"%GAME_DIR%\.minecraft"
VERSION_NAME = "真菌起源"
VERSION_DIR = os.path.join(MC_DIR, "versions", VERSION_NAME)
LATEST_LOG = os.path.join(VERSION_DIR, "logs", "latest.log")
LAUNCH_SCRIPT = r"\python\launch_fungal.py"


def test_fungal():
    tf = GameTestFramework("mc_fungal")

    # 阶段一：启动游戏
    launch_result = tf.launch_game(
        cmd=["py", LAUNCH_SCRIPT],
        window_title="Minecraft",
        launcher_title="HMCL",
        timeout=300,
        cwd="/python",
    )
    if launch_result["status"] == "FAIL":
        tf.generate_report()
        return

    # 阶段二：等待主菜单 + 点击单人游戏
    tf.navigate_menu([
        {"type": "wait", "time": 10, "desc": "等待主菜单完全加载"},
        {"type": "click", "ox": 0, "oy": 50, "desc": "点击单人游戏"},
        {"type": "wait", "time": 3, "desc": "等待世界列表"},
    ], wait_stable=20)

    # 阶段三：创建新世界
    tf.navigate_menu([
        {"type": "click", "ox": 0, "oy": 150, "desc": "点击创建新世界"},
        {"type": "wait", "time": 3, "desc": "等待创建界面"},
        {"type": "click", "ox": 0, "oy": 200, "desc": "点击创建"},
        {"type": "wait", "time": 5, "desc": "等待确认"},
    ])

    # 阶段四：等待世界加载
    load_result = tf.wait_for_game_load(
        log_path=LATEST_LOG,
        log_keywords=["Saving chunks"],
        timeout=120,
    )
    if load_result["status"] == "FAIL":
        tf.exit_game(method="kill")
        tf.generate_report()
        return

    time.sleep(10)
    tf.screenshot("world", "loaded")

    # 阶段五：基础操控测试
    tf.test_movement()

    # 阶段六：玩法测试 - 真菌起源特有
    tf.test_gameplay([
        {"type": "key", "key": "e", "desc": "打开物品栏", "delay": 2},
        {"type": "wait", "time": 2, "desc": "查看物品栏（检查模组物品）"},
        {"type": "key", "key": "escape", "desc": "关闭物品栏", "delay": 1},
        {"type": "click", "ox": 0, "oy": 0, "desc": "左键攻击", "delay": 1},
        {"type": "hold", "key": "w", "duration": 3, "desc": "向前走3秒"},
        {"type": "key", "key": "space", "desc": "跳跃"},
        {"type": "hold", "key": "d", "duration": 2, "desc": "右移2秒"},
        {"type": "hold", "key": "w", "duration": 5, "desc": "继续前进探索"},
        {"type": "key", "key": "space", "desc": "跳跃过障碍"},
        {"type": "hold", "key": "w", "duration": 3, "desc": "继续前进"},
    ])

    # 阶段七：稳定性
    tf.test_stability(duration_seconds=30, check_interval=10)

    # 阶段八：退出
    tf.exit_game(method="key", key="escape")

    tf.generate_report()


if __name__ == "__main__":
    test_fungal()
