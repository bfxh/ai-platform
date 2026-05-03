#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能自动翻译工具

功能：
- 自动检测文件中的外文内容
- 支持多种文件格式（代码文件、文档、配置文件等）
- 智能识别需要翻译的字符串、注释、文档
- 保持代码结构，只翻译内容
- 支持批量翻译整个项目
- 翻译缓存，避免重复翻译
- 支持多种翻译服务（本地/在线）

用法：
    python auto_translate.py scan <path>              # 扫描需要翻译的内容
    python auto_translate.py translate <file>         # 翻译单个文件
    python auto_translate.py translate-dir <path>     # 批量翻译目录
    python auto_translate.py config                   # 配置翻译设置
    python auto_translate.py cache                    # 管理翻译缓存
    python auto_translate.py detect <text>            # 检测语言

MCP调用：
    {"tool": "auto_translate", "action": "translate", "params": {...}}
"""

import json
import sys
import os
import re
import hashlib
import sqlite3
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict

# ============================================================
# 配置
# ============================================================
AI_PATH = Path("/python")
MCP_PATH = AI_PATH / "MCP"
CONFIG_PATH = AI_PATH / "MCP_Skills"
CACHE_PATH = AI_PATH / "Temp" / "translate_cache"
CACHE_PATH.mkdir(parents=True, exist_ok=True)

# 翻译缓存数据库
TRANSLATE_DB = CONFIG_PATH / "auto_translate.db"

# 语言检测模式
LANGUAGE_PATTERNS = {
    "en": re.compile(r'^[a-zA-Z\s\.,!?;:\-\(\)\[\]{}"\'\d]+$'),
    "zh": re.compile(r'[\u4e00-\u9fff]'),
    "ja": re.compile(r'[\u3040-\u309f\u30a0-\u30ff]'),
    "ko": re.compile(r'[\uac00-\ud7af]'),
}

# 文件类型配置
FILE_CONFIG = {
    ".py": {
        "type": "python",
        "string_patterns": [
            (r'"""(.*?)"""', 'triple_double'),
            (r"'''(.*?)'''", 'triple_single'),
            (r'"([^"\n]*)"', 'double'),
            (r"'([^'\n]*)'", 'single'),
        ],
        "comment_patterns": [
            (r'#(.*)$', 'line'),
        ],
        "doc_patterns": [
            (r'"""(.*?)"""', 'docstring'),
        ]
    },
    ".js": {
        "type": "javascript",
        "string_patterns": [
            (r'`(.*?)`', 'template'),
            (r'"([^"\n]*)"', 'double'),
            (r"'([^'\n]*)'", 'single'),
        ],
        "comment_patterns": [
            (r'//(.*)$', 'line'),
            (r'/\*(.*?)\*/', 'block'),
        ]
    },
    ".html": {
        "type": "html",
        "string_patterns": [
            (r'>([^<]*?)</', 'text'),
            (r'alt="([^"]*)"', 'alt'),
            (r'title="([^"]*)"', 'title'),
            (r'placeholder="([^"]*)"', 'placeholder'),
        ],
        "comment_patterns": [
            (r'<!--(.*?)-->', 'html'),
        ]
    },
    ".md": {
        "type": "markdown",
        "string_patterns": [
            (r'^([^#\n\-\*\|\[\]`].*)$', 'text'),
        ],
        "code_block_pattern": r'```[\s\S]*?```',
    },
    ".json": {
        "type": "json",
        "string_patterns": [
            (r'"([^"\n]*)"\s*:', 'key'),
            (r':\s*"([^"\n]*)"', 'value'),
        ]
    },
    ".yaml": {
        "type": "yaml",
        "string_patterns": [
            (r'^([^#\n:]+):\s*([^#\n]+)$', 'pair'),
        ]
    },
    ".txt": {
        "type": "text",
        "string_patterns": [
            (r'^(.*)$', 'line'),
        ]
    }
}

# 翻译服务配置
TRANSLATE_SERVICES = {
    "local": {
        "name": "本地翻译",
        "enabled": True,
        "description": "使用本地词典进行简单翻译"
    },
    "google": {
        "name": "Google 翻译",
        "enabled": False,
        "description": "使用 Google Translate API",
        "api_key": ""
    },
    "baidu": {
        "name": "百度翻译",
        "enabled": False,
        "description": "使用百度翻译 API",
        "app_id": "",
        "secret_key": ""
    },
    "tencent": {
        "name": "腾讯翻译",
        "enabled": False,
        "description": "使用腾讯翻译 API",
        "secret_id": "",
        "secret_key": ""
    }
}

# 简单本地词典
LOCAL_DICT = {
    "hello": "你好",
    "world": "世界",
    "file": "文件",
    "folder": "文件夹",
    "directory": "目录",
    "path": "路径",
    "name": "名称",
    "size": "大小",
    "type": "类型",
    "date": "日期",
    "time": "时间",
    "error": "错误",
    "warning": "警告",
    "success": "成功",
    "failed": "失败",
    "loading": "加载中",
    "processing": "处理中",
    "completed": "已完成",
    "cancel": "取消",
    "confirm": "确认",
    "save": "保存",
    "delete": "删除",
    "edit": "编辑",
    "create": "创建",
    "open": "打开",
    "close": "关闭",
    "search": "搜索",
    "find": "查找",
    "replace": "替换",
    "copy": "复制",
    "paste": "粘贴",
    "cut": "剪切",
    "undo": "撤销",
    "redo": "重做",
    "settings": "设置",
    "options": "选项",
    "help": "帮助",
    "about": "关于",
    "exit": "退出",
    "quit": "退出",
    "start": "开始",
    "stop": "停止",
    "pause": "暂停",
    "resume": "继续",
    "next": "下一步",
    "previous": "上一步",
    "back": "返回",
    "forward": "前进",
    "up": "向上",
    "down": "向下",
    "left": "向左",
    "right": "向右",
    "top": "顶部",
    "bottom": "底部",
    "center": "中心",
    "middle": "中间",
    "first": "第一",
    "last": "最后",
    "new": "新建",
    "old": "旧的",
    "all": "全部",
    "none": "无",
    "some": "部分",
    "many": "许多",
    "few": "少数",
    "more": "更多",
    "less": "更少",
    "most": "大多数",
    "least": "最少",
    "other": "其他",
    "another": "另一个",
    "same": "相同",
    "different": "不同",
    "similar": "相似",
    "equal": "相等",
    "greater": "大于",
    "less_than": "小于",
    "between": "之间",
    "before": "之前",
    "after": "之后",
    "during": "期间",
    "while": "当...时",
    "until": "直到",
    "since": "自从",
    "ago": "以前",
    "later": "稍后",
    "soon": "很快",
    "now": "现在",
    "today": "今天",
    "yesterday": "昨天",
    "tomorrow": "明天",
    "morning": "早上",
    "afternoon": "下午",
    "evening": "晚上",
    "night": "夜晚",
    "day": "天",
    "week": "周",
    "month": "月",
    "year": "年",
    "hour": "小时",
    "minute": "分钟",
    "second": "秒",
    "millisecond": "毫秒",
}

# ============================================================
# 翻译缓存管理
# ============================================================
class TranslateCache:
    """翻译缓存管理"""
    
    def __init__(self):
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        CONFIG_PATH.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(TRANSLATE_DB))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS translations (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                source_lang TEXT,
                target_lang TEXT NOT NULL,
                translation TEXT NOT NULL,
                service TEXT,
                created_at TEXT,
                use_count INTEGER DEFAULT 1
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_source ON translations(source)
        """)
        
        conn.commit()
        conn.close()
    
    def get(self, source: str, target_lang: str = "zh") -> Optional[str]:
        """获取缓存的翻译"""
        source_hash = hashlib.md5(source.encode()).hexdigest()
        
        conn = sqlite3.connect(str(TRANSLATE_DB))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT translation FROM translations 
            WHERE id = ? AND target_lang = ?
        """, (source_hash, target_lang))
        
        result = cursor.fetchone()
        
        if result:
            # 更新使用次数
            cursor.execute("""
                UPDATE translations SET use_count = use_count + 1 
                WHERE id = ? AND target_lang = ?
            """, (source_hash, target_lang))
            conn.commit()
        
        conn.close()
        
        return result[0] if result else None
    
    def set(self, source: str, translation: str, target_lang: str = "zh", service: str = "local"):
        """设置缓存"""
        source_hash = hashlib.md5(source.encode()).hexdigest()
        
        conn = sqlite3.connect(str(TRANSLATE_DB))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO translations 
            (id, source, target_lang, translation, service, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            source_hash,
            source,
            target_lang,
            translation,
            service,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def clear(self):
        """清空缓存"""
        conn = sqlite3.connect(str(TRANSLATE_DB))
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM translations")
        
        conn.commit()
        conn.close()
    
    def stats(self) -> Dict:
        """获取缓存统计"""
        conn = sqlite3.connect(str(TRANSLATE_DB))
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*), SUM(use_count) FROM translations")
        count, total_uses = cursor.fetchone()
        
        cursor.execute("SELECT service, COUNT(*) FROM translations GROUP BY service")
        services = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            "total_entries": count or 0,
            "total_uses": total_uses or 0,
            "services": services
        }

# ============================================================
# 翻译引擎
# ============================================================
class TranslateEngine:
    """翻译引擎"""
    
    def __init__(self):
        self.cache = TranslateCache()
        self.service = "local"
    
    def detect_language(self, text: str) -> str:
        """检测语言"""
        if LANGUAGE_PATTERNS["zh"].search(text):
            return "zh"
        elif LANGUAGE_PATTERNS["ja"].search(text):
            return "ja"
        elif LANGUAGE_PATTERNS["ko"].search(text):
            return "ko"
        elif LANGUAGE_PATTERNS["en"].match(text.strip()):
            return "en"
        else:
            return "unknown"
    
    def translate(self, text: str, target_lang: str = "zh", source_lang: str = None) -> str:
        """翻译文本"""
        if not text or not text.strip():
            return text
        
        text = text.strip()
        
        # 检测源语言
        if not source_lang:
            source_lang = self.detect_language(text)
        
        # 如果目标语言相同，无需翻译
        if source_lang == target_lang:
            return text
        
        # 检查缓存
        cached = self.cache.get(text, target_lang)
        if cached:
            return cached
        
        # 根据服务选择翻译方式
        if self.service == "local":
            translation = self._local_translate(text, target_lang)
        else:
            translation = self._online_translate(text, target_lang, source_lang)
        
        # 缓存结果
        self.cache.set(text, translation, target_lang, self.service)
        
        return translation
    
    def _local_translate(self, text: str, target_lang: str) -> str:
        """本地翻译"""
        # 简单词典匹配
        words = text.lower().split()
        translated_words = []
        
        for word in words:
            # 去除标点
            clean_word = re.sub(r'[^\w\s]', '', word)
            
            if clean_word in LOCAL_DICT:
                translated_words.append(LOCAL_DICT[clean_word])
            else:
                translated_words.append(word)
        
        translated = " ".join(translated_words)
        
        # 如果词典没有匹配，保留原文并添加标记
        if translated == text:
            return text
        
        return translated
    
    def _online_translate(self, text: str, target_lang: str, source_lang: str) -> str:
        """在线翻译（预留接口）"""
        # TODO: 实现在线翻译 API 调用
        return self._local_translate(text, target_lang)
    
    def translate_batch(self, texts: List[str], target_lang: str = "zh") -> List[str]:
        """批量翻译"""
        return [self.translate(t, target_lang) for t in texts]

# ============================================================
# 文件扫描器
# ============================================================
class FileScanner:
    """文件扫描器"""
    
    def __init__(self):
        self.engine = TranslateEngine()
    
    def scan_file(self, file_path: Path) -> List[Dict]:
        """扫描文件中的可翻译内容"""
        if not file_path.exists():
            return []
        
        ext = file_path.suffix.lower()
        
        if ext not in FILE_CONFIG:
            return []
        
        config = FILE_CONFIG[ext]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            return []
        
        translatable = []
        
        # 扫描字符串
        if "string_patterns" in config:
            for pattern, pattern_type in config["string_patterns"]:
                for match in re.finditer(pattern, content, re.MULTILINE):
                    text = match.group(1) if match.groups() else match.group(0)
                    
                    if self._should_translate(text):
                        translatable.append({
                            "type": "string",
                            "subtype": pattern_type,
                            "text": text,
                            "position": match.span(),
                            "line": content[:match.start()].count('\n') + 1
                        })
        
        # 扫描注释
        if "comment_patterns" in config:
            for pattern, pattern_type in config["comment_patterns"]:
                for match in re.finditer(pattern, content, re.MULTILINE):
                    text = match.group(1) if match.groups() else match.group(0)
                    
                    if self._should_translate(text):
                        translatable.append({
                            "type": "comment",
                            "subtype": pattern_type,
                            "text": text,
                            "position": match.span(),
                            "line": content[:match.start()].count('\n') + 1
                        })
        
        return translatable
    
    def _should_translate(self, text: str) -> bool:
        """判断是否需要翻译"""
        if not text or len(text.strip()) < 2:
            return False
        
        text = text.strip()
        
        # 检测语言
        lang = self.engine.detect_language(text)
        
        # 如果是中文，不需要翻译
        if lang == "zh":
            return False
        
        # 如果主要是英文，需要翻译
        if lang == "en":
            # 排除纯数字、纯符号
            if re.match(r'^[\d\s\W]+$', text):
                return False
            return True
        
        # 其他语言也翻译
        if lang in ["ja", "ko"]:
            return True
        
        return False
    
    def scan_directory(self, dir_path: Path, recursive: bool = True) -> Dict[str, List[Dict]]:
        """扫描目录"""
        results = {}
        
        if not dir_path.exists():
            return results
        
        pattern = "**/*" if recursive else "*"
        
        for file_path in dir_path.glob(pattern):
            if not file_path.is_file():
                continue
            
            if file_path.suffix.lower() not in FILE_CONFIG:
                continue
            
            translatable = self.scan_file(file_path)
            
            if translatable:
                results[str(file_path)] = translatable
        
        return results

# ============================================================
# 文件翻译器
# ============================================================
class FileTranslator:
    """文件翻译器"""
    
    def __init__(self):
        self.scanner = FileScanner()
        self.engine = TranslateEngine()
    
    def translate_file(self, file_path: Path, output_path: Path = None, dry_run: bool = False) -> Dict:
        """翻译文件"""
        if not file_path.exists():
            return {"success": False, "error": "文件不存在"}
        
        # 扫描可翻译内容
        translatable = self.scanner.scan_file(file_path)
        
        if not translatable:
            return {"success": True, "translated": 0, "message": "没有需要翻译的内容"}
        
        print(f"发现 {len(translatable)} 处可翻译内容")
        
        if dry_run:
            return {
                "success": True,
                "translated": 0,
                "dry_run": True,
                "items": translatable
            }
        
        # 读取文件
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {"success": False, "error": f"读取文件失败: {e}"}
        
        # 按位置倒序排序（从后往前替换，避免位置变化）
        translatable.sort(key=lambda x: x["position"][0], reverse=True)
        
        translated_count = 0
        
        for item in translatable:
            original = item["text"]
            translated = self.engine.translate(original)
            
            if translated != original:
                start, end = item["position"]
                # 替换内容
                content = content[:start] + content[start:end].replace(original, translated) + content[end:]
                translated_count += 1
                print(f"  翻译: '{original}' -> '{translated}'")
        
        # 保存文件
        output = output_path or file_path
        
        try:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "translated": translated_count,
                "output": str(output)
            }
        
        except Exception as e:
            return {"success": False, "error": f"保存文件失败: {e}"}
    
    def translate_directory(self, dir_path: Path, output_dir: Path = None, dry_run: bool = False) -> Dict:
        """批量翻译目录"""
        if not dir_path.exists():
            return {"success": False, "error": "目录不存在"}
        
        # 扫描所有文件
        results = self.scanner.scan_directory(dir_path)
        
        if not results:
            return {"success": True, "translated": 0, "message": "没有发现需要翻译的文件"}
        
        print(f"发现 {len(results)} 个文件需要翻译")
        
        if dry_run:
            return {
                "success": True,
                "translated": 0,
                "dry_run": True,
                "files": list(results.keys())
            }
        
        # 翻译每个文件
        total_translated = 0
        success_count = 0
        
        for file_path_str, items in results.items():
            file_path = Path(file_path_str)
            
            if output_dir:
                rel_path = file_path.relative_to(dir_path)
                output_path = output_dir / rel_path
                output_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                output_path = file_path
            
            result = self.translate_file(file_path, output_path)
            
            if result.get("success"):
                total_translated += result.get("translated", 0)
                success_count += 1
        
        return {
            "success": True,
            "files_processed": len(results),
            "files_success": success_count,
            "total_translated": total_translated
        }

# ============================================================
# MCP 接口
# ============================================================
class MCPInterface:
    """MCP 接口"""
    
    def __init__(self):
        self.translator = FileTranslator()
        self.engine = TranslateEngine()
        self.cache = TranslateCache()
    
    def handle(self, request: Dict) -> Dict:
        """处理 MCP 请求"""
        action = request.get("action")
        params = request.get("params", {})
        
        if action == "scan":
            path = Path(params.get("path", "."))
            results = self.translator.scanner.scan_directory(path)
            return {
                "success": True,
                "files": len(results),
                "results": results
            }
        
        elif action == "translate":
            file_path = Path(params["file"])
            output_path = Path(params["output"]) if params.get("output") else None
            dry_run = params.get("dry_run", False)
            return self.translator.translate_file(file_path, output_path, dry_run)
        
        elif action == "translate_dir":
            dir_path = Path(params["dir"])
            output_dir = Path(params["output"]) if params.get("output") else None
            dry_run = params.get("dry_run", False)
            return self.translator.translate_directory(dir_path, output_dir, dry_run)
        
        elif action == "detect":
            text = params.get("text", "")
            lang = self.engine.detect_language(text)
            return {
                "success": True,
                "text": text,
                "language": lang
            }
        
        elif action == "translate_text":
            text = params.get("text", "")
            target_lang = params.get("target_lang", "zh")
            translation = self.engine.translate(text, target_lang)
            return {
                "success": True,
                "original": text,
                "translation": translation,
                "target_lang": target_lang
            }
        
        elif action == "cache_stats":
            stats = self.cache.stats()
            return {"success": True, "stats": stats}
        
        elif action == "cache_clear":
            self.cache.clear()
            return {"success": True, "message": "缓存已清空"}
        
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
    translator = FileTranslator()
    engine = TranslateEngine()
    cache = TranslateCache()
    
    if cmd == "scan":
        if len(sys.argv) < 3:
            print("用法: auto_translate.py scan <path>")
            return
        
        path = Path(sys.argv[2])
        print(f"扫描: {path}")
        
        results = translator.scanner.scan_directory(path)
        
        print(f"\n发现 {len(results)} 个文件需要翻译:")
        print("-" * 80)
        
        for file_path, items in results.items():
            print(f"\n{file_path}:")
            for item in items[:5]:  # 最多显示5个
                print(f"  行 {item['line']}: [{item['type']}] {item['text'][:50]}...")
            if len(items) > 5:
                print(f"  ... 还有 {len(items) - 5} 处")
    
    elif cmd == "translate":
        if len(sys.argv) < 3:
            print("用法: auto_translate.py translate <file> [output]")
            return
        
        file_path = Path(sys.argv[2])
        output_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None
        
        print(f"翻译文件: {file_path}")
        
        result = translator.translate_file(file_path, output_path)
        
        if result.get("success"):
            print(f"✓ 翻译完成: {result.get('translated', 0)} 处")
            if output_path:
                print(f"  输出: {output_path}")
        else:
            print(f"✗ 翻译失败: {result.get('error')}")
    
    elif cmd == "translate-dir":
        if len(sys.argv) < 3:
            print("用法: auto_translate.py translate-dir <path> [output]")
            return
        
        dir_path = Path(sys.argv[2])
        output_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else None
        
        print(f"翻译目录: {dir_path}")
        
        result = translator.translate_directory(dir_path, output_dir)
        
        if result.get("success"):
            print(f"✓ 批量翻译完成")
            print(f"  处理文件: {result.get('files_processed', 0)}")
            print(f"  成功: {result.get('files_success', 0)}")
            print(f"  翻译条目: {result.get('total_translated', 0)}")
        else:
            print(f"✗ 翻译失败: {result.get('error')}")
    
    elif cmd == "detect":
        if len(sys.argv) < 3:
            print("用法: auto_translate.py detect <text>")
            return
        
        text = sys.argv[2]
        lang = engine.detect_language(text)
        
        lang_names = {
            "zh": "中文",
            "en": "英文",
            "ja": "日文",
            "ko": "韩文",
            "unknown": "未知"
        }
        
        print(f"文本: {text}")
        print(f"语言: {lang_names.get(lang, lang)}")
    
    elif cmd == "cache":
        stats = cache.stats()
        print("翻译缓存统计:")
        print(f"  总条目: {stats['total_entries']}")
        print(f"  总使用: {stats['total_uses']}")
        print(f"  服务分布: {stats['services']}")
    
    elif cmd == "mcp":
        # MCP 服务器模式
        print("自动翻译 MCP 服务器已启动")
        print("支持操作: scan, translate, translate_dir, detect, translate_text, cache_stats, cache_clear")
        
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
