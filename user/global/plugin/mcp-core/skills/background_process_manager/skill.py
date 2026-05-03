#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后台进程管理技能
用于识别和关闭不需要的后台程序，特别是不在任务栏显示的程序
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from skills.base import Skill as SkillBase

class BackgroundProcessManagerSkill(SkillBase):
    name = "background_process_manager"
    description = "后台进程管理 - 管理和关闭不需要的后台进程，特别是WPC等不在任务栏显示的程序"
    version = "1.0.0"
    author = "MCP Core Team"
    
    def __init__(self, config: dict = None):
        # 先设置默认值，避免父类初始化时调用_load_config出错
        self.config_file = "background_process_config.json"
        self.default_excluded_processes = [
            # 编程相关软件
            "code.exe", "visualstudio.exe", "devenv.exe", "blender.exe", "godot.exe",
            "python.exe", "node.exe", "npm.exe", "git.exe",
            # 系统关键进程
            "explorer.exe", "svchost.exe", "winlogon.exe", "csrss.exe", "smss.exe",
            "lsass.exe", "services.exe", "wininit.exe",
            # 安全软件
            "antimalware.exe", "defender.exe",
            # 常用工具
            "chrome.exe", "firefox.exe", "edge.exe", "notepad.exe"
        ]
        self.default_target_processes = [
            # 需要关闭的进程
            "WPC.exe", "WPCService.exe",
            "Adobe CEF Helper.exe", "Adobe Desktop Service.exe",
            "Spotify.exe", "Steam.exe", "Discord.exe",
            "OneDrive.exe", "Dropbox.exe", "GoogleDrive.exe",
            "Teams.exe", "Skype.exe", "Zoom.exe",
            "iTunes.exe", "QuickTimePlayer.exe",
            "Origin.exe", "EpicGamesLauncher.exe", "UbisoftConnect.exe"
        ]
        self.excluded_processes = []
        self.target_processes = []
        self.log_file = "background_process_log.txt"
        
        super().__init__(config)
        # 父类初始化后再从配置中获取
        self.config_file = self.config.get("config_file", "background_process_config.json")
        self.excluded_processes = self.config.get("excluded_processes", self.default_excluded_processes)
        self.target_processes = self.config.get("target_processes", self.default_target_processes)
        self.log_file = self.config.get("log_file", "background_process_log.txt")
        
        # 确保配置文件存在
        self.save_config()
    
    def save_config(self):
        """保存配置文件"""
        config = {
            "config_file": self.config_file,
            "excluded_processes": self.excluded_processes,
            "target_processes": self.target_processes,
            "log_file": self.log_file
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
    
    def get_running_processes(self):
        """获取当前运行的进程"""
        try:
            # 使用PowerShell获取进程信息
            cmd = ["powershell", "Get-Process | Select-Object Name, ProcessName, Id, CPU, MemoryMB | ConvertTo-Json"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            processes = json.loads(result.stdout)
            return processes
        except Exception as e:
            self.logger.error(f"获取进程信息失败: {e}")
            return []
    
    def is_excluded(self, process_name):
        """检查进程是否在排除列表中"""
        for excluded in self.excluded_processes:
            if excluded.lower() in process_name.lower():
                return True
        return False
    
    def is_target(self, process_name):
        """检查进程是否在目标列表中"""
        for target in self.target_processes:
            if target.lower() in process_name.lower():
                return True
        return False
    
    def kill_process(self, process_id):
        """终止进程"""
        try:
            cmd = ["powershell", f"Stop-Process -Id {process_id} -Force"]
            subprocess.run(cmd, check=True)
            return True
        except Exception as e:
            self.logger.error(f"终止进程失败 (ID: {process_id}): {e}")
            return False
    
    def log_action(self, action, process_name, process_id):
        """记录操作日志"""
        try:
            log_entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {action}: {process_name} (ID: {process_id})"
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + '\n')
            self.logger.info(log_entry)
        except Exception as e:
            self.logger.error(f"记录日志失败: {e}")
    
    def clean_background_processes(self):
        """清理后台进程"""
        self.logger.info("开始清理后台进程...")
        processes = self.get_running_processes()
        
        killed_count = 0
        for process in processes:
            process_name = process.get("Name", "").strip()
            process_id = process.get("Id", 0)
            
            if not process_name or process_id == 0:
                continue
            
            # 检查是否在排除列表中
            if self.is_excluded(process_name):
                continue
            
            # 检查是否在目标列表中
            if self.is_target(process_name):
                self.logger.info(f"发现目标进程: {process_name} (ID: {process_id})")
                if self.kill_process(process_id):
                    self.log_action("KILLED", process_name, process_id)
                    killed_count += 1
                else:
                    self.log_action("FAILED", process_name, process_id)
        
        result = f"清理完成，共终止 {killed_count} 个后台进程"
        self.logger.info(result)
        return result
    
    def list_running_processes(self):
        """列出当前运行的进程"""
        self.logger.info("列出当前运行的进程")
        processes = self.get_running_processes()
        
        process_list = []
        for process in processes:
            process_name = process.get("Name", "").strip()
            process_id = process.get("Id", 0)
            cpu = process.get("CPU", 0) or 0
            memory = process.get("MemoryMB", 0) or 0
            
            status = "[EXCLUDED]" if self.is_excluded(process_name) else "[TARGET]" if self.is_target(process_name) else "[OTHER]"
            process_info = f"{status} {process_name} (ID: {process_id}, CPU: {cpu:.2f}%, Memory: {memory:.2f}MB)"
            process_list.append(process_info)
        
        return "\n".join(process_list)
    
    def add_excluded_process(self, process_name):
        """添加到排除列表"""
        if process_name not in self.excluded_processes:
            self.excluded_processes.append(process_name)
            self.save_config()
            result = f"已将 {process_name} 添加到排除列表"
            self.logger.info(result)
            return result
        else:
            result = f"{process_name} 已经在排除列表中"
            self.logger.info(result)
            return result
    
    def add_target_process(self, process_name):
        """添加到目标列表"""
        if process_name not in self.target_processes:
            self.target_processes.append(process_name)
            self.save_config()
            result = f"已将 {process_name} 添加到目标列表"
            self.logger.info(result)
            return result
        else:
            result = f"{process_name} 已经在目标列表中"
            self.logger.info(result)
            return result
    
    def remove_excluded_process(self, process_name):
        """从排除列表中移除"""
        if process_name in self.excluded_processes:
            self.excluded_processes.remove(process_name)
            self.save_config()
            result = f"已将 {process_name} 从排除列表中移除"
            self.logger.info(result)
            return result
        else:
            result = f"{process_name} 不在排除列表中"
            self.logger.info(result)
            return result
    
    def remove_target_process(self, process_name):
        """从目标列表中移除"""
        if process_name in self.target_processes:
            self.target_processes.remove(process_name)
            self.save_config()
            result = f"已将 {process_name} 从目标列表中移除"
            self.logger.info(result)
            return result
        else:
            result = f"{process_name} 不在目标列表中"
            self.logger.info(result)
            return result
    
    def show_config(self):
        """显示当前配置"""
        self.logger.info("显示当前配置")
        config_info = []
        config_info.append("当前配置:")
        config_info.append("\n排除列表 (不会被关闭的进程):")
        for process in self.excluded_processes:
            config_info.append(f"  - {process}")
        
        config_info.append("\n目标列表 (会被关闭的进程):")
        for process in self.target_processes:
            config_info.append(f"  - {process}")
        
        return "\n".join(config_info)
    
    def execute(self, command: str, **kwargs):
        """执行技能命令"""
        if command == "clean":
            return self.clean_background_processes()
        elif command == "list":
            return self.list_running_processes()
        elif command == "config":
            return self.show_config()
        elif command == "add-excluded" and "process" in kwargs:
            return self.add_excluded_process(kwargs["process"])
        elif command == "add-target" and "process" in kwargs:
            return self.add_target_process(kwargs["process"])
        elif command == "remove-excluded" and "process" in kwargs:
            return self.remove_excluded_process(kwargs["process"])
        elif command == "remove-target" and "process" in kwargs:
            return self.remove_target_process(kwargs["process"])
        else:
            return "无效的命令，请使用以下命令: clean, list, config, add-excluded, add-target, remove-excluded, remove-target"

    def get_info(self):
        """获取技能信息"""
        return {
            "name": "Background Process Manager",
            "description": "管理和关闭不需要的后台进程，特别是WPC等不在任务栏显示的程序",
            "version": "1.0.0",
            "author": "MCP Core Team",
            "commands": [
                {
                    "name": "clean",
                    "description": "清理后台进程"
                },
                {
                    "name": "list",
                    "description": "列出当前运行的进程"
                },
                {
                    "name": "config",
                    "description": "显示当前配置"
                },
                {
                    "name": "add-excluded",
                    "description": "添加进程到排除列表",
                    "parameters": [
                        {
                            "name": "process",
                            "type": "string",
                            "required": true,
                            "description": "进程名称"
                        }
                    ]
                },
                {
                    "name": "add-target",
                    "description": "添加进程到目标列表",
                    "parameters": [
                        {
                            "name": "process",
                            "type": "string",
                            "required": true,
                            "description": "进程名称"
                        }
                    ]
                },
                {
                    "name": "remove-excluded",
                    "description": "从排除列表中移除进程",
                    "parameters": [
                        {
                            "name": "process",
                            "type": "string",
                            "required": true,
                            "description": "进程名称"
                        }
                    ]
                },
                {
                    "name": "remove-target",
                    "description": "从目标列表中移除进程",
                    "parameters": [
                        {
                            "name": "process",
                            "type": "string",
                            "required": true,
                            "description": "进程名称"
                        }
                    ]
                }
            ]
        }

# 测试代码
if __name__ == "__main__":
    skill = BackgroundProcessManagerSkill()
    print(skill.execute("list"))
    print("\n" + "=" * 50 + "\n")
    print(skill.execute("config"))