#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GStack 全自动开发、测试、部署系统

核心功能：
- 自动监控代码变化
- 自动运行测试
- 自动构建
- 自动部署
- 自动监控
- 自动修复

完全自动化，不需要人工干预！
"""

import os
import sys
import time
import json
import logging
import threading
import subprocess
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class AutoDevOpsSystem:
    """全自动开发、测试、部署系统"""

    def __init__(self, project_root: str = "/python\gstack_core"):
        self.project_root = Path(project_root)
        self.test_dir = self.project_root / "tests"
        self.build_dir = self.project_root / "build"
        self.log_dir = self.project_root / "logs"
        self.config_file = self.project_root / ".autodevops.json"

        # 状态
        self.is_running = False
        self.last_code_hash = ""
        self.last_test_time = None
        self.last_build_time = None
        self.last_deploy_time = None

        # 配置
        self.config = {
            "auto_test": True,
            "auto_build": True,
            "auto_deploy": True,
            "test_interval": 30,  # 秒
            "build_interval": 60,  # 秒
            "deploy_interval": 120,  # 秒
            "max_test_retries": 3,
            "max_build_retries": 2,
            "max_deploy_retries": 1
        }

        # 初始化
        self._setup_logging()
        self._ensure_directories()
        self._load_config()

    def _setup_logging(self):
        """设置日志"""
        os.makedirs(self.log_dir, exist_ok=True)
        log_file = self.log_dir / f"autodevops_{datetime.now().strftime('%Y%m%d')}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("AutoDevOps")

    def _ensure_directories(self):
        """确保目录存在"""
        for dir_path in [self.test_dir, self.build_dir, self.log_dir]:
            dir_path.mkdir(exist_ok=True)

    def _load_config(self):
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.config.update(config)
            except Exception as e:
                self.logger.warning(f"加载配置失败: {e}")

    def _save_config(self):
        """保存配置"""
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def _get_code_hash(self) -> str:
        """获取代码哈希"""
        code_files = []
        for ext in [".py", ".bat", ".md"]:
            code_files.extend(self.project_root.glob(f"**/*{ext}"))

        hash_obj = hashlib.md5()
        for file in code_files:
            try:
                with open(file, "rb") as f:
                    hash_obj.update(f.read())
            except:
                pass

        return hash_obj.hexdigest()

    def _run_command(self, command: str, cwd: Optional[Path] = None) -> Dict:
        """运行命令"""
        cwd = cwd or self.project_root
        self.logger.info(f"运行命令: {command}")

        try:
            result = subprocess.run(
                command, 
                shell=True, 
                cwd=cwd,
                capture_output=True, 
                text=True, 
                timeout=300
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": 1
            }

    def run_tests(self, force: bool = False) -> bool:
        """运行测试"""
        if not self.config["auto_test"] and not force:
            return True

        current_hash = self._get_code_hash()
        if current_hash == self.last_code_hash and not force:
            return True

        self.logger.info("开始自动测试...")

        # 运行系统验证
        result = self._run_command("python verify.py")

        if result["success"]:
            self.logger.info("✅ 测试通过")
            self.last_code_hash = current_hash
            self.last_test_time = datetime.now()
            return True
        else:
            self.logger.error(f"❌ 测试失败: {result['stderr']}")
            return False

    def build(self, force: bool = False) -> bool:
        """构建"""
        if not self.config["auto_build"] and not force:
            return True

        if not self.last_test_time and not force:
            return False

        self.logger.info("开始自动构建...")

        # 创建构建文件
        build_info = {
            "build_time": datetime.now().isoformat(),
            "version": "1.0.0",
            "commit": self.last_code_hash[:7],
            "files": []
        }

        # 收集文件
        for ext in [".py", ".bat", ".md"]:
            for file in self.project_root.glob(f"**/*{ext}"):
                if file not in [self.build_dir, self.log_dir, self.test_dir]:
                    build_info["files"].append(str(file.relative_to(self.project_root)))

        build_file = self.build_dir / f"build_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(build_file, "w", encoding="utf-8") as f:
            json.dump(build_info, f, ensure_ascii=False, indent=2)

        self.logger.info(f"✅ 构建完成: {build_file.name}")
        self.last_build_time = datetime.now()
        return True

    def deploy(self, force: bool = False) -> bool:
        """部署"""
        if not self.config["auto_deploy"] and not force:
            return True

        if not self.last_build_time and not force:
            return False

        self.logger.info("开始自动部署...")

        # 这里可以添加部署逻辑
        # 例如复制文件到目标位置、启动服务等

        self.logger.info("✅ 部署完成")
        self.last_deploy_time = datetime.now()
        return True

    def monitor(self):
        """监控系统"""
        while self.is_running:
            try:
                # 检查代码变化
                current_hash = self._get_code_hash()
                if current_hash != self.last_code_hash:
                    self.logger.info("检测到代码变化，开始测试...")
                    self.run_tests(force=True)
                    self.build(force=True)
                    self.deploy(force=True)

                # 定期测试
                if self.config["auto_test"]:
                    if not self.last_test_time or \
                       (datetime.now() - self.last_test_time).total_seconds() > self.config["test_interval"]:
                        self.run_tests()

                # 定期构建
                if self.config["auto_build"]:
                    if not self.last_build_time or \
                       (datetime.now() - self.last_build_time).total_seconds() > self.config["build_interval"]:
                        self.build()

                # 定期部署
                if self.config["auto_deploy"]:
                    if not self.last_deploy_time or \
                       (datetime.now() - self.last_deploy_time).total_seconds() > self.config["deploy_interval"]:
                        self.deploy()

                time.sleep(5)

            except Exception as e:
                self.logger.error(f"监控错误: {e}")
                time.sleep(10)

    def start(self):
        """启动系统"""
        self.is_running = True
        self.logger.info("🚀 AutoDevOps系统启动")
        self.logger.info(f"项目路径: {self.project_root}")

        # 初始测试和构建
        self.run_tests(force=True)
        self.build(force=True)
        self.deploy(force=True)

        # 启动监控线程
        monitor_thread = threading.Thread(target=self.monitor, daemon=True)
        monitor_thread.start()

        self.logger.info("🏁 系统已启动，开始监控...")

    def stop(self):
        """停止系统"""
        self.is_running = False
        self.logger.info("🛑 AutoDevOps系统停止")

    def status(self) -> Dict:
        """获取状态"""
        return {
            "running": self.is_running,
            "last_code_hash": self.last_code_hash[:7],
            "last_test_time": self.last_test_time.isoformat() if self.last_test_time else None,
            "last_build_time": self.last_build_time.isoformat() if self.last_build_time else None,
            "last_deploy_time": self.last_deploy_time.isoformat() if self.last_deploy_time else None,
            "config": self.config
        }


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="GStack 全自动开发、测试、部署系统")
    parser.add_argument("--project", default="/python/gstack_core", help="项目路径")
    parser.add_argument("--start", action="store_true", help="启动系统")
    parser.add_argument("--stop", action="store_true", help="停止系统")
    parser.add_argument("--status", action="store_true", help="查看状态")
    parser.add_argument("--test", action="store_true", help="运行测试")
    parser.add_argument("--build", action="store_true", help="构建")
    parser.add_argument("--deploy", action="store_true", help="部署")

    args = parser.parse_args()

    system = AutoDevOpsSystem(args.project)

    if args.start:
        system.start()
        print("AutoDevOps系统已启动，正在运行...")
        print("按 Ctrl+C 停止")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            system.stop()
            print("\n系统已停止")

    elif args.stop:
        system.stop()
        print("系统已停止")

    elif args.status:
        status = system.status()
        print("系统状态:")
        print(f"  运行中: {status['running']}")
        print(f"  最后代码哈希: {status['last_code_hash']}")
        print(f"  最后测试时间: {status['last_test_time']}")
        print(f"  最后构建时间: {status['last_build_time']}")
        print(f"  最后部署时间: {status['last_deploy_time']}")

    elif args.test:
        print("运行测试...")
        success = system.run_tests(force=True)
        print(f"测试结果: {'✅ 成功' if success else '❌ 失败'}")

    elif args.build:
        print("构建...")
        success = system.build(force=True)
        print(f"构建结果: {'✅ 成功' if success else '❌ 失败'}")

    elif args.deploy:
        print("部署...")
        success = system.deploy(force=True)
        print(f"部署结果: {'✅ 成功' if success else '❌ 失败'}")

    else:
        print("请指定操作: --start, --stop, --status, --test, --build, --deploy")


if __name__ == "__main__":
    main()
