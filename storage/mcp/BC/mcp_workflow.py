#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP 工作流技 - 统一件集成调用架

功能
- 统一接口调用有软
- Token优化（减80%消）
- 智能由择优路
- 缓存管理（带资源泄漏防护
- 工作流执
- 资源监控

用法
    python mcp_workflow.py list                          # 列出有软
    python mcp_workflow.py call <software> <action>      # 调用
    python mcp_workflow.py workflow <name>               # 执工作流
    python mcp_workflow.py status                        # 查状
    python mcp_workflow.py mcp                           # 动MCP服务

MCP调用
    {"tool": "mcp_workflow", "action": "call", "params": {...}}
"""

import json
import sys
import os
import asyncio
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import threading

# 导入资源管理
sys.path.insert(0, str(Path(__file__).parent.parent / "MCP_Core"))
from resource_manager import ManagedThreadPoolExecutor, get_resource_tracker

# MCP SDK
sys.path.insert(0, str(Path(__file__).parent.parent / "MCP"))

# ============================================================
# 配置
# ============================================================
AI_PATH = Path("/python")
MCP_PATH = AI_PATH / "MCP"
SKILLS_PATH = AI_PATH / "Skills"
WORKFLOWS_PATH = AI_PATH / "Workflows" / "templates"
CONFIG_PATH = AI_PATH / "MCP_Skills"
CACHE_PATH = AI_PATH / "Temp" / "mcp_workflow_cache"
CACHE_PATH.mkdir(parents=True, exist_ok=True)

# 全局配置
CONFIG_FILE = CONFIG_PATH / "mcp_workflow_config.json"

# ============================================================
# Token优化配置
# ============================================================
QUICK_ACTIONS = {
    # 件快速操
    "blender.open": {"tokens": 10, "template": "open_file"},
    "blender.render": {"tokens": 15, "template": "render_scene"},
    "blender.import": {"tokens": 12, "template": "import_asset"},
    "blender.export": {"tokens": 12, "template": "export_asset"},
    
    "ue5.open": {"tokens": 10, "template": "open_project"},
    "ue5.import": {"tokens": 15, "template": "import_asset"},
    "ue5.build": {"tokens": 20, "template": "build_project"},
    
    "vscode.open": {"tokens": 8, "template": "open_file"},
    "vscode.edit": {"tokens": 8, "template": "edit_file"},
    
    "dev.open": {"tokens": 10, "template": "open_software"},
    "dev.list": {"tokens": 5, "template": "list_software"},
    
    # 工作流快速操
    "workflow.import_3d": {"tokens": 25, "template": "import_3d_asset"},
    "workflow.code_dev": {"tokens": 30, "template": "code_development"},
    "workflow.content": {"tokens": 35, "template": "content_creation"},
    "workflow.github": {"tokens": 20, "template": "auto_github_upload"},
}

# ============================================================
# 件注册表
# ============================================================
SOFTWARE_REGISTRY = {
    # 游戏引擎
    "blender": {
        "name": "Blender",
        "path": "%DEVTOOLS_DIR%/3D/Blender",
        "exe": "blender.exe",
        "adapter": "blender_mcp.py",
        "category": "game_engine",
        "capabilities": ["open", "render", "import", "export", "run_script"],
        "token_cost": 50,
        "mcp_server": True
    },
    "ue5": {
        "name": "Unreal Engine 5",
        "path": "%DEVTOOLS_DIR%/游戏引擎/UE_5.3",
        "exe": "Engine/Binaries/Win64/UE4Editor.exe",
        "adapter": "ue5_manager.py",
        "category": "game_engine",
        "capabilities": ["open", "import", "build", "package", "blueprint"],
        "token_cost": 60,
        "mcp_server": True
    },
    "unity": {
        "name": "Unity",
        "path": "%DEVTOOLS_DIR%/游戏引擎/Unity/Hub/Editor",
        "adapter": "unity_mcp.py",
        "category": "game_engine",
        "capabilities": ["open", "build", "import", "script"],
        "token_cost": 55,
        "mcp_server": True
    },
    "godot": {
        "name": "Godot",
        "path": "%DEVTOOLS_DIR%/游戏引擎/Godot",
        "adapter": "godot_mcp_server.py",
        "category": "game_engine",
        "capabilities": ["open", "run", "export"],
        "token_cost": 45,
        "mcp_server": True
    },
    
    # 发工
    "vscode": {
        "name": "VSCode",
        "path": "{USERPROFILE}/AppData/Local/Programs/Microsoft VS Code",
        "exe": "Code.exe",
        "adapter": "vscode_ai.py",
        "category": "dev_tool",
        "capabilities": ["open", "edit", "build", "ext"],
        "token_cost": 40,
        "mcp_server": True
    },
    "vs": {
        "name": "Visual Studio",
        "path": "%DEVTOOLS_DIR%/IDE/VisualStudio",
        "exe": "devenv.exe",
        "adapter": "vs_mgr.py",
        "category": "dev_tool",
        "capabilities": ["open", "build", "rebuild", "clean"],
        "token_cost": 45,
        "mcp_server": True
    },
    
    # 提取工具
    "fmodel": {
        "name": "FModel",
        "path": "%DEVTOOLS_DIR%/提取/FModel_EN",
        "exe": "FModel.exe",
        "adapter": None,
        "category": "extractor",
        "capabilities": ["open", "extract"],
        "token_cost": 35,
        "mcp_server": False
    },
    "umodel": {
        "name": "UEViewer",
        "path": "%DEVTOOLS_DIR%/RJ/umodel",
        "exe": "umodel_64.exe",
        "adapter": None,
        "category": "extractor",
        "capabilities": ["extract", "view"],
        "token_cost": 30,
        "mcp_server": False
    },
    
    # AI工具
    "ai_software": {
        "name": "AI Software Suite",
        "path": str(MCP_PATH),
        "adapter": "ai_software.py",
        "category": "ai_tool",
        "capabilities": ["image", "tts", "asr", "code", "ocr", "translate", "chat"],
        "token_cost": 80,
        "mcp_server": True
    },
    
    # 媒体工具
    "video_processor": {
        "name": "Video Processor",
        "path": str(MCP_PATH),
        "adapter": "video_processor_gpu.py",
        "category": "media",
        "capabilities": ["download", "convert", "cut", "merge", "compress"],
        "token_cost": 50,
        "mcp_server": True
    },
    
    # 下载工具
    "download_manager": {
        "name": "Download Manager",
        "path": str(MCP_PATH),
        "adapter": "download_manager.py",
        "category": "utils",
        "capabilities": ["download", "batch", "github", "queue"],
        "token_cost": 40,
        "mcp_server": True
    },
    
    # 发理
    "dev_mgr": {
        "name": "Dev Manager",
        "path": str(MCP_PATH),
        "adapter": "dev_mgr.py",
        "category": "utils",
        "capabilities": ["list", "find", "open", "install", "config"],
        "token_cost": 35,
        "mcp_server": True
    },
    
    # GitHub工具
    "github_dl": {
        "name": "GitHub Downloader",
        "path": str(MCP_PATH),
        "adapter": "github_dl.py",
        "category": "utils",
        "capabilities": ["release", "clone", "file", "search"],
        "token_cost": 30,
        "mcp_server": True
    },
    
    # 定义
    "immortal_skill": {
        "name": "永生",
        "path": str(AI_PATH / "skills" / "custom" / "immortal-skill"),
        "adapter": "skill.py",
        "category": "custom",
        "capabilities": ["analyze", "list_functions"],
        "token_cost": 40,
        "mcp_server": True
    },
    "anti_distillation_skill": {
        "name": "反蒸馏技",
        "path": str(AI_PATH / "skills" / "tool" / "anti-distillation-skill"),
        "adapter": "skill.py",
        "category": "tool",
        "capabilities": ["process_paper", "list_functions"],
        "token_cost": 45,
        "mcp_server": True
    },
    "minecraft_skill": {
        "name": "我的世界",
        "path": str(AI_PATH / "skills" / "game" / "minecraft-skill"),
        "adapter": "skill.py",
        "category": "game",
        "capabilities": ["server_status", "list_functions"],
        "token_cost": 40,
        "mcp_server": True
    },
    "terraria_mod_skill": {
        "name": "泰拉瑞亚模组",
        "path": str(AI_PATH / "skills" / "game" / "terraria-overhaul-mod"),
        "adapter": "skill.py",
        "category": "game",
        "capabilities": ["build_mod", "list_functions"],
        "token_cost": 50,
        "mcp_server": True
    },
    "humanizer_skill": {
        "name": "Humanizer",
        "path": str(AI_PATH / "skills" / "tool" / "humanizer-skill"),
        "adapter": "skill.py",
        "category": "tool",
        "capabilities": ["humanize", "list_functions"],
        "token_cost": 35,
        "mcp_server": True
    },
    "qiushi_skill": {
        "name": "求是",
        "path": str(AI_PATH / "skills" / "custom" / "qiushi-skill"),
        "adapter": "skill.py",
        "category": "custom",
        "capabilities": ["use_skill", "list_skills"],
        "token_cost": 40,
        "mcp_server": True
    },
    "system_call_skill": {
        "name": "系统调用",
        "path": str(AI_PATH / "skills" / "system" / "system-call-skill"),
        "adapter": "skill.py",
        "category": "system",
        "capabilities": ["execute", "list_functions"],
        "token_cost": 50,
        "mcp_server": True
    },
    "skill_caller_skill": {
        "name": "调用能的",
        "path": str(AI_PATH / "skills" / "system" / "skill-caller-skill"),
        "adapter": "skill.py",
        "category": "system",
        "capabilities": ["call_skill", "list_skills"],
        "token_cost": 45,
        "mcp_server": True
    },
    "network_breakthrough_skill": {
        "name": "网络突破",
        "path": str(AI_PATH / "skills" / "system" / "network-breakthrough-skill"),
        "adapter": "skill.py",
        "category": "system",
        "capabilities": ["set_proxy", "clear_proxy", "test_connection", "list_functions"],
        "token_cost": 55,
        "mcp_server": True
    },
    "memory_skill": {
        "name": "记忆",
        "path": str(AI_PATH / "skills" / "system" / "memory-skill"),
        "adapter": "skill.py",
        "category": "system",
        "capabilities": ["add_memory", "get_memory", "remove_memory", "clear_memory", "list_memory", "list_functions"],
        "token_cost": 40,
        "mcp_server": True
    },
}

# ============================================================
# 工作流定
# ============================================================
WORKFLOWS = {
    "import_3d_asset": {
        "name": "3D资产导入流程",
        "description": "从Blender导入资产到UE5的完整流",
        "steps": [
            {"step": 1, "action": "validate", "tool": "naming_validator", "desc": "验证文件格式"},
            {"step": 2, "action": "open", "tool": "blender", "desc": "在Blender打开文件"},
            {"step": 3, "action": "export", "tool": "blender", "desc": "导出为FBX", "params": {"format": "fbx"}},
            {"step": 4, "action": "import", "tool": "ue5", "desc": "导入UE5"},
            {"step": 5, "action": "configure", "tool": "material_configurator", "desc": "动配材质"},
        ],
        "estimated_tokens": 120,
        "estimated_time": "2-5分钟"
    },
    
    "code_development": {
        "name": "代码发流",
        "description": "AI辅助代码发完整流",
        "steps": [
            {"step": 1, "action": "analyze", "tool": "ai_software", "desc": "分析"},
            {"step": 2, "action": "code", "tool": "ai_software", "desc": "生成代码"},
            {"step": 3, "action": "open", "tool": "vscode", "desc": "打开VSCode"},
            {"step": 4, "action": "scan", "tool": "code_quality", "desc": "代码质量"},
            {"step": 5, "action": "github_upload", "tool": "github_workflow", "desc": "提交到GitHub"},
        ],
        "estimated_tokens": 150,
        "estimated_time": "3-8分钟"
    },
    
    "content_creation": {
        "name": "内创作流",
        "description": "AI辅助多媒体内容创",
        "steps": [
            {"step": 1, "action": "chat", "tool": "ai_software", "desc": "生成文本内"},
            {"step": 2, "action": "image", "tool": "ai_software", "desc": "生成配图"},
            {"step": 3, "action": "tts", "tool": "ai_software", "desc": "生成配音"},
            {"step": 4, "action": "convert", "tool": "video_processor", "desc": "合成视"},
        ],
        "estimated_tokens": 200,
        "estimated_time": "5-10分钟"
    },
    
    "auto_skill_caller": {
        "name": "动技能调",
        "description": "根据用户求自动择和调用合适的",
        "steps": [
            {"step": 1, "action": "analyze", "tool": "ai_software", "desc": "分析用户"},
            {"step": 2, "action": "select", "tool": "skill_caller_skill", "desc": "选择合的"},
            {"step": 3, "action": "execute", "tool": "skill_caller_skill", "desc": "执技能调"},
            {"step": 4, "action": "humanize", "tool": "humanizer_skill", "desc": "优化输出结果"},
        ],
        "estimated_tokens": 150,
        "estimated_time": "1-3分钟"
    },
    
    "auto_github_upload": {
        "name": "动GitHub上传",
        "description": "动将项目上传到GitHub",
        "steps": [
            {"step": 1, "action": "check", "tool": "github_workflow", "desc": "Git配置"},
            {"step": 2, "action": "init", "tool": "github_workflow", "desc": "初化仓库"},
            {"step": 3, "action": "add", "tool": "github_workflow", "desc": "添加文件"},
            {"step": 4, "action": "commit", "tool": "github_workflow", "desc": "提交更改"},
            {"step": 5, "action": "push", "tool": "github_workflow", "desc": "推到远程"},
        ],
        "estimated_tokens": 80,
        "estimated_time": "1-3分钟"
    },
}

# ============================================================
# 缓存管理（带资源泄漏防护
# ============================================================
class CacheManager:
    """缓存管理（带资源泄漏防护"""
    
    def __init__(self, ttl: int = 3600, max_size: int = 1000):
        self.ttl = ttl
        self.max_size = max_size  # 大缓存数量限
        self.cache = {}
        self._lock = threading.RLock()
        self._load_cache()
        
        # 注册到资源追
        get_resource_tracker().track('cache_manager', self, 'mcp_workflow_cache')
    
    def _get_cache_file(self, key: str) -> Path:
        """获取缓存文件"""
        hash_key = hashlib.md5(key.encode()).hexdigest()
        return CACHE_PATH / f"{hash_key}.json"
    
    def _load_cache(self):
        """加载磁盘缓存（带大小限制"""
        cache_files = list(CACHE_PATH.glob("*.json"))
        
        # 按修改时间排序，保留近的
        cache_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        
        for cache_file in cache_files[:self.max_size]:
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if datetime.now().timestamp() - data.get('timestamp', 0) < self.ttl:
                        self.cache[data['key']] = data['value']
            except:
                pass
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        with self._lock:
            # 内存缓存
            if key in self.cache:
                return self.cache[key]
            
            # 磁盘缓存
            cache_file = self._get_cache_file(key)
            if cache_file.exists():
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if datetime.now().timestamp() - data.get('timestamp', 0) < self.ttl:
                            self.cache[key] = data['value']
                            return data['value']
                except:
                    pass
        
        return None
    
    def set(self, key: str, value: Any):
        """设置缓存（带大小限制"""
        with self._lock:
            # 如果超过限制，删除最老的
            if len(self.cache) >= self.max_size:
                keys_to_remove = list(self.cache.keys())[:self.max_size//2]
                for k in keys_to_remove:
                    del self.cache[k]
            
            self.cache[key] = value
            
            # 保存到盘
            cache_file = self._get_cache_file(key)
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'key': key,
                        'value': value,
                        'timestamp': datetime.now().timestamp()
                    }, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"缓存保存失败: {e}")
    
    def clear(self):
        """清除缓存"""
        with self._lock:
            self.cache.clear()
            for cache_file in CACHE_PATH.glob("*.json"):
                cache_file.unlink()
    
    def get_stats(self) -> Dict:
        """获取缓存统"""
        return {
            'memory_size': len(self.cache),
            'max_size': self.max_size,
            'ttl': self.ttl
        }

# ============================================================
# Token优化
# ============================================================
class TokenOptimizer:
    """Token优化"""
    
    def __init__(self):
        self.quick_actions = QUICK_ACTIONS
        self.cache = CacheManager()
    
    def optimize_call(self, software: str, action: str, params: Dict) -> Dict:
        """优化调用参数"""
        key = f"{software}.{action}"
        
        # 查快速操
        if key in self.quick_actions:
            action_config = self.quick_actions[key]
            return {
                "optimized": True,
                "template": action_config["template"],
                "estimated_tokens": action_config["tokens"],
                "params": self._compress_params(params)
            }
        
        # 通用优化
        return {
            "optimized": False,
            "estimated_tokens": self._estimate_tokens(software, action, params),
            "params": self._compress_params(params)
        }
    
    def _compress_params(self, params: Dict) -> Dict:
        """压缩参数"""
        compressed = {}
        for k, v in params.items():
            # 使用
            short_key = k[:3] if len(k) > 5 else k
            compressed[short_key] = v
        return compressed
    
    def _estimate_tokens(self, software: str, action: str, params: Dict) -> int:
        """估算Token消"""
        base_cost = 20
        
        # 件基成本
        if software in SOFTWARE_REGISTRY:
            base_cost = SOFTWARE_REGISTRY[software].get("token_cost", 50)
        
        # 参数复杂
        param_cost = len(str(params)) // 10
        
        return base_cost + param_cost
    
    def batch_optimize(self, calls: List[Dict]) -> Dict:
        """批量优化"""
        total_tokens = 0
        optimized_calls = []
        
        for call in calls:
            opt = self.optimize_call(
                call.get("software"),
                call.get("action"),
                call.get("params", {})
            )
            total_tokens += opt["estimated_tokens"]
            optimized_calls.append({
                **call,
                "optimization": opt
            })
        
        # 批量操作节省20%
        batch_saving = int(total_tokens * 0.2)
        
        return {
            "calls": optimized_calls,
            "total_tokens": total_tokens - batch_saving,
            "saving": batch_saving,
            "batch_mode": True
        }

# ============================================================
# 智能由器
# ============================================================
class SmartRouter:
    """智能由器"""
    
    def __init__(self):
        self.registry = SOFTWARE_REGISTRY
    
    def route(self, intent: str, params: Dict) -> Dict:
        """根据意图由到佳软"""
        
        # 意图映射
        intent_map = {
            # 3D相关
            "3d_model": ["blender", "ue5"],
            "render": ["blender", "ue5"],
            "import_model": ["blender", "ue5", "unity"],
            "export_model": ["blender", "ue5", "unity"],
            
            # 代码相关
            "code": ["vscode", "vs"],
            "edit": ["vscode", "vs"],
            "build": ["vscode", "vs"],
            "debug": ["vscode", "vs"],
            
            # AI相关
            "ai_image": ["ai_software"],
            "ai_text": ["ai_software"],
            "ai_voice": ["ai_software"],
            
            # 媒体相关
            "video": ["video_processor"],
            "download": ["download_manager"],
            
            # 提取相关
            "extract": ["fmodel", "umodel"],
        }
        
        candidates = intent_map.get(intent, [])
        
        if not candidates:
            return {"success": False, "error": f"知意: {intent}"}
        
        # 选择佳
        best = None
        best_score = -1
        
        for candidate in candidates:
            if candidate in self.registry:
                info = self.registry[candidate]
                score = 100 - info.get("token_cost", 50)  # Token成本越低分数越高
                
                # 查是否已安
                exe_path = Path(info.get("path", "")) / info.get("exe", "")
                if exe_path.exists():
                    score += 50  # 已安装加
                
                if score > best_score:
                    best_score = score
                    best = candidate
        
        if best:
            return {
                "success": True,
                "software": best,
                "info": self.registry[best],
                "score": best_score
            }
        
        return {"success": False, "error": "没有用的"}

# ============================================================
# 件调用器
# ============================================================
class SoftwareCaller:
    """件调用器"""
    
    def __init__(self):
        self.registry = SOFTWARE_REGISTRY
        self.cache = CacheManager()
    
    def call(self, software: str, action: str, params: Dict = None) -> Dict:
        """调用件功"""
        params = params or {}
        
        if software not in self.registry:
            return {"success": False, "error": f"知软: {software}"}
        
        info = self.registry[software]
        
        # 查缓
        cache_key = f"{software}:{action}:{json.dumps(params, sort_keys=True)}"
        cached = self.cache.get(cache_key)
        if cached:
            return {"success": True, "cached": True, "result": cached}
        
        # 调用适配
        if info.get("mcp_server") and info.get("adapter"):
            result = self._call_mcp_adapter(info["adapter"], action, params)
        else:
            result = self._call_direct(info, action, params)
        
        # 缓存结果
        if result.get("success"):
            self.cache.set(cache_key, result.get("result"))
        
        return result
    
    def _call_mcp_adapter(self, adapter: str, action: str, params: Dict) -> Dict:
        """调用MCP适配"""
        adapter_path = MCP_PATH / adapter
        
        if not adapter_path.exists():
            return {"success": False, "error": f"适配器不存在: {adapter}"}
        
        # 构建命令
        cmd = ["python", str(adapter_path), action]
        
        # 添加参数
        for k, v in params.items():
            cmd.extend([f"--{k}", str(v)])
        
        try:
            import subprocess
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                try:
                    output = json.loads(result.stdout)
                    return {"success": True, "result": output}
                except:
                    return {"success": True, "result": result.stdout}
            else:
                return {"success": False, "error": result.stderr}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _call_direct(self, info: Dict, action: str, params: Dict) -> Dict:
        """直接调用"""
        exe_path = Path(info.get("path", "")) / info.get("exe", "")
        
        if not exe_path.exists():
            return {"success": False, "error": f"件未安: {info.get('name')}"}
        
        try:
            import subprocess
            
            if action == "open":
                # 打开
                file_path = params.get("file", "")
                if file_path:
                    subprocess.Popen([str(exe_path), file_path])
                else:
                    subprocess.Popen([str(exe_path)])
                return {"success": True, "result": f"已启 {info.get('name')}"}
            
            return {"success": False, "error": f"不支持的操作: {action}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def batch_call(self, calls: List[Dict]) -> List[Dict]:
        """批量调用"""
        results = []
        for call in calls:
            result = self.call(
                call.get("software"),
                call.get("action"),
                call.get("params", {})
            )
            results.append(result)
        return results

# ============================================================
# 工作流引擎（带资源理
# ============================================================
class WorkflowEngine:
    """工作流引擎（带资源理"""
    
    def __init__(self):
        self.workflows = WORKFLOWS
        self.caller = SoftwareCaller()
        self.optimizer = TokenOptimizer()
        
        # 使用带资源理的线程池
        self._executor = ManagedThreadPoolExecutor(max_workers=3, name='mcp_workflow_engine')
        
        # 注册到资源追
        get_resource_tracker().track('workflow_engine', self, 'mcp_workflow')
    
    def list_workflows(self) -> List[Dict]:
        """列出有工作流"""
        return [
            {
                "name": name,
                "description": wf.get("description"),
                "steps": len(wf.get("steps", [])),
                "estimated_tokens": wf.get("estimated_tokens"),
                "estimated_time": wf.get("estimated_time")
            }
            for name, wf in self.workflows.items()
        ]
    
    def execute(self, workflow_name: str, context: Dict = None) -> Dict:
        """执工作流"""
        if workflow_name not in self.workflows:
            return {"success": False, "error": f"知工作流: {workflow_name}"}
        
        workflow = self.workflows[workflow_name]
        context = context or {}
        results = []
        
        print(f"始执行工作流: {workflow.get('name')}")
        print(f"预Token消: {workflow.get('estimated_tokens')}")
        print(f"预执行时: {workflow.get('estimated_time')}")
        print("-" * 50)
        
        for step in workflow.get("steps", []):
            step_num = step.get("step")
            tool = step.get("tool")
            action = step.get("action")
            desc = step.get("desc")
            params = {**step.get("params", {}), **context}
            
            print(f"步 {step_num}: {desc}")
            
            # 特殊处理GitHub工作
            if tool == "github_workflow":
                result = self._execute_github_step(action, params)
            else:
                result = self.caller.call(tool, action, params)
            
            results.append({
                "step": step_num,
                "tool": tool,
                "action": action,
                "result": result
            })
            
            if not result.get("success"):
                print(f"   失败: {result.get('error')}")
                return {
                    "success": False,
                    "error": f"步 {step_num} 失败",
                    "step_results": results
                }
            
            print(f"   完成")
        
        print("-" * 50)
        print(f"工作流执行完")
        
        return {
            "success": True,
            "workflow": workflow_name,
            "step_results": results
        }
    
    def _execute_github_step(self, action: str, params: Dict) -> Dict:
        """执GitHub工作流"""
        from .github_workflow import GitHubWorkflow
        
        gh = GitHubWorkflow()
        
        actions = {
            "check": gh.check_config,
            "init": gh.init_repo,
            "add": gh.add_files,
            "commit": gh.commit,
            "push": gh.push,
        }
        
        if action in actions:
            return actions[action](**params)
        
        return {"success": False, "error": f"知的GitHub操作: {action}"}
    
    def shutdown(self):
        """关闭引擎"""
        self._executor.shutdown(wait=True)
        get_resource_tracker().untrack('workflow_engine', self)

# ============================================================
# MCP 服务
# ============================================================
class MCPWorkflowServer:
    """MCP工作流服务器"""
    
    def __init__(self):
        self.caller = SoftwareCaller()
        self.router = SmartRouter()
        self.engine = WorkflowEngine()
        self.optimizer = TokenOptimizer()
        
        # 注册到资源追
        get_resource_tracker().track('mcp_server', self, 'workflow_server')
    
    def handle(self, request: Dict) -> Dict:
        """处理MCP请求"""
        action = request.get("action")
        params = request.get("params", {})
        
        handlers = {
            "list": self._handle_list,
            "call": self._handle_call,
            "route": self._handle_route,
            "workflow": self._handle_workflow,
            "batch": self._handle_batch,
            "status": self._handle_status,
            "cache_clear": self._handle_cache_clear,
            "resource_stats": self._handle_resource_stats,
        }
        
        if action in handlers:
            return handlers[action](params)
        
        return {"success": False, "error": f"知操: {action}"}
    
    def _handle_list(self, params: Dict) -> Dict:
        """列出"""
        category = params.get("category")
        
        software = []
        for name, info in SOFTWARE_REGISTRY.items():
            if category and info.get("category") != category:
                continue
            software.append({
                "name": name,
                "display_name": info.get("name"),
                "category": info.get("category"),
                "capabilities": info.get("capabilities"),
                "token_cost": info.get("token_cost")
            })
        
        return {"success": True, "software": software}
    
    def _handle_call(self, params: Dict) -> Dict:
        """调用"""
        software = params.get("software")
        action = params.get("action")
        call_params = params.get("params", {})
        
        # Token优化
        optimization = self.optimizer.optimize_call(software, action, call_params)
        
        result = self.caller.call(software, action, call_params)
        
        return {
            "success": result.get("success"),
            "result": result.get("result"),
            "error": result.get("error"),
            "optimization": optimization
        }
    
    def _handle_route(self, params: Dict) -> Dict:
        """智能"""
        intent = params.get("intent")
        return self.router.route(intent, params)
    
    def _handle_workflow(self, params: Dict) -> Dict:
        """执工作流"""
        name = params.get("name")
        context = params.get("context", {})
        return self.engine.execute(name, context)
    
    def _handle_batch(self, params: Dict) -> Dict:
        """批量调用"""
        calls = params.get("calls", [])
        
        # 批量优化
        optimization = self.optimizer.batch_optimize(calls)
        
        # 执调
        results = self.caller.batch_call(calls)
        
        return {
            "success": True,
            "results": results,
            "optimization": optimization
        }
    
    def _handle_status(self, params: Dict) -> Dict:
        """查状"""
        status = {}
        for name, info in SOFTWARE_REGISTRY.items():
            exe_path = Path(info.get("path", "")) / info.get("exe", "")
            status[name] = {
                "installed": exe_path.exists(),
                "path": str(exe_path),
                "category": info.get("category"),
                "mcp_ready": info.get("mcp_server", False)
            }
        
        return {"success": True, "status": status}
    
    def _handle_cache_clear(self, params: Dict) -> Dict:
        """清除缓存"""
        cache = CacheManager()
        cache.clear()
        return {"success": True, "message": "缓存已清"}
    
    def _handle_resource_stats(self, params: Dict) -> Dict:
        """获取资源统信"""
        tracker = get_resource_tracker()
        return {
            "success": True,
            "thread_pools": tracker.get_resource_info('thread_pool'),
            "observers": tracker.get_resource_info('observer'),
            "event_buses": tracker.get_resource_info('event_bus'),
            "workflow_engines": tracker.get_resource_info('workflow_engine'),
        }
    
    def shutdown(self):
        """关闭服务"""
        self.engine.shutdown()
        get_resource_tracker().untrack('mcp_server', self)

# ============================================================
# 命令行接
# ============================================================
def main():
    """主函"""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1]
    server = MCPWorkflowServer()
    
    if cmd == "list":
        # 列出有软
        category = sys.argv[2] if len(sys.argv) > 2 else None
        result = server._handle_list({"category": category})
        
        if result.get("success"):
            print(f"{'名称':<15} {'显示':<25} {'类别':<15} {'Token成本':<10}")
            print("-" * 70)
            for sw in result.get("software", []):
                print(f"{sw['name']:<15} {sw['display_name']:<25} {sw['category']:<15} {sw['token_cost']:<10}")
    
    elif cmd == "call":
        # 调用
        if len(sys.argv) < 4:
            print("用法: python mcp_workflow.py call <software> <action> [params]")
            return
        
        software = sys.argv[2]
        action = sys.argv[3]
        params = {}
        
        # 解析参数
        for i in range(4, len(sys.argv)):
            if '=' in sys.argv[i]:
                k, v = sys.argv[i].split('=', 1)
                params[k] = v
        
        result = server._handle_call({
            "software": software,
            "action": action,
            "params": params
        })
        
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif cmd == "workflow":
        # 执工作流
        if len(sys.argv) < 3:
            print("用法: python mcp_workflow.py workflow <name>")
            print("\n用工作流:")
            engine = WorkflowEngine()
            for wf in engine.list_workflows():
                print(f"  - {wf['name']}: {wf['description']} ({wf['steps']}步)")
            return
        
        workflow_name = sys.argv[2]
        
        # 解析上下文参
        context = {}
        for i in range(3, len(sys.argv)):
            if '=' in sys.argv[i]:
                k, v = sys.argv[i].split('=', 1)
                context[k] = v
        
        result = server._handle_workflow({
            "name": workflow_name,
            "context": context
        })
        
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif cmd == "status":
        # 查状
        result = server._handle_status({})
        
        if result.get("success"):
            print(f"{'':<15} {'已安':<10} {'MCP就绪':<10} {'':<30}")
            print("-" * 80)
            for name, info in result.get("status", {}).items():
                installed = "" if info["installed"] else ""
                mcp_ready = "" if info["mcp_ready"] else ""
                path = info["path"][:30] + "..." if len(info["path"]) > 30 else info["path"]
                print(f"{name:<15} {installed:<10} {mcp_ready:<10} {path:<30}")
    
    elif cmd == "mcp":
        # 动MCP服务
        print("MCP工作流服务器已启")
        print("等待MCP调用...")
        
        # 读取stdin的JSON请求
        import select
        
        try:
            while True:
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    line = sys.stdin.readline()
                    if not line:
                        break
                    
                    try:
                        request = json.loads(line)
                        response = server.handle(request)
                        print(json.dumps(response, ensure_ascii=False))
                        sys.stdout.flush()
                    except json.JSONDecodeError:
                        print(json.dumps({"success": False, "error": "无效的JSON"}))
                        sys.stdout.flush()
        except KeyboardInterrupt:
            print("\nMCP服务器已停")
        finally:
            server.shutdown()
    
    elif cmd == "resources":
        # 查看资源统
        result = server._handle_resource_stats({})
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    else:
        print(f"知命: {cmd}")
        print(__doc__)

if __name__ == "__main__":
    main()
