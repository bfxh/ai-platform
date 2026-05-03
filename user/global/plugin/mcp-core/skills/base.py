#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - 技能基础类与注册中心（已修复资源泄漏）

功能:
- 技能基类定义
- 技能注册与管理
- 钩子管理
- 资源泄漏防护
"""

import os
import sys
import importlib
import traceback
from functools import wraps
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
import threading

# 添加上级目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from resource_manager import HookManager, get_resource_tracker

__all__ = ['Skill', 'SkillBase', 'SkillInfo', 'SkillRegistry', 'get_registry', 'skill', 'action', 'handle_errors']


def handle_errors(func):
    """错误处理装饰器 - 捕获异常并返回标准化错误结果"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
    return wrapper


@dataclass
class SkillInfo:
    """技能信息"""
    name: str
    description: str
    version: str
    author: str
    actions: List[str]
    path: str
    instance: Any = None


class Skill(ABC):
    """技能基类"""
    
    name: str = ""
    description: str = ""
    version: str = "1.0"
    author: str = ""
    
    def __init__(self, config: Optional[Dict] = None):
        self._hooks = HookManager(max_hooks_per_type=30)
        self.config = config or {}
    
    @abstractmethod
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行技能动作"""
        pass
    
    def register_hook(self, hook_type: str, callback: Callable, name: str = "", priority: int = 0):
        """注册钩子"""
        return self._hooks.register(hook_type, callback, name, priority)
    
    def unregister_hook(self, hook_type: str, callback: Callable):
        """注销钩子"""
        return self._hooks.unregister(hook_type, callback)
    
    def execute_hooks(self, hook_type: str, *args, **kwargs):
        """执行钩子"""
        return self._hooks.execute(hook_type, *args, **kwargs)
    
    def clear_hooks(self, hook_type: str = None):
        """清除钩子"""
        self._hooks.clear(hook_type)
    
    def get_hook_info(self, hook_type: str = None) -> Dict[str, List[dict]]:
        """获取钩子信息"""
        return self._hooks.get_hook_info(hook_type)


class SkillRegistry:
    """技能注册中心（已修复资源泄漏）"""
    
    def __init__(self):
        self._skills: Dict[str, SkillInfo] = {}
        self._loaded_skills: Dict[str, Skill] = {}
        self._lock = threading.RLock()
        
        # 使用钩子管理器
        self._global_hooks = HookManager(max_hooks_per_type=50)
        
        # 注册到资源追踪器
        get_resource_tracker().track('skill_registry', self, 'main_registry')
        
        # 自动注册基础设施适配器钩子（session_memory）
        self._init_infra_hooks()
    
    def register(self, skill_class: type):
        """注册技能类"""
        if not issubclass(skill_class, Skill):
            raise ValueError("必须继承自 Skill 类")
        
        if not skill_class.name:
            raise ValueError("技能必须设置 name 属性")
        
        with self._lock:
            self._skills[skill_class.name] = SkillInfo(
                name=skill_class.name,
                description=skill_class.description,
                version=skill_class.version,
                author=skill_class.author,
                actions=[],
                path=""
            )
    
    def register_from_module(self, module_path: str):
        """从模块注册技能"""
        try:
            module = importlib.import_module(module_path)
            
            for name in dir(module):
                obj = getattr(module, name)
                if isinstance(obj, type) and issubclass(obj, Skill) and obj != Skill:
                    self.register(obj)
            
            return True
        except Exception as e:
            print(f"[SkillRegistry] 加载模块失败 {module_path}: {e}")
            return False
    
    def load_skills_from_directory(self, skills_dir: str = "skills"):
        """从目录加载所有技能"""
        skills_path = Path(skills_dir)
        
        if not skills_path.exists():
            return
        
        for item in skills_path.iterdir():
            if item.is_dir():
                # 尝试加载目录中的 __init__.py
                init_file = item / "__init__.py"
                if init_file.exists():
                    module_name = f"skills.{item.name}"
                    self.register_from_module(module_name)
            elif item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
                # 直接加载 .py 文件
                module_name = f"skills.{item.stem}"
                self.register_from_module(module_name)
    
    def get(self, skill_name: str) -> Optional[Skill]:
        """获取技能实例"""
        with self._lock:
            if skill_name in self._loaded_skills:
                return self._loaded_skills[skill_name]
            
            if skill_name not in self._skills:
                return None
            
            # 尝试实例化
            try:
                info = self._skills[skill_name]
                
                # 查找技能类
                skill_class = None
                for module_name in ['skills.' + skill_name.replace('-', '_')]:
                    try:
                        module = importlib.import_module(module_name)
                        for name in dir(module):
                            obj = getattr(module, name)
                            if isinstance(obj, type) and issubclass(obj, Skill) and getattr(obj, 'name', '') == skill_name:
                                skill_class = obj
                                break
                    except:
                        continue
                
                if skill_class is None:
                    return None
                
                # 创建实例
                instance = skill_class()
                self._loaded_skills[skill_name] = instance
                
                # 更新技能信息
                info.instance = instance
                info.actions = self._get_skill_actions(instance)
                
                return instance
            
            except Exception as e:
                print(f"[SkillRegistry] 实例化技能失败 {skill_name}: {e}")
                return None
    
    def _get_skill_actions(self, instance: Skill) -> List[str]:
        """获取技能可用动作"""
        actions = []
        
        # 查找所有以 'action_' 开头的方法
        for name in dir(instance):
            if name.startswith('action_'):
                action_name = name[7:]  # 去掉 'action_' 前缀
                actions.append(action_name)
        
        return actions
    
    def execute(self, skill_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行技能"""
        # 执行前置钩子
        before_results = self._global_hooks.execute('before_skill_execute', skill_name, params)
        
        try:
            skill = self.get(skill_name)
            
            if not skill:
                return {
                    'success': False,
                    'error': f"技能不存在: {skill_name}"
                }
            
            action = params.get('action', '')
            
            # 执行技能内部钩子
            skill.execute_hooks('before_execute', action, params)
            
            # 执行动作
            result = skill.execute(action, params)
            
            # 执行技能内部钩子
            skill.execute_hooks('after_execute', action, params, result)
            
            return result
        
        except Exception as e:
            # 执行错误钩子
            self._global_hooks.execute('skill_error', skill_name, params, e)
            
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
        finally:
            # 执行后置钩子
            self._global_hooks.execute('after_skill_execute', skill_name, params)
    
    def list(self) -> List[Dict]:
        """列出所有技能"""
        result = []
        
        with self._lock:
            for name, info in self._skills.items():
                is_loaded = name in self._loaded_skills
                
                result.append({
                    'name': name,
                    'description': info.description,
                    'version': info.version,
                    'author': info.author,
                    'actions': info.actions,
                    'is_loaded': is_loaded,
                    'path': info.path
                })
        
        return result
    
    def unload(self, skill_name: str):
        """卸载技能"""
        with self._lock:
            if skill_name in self._loaded_skills:
                # 清理钩子
                skill = self._loaded_skills[skill_name]
                skill.clear_hooks()
                del self._loaded_skills[skill_name]
                
                # 更新技能信息
                if skill_name in self._skills:
                    self._skills[skill_name].instance = None
    
    def unload_all(self):
        """卸载所有技能"""
        with self._lock:
            for skill_name in list(self._loaded_skills.keys()):
                self.unload(skill_name)
    
    def register_global_hook(self, hook_type: str, callback: Callable, name: str = "", priority: int = 0):
        """注册全局钩子"""
        return self._global_hooks.register(hook_type, callback, name, priority)
    
    def unregister_global_hook(self, hook_type: str, callback: Callable):
        """注销全局钩子"""
        return self._global_hooks.unregister(hook_type, callback)
    
    def get_global_hook_info(self, hook_type: str = None) -> Dict[str, List[dict]]:
        """获取全局钩子信息"""
        return self._global_hooks.get_hook_info(hook_type)
    
    def clear_global_hooks(self, hook_type: str = None):
        """清除全局钩子"""
        self._global_hooks.clear(hook_type)
    
    def shutdown(self):
        """关闭注册中心"""
        self.unload_all()
        self.clear_global_hooks()
        get_resource_tracker().untrack('skill_registry', self)

    def _init_infra_hooks(self):
        """自动注册基础设施适配器钩子（session_memory）"""
        try:
            import importlib
            adapter_module = importlib.import_module('core.infra_adapter')
            adapter = adapter_module.get_adapter()
            if adapter._memory:
                self.register_global_hook("before_skill_execute",
                                          adapter._on_skill_before, "infra_before")
                self.register_global_hook("after_skill_execute",
                                          adapter._on_skill_after, "infra_after")
                self.register_global_hook("skill_error",
                                          adapter._on_skill_error, "infra_error")
        except Exception:
            pass  # 静默失败，适配器是可选的


