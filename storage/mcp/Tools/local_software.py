#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地软件调用器 - 集成Everything搜索

功能：
- 调用Everything搜索本地软件
- 支持C盘、D盘、F盘等所有磁盘
- 自动发现可执行文件
- 智能分类软件
- 快速启动软件
- 支持通过名称、路径、类型搜索

用法：
    python local_software.py search <keyword>     # 搜索软件
    python local_software.py list                 # 列出已发现的软件
    python local_software.py open <name>          # 打开软件
    python local_software.py scan                 # 全盘扫描软件
    python local_software.py refresh              # 刷新软件列表
    python local_software.py info <name>          # 查看软件信息

MCP调用：
    {"tool": "local_software", "action": "search", "keyword": "blender"}
"""

import json
import sys
import os
import subprocess
import sqlite3
import winreg
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

# ============================================================
# 配置
# ============================================================
AI_PATH = Path("/python")
MCP_PATH = AI_PATH / "MCP"
CONFIG_PATH = AI_PATH / "MCP_Skills"

# Everything 路径
EVERYTHING_PATHS = [
    Path("C:/Program Files/Everything/Everything.exe"),
    Path("C:/Program Files (x86)/Everything/Everything.exe"),
    Path("%DEVTOOLS_DIR%/工具/Everything/Everything.exe"),
]

# 软件数据库
SOFTWARE_DB = CONFIG_PATH / "local_software.db"

# 可执行文件扩展名
EXE_EXTENSIONS = ['.exe', '.bat', '.cmd', '.lnk']

# 软件分类规则
CATEGORY_RULES = {
    "game_engine": ["unity", "unreal", "blender", "godot", "maya", "3dsmax", "c4d"],
    "dev_tool": ["vscode", "visual studio", "pycharm", "idea", "eclipse", "sublime", "cursor"],
    "extractor": ["fmodel", "umodel", "assetripper", "assetstudio", "ilspy", "dnspy"],
    "ai_tool": ["stable diffusion", "comfyui", "fooocus", "invokeai", "ollama"],
    "media": ["ffmpeg", "obs", "premiere", "after effects", "davinci", "vlc"],
    "download": ["idm", "aria2", "motrix", "qbittorrent"],
    "system": ["7-zip", "everything", "powertoys", "ditto", "snipaste", "sharex"],
    "network": ["clash", "v2ray", "shadowsocks", "proxifier", "putty"],
    "browser": ["chrome", "firefox", "edge", "brave", "opera"],
    "communication": ["qq", "wechat", "discord", "telegram", "slack", "teams"],
    "game_platform": ["steam", "epic", "gog", "origin", "uplay", "battle.net"],
    "office": ["word", "excel", "powerpoint", "outlook", "acrobat", "wps"],
}

# ============================================================
# Everything 接口
# ============================================================
class EverythingAPI:
    """Everything 搜索接口"""
    
    def __init__(self):
        self.es_path = self._find_es()
    
    def _find_es(self) -> Optional[Path]:
        """查找 Everything ES 工具"""
        # 常见路径
        paths = [
            Path("C:/Program Files/Everything/es.exe"),
            Path("C:/Program Files (x86)/Everything/es.exe"),
            Path("%DEVTOOLS_DIR%/工具/Everything/es.exe"),
        ]
        
        for path in paths:
            if path.exists():
                return path
        
        return None
    
    def is_available(self) -> bool:
        """检查 Everything 是否可用"""
        return self.es_path is not None
    
    def search(self, keyword: str, max_results: int = 20) -> List[Dict]:
        """使用 Everything 搜索文件"""
        if not self.is_available():
            return []
        
        results = []
        
        try:
            # 构建搜索命令
            cmd = [
                str(self.es_path),
                "-n", str(max_results),
                "-s",  # 按大小排序
                f"{keyword} ext:exe"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    line = line.strip()
                    if line and not line.startswith('>'):
                        file_path = Path(line)
                        if file_path.exists() and file_path.suffix.lower() in EXE_EXTENSIONS:
                            results.append({
                                "path": str(file_path),
                                "name": file_path.stem,
                                "size": file_path.stat().st_size if file_path.exists() else 0
                            })
        
        except Exception as e:
            print(f"Everything 搜索失败: {e}")
        
        return results

# ============================================================
# 软件管理器
# ============================================================
class SoftwareManager:
    """本地软件管理器"""
    
    def __init__(self):
        self.everything = EverythingAPI()
        self._init_database()
        self.software_cache = {}
    
    def _init_database(self):
        """初始化数据库"""
        CONFIG_PATH.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(SOFTWARE_DB))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS software (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                display_name TEXT,
                path TEXT NOT NULL,
                exe_name TEXT,
                category TEXT,
                size_mb REAL,
                discovered_at TEXT,
                last_used TEXT,
                use_count INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_name ON software(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON software(category)")
        
        conn.commit()
        conn.close()
    
    def _detect_category(self, name: str, path: str) -> str:
        """检测软件类别"""
        name_lower = name.lower()
        path_lower = path.lower()
        
        for category, keywords in CATEGORY_RULES.items():
            for keyword in keywords:
                if keyword in name_lower or keyword in path_lower:
                    return category
        
        return "unknown"
    
    def _generate_id(self, path: str) -> str:
        """生成软件ID"""
        import hashlib
        return hashlib.md5(path.encode()).hexdigest()[:12]
    
    def search(self, keyword: str) -> List[Dict]:
        """搜索软件"""
        results = []
        
        # 使用 Everything 搜索
        if self.everything.is_available():
            everything_results = self.everything.search(keyword, max_results=20)
            
            for result in everything_results:
                software_id = self._generate_id(result["path"])
                
                software_info = {
                    "id": software_id,
                    "name": result["name"],
                    "display_name": result["name"],
                    "path": result["path"],
                    "exe_name": Path(result["path"]).name,
                    "category": self._detect_category(result["name"], result["path"]),
                    "size_mb": round(result["size"] / (1024 * 1024), 2)
                }
                
                results.append(software_info)
                
                # 缓存结果
                self.software_cache[software_id] = software_info
        
        # 从数据库搜索
        db_results = self._search_db(keyword)
        
        # 合并结果（去重）
        existing_paths = {r["path"] for r in results}
        for db_result in db_results:
            if db_result["path"] not in existing_paths:
                results.append(db_result)
        
        return results
    
    def _search_db(self, keyword: str) -> List[Dict]:
        """从数据库搜索"""
        results = []
        
        try:
            conn = sqlite3.connect(str(SOFTWARE_DB))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM software 
                WHERE name LIKE ? OR display_name LIKE ? OR category LIKE ?
                ORDER BY use_count DESC
            """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
            
            for row in cursor.fetchall():
                results.append({
                    "id": row[0],
                    "name": row[1],
                    "display_name": row[2],
                    "path": row[3],
                    "exe_name": row[4],
                    "category": row[5],
                    "size_mb": row[6],
                    "discovered_at": row[7],
                    "last_used": row[8],
                    "use_count": row[9]
                })
            
            conn.close()
        except:
            pass
        
        return results
    
    def list_all(self, category: str = None) -> List[Dict]:
        """列出所有软件"""
        results = []
        
        try:
            conn = sqlite3.connect(str(SOFTWARE_DB))
            cursor = conn.cursor()
            
            if category:
                cursor.execute("""
                    SELECT * FROM software 
                    WHERE category = ?
                    ORDER BY use_count DESC, name
                """, (category,))
            else:
                cursor.execute("""
                    SELECT * FROM software 
                    ORDER BY category, use_count DESC, name
                """)
            
            for row in cursor.fetchall():
                results.append({
                    "id": row[0],
                    "name": row[1],
                    "display_name": row[2],
                    "path": row[3],
                    "exe_name": row[4],
                    "category": row[5],
                    "size_mb": row[6],
                    "discovered_at": row[7],
                    "last_used": row[8],
                    "use_count": row[9]
                })
            
            conn.close()
        except:
            pass
        
        return results
    
    def open_software(self, name: str) -> Dict:
        """打开软件"""
        # 搜索软件
        results = self.search(name)
        
        if not results:
            return {"success": False, "error": f"未找到软件: {name}"}
        
        # 使用第一个结果
        software = results[0]
        
        try:
            # 启动软件
            subprocess.Popen(
                [software["path"]],
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            # 更新使用记录
            self._update_usage(software["id"])
            
            return {
                "success": True,
                "software": software["name"],
                "path": software["path"],
                "category": software["category"]
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _update_usage(self, software_id: str):
        """更新使用记录"""
        try:
            conn = sqlite3.connect(str(SOFTWARE_DB))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO software (id, name, display_name, path, exe_name, category, size_mb, discovered_at, last_used, use_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                ON CONFLICT(id) DO UPDATE SET
                    use_count = use_count + 1,
                    last_used = ?
            """, (
                software_id,
                self.software_cache.get(software_id, {}).get("name", ""),
                self.software_cache.get(software_id, {}).get("display_name", ""),
                self.software_cache.get(software_id, {}).get("path", ""),
                self.software_cache.get(software_id, {}).get("exe_name", ""),
                self.software_cache.get(software_id, {}).get("category", ""),
                self.software_cache.get(software_id, {}).get("size_mb", 0),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
        except:
            pass
    
    def get_info(self, name: str) -> Optional[Dict]:
        """获取软件信息"""
        results = self.search(name)
        return results[0] if results else None
    
    def get_categories(self) -> List[str]:
        """获取所有类别"""
        try:
            conn = sqlite3.connect(str(SOFTWARE_DB))
            cursor = conn.cursor()
            
            cursor.execute("SELECT DISTINCT category FROM software ORDER BY category")
            categories = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return categories
        except:
            return list(CATEGORY_RULES.keys())

# ============================================================
# MCP 接口
# ============================================================
class MCPInterface:
    """MCP 接口"""
    
    def __init__(self):
        self.manager = SoftwareManager()
    
    def handle(self, request: Dict) -> Dict:
        """处理 MCP 请求"""
        action = request.get("action")
        params = request.get("params", {})
        
        if action == "search":
            keyword = params.get("keyword", "")
            results = self.manager.search(keyword)
            return {"success": True, "keyword": keyword, "count": len(results), "results": results}
        
        elif action == "list":
            category = params.get("category")
            results = self.manager.list_all(category)
            return {"success": True, "category": category, "count": len(results), "results": results}
        
        elif action == "open":
            name = params.get("name")
            return self.manager.open_software(name)
        
        elif action == "info":
            name = params.get("name")
            software = self.manager.get_info(name)
            if software:
                return {"success": True, "software": software}
            else:
                return {"success": False, "error": f"未找到软件: {name}"}
        
        elif action == "categories":
            categories = self.manager.get_categories()
            return {"success": True, "categories": categories}
        
        else:
            return {"success": False, "error": f"未知操作: {action}"}

# ============================================================
# 命令行接口
# ============================================================
def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1]
    manager = SoftwareManager()
    
    if cmd == "search":
        if len(sys.argv) < 3:
            print("用法: local_software.py search <keyword>")
            return
        
        keyword = sys.argv[2]
        print(f"搜索: {keyword}")
        
        if manager.everything.is_available():
            print(f"✓ 使用 Everything 搜索")
        else:
            print(f"⚠ Everything 不可用，使用数据库搜索")
        
        results = manager.search(keyword)
        
        print(f"\n找到 {len(results)} 个结果:")
        print("-" * 80)
        print(f"{'名称':<20} {'类别':<15} {'大小(MB)':<12} {'路径':<30}")
        print("-" * 80)
        
        for s in results[:20]:
            path_display = s["path"][:30] + "..." if len(s["path"]) > 30 else s["path"]
            print(f"{s['name']:<20} {s['category']:<15} {s['size_mb']:<12.1f} {path_display:<30}")
    
    elif cmd == "list":
        category = sys.argv[2] if len(sys.argv) > 2 else None
        results = manager.list_all(category)
        
        if category:
            print(f"类别 '{category}' 的软件 ({len(results)} 个):")
        else:
            print(f"所有软件 ({len(results)} 个):")
        
        print("-" * 80)
        print(f"{'名称':<20} {'类别':<15} {'使用次数':<10} {'路径':<30}")
        print("-" * 80)
        
        current_category = ""
        for s in results:
            if not category and s["category"] != current_category:
                current_category = s["category"]
                print(f"\n[{current_category}]")
            
            path_display = s["path"][:30] + "..." if len(s["path"]) > 30 else s["path"]
            print(f"{s['name']:<20} {s['category']:<15} {s['use_count']:<10} {path_display:<30}")
    
    elif cmd == "open":
        if len(sys.argv) < 3:
            print("用法: local_software.py open <name>")
            return
        
        name = sys.argv[2]
        result = manager.open_software(name)
        
        if result.get("success"):
            print(f"✓ 已启动: {result['software']}")
            print(f"  路径: {result['path']}")
        else:
            print(f"✗ 启动失败: {result.get('error')}")
    
    elif cmd == "info":
        if len(sys.argv) < 3:
            print("用法: local_software.py info <name>")
            return
        
        name = sys.argv[2]
        software = manager.get_info(name)
        
        if software:
            print(f"软件信息: {software['name']}")
            print("-" * 40)
            print(f"显示名称: {software['display_name']}")
            print(f"类别: {software['category']}")
            print(f"路径: {software['path']}")
            print(f"大小: {software['size_mb']:.2f} MB")
            print(f"使用次数: {software.get('use_count', 0)}")
        else:
            print(f"未找到软件: {name}")
    
    elif cmd == "mcp":
        # MCP 服务器模式
        print("本地软件管理器 MCP 服务器已启动")
        print("支持操作: search, list, open, info, categories")
        
        mcp = MCPInterface()
        
        import select
        
        while True:
            if select.select([sys.stdin], [], [], 0.1)[0]:
                line = sys.stdin.readline()
                if not line:
                    break
                
                try:
                    request = json.loads(line)
                    response = mcp.handle(request)
                    print(json.dumps(response, ensure_ascii=False))
                    sys.stdout.flush()
                except json.JSONDecodeError:
                    print(json.dumps({"success": False, "error": "无效的JSON"}))
                    sys.stdout.flush()
    
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)

if __name__ == "__main__":
    main()
