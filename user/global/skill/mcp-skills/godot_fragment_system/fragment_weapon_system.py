import os
import subprocess
import json
import time
import psutil

class FragmentWeaponSystem:
    def __init__(self):
        self.game_process = None
        self.fragments = {
            "cube": 0,      # 立方体碎片
            "sphere": 0,     # 球体碎片
            "pyramid": 0,    # 金字塔碎片
            "cylinder": 0,   # 圆柱体碎片
            "prism": 0       # 棱柱碎片
        }
        self.weapons = []
        self.templates = {
            "handle": {"min_cube": 1, "min_sphere": 0, "min_pyramid": 0, "min_cylinder": 0, "min_prism": 0, "ideal_cube": 2, "ideal_sphere": 1, "ideal_pyramid": 0, "ideal_cylinder": 0, "ideal_prism": 0},  # 手柄模板
            "blade": {"min_cube": 0, "min_sphere": 0, "min_pyramid": 2, "min_cylinder": 0, "min_prism": 0, "ideal_cube": 0, "ideal_sphere": 0, "ideal_pyramid": 3, "ideal_cylinder": 1, "ideal_prism": 0},  # 刀刃模板
            "head": {"min_cube": 2, "min_sphere": 0, "min_pyramid": 1, "min_cylinder": 0, "min_prism": 0, "ideal_cube": 3, "ideal_sphere": 1, "ideal_pyramid": 2, "ideal_cylinder": 0, "ideal_prism": 1},   # 斧头头模板
            "bowstring": {"min_cube": 0, "min_sphere": 0, "min_pyramid": 0, "min_cylinder": 1, "min_prism": 0, "ideal_cube": 0, "ideal_sphere": 0, "ideal_pyramid": 0, "ideal_cylinder": 2, "ideal_prism": 1},  # 弓弦模板
            "bow_limb": {"min_cube": 0, "min_sphere": 0, "min_pyramid": 0, "min_cylinder": 0, "min_prism": 2, "ideal_cube": 1, "ideal_sphere": 0, "ideal_pyramid": 0, "ideal_cylinder": 1, "ideal_prism": 3}  # 弓臂模板
        }
        self.weapon_parts = {
            "sword": ["handle", "blade"],
            "axe": ["handle", "head"],
            "bow": ["handle", "bow_limb", "bowstring"]
        }
        self.template_registry = []  # 模板注册表，用于社区贡献
        
    def start_game(self, project_path):
        """启动Godot游戏"""
        try:
            # 查找Godot可执行文件
            godot_path = self._find_godot_executable()
            if not godot_path:
                return {"success": False, "message": "未找到Godot可执行文件"}
            
            # 启动Godot游戏
            self.game_process = subprocess.Popen([godot_path, "--path", project_path, "--editor"])
            time.sleep(3)  # 等待游戏启动
            
            if self.game_process.poll() is None:
                return {"success": True, "message": "Godot游戏已启动"}
            else:
                return {"success": False, "message": "Godot游戏启动失败"}
                
        except Exception as e:
            return {"success": False, "message": f"启动游戏时出错: {str(e)}"}
    
    def stop_game(self):
        """停止Godot游戏"""
        try:
            if self.game_process and self.game_process.poll() is None:
                self.game_process.terminate()
                self.game_process.wait(timeout=5)
                return {"success": True, "message": "Godot游戏已停止"}
            else:
                # 查找并终止所有Godot进程
                for process in psutil.process_iter(['name']):
                    if 'godot' in process.info['name'].lower():
                        process.terminate()
                return {"success": True, "message": "Godot游戏进程已终止"}
                
        except Exception as e:
            return {"success": False, "message": f"停止游戏时出错: {str(e)}"}
    
    def collect_fragment(self, fragment_type, quantity):
        """收集碎片"""
        try:
            if fragment_type in self.fragments:
                self.fragments[fragment_type] += quantity
                return {
                    "success": True,
                    "message": f"成功收集 {quantity} 个 {fragment_type} 碎片",
                    "total_fragments": self.fragments
                }
            else:
                return {"success": False, "message": "无效的碎片类型"}
                
        except Exception as e:
            return {"success": False, "message": f"收集碎片时出错: {str(e)}"}
    
    def craft_weapon(self, weapon_type):
        """制造武器"""
        try:
            if weapon_type not in self.weapon_parts:
                return {"success": False, "message": "无效的武器类型"}
            
            # 计算最低碎片需求
            min_required = {"cube": 0, "sphere": 0, "pyramid": 0, "cylinder": 0, "prism": 0}
            ideal_required = {"cube": 0, "sphere": 0, "pyramid": 0, "cylinder": 0, "prism": 0}
            
            for part in self.weapon_parts[weapon_type]:
                if part not in self.templates:
                    return {"success": False, "message": f"无效的武器部件: {part}"}
                
                part_template = self.templates[part]
                min_required["cube"] += part_template.get("min_cube", 0)
                min_required["sphere"] += part_template.get("min_sphere", 0)
                min_required["pyramid"] += part_template.get("min_pyramid", 0)
                min_required["cylinder"] += part_template.get("min_cylinder", 0)
                min_required["prism"] += part_template.get("min_prism", 0)
                ideal_required["cube"] += part_template.get("ideal_cube", 0)
                ideal_required["sphere"] += part_template.get("ideal_sphere", 0)
                ideal_required["pyramid"] += part_template.get("ideal_pyramid", 0)
                ideal_required["cylinder"] += part_template.get("ideal_cylinder", 0)
                ideal_required["prism"] += part_template.get("ideal_prism", 0)
            
            # 检查最低碎片是否足够
            for fragment_type, required in min_required.items():
                if self.fragments.get(fragment_type, 0) < required:
                    return {"success": False, "message": f"碎片不足，至少需要 {required} 个 {fragment_type} 碎片"}
            
            # 计算实际使用的碎片数量（基于实际拥有的碎片和理想需求）
            actual_used = {}
            for fragment_type in ["cube", "sphere", "pyramid", "cylinder", "prism"]:
                available = self.fragments.get(fragment_type, 0)
                ideal = ideal_required.get(fragment_type, 0)
                actual_used[fragment_type] = min(available, ideal)
                # 确保至少满足最低需求
                actual_used[fragment_type] = max(actual_used[fragment_type], min_required.get(fragment_type, 0))
            
            # 消耗碎片
            for fragment_type, used in actual_used.items():
                self.fragments[fragment_type] -= used
            
            # 计算武器质量和属性
            quality = self._calculate_weapon_quality(actual_used, ideal_required)
            base_damage = self._get_weapon_damage(weapon_type)
            base_attack_speed = self._get_weapon_attack_speed(weapon_type)
            
            # 根据质量调整属性
            damage = int(base_damage * quality)
            attack_speed = base_attack_speed * (0.8 + 0.4 * quality)
            
            # 创建武器
            weapon = {
                "type": weapon_type,
                "name": f"{self._get_weapon_name(weapon_type)} ({int(quality * 100)}%)",
                "damage": damage,
                "attack_speed": round(attack_speed, 2),
                "quality": round(quality, 2),
                "crafted_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "parts": self.weapon_parts[weapon_type],
                "fragments_used": actual_used,
                "min_required": min_required,
                "ideal_required": ideal_required
            }
            
            self.weapons.append(weapon)
            
            return {
                "success": True,
                "message": f"成功制造 {weapon['name']}",
                "weapon": weapon
            }
            
        except Exception as e:
            return {"success": False, "message": f"制造武器时出错: {str(e)}"}
    
    def _calculate_weapon_quality(self, actual, ideal):
        """计算武器质量"""
        total_actual = sum(actual.values())
        total_ideal = sum(ideal.values())
        
        if total_ideal == 0:
            return 1.0
        
        # 计算质量比例
        quality = total_actual / total_ideal
        
        # 确保质量在0.5到1.0之间
        return max(0.5, min(1.0, quality))
    
    def get_inventory(self):
        """获取背包信息"""
        try:
            return {
                "success": True,
                "message": "获取背包信息成功",
                "fragments": self.fragments,
                "weapons": self.weapons,
                "templates": self.templates,
                "weapon_parts": self.weapon_parts,
                "template_registry": self.template_registry
            }
        except Exception as e:
            return {"success": False, "message": f"获取背包信息时出错: {str(e)}"}
    
    def add_template(self, template_name, template_data):
        """添加模板"""
        try:
            # 验证模板数据
            required_fields = ["min_common", "min_rare", "min_epic", "ideal_common", "ideal_rare", "ideal_epic"]
            for field in required_fields:
                if field not in template_data:
                    return {"success": False, "message": f"模板缺少必要字段: {field}"}
            
            # 添加模板
            self.templates[template_name] = template_data
            
            # 注册到模板注册表
            template_info = {
                "name": template_name,
                "data": template_data,
                "added_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.template_registry.append(template_info)
            
            return {
                "success": True,
                "message": f"成功添加模板: {template_name}",
                "template": template_info
            }
        except Exception as e:
            return {"success": False, "message": f"添加模板时出错: {str(e)}"}
    
    def list_templates(self):
        """列出所有模板"""
        try:
            return {
                "success": True,
                "message": "获取模板列表成功",
                "templates": self.templates,
                "template_registry": self.template_registry
            }
        except Exception as e:
            return {"success": False, "message": f"获取模板列表时出错: {str(e)}"}
    
    def test_system(self):
        """测试碎片武器系统"""
        try:
            test_results = {
                "start_game": False,
                "collect_fragment": False,
                "craft_weapon": False,
                "get_inventory": False
            }
            
            # 测试收集碎片（确保有足够的碎片制造武器）
            collect_common = self.collect_fragment("common", 20)
            collect_rare = self.collect_fragment("rare", 10)
            collect_epic = self.collect_fragment("epic", 5)
            if collect_common["success"] and collect_rare["success"] and collect_epic["success"]:
                test_results["collect_fragment"] = True
            
            # 测试获取背包
            inventory_result = self.get_inventory()
            if inventory_result["success"]:
                test_results["get_inventory"] = True
            
            # 测试制造武器
            craft_result = self.craft_weapon("sword")
            if craft_result["success"]:
                test_results["craft_weapon"] = True
            
            # 测试启动游戏（不实际启动，只检查路径）
            godot_path = self._find_godot_executable()
            if godot_path:
                test_results["start_game"] = True
            
            all_passed = all(test_results.values())
            
            return {
                "success": all_passed,
                "message": "系统测试完成" if all_passed else "部分测试失败",
                "test_results": test_results
            }
            
        except Exception as e:
            return {"success": False, "message": f"测试系统时出错: {str(e)}"}
    
    def _find_godot_executable(self):
        """查找Godot可执行文件"""
        # 常见的Godot安装路径
        possible_paths = [
            "%SOFTWARE_DIR%\\KF\\JM\\Godot_v4.6.1-stable_win64.exe",
            "C:\\Program Files\\Godot\\Godot.exe",
            "C:\\Program Files (x86)\\Godot\\Godot.exe"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # 搜索环境变量
        for path in os.environ["PATH"].split(os.pathsep):
            godot_path = os.path.join(path, "godot.exe")
            if os.path.exists(godot_path):
                return godot_path
        
        return None
    
    def _get_weapon_name(self, weapon_type):
        """获取武器名称"""
        names = {
            "sword": "钢铁剑",
            "axe": "战斧",
            "bow": "长弓"
        }
        return names.get(weapon_type, weapon_type)
    
    def _get_weapon_damage(self, weapon_type):
        """获取武器伤害"""
        damage = {
            "sword": 10,
            "axe": 15,
            "bow": 8
        }
        return damage.get(weapon_type, 5)
    
    def _get_weapon_attack_speed(self, weapon_type):
        """获取武器攻击速度"""
        attack_speed = {
            "sword": 1.0,
            "axe": 0.8,
            "bow": 1.2
        }
        return attack_speed.get(weapon_type, 1.0)

def start_skill_server():
    """启动技能服务器"""
    import socket
    
    system = FragmentWeaponSystem()
    host = 'localhost'
    port = 8905
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"游戏控制技能服务已启动，监听端口 {port}")
        
        while True:
            conn, addr = s.accept()
            with conn:
                print(f"连接来自: {addr}")
                data = conn.recv(4096)
                if not data:
                    break
                
                try:
                    request = json.loads(data.decode('utf-8'))
                    command = request.get('command')
                    params = request.get('params', {})
                    
                    if command == 'start_game':
                        result = system.start_game(params.get('project_path', '%SOFTWARE_DIR%\\KF\\JM\\GodotProject'))
                    elif command == 'stop_game':
                        result = system.stop_game()
                    elif command == 'collect_fragment':
                        result = system.collect_fragment(
                            params.get('fragment_type', 'common'),
                            params.get('quantity', 1)
                        )
                    elif command == 'craft_weapon':
                        result = system.craft_weapon(params.get('weapon_type', 'sword'))
                    elif command == 'get_inventory':
                        result = system.get_inventory()
                    elif command == 'test_system':
                        result = system.test_system()
                    elif command == 'add_template':
                        result = system.add_template(
                            params.get('template_name'),
                            params.get('template_data')
                        )
                    elif command == 'list_templates':
                        result = system.list_templates()
                    elif command == 'get_info':
                        result = {
                            "success": True,
                            "message": "游戏控制技能",
                            "description": "管理Godot游戏中的碎片武器系统",
                            "commands": [
                                "start_game: 启动Godot游戏",
                                "stop_game: 停止Godot游戏",
                                "collect_fragment: 收集碎片",
                                "craft_weapon: 制造武器",
                                "get_inventory: 获取背包信息",
                                "test_system: 测试系统",
                                "add_template: 添加模板",
                                "list_templates: 列出所有模板"
                            ]
                        }
                    else:
                        result = {"success": False, "message": f"未知命令: {command}"}
                    
                except Exception as e:
                    result = {"success": False, "message": f"处理请求时出错: {str(e)}"}
                
                conn.sendall(json.dumps(result).encode('utf-8'))

if __name__ == "__main__":
    # 启动技能服务器
    start_skill_server()