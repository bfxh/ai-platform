#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - 软件位置管理技能

功能:
- 管理软件安装位置
- 自动扫描D:\rj和F:\rj目录
- 支持添加自定义软件位置
- 提供软件搜索和管理功能
"""

import json
import os
import glob
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import sys
# 导入技能基类
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from skills.base import Skill, handle_errors


class SoftwareLocationManager(Skill):
    """软件位置管理技能"""

    name = "software_location_manager"
    description = "软件位置管理 - 管理软件安装位置和自动扫描"
    version = "1.0.0"
    author = "MCP Core Team"

    def __init__(self, config: Optional[Dict] = None):
        # 先设置默认值，避免父类初始化时调用_load_config出错
        self.config_file = "software_locations.json"
        self.default_locations = ["D:\\rj", "F:\rj"]
        self.locations = []
        self.software_list = []
        
        super().__init__(config)
        # 父类初始化后再从配置中获取
        self.config_file = self.config.get("config_file", "software_locations.json")

    def initialize(self):
        """初始化技能"""
        super().initialize()
        self._load_config()
        self._scan_default_locations()
        self.logger.info("软件位置管理器已初始化")
        return True

    def shutdown(self):
        """关闭技能"""
        self._save_config()
        self.logger.info("软件位置管理器已关闭")

    def get_parameters(self) -> Dict:
        """获取参数定义"""
        return {
            "action": {
                "type": "string",
                "required": True,
                "description": "执行的动作",
                "enum": [
                    "add_location",
                    "remove_location",
                    "list_locations",
                    "scan_locations",
                    "search_software",
                    "list_software",
                    "get_software_details",
                    "update_software"
                ]
            },
            "location": {
                "type": "string",
                "required": False,
                "description": "软件位置路径"
            },
            "location_id": {
                "type": "string",
                "required": False,
                "description": "位置ID"
            },
            "query": {
                "type": "string",
                "required": False,
                "description": "软件搜索查询"
            },
            "software_id": {
                "type": "string",
                "required": False,
                "description": "软件ID"
            }
        }

    def validate_params(self, params: Dict) -> tuple[bool, Optional[str]]:
        """验证参数"""
        if "action" not in params:
            return False, "缺少必需参数: action"

        action = params["action"]

        if action == "add_location" and "location" not in params:
            return False, "添加位置需要 location 参数"

        if action == "remove_location" and "location_id" not in params:
            return False, "删除位置需要 location_id 参数"

        if action == "search_software" and "query" not in params:
            return False, "搜索软件需要 query 参数"

        if action == "get_software_details" and "software_id" not in params:
            return False, "获取软件详情需要 software_id 参数"

        return True, None

    @handle_errors
    def execute(self, params: Dict) -> Dict:
        """执行技能"""
        action = params.get("action")

        if action == "add_location":
            return self._add_location(params)
        elif action == "remove_location":
            return self._remove_location(params)
        elif action == "list_locations":
            return self._list_locations()
        elif action == "scan_locations":
            return self._scan_locations()
        elif action == "search_software":
            return self._search_software(params)
        elif action == "list_software":
            return self._list_software()
        elif action == "get_software_details":
            return self._get_software_details(params)
        elif action == "update_software":
            return self._update_software()
        else:
            return {
                "success": False,
                "error": f"未知动作: {action}"
            }

    def _load_config(self):
        """加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.locations = data.get("locations", [])
                    self.software_list = data.get("software", [])
                self.logger.info(f"从配置加载了 {len(self.locations)} 个位置和 {len(self.software_list)} 个软件")
            except Exception as e:
                self.logger.error(f"加载配置失败: {e}")
                self._initialize_defaults()
        else:
            self._initialize_defaults()

    def _save_config(self):
        """保存配置"""
        try:
            data = {
                "locations": self.locations,
                "software": self.software_list,
                "last_updated": datetime.now().isoformat()
            }
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"配置已保存，共 {len(self.locations)} 个位置和 {len(self.software_list)} 个软件")
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")

    def _initialize_defaults(self):
        """初始化默认配置"""
        # 添加默认位置
        for location in self.default_locations:
            if location not in [loc["path"] for loc in self.locations]:
                self.locations.append({
                    "id": f"loc_{len(self.locations) + 1}",
                    "path": location,
                    "type": "default",
                    "added_at": datetime.now().isoformat()
                })
        self._save_config()
        self.logger.info("初始化默认软件位置")

    def _scan_default_locations(self):
        """扫描默认位置"""
        for location in self.default_locations:
            if os.path.exists(location):
                self.logger.info(f"扫描默认位置: {location}")
                self._scan_location(location)

    def _add_location(self, params: Dict) -> Dict:
        """添加软件位置"""
        location = params.get("location")

        if not os.path.exists(location):
            return {
                "success": False,
                "error": f"位置不存在: {location}"
            }

        # 检查是否已存在
        if location in [loc["path"] for loc in self.locations]:
            return {
                "success": False,
                "error": f"位置已存在: {location}"
            }

        # 添加位置
        location_id = f"loc_{len(self.locations) + 1}"
        self.locations.append({
            "id": location_id,
            "path": location,
            "type": "custom",
            "added_at": datetime.now().isoformat()
        })

        # 扫描新位置
        self._scan_location(location)
        self._save_config()

        return {
            "success": True,
            "message": f"位置 '{location}' 添加成功",
            "location_id": location_id
        }

    def _remove_location(self, params: Dict) -> Dict:
        """删除软件位置"""
        location_id = params.get("location_id")

        # 查找位置
        location_to_remove = None
        for loc in self.locations:
            if loc["id"] == location_id:
                location_to_remove = loc
                break

        if not location_to_remove:
            return {
                "success": False,
                "error": f"位置ID不存在: {location_id}"
            }

        # 不允许删除默认位置
        if location_to_remove["type"] == "default":
            return {
                "success": False,
                "error": "默认位置不能删除"
            }

        # 从软件列表中移除该位置的软件
        self.software_list = [sw for sw in self.software_list if sw["location_id"] != location_id]

        # 移除位置
        self.locations = [loc for loc in self.locations if loc["id"] != location_id]
        self._save_config()

        return {
            "success": True,
            "message": f"位置 '{location_to_remove['path']}' 删除成功"
        }

    def _list_locations(self) -> Dict:
        """列出所有软件位置"""
        return {
            "success": True,
            "locations": self.locations,
            "count": len(self.locations)
        }

    def _scan_locations(self) -> Dict:
        """扫描所有位置"""
        scanned_count = 0
        new_software = 0

        for location in self.locations:
            location_path = location["path"]
            if os.path.exists(location_path):
                count = self._scan_location(location_path, location["id"])
                scanned_count += 1
                new_software += count

        self._save_config()

        return {
            "success": True,
            "message": f"扫描完成，共扫描 {scanned_count} 个位置，发现 {new_software} 个新软件",
            "scanned_locations": scanned_count,
            "new_software": new_software,
            "total_software": len(self.software_list)
        }

    def _scan_location(self, location_path: str, location_id: str = None) -> int:
        """扫描单个位置"""
        new_software_count = 0
        software_paths = []

        # 查找常见的软件安装目录和可执行文件
        patterns = [
            "**/*.exe",
            "**/*.lnk",
            "**/unins000.exe",
            "**/setup.exe"
        ]

        for pattern in patterns:
            software_paths.extend(glob.glob(os.path.join(location_path, pattern), recursive=True))

        # 去重
        software_paths = list(set(software_paths))

        for software_path in software_paths:
            # 提取软件名称
            software_name = os.path.basename(software_path)
            software_id = f"sw_{hash(software_path)}"

            # 检查是否已存在
            existing = False
            for sw in self.software_list:
                if sw["path"] == software_path:
                    existing = True
                    break

            if not existing:
                # 获取文件信息
                file_info = os.stat(software_path)
                self.software_list.append({
                    "id": software_id,
                    "name": software_name,
                    "path": software_path,
                    "location_id": location_id,
                    "size": file_info.st_size,
                    "modified_at": datetime.fromtimestamp(file_info.st_mtime).isoformat(),
                    "discovered_at": datetime.now().isoformat()
                })
                new_software_count += 1

        return new_software_count

    def _search_software(self, params: Dict) -> Dict:
        """搜索软件"""
        query = params.get("query", "").lower()
        results = []

        for software in self.software_list:
            if query in software["name"].lower() or query in software["path"].lower():
                results.append(software)

        return {
            "success": True,
            "results": results,
            "count": len(results),
            "query": query
        }

    def _list_software(self) -> Dict:
        """列出所有软件"""
        # 按位置分组
        software_by_location = {}
        for location in self.locations:
            software_by_location[location["id"]] = {
                "location": location,
                "software": []
            }

        for software in self.software_list:
            location_id = software.get("location_id")
            if location_id in software_by_location:
                software_by_location[location_id]["software"].append(software)

        return {
            "success": True,
            "software_by_location": software_by_location,
            "total_software": len(self.software_list)
        }

    def _get_software_details(self, params: Dict) -> Dict:
        """获取软件详情"""
        software_id = params.get("software_id")

        for software in self.software_list:
            if software["id"] == software_id:
                # 获取位置信息
                location_info = None
                for location in self.locations:
                    if location["id"] == software.get("location_id"):
                        location_info = location
                        break

                software_with_location = software.copy()
                if location_info:
                    software_with_location["location"] = location_info

                return {
                    "success": True,
                    "software": software_with_location
                }

        return {
            "success": False,
            "error": f"软件ID不存在: {software_id}"
        }

    def _update_software(self) -> Dict:
        """更新软件列表"""
        # 重新扫描所有位置
        self.software_list = []
        for location in self.locations:
            if os.path.exists(location["path"]):
                self._scan_location(location["path"], location["id"])

        self._save_config()

        return {
            "success": True,
            "message": "软件列表已更新",
            "total_software": len(self.software_list)
        }


# 技能实例
skill = SoftwareLocationManager()


if __name__ == "__main__":
    # 测试技能
    skill.initialize()

    # 列出位置
    print("1. 列出所有位置:")
    result = skill.execute({"action": "list_locations"})
    print(f"   共 {result.get('count', 0)} 个位置")
    for loc in result.get('locations', []):
        print(f"   - {loc['path']} (类型: {loc['type']})")

    # 扫描位置
    print("\n2. 扫描位置:")
    result = skill.execute({"action": "scan_locations"})
    print(f"   {result.get('message')}")

    # 列出软件
    print("\n3. 列出软件:")
    result = skill.execute({"action": "list_software"})
    print(f"   共 {result.get('total_software', 0)} 个软件")

    # 搜索软件
    print("\n4. 搜索软件:")
    result = skill.execute({"action": "search_software", "query": "exe"})
    print(f"   找到 {result.get('count', 0)} 个匹配的软件")

    skill.shutdown()
    print("\n软件位置管理器测试完成")
