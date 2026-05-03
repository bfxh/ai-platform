#!/usr/bin/env python3
"""
Minecraft 整合包测试 - 玩家视角完整测试
支持：我即是虫群v2.0 / 真菌起源 / 新起源 / 任意版本
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
from game_test_framework import GameTestFramework

MC_DIR = r"%GAME_DIR%\.minecraft"

PACKS = {
    "虫群2.0": {
        "version": "我即是虫群v2.0",
        "loader": "forge",
        "game_version": "1.12.2",
        "launch_script": "launch_mc.py",
        "log_keyword": "Loaded",
    },
    "1.20.4": {
        "version": "我即是虫群-1.20.4",
        "loader": "neoforge",
        "game_version": "1.20.4",
        "launch_script": "launch_1204.py",
        "log_keyword": "Saving chunks",
    },
    "真菌起源": {
        "version": "真菌起源",
        "loader": "forge",
        "game_version": "1.20.1",
        "launch_script": "launch_fungal.py",
        "log_keyword": "Saving chunks",
    },
    "新起源": {
        "version": "新起源",
        "loader": "forge",
        "game_version": "1.20.4",
        "launch_script": "launch_1204.py",
        "log_keyword": "Saving chunks",
    },
}


def get_log_path(version_name: str) -> str:
    return os.path.join(MC_DIR, "versions", version_name, "logs", "latest.log")


def check_mod_errors(version_name: str) -> list:
    log_path = get_log_path(version_name)
    errors = []
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if "FATAL" in line or "MissingModsException" in line:
                        errors.append(line.strip())
        except Exception:
            pass
    return errors


def test_pack(pack_key: str):
    pack = PACKS[pack_key]
    version_name = pack["version"]
    log_path = get_log_path(version_name)

    print(f"\n{'='*60}")
    print(f"  测试整合包: {pack_key} ({version_name})")
    print(f"  MC {pack['game_version']} / {pack['loader']}")
    print(f"{'='*60}")

    tf = GameTestFramework(f"mc_{pack_key}")

    # 预检查：日志错误
    errors = check_mod_errors(version_name)
    if errors:
        print(f"  ⚠ 发现 {len(errors)} 个致命错误:")
        for e in errors[:5]:
            print(f"    {e}")
        tf.record("precheck", "FAIL", 0, f"{len(errors)} fatal errors in log")

    # 阶段一：启动游戏
    launch_result = tf.launch_game(
        cmd=["py", os.path.join("/python", pack["launch_script"])],
        window_title="Minecraft",
        launcher_title="HMCL",
        timeout=180,
        cwd="/python",
    )
    if launch_result["status"] == "FAIL":
        tf.generate_report()
        return

    # 阶段二：主菜单 → 点击单人游戏
    tf.navigate_menu([
        {"type": "wait", "time": 8, "desc": "等待主菜单加载"},
        {"type": "click", "ox": 0, "oy": 50, "desc": "点击单人游戏"},
        {"type": "wait", "time": 3, "desc": "等待世界列表"},
    ], wait_stable=15)

    # 阶段三：创建新世界
    tf.navigate_menu([
        {"type": "click", "ox": 0, "oy": 150, "desc": "点击创建新世界"},
        {"type": "wait", "time": 3, "desc": "等待创建界面"},
        {"type": "click", "ox": 0, "oy": 200, "desc": "点击创建"},
        {"type": "wait", "time": 5, "desc": "等待确认"},
    ])

    # 阶段四：等待世界加载
    load_result = tf.wait_for_game_load(
        log_path=log_path,
        log_keywords=[pack["log_keyword"]],
        timeout=120,
    )
    if load_result["status"] == "FAIL":
        tf.exit_game(method="kill")
        tf.generate_report()
        return

    time.sleep(10)
    tf.screenshot("world", "loaded")

    # 阶段五：基础操控
    tf.test_movement()

    # 阶段六：玩法测试
    tf.test_gameplay([
        {"type": "key", "key": "e", "desc": "打开物品栏", "delay": 2},
        {"type": "wait", "time": 2, "desc": "查看物品栏"},
        {"type": "key", "key": "escape", "desc": "关闭物品栏", "delay": 1},
        {"type": "click", "ox": 0, "oy": 0, "desc": "左键攻击/破坏", "delay": 1},
        {"type": "hold", "key": "w", "duration": 3, "desc": "向前走3秒"},
        {"type": "key", "key": "space", "desc": "跳跃"},
        {"type": "hold", "key": "w", "duration": 5, "desc": "继续前进探索"},
    ])

    # 阶段七：稳定性
    tf.test_stability(duration_seconds=30, check_interval=10)

    # 阶段八：退出
    tf.exit_game(method="key", key="escape")

    tf.generate_report()


if __name__ == "__main__":
    pack_name = sys.argv[1] if len(sys.argv) > 1 else "1.20.4"
    if pack_name not in PACKS:
        print(f"可用整合包: {', '.join(PACKS.keys())}")
        sys.exit(1)
    test_pack(pack_name)
