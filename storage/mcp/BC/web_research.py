#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络研究工具 - 搜索 + 抓取 + 分析 + 下载

功能：
- 多源搜索（Google/Bing/百度）
- 网页内容抓取
- 内容分析与摘要
- 自动下载资源
- 生成研究报告
- 翻译外文内容

用法：
    python web_research.py search <query>              # 搜索
    python web_research.py fetch <url>                 # 抓取页面
    python web_research.py analyze <url>               # 分析页面
    python web_research.py research <topic>            # 完整研究
    python web_research.py download <url>              # 下载资源
    python web_research.py report <topic>              # 生成报告

MCP调用：
    {"tool": "web_research", "action": "research", "params": {"topic": "..."}}
"""

import json
import sys
import os
import re
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import html

# ============================================================
# 配置
# ============================================================
AI_PATH = Path("/python")
MCP_PATH = AI_PATH / "MCP"
RESEARCH_PATH = AI_PATH / "Research"
RESEARCH_PATH.mkdir(parents=True, exist_ok=True)

# 搜索引擎配置
SEARCH_ENGINES = {
    "google": {
        "url": "https://www.google.com/search",
        "param": "q",
    },
    "bing": {
        "url": "https://www.bing.com/search",
        "param": "q",
    },
    "baidu": {
        "url": "https://www.baidu.com/s",
        "param": "wd",
    }
}

# 用户代理
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# ============================================================
# 搜索结果
# ============================================================
@dataclass
class SearchResult:
    """搜索结果"""
    title: str
    url: str
    snippet: str
    source: str

# ============================================================
# 网络研究工具
# ============================================================
class WebResearch:
    """网络研究工具"""
    
    def __init__(self):
        self.results: List[SearchResult] = []
    
    def search(self, query: str, engine: str = "google", num_results: int = 10) -> Dict:
        """搜索"""
        try:
            # 构建搜索 URL
            if engine not in SEARCH_ENGINES:
                return {"success": False, "error": f"不支持的搜索引擎: {engine}"}
            
            config = SEARCH_ENGINES[engine]
            params = urllib.parse.urlencode({config["param"]: query})
            url = f"{config['url']}?{params}"
            
            # 发送请求
            headers = {"User-Agent": USER_AGENT}
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                html_content = response.read().decode('utf-8', errors='ignore')
            
            # 解析结果（简化版）
            results = self._parse_search_results(html_content, engine)
            
            return {
                "success": True,
                "query": query,
                "engine": engine,
                "results_count": len(results),
                "results": results[:num_results]
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _parse_search_results(self, html_content: str, engine: str) -> List[Dict]:
        """解析搜索结果"""
        results = []
        
        # 简单的正则提取（实际应用中应该使用 BeautifulSoup）
        if engine == "google":
            # 提取链接和标题
            pattern = r'<a href="/url\?q=([^"]+)"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, html_content)
            
            for url, title in matches[:10]:
                if url.startswith('http'):
                    results.append({
                        "title": html.unescape(title),
                        "url": urllib.parse.unquote(url),
                        "snippet": "",
                        "source": engine
                    })
        
        return results
    
    def fetch(self, url: str) -> Dict:
        """抓取网页"""
        try:
            headers = {"User-Agent": USER_AGENT}
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read()
                charset = response.headers.get_content_charset() or 'utf-8'
                html_content = content.decode(charset, errors='ignore')
            
            # 提取文本内容
            text_content = self._extract_text(html_content)
            
            # 提取标题
            title = self._extract_title(html_content)
            
            # 提取链接
            links = self._extract_links(html_content, url)
            
            # 提取图片
            images = self._extract_images(html_content, url)
            
            return {
                "success": True,
                "url": url,
                "title": title,
                "content": text_content[:5000],  # 限制长度
                "links": links[:20],
                "images": images[:10],
                "size": len(html_content)
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _extract_text(self, html_content: str) -> str:
        """提取文本内容"""
        # 移除 script 和 style
        text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        
        # 移除 HTML 标签
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # 解码 HTML 实体
        text = html.unescape(text)
        
        # 清理空白
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _extract_title(self, html_content: str) -> str:
        """提取标题"""
        match = re.search(r'<title[^>]*>([^<]*)</title>', html_content, re.IGNORECASE)
        return html.unescape(match.group(1)) if match else ""
    
    def _extract_links(self, html_content: str, base_url: str) -> List[Dict]:
        """提取链接"""
        links = []
        pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>'
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        
        for href, text in matches[:20]:
            if href.startswith('http'):
                links.append({
                    "url": href,
                    "text": html.unescape(text.strip())[:100]
                })
        
        return links
    
    def _extract_images(self, html_content: str, base_url: str) -> List[Dict]:
        """提取图片"""
        images = []
        pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        
        for src in matches[:10]:
            if src.startswith('http'):
                images.append({"url": src})
        
        return images
    
    def analyze(self, url: str) -> Dict:
        """分析网页"""
        # 抓取页面
        fetch_result = self.fetch(url)
        
        if not fetch_result.get("success"):
            return fetch_result
        
        content = fetch_result["content"]
        
        # 分析内容
        analysis = {
            "word_count": len(content.split()),
            "char_count": len(content),
            "has_code": bool(re.search(r'(def |class |function |var |const )', content)),
            "has_links": len(fetch_result.get("links", [])) > 0,
            "has_images": len(fetch_result.get("images", [])) > 0,
            "language": self._detect_language(content),
            "topics": self._extract_topics(content),
            "summary": self._generate_summary(content)
        }
        
        return {
            "success": True,
            "url": url,
            "title": fetch_result["title"],
            "analysis": analysis,
            "fetch_result": fetch_result
        }
    
    def _detect_language(self, content: str) -> str:
        """检测语言"""
        # 简单的语言检测
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
        total_chars = len(content)
        
        if chinese_chars / max(total_chars, 1) > 0.1:
            return "zh"
        return "en"
    
    def _extract_topics(self, content: str) -> List[str]:
        """提取主题"""
        # 简单的关键词提取
        words = re.findall(r'\b[A-Za-z]{4,}\b', content.lower())
        word_freq = {}
        
        for word in words:
            if word not in ['this', 'that', 'with', 'from', 'they', 'have', 'were', 'been']:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 返回频率最高的词
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:5]]
    
    def _generate_summary(self, content: str, max_length: int = 200) -> str:
        """生成摘要"""
        sentences = re.split(r'[.!?。！？]+', content)
        
        if sentences:
            summary = sentences[0].strip()
            if len(summary) > max_length:
                summary = summary[:max_length] + "..."
            return summary
        
        return content[:max_length] + "..." if len(content) > max_length else content
    
    def research(self, topic: str, depth: int = 2) -> Dict:
        """完整研究"""
        print(f"开始研究主题: {topic}")
        
        # 1. 搜索
        search_result = self.search(topic, num_results=10)
        
        if not search_result.get("success"):
            return search_result
        
        # 2. 抓取前几个结果
        detailed_results = []
        for result in search_result["results"][:depth]:
            print(f"  分析: {result['title']}")
            
            fetch_result = self.fetch(result['url'])
            if fetch_result.get("success"):
                analyze_result = self.analyze(result['url'])
                detailed_results.append({
                    "search": result,
                    "fetch": fetch_result,
                    "analysis": analyze_result.get("analysis", {})
                })
        
        # 3. 生成研究摘要
        summary = self._generate_research_summary(topic, detailed_results)
        
        return {
            "success": True,
            "topic": topic,
            "search_results": search_result,
            "detailed_analysis": detailed_results,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_research_summary(self, topic: str, results: List[Dict]) -> Dict:
        """生成研究摘要"""
        all_topics = []
        all_summaries = []
        
        for result in results:
            if "analysis" in result:
                all_topics.extend(result["analysis"].get("topics", []))
                all_summaries.append(result["analysis"].get("summary", ""))
        
        # 统计主题频率
        topic_freq = {}
        for t in all_topics:
            topic_freq[t] = topic_freq.get(t, 0) + 1
        
        top_topics = sorted(topic_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "key_topics": [t[0] for t in top_topics],
            "sources_analyzed": len(results),
            "brief": " ".join(all_summaries[:3]) if all_summaries else ""
        }
    
    def download_resource(self, url: str, output_dir: str = None) -> Dict:
        """下载资源"""
        try:
            if output_dir is None:
                output_dir = RESEARCH_PATH / "downloads"
            else:
                output_dir = Path(output_dir)
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 获取文件名
            parsed = urllib.parse.urlparse(url)
            filename = Path(parsed.path).name or "download"
            
            output_path = output_dir / filename
            
            # 下载
            headers = {"User-Agent": USER_AGENT}
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=60) as response:
                with open(output_path, 'wb') as f:
                    f.write(response.read())
            
            return {
                "success": True,
                "url": url,
                "saved_to": str(output_path),
                "size": output_path.stat().st_size
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_report(self, topic: str, research_result: Dict) -> Dict:
        """生成研究报告"""
        try:
            report_file = RESEARCH_PATH / f"{topic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(f"# 研究报告: {topic}\n\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # 摘要
                summary = research_result.get("summary", {})
                f.write("## 摘要\n\n")
                f.write(f"**关键主题**: {', '.join(summary.get('key_topics', []))}\n\n")
                f.write(f"**分析来源**: {summary.get('sources_analyzed', 0)} 个\n\n")
                f.write(f"**简介**: {summary.get('brief', '')}\n\n")
                
                # 详细结果
                f.write("## 详细分析\n\n")
                for i, result in enumerate(research_result.get("detailed_analysis", []), 1):
                    search = result.get("search", {})
                    analysis = result.get("analysis", {})
                    
                    f.write(f"### {i}. {search.get('title', 'Unknown')}\n\n")
                    f.write(f"- **URL**: {search.get('url', '')}\n")
                    f.write(f"- **词数**: {analysis.get('word_count', 0)}\n")
                    f.write(f"- **语言**: {analysis.get('language', 'unknown')}\n")
                    f.write(f"- **主题**: {', '.join(analysis.get('topics', []))}\n\n")
                    f.write(f"**摘要**: {analysis.get('summary', '')}\n\n")
                
                # 搜索原始结果
                f.write("## 搜索结果\n\n")
                for result in research_result.get("search_results", {}).get("results", []):
                    f.write(f"- [{result.get('title', '')}]({result.get('url', '')})\n")
                
                f.write("\n---\n\n")
                f.write("*报告由 AI Web Research 工具生成*\n")
            
            return {
                "success": True,
                "report_file": str(report_file),
                "topic": topic
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}

# ============================================================
# MCP 接口
# ============================================================
class MCPInterface:
    """MCP 接口"""
    
    def __init__(self):
        self.research = WebResearch()
    
    def handle(self, request: Dict) -> Dict:
        """处理 MCP 请求"""
        action = request.get("action")
        params = request.get("params", {})
        
        if action == "search":
            query = params.get("query")
            engine = params.get("engine", "google")
            num = params.get("num", 10)
            return self.research.search(query, engine, num)
        
        elif action == "fetch":
            url = params.get("url")
            return self.research.fetch(url)
        
        elif action == "analyze":
            url = params.get("url")
            return self.research.analyze(url)
        
        elif action == "research":
            topic = params.get("topic")
            depth = params.get("depth", 2)
            return self.research.research(topic, depth)
        
        elif action == "download":
            url = params.get("url")
            output_dir = params.get("output_dir")
            return self.research.download_resource(url, output_dir)
        
        elif action == "report":
            topic = params.get("topic")
            research_result = params.get("research_result")
            return self.research.generate_report(topic, research_result)
        
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
    research = WebResearch()
    
    if cmd == "search":
        if len(sys.argv) < 3:
            print("用法: web_research.py search <query> [engine]")
            return
        
        query = sys.argv[2]
        engine = sys.argv[3] if len(sys.argv) > 3 else "google"
        
        result = research.search(query, engine)
        
        if result.get("success"):
            print(f"搜索结果: {result['query']}")
            print("=" * 60)
            for i, r in enumerate(result["results"], 1):
                print(f"\n{i}. {r['title']}")
                print(f"   URL: {r['url']}")
        else:
            print(f"搜索失败: {result.get('error')}")
    
    elif cmd == "fetch":
        if len(sys.argv) < 3:
            print("用法: web_research.py fetch <url>")
            return
        
        url = sys.argv[2]
        result = research.fetch(url)
        
        if result.get("success"):
            print(f"页面: {result['title']}")
            print(f"URL: {result['url']}")
            print("=" * 60)
            print(f"\n内容:\n{result['content'][:1000]}...")
        else:
            print(f"抓取失败: {result.get('error')}")
    
    elif cmd == "analyze":
        if len(sys.argv) < 3:
            print("用法: web_research.py analyze <url>")
            return
        
        url = sys.argv[2]
        result = research.analyze(url)
        
        if result.get("success"):
            print(f"分析: {result['title']}")
            print("=" * 60)
            analysis = result["analysis"]
            print(f"\n词数: {analysis['word_count']}")
            print(f"语言: {analysis['language']}")
            print(f"主题: {', '.join(analysis['topics'])}")
            print(f"\n摘要: {analysis['summary']}")
        else:
            print(f"分析失败: {result.get('error')}")
    
    elif cmd == "research":
        if len(sys.argv) < 3:
            print("用法: web_research.py research <topic>")
            return
        
        topic = sys.argv[2]
        result = research.research(topic)
        
        if result.get("success"):
            print(f"研究完成: {result['topic']}")
            print("=" * 60)
            summary = result["summary"]
            print(f"\n关键主题: {', '.join(summary['key_topics'])}")
            print(f"分析来源: {summary['sources_analyzed']}")
            print(f"\n简介: {summary['brief'][:200]}...")
        else:
            print(f"研究失败: {result.get('error')}")
    
    elif cmd == "mcp":
        # MCP 服务器模式
        print("网络研究工具 MCP 已启动")
        
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