# 全局技能注册中心实例
_registry_instance = None


def get_registry() -> SkillRegistry:
    """获取全局技能注册中心"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = SkillRegistry()
    return _registry_instance


# 装饰器：注册技能
def skill(name: str = "", description: str = "", version: str = "1.0", author: str = ""):
    """装饰器：注册技能类"""
    def decorator(cls):
        if not issubclass(cls, Skill):
            raise ValueError("装饰器只能用于 Skill 子类")
        
        cls.name = name if name else cls.__name__
        cls.description = description if description else getattr(cls, 'description', '')
        cls.version = version if version else getattr(cls, 'version', '1.0')
        cls.author = author if author else getattr(cls, 'author', '')
        
        # 注册到全局注册中心
        get_registry().register(cls)
        
        return cls
    return decorator


# 装饰器：注册技能动作
def action(name: str = ""):
    """装饰器：注册技能动作"""
    def decorator(func):
        func._is_skill_action = True
        func._action_name = name if name else func.__name__
        return func
    return decorator


SkillBase = Skill


if __name__ == '__main__':
    # 测试技能注册中心
    registry = get_registry()
    
    print("技能注册中心测试")
    
    # 列出技能
    print("\n1. 技能列表:")
    skills = registry.list()
    for skill_info in skills:
        print(f"   - {skill_info['name']}: {skill_info['description']}")
    
    # 注册测试钩子
    def on_skill_execute(skill_name, params):
        print(f"[钩子] 技能执行: {skill_name}")
    
    registry.register_global_hook('before_skill_execute', on_skill_execute, 'test_hook')
    
    print(f"\n2. 全局钩子信息: {registry.get_global_hook_info()}")
    
    registry.shutdown()
    print("\n技能注册中心测试完成")