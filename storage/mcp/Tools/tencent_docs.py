#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯离线文档管理器

用法:
  python /python\MCP\tencent_docs.py init
  python /python\MCP\tencent_docs.py crawl --max-pages 1200 --per-product 220
  python /python\MCP\tencent_docs.py search 微信支付 回调签名
  python /python\MCP\tencent_docs.py status
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import hashlib
from collections import defaultdict, deque
from datetime import datetime
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

AI_DIR = Path("/python")
BASE_DIR = AI_DIR / "docs" / "tencent"
MANIFEST_PATH = BASE_DIR / "manifest.json"
INDEX_PATH = BASE_DIR / "index.jsonl"
README_PATH = BASE_DIR / "README.md"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0 Safari/537.36 TencentDocsOfflineCrawler/1.0"
TRACKING_QUERY_KEYS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "spm", "from", "scene", "source", "sessionid", "share_token",
}
SKIP_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico",
    ".css", ".js", ".mjs", ".woff", ".woff2", ".ttf", ".eot",
    ".pdf", ".zip", ".rar", ".7z", ".exe", ".apk", ".dmg", ".iso",
    ".mp3", ".mp4", ".avi", ".mov", ".wmv", ".flv", ".map", ".json",
}

DEFAULT_MANIFEST = {
    "version": 1,
    "updated": "2026-04-03",
    "base_dir": str(BASE_DIR),
    "products": [
        {
            "slug": "tencent-cloud-api",
            "name": "腾讯云 API",
            "start_urls": [
                "https://cloud.tencent.cn/document/api",
                "https://cloud.tencent.cn/document/product",
            ],
            "allowed_prefixes": [
                "https://cloud.tencent.cn/document/api",
                "https://cloud.tencent.cn/document/product",
            ],
        },
        {
            "slug": "wechat-mini-program",
            "name": "微信小程序",
            "start_urls": [
                "https://developers.weixin.qq.com/miniprogram/dev/framework/",
                "https://developers.weixin.qq.com/miniprogram/dev/reference/",
                "https://developers.weixin.qq.com/miniprogram/dev/component/",
                "https://developers.weixin.qq.com/miniprogram/dev/api/",
                "https://developers.weixin.qq.com/miniprogram/dev/server-api/",
            ],
            "allowed_prefixes": [
                "https://developers.weixin.qq.com/miniprogram/dev/framework/",
                "https://developers.weixin.qq.com/miniprogram/dev/reference/",
                "https://developers.weixin.qq.com/miniprogram/dev/component/",
                "https://developers.weixin.qq.com/miniprogram/dev/api/",
                "https://developers.weixin.qq.com/miniprogram/dev/server-api/",
                "https://developers.weixin.qq.com/miniprogram/dev/platform-capabilities/",
            ],
        },
        {
            "slug": "wechat-pay",
            "name": "微信支付",
            "start_urls": [
                "https://pay.weixin.qq.com/wiki/doc/api/index.html",
                "https://pay.weixin.qq.com/doc/global/v3/zh",
                "https://pay.wechatpay.cn/docs/",
            ],
            "allowed_prefixes": [
                "https://pay.weixin.qq.com/wiki/doc/api/",
                "https://pay.weixin.qq.com/doc/",
                "https://pay.wechatpay.cn/docs/",
            ],
        },
        {
            "slug": "cloudbase",
            "name": "微信云开发 CloudBase",
            "start_urls": [
                "https://developers.weixin.qq.com/miniprogram/dev/wxcloudservice/wxcloud/guide/index.html",
                "https://developers.weixin.qq.com/miniprogram/dev/wxcloud/reference-http-api/",
                "https://developers.weixin.qq.com/miniprogram/dev/wxcloud/reference-sdk-api/Cloud.init.html",
                "https://docs.cloudbase.net/toolbox/quick-start",
            ],
            "allowed_prefixes": [
                "https://developers.weixin.qq.com/miniprogram/dev/wxcloudservice/",
                "https://developers.weixin.qq.com/miniprogram/dev/wxcloud/",
                "https://docs.cloudbase.net/",
            ],
        },
        {
            "slug": "trtc",
            "name": "腾讯云实时音视频 TRTC",
            "start_urls": [
                "https://trtc.io/zh/document",
                "https://cloud.tencent.cn/document/product/647",
                "https://cloud.tencent.cn/document/product/647/49327",
            ],
            "allowed_prefixes": [
                "https://trtc.io/zh/document",
                "https://cloud.tencent.cn/document/product/647",
            ],
        },
        {
            "slug": "tencent-map-mini-program",
            "name": "腾讯地图小程序",
            "start_urls": [
                "https://lbs.qq.com/miniProgram/jsSdk/jsSdkGuide/jsSdkOverview",
                "https://lbs.qq.com/miniProgram/jsSdk/jsSdkGuide/",
                "https://lbs.qq.com/product/miniapp/jssdk/",
                "https://developers.weixin.qq.com/miniprogram/dev/component/map.html",
                "https://developers.weixin.qq.com/miniprogram/dev/api/media/map/wx.createMapContext.html",
            ],
            "allowed_prefixes": [
                "https://lbs.qq.com/miniProgram/jsSdk/",
                "https://lbs.qq.com/product/miniapp/jssdk/",
                "https://lbs.qq.com/faq/miniprogramFaq/",
                "https://developers.weixin.qq.com/miniprogram/dev/component/map",
                "https://developers.weixin.qq.com/miniprogram/dev/api/media/map/",
                "https://developers.weixin.qq.com/miniprogram/dev/platform-capabilities/miniapp/handbook/",
            ],
        },
        {
            "slug": "wechat-game",
            "name": "微信小游戏",
            "start_urls": [
                "https://developers.weixin.qq.com/minigame/dev/api/",
                "https://developers.weixin.qq.com/minigame/dev/guide/framework/framework-readme.html",
                "https://developers.weixin.qq.com/minigame/introduction/commercialization/",
            ],
            "allowed_prefixes": [
                "https://developers.weixin.qq.com/minigame/dev/api/",
                "https://developers.weixin.qq.com/minigame/dev/guide/",
                "https://developers.weixin.qq.com/minigame/introduction/",
            ],
        },
        {
            "slug": "tdesign",
            "name": "TDesign",
            "start_urls": [
                "https://tencent.github.io/tdesign/README_zh-CN.html",
                "https://tdesign.tencent.com/miniprogram/overview",
                "https://tdesign.tencent.com/vue-next/overview",
                "https://tdesign.tencent.com/react/overview",
                "https://tdesign.tencent.com/flutter/getting-started",
            ],
            "allowed_prefixes": [
                "https://tencent.github.io/tdesign/",
                "https://tdesign.tencent.com/miniprogram/",
                "https://tdesign.tencent.com/vue-next/",
                "https://tdesign.tencent.com/react/",
                "https://tdesign.tencent.com/vue/",
                "https://tdesign.tencent.com/flutter/",
                "https://tdesign.tencent.com/mobile-vue/",
                "https://tdesign.tencent.com/mobile-react/",
                "https://tdesign.tencent.com/uniapp/",
            ],
        },
    ],
}

ROBOTS_CACHE: Dict[str, RobotFileParser | None] = {}


class DocHTMLParser(HTMLParser):
    BLOCK_TAGS = {
        "p", "div", "section", "article", "main", "header", "footer", "aside",
        "h1", "h2", "h3", "h4", "h5", "h6", "li", "ul", "ol",
        "pre", "code", "table", "tr", "td", "th", "blockquote", "br",
    }
    SKIP_TAGS = {"script", "style", "noscript", "svg", "canvas"}

    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.links: List[str] = []
        self.text_parts: List[str] = []
        self.title_parts: List[str] = []
        self.skip_depth = 0
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        attr_map = dict(attrs)
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag == "title":
            self.in_title = True
        if tag == "a":
            href = attr_map.get("href")
            if href:
                self.links.append(urljoin(self.base_url, href))
        if tag in self.BLOCK_TAGS:
            self.text_parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        if tag == "title":
            self.in_title = False
        if tag in self.BLOCK_TAGS:
            self.text_parts.append("\n")

    def handle_data(self, data):
        if self.skip_depth:
            return
        value = unescape(data or "")
        value = re.sub(r"\s+", " ", value).strip()
        if not value:
            return
        if self.in_title:
            self.title_parts.append(value)
        self.text_parts.append(value)

    def title(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self.title_parts)).strip()

    def text(self) -> str:
        text = "\n".join(self.text_parts)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_dirs() -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)


def write_manifest_if_missing() -> dict:
    ensure_dirs()
    if not MANIFEST_PATH.exists():
        MANIFEST_PATH.write_text(json.dumps(DEFAULT_MANIFEST, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    write_readme(manifest)
    return manifest


def write_readme(manifest: dict) -> None:
    lines = [
        "# Tencent Offline Docs",
        "",
        f"- 根目录: `{BASE_DIR}`",
        f"- manifest: `{MANIFEST_PATH}`",
        f"- index: `{INDEX_PATH}`",
        "",
        "## 可用命令",
        "",
        "```bash",
        "python /python\\ai.py tencent docs init",
        "python /python\\ai.py tencent docs crawl --max-pages 1200 --per-product 220",
        "python /python\\ai.py tencent docs search 微信支付 回调签名",
        "python /python\\ai.py tencent docs status",
        "```",
        "",
        "## 产品范围",
        "",
    ]
    for product in manifest.get("products", []):
        lines.append(f"- `{product['slug']}`: {product['name']}")
    README_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def normalize_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url.strip())
    if not parsed.scheme.startswith("http"):
        return ""
    query_items = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k not in TRACKING_QUERY_KEYS]
    query = urlencode(query_items, doseq=True)
    path = parsed.path or "/"
    if path != "/":
        path = re.sub(r"//+", "/", path)
    normalized = parsed._replace(fragment="", query=query, path=path)
    return urlunparse(normalized)


def safe_slug(value: str) -> str:
    value = re.sub(r"https?://", "", value)
    value = re.sub(r"[^0-9A-Za-z._-]+", "_", value)
    value = value.strip("._-")
    return value or "index"


def path_for_url(product_slug: str, url: str) -> Path:
    parsed = urlparse(url)
    base = safe_slug(f"{parsed.netloc}_{parsed.path}")
    base = base[:120].rstrip("._-") or "index"
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    return BASE_DIR / product_slug / f"{base}__{digest}.md"


def should_follow(url: str, product: dict) -> bool:
    url = normalize_url(url)
    if not url:
        return False
    lower = url.lower()
    if any(lower.endswith(suffix) for suffix in SKIP_SUFFIXES):
        return False
    if any(lower.startswith(prefix.lower()) for prefix in product.get("allowed_prefixes", [])):
        return True
    return False


def get_robot_parser(root: str) -> RobotFileParser | None:
    if root in ROBOTS_CACHE:
        return ROBOTS_CACHE[root]
    parser = RobotFileParser()
    parser.set_url(f"{root}/robots.txt")
    try:
        parser.read()
        ROBOTS_CACHE[root] = parser
    except Exception:
        ROBOTS_CACHE[root] = None
    return ROBOTS_CACHE[root]


def can_fetch(url: str) -> bool:
    parsed = urlparse(url)
    root = f"{parsed.scheme}://{parsed.netloc}"
    parser = get_robot_parser(root)
    if parser is None:
        return True
    try:
        return parser.can_fetch(USER_AGENT, url)
    except Exception:
        return True


def fetch_url(url: str, timeout: int = 25) -> Tuple[str, str]:
    req = Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    })
    with urlopen(req, timeout=timeout) as resp:
        content_type = resp.headers.get("Content-Type", "")
        raw = resp.read()
        charset = resp.headers.get_content_charset() or "utf-8"
        try:
            text = raw.decode(charset, errors="ignore")
        except LookupError:
            text = raw.decode("utf-8", errors="ignore")
    return content_type, text


def parse_document(url: str, html: str) -> Tuple[str, str, List[str]]:
    parser = DocHTMLParser(url)
    try:
        parser.feed(html)
        title = parser.title() or url
        text = parser.text()
        links = [normalize_url(link) for link in parser.links]
    except Exception:
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.I | re.S)
        title = re.sub(r"\s+", " ", unescape(title_match.group(1))).strip() if title_match else url
        cleaned = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\1>", " ", html)
        cleaned = re.sub(r"(?s)<!--.*?-->", " ", cleaned)
        links = [normalize_url(urljoin(url, href)) for href in re.findall(r"href=['\"]([^'\"]+)['\"]", cleaned, flags=re.I)]
        text = re.sub(r"(?s)<[^>]+>", " ", cleaned)
        text = re.sub(r"\s+", " ", unescape(text)).strip()
    links = [link for link in links if link]
    deduped = []
    seen = set()
    for link in links:
        if link not in seen:
            deduped.append(link)
            seen.add(link)
    return title, text, deduped



def load_index() -> Tuple[Dict[str, dict], List[dict]]:
    by_url: Dict[str, dict] = {}
    entries: List[dict] = []
    if not INDEX_PATH.exists():
        return by_url, entries
    for line in INDEX_PATH.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        url = item.get("url")
        if url:
            by_url[url] = item
            entries.append(item)
    return by_url, entries


def append_index(entry: dict) -> None:
    ensure_dirs()
    with INDEX_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def render_markdown(product: dict, url: str, title: str, text: str) -> str:
    header = [
        f"# {title}",
        "",
        f"- Product: {product['name']}",
        f"- URL: {url}",
        f"- Fetched: {now_str()}",
        "",
        "---",
        "",
    ]
    body = text[:180000].strip()
    return "\n".join(header) + body + "\n"


def command_init(_: argparse.Namespace) -> int:
    manifest = write_manifest_if_missing()
    print(json.dumps({
        "status": "ok",
        "base_dir": str(BASE_DIR),
        "products": [{"slug": p["slug"], "name": p["name"]} for p in manifest.get("products", [])],
    }, ensure_ascii=False, indent=2))
    return 0


def command_status(_: argparse.Namespace) -> int:
    manifest = write_manifest_if_missing()
    _, entries = load_index()
    counts = defaultdict(int)
    for item in entries:
        counts[item.get("product", "unknown")] += 1
    result = {
        "status": "ok",
        "base_dir": str(BASE_DIR),
        "index_exists": INDEX_PATH.exists(),
        "total_docs": len(entries),
        "products": [],
    }
    for product in manifest.get("products", []):
        product_dir = BASE_DIR / product["slug"]
        result["products"].append({
            "slug": product["slug"],
            "name": product["name"],
            "docs": counts.get(product["slug"], 0),
            "dir": str(product_dir),
        })
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def build_query_terms(query: str) -> List[str]:
    seen = set()
    terms: List[str] = []
    for part in re.split(r"[\s,，。；;、|/]+", query.lower()):
        part = part.strip()
        if part and part not in seen:
            terms.append(part)
            seen.add(part)
    return terms



def expand_cjk_term(term: str) -> List[str]:
    if re.fullmatch(r"[\u4e00-\u9fff]+", term or "") and len(term) >= 4:
        return [term[i:i + 2] for i in range(len(term) - 1)]
    return []



def score_search_candidate(query: str, terms: List[str], title: str, url: str, text: str) -> Tuple[int, int]:
    phrase = query.lower()
    title_lower = (title or "").lower()
    url_lower = (url or "").lower()
    text_lower = (text or "").lower()

    score = 0
    matched_terms = 0

    if phrase:
        score += title_lower.count(phrase) * 12
        score += url_lower.count(phrase) * 5
        score += text_lower.count(phrase) * 3

    for term in terms:
        term_score = 0
        term_score += title_lower.count(term) * 5
        term_score += url_lower.count(term) * 2
        term_score += text_lower.count(term)
        if term_score > 0:
            matched_terms += 1
            score += term_score
            continue

        partials = expand_cjk_term(term)
        if not partials:
            continue

        partial_score = 0
        partial_hits = 0
        for partial in partials:
            hit_score = 0
            hit_score += title_lower.count(partial) * 2
            hit_score += url_lower.count(partial)
            hit_score += text_lower.count(partial)
            if hit_score > 0:
                partial_hits += 1
                partial_score += hit_score

        if partial_hits >= max(2, len(partials) // 2):
            matched_terms += 1
            score += partial_score

    return score, matched_terms




def read_local_search_text(path_str: str, limit: int = 160000) -> str:
    if not path_str:
        return ""
    try:
        return Path(path_str).read_text(encoding="utf-8", errors="ignore")[:limit]
    except Exception:
        return ""



def build_search_snippet(text: str, query: str, terms: List[str], width: int = 220) -> str:
    clean = re.sub(r"\s+", " ", text or "").strip()
    if not clean:
        return ""
    lower_clean = clean.lower()
    targets = [query.lower()] + terms
    hit_positions = []
    for target in targets:
        if not target:
            continue
        pos = lower_clean.find(target)
        if pos >= 0:
            hit_positions.append(pos)
    if not hit_positions:
        return clean[:width]
    start = max(min(hit_positions) - 60, 0)
    end = min(start + width, len(clean))
    return clean[start:end]



def command_search(args: argparse.Namespace) -> int:
    query = " ".join(args.query).strip()
    if not query:
        print("search 需要关键词")
        return 1

    _, entries = load_index()
    terms = build_query_terms(query)
    results = []

    for item in entries:
        if args.product and item.get("product") != args.product:
            continue

        title = item.get("title") or ""
        url = item.get("url") or ""
        cached_text = item.get("search_text") or ""
        score, matched_terms = score_search_candidate(query, terms, title, url, cached_text)
        snippet = item.get("snippet") or ""

        needs_local_scan = score <= 0 or (len(terms) > 1 and matched_terms < len(terms))
        if needs_local_scan:
            local_text = read_local_search_text(item.get("local_path") or "")
            if local_text:
                local_score, local_matched_terms = score_search_candidate(query, terms, title, url, local_text)
                if local_score >= score:
                    score = local_score
                    matched_terms = local_matched_terms
                    snippet = build_search_snippet(local_text, query, terms)

        if len(terms) > 1 and matched_terms < len(terms):
            continue
        if score <= 0:
            continue

        results.append((score, snippet, item))

    results.sort(key=lambda x: (-x[0], x[2].get("title", "")))
    payload = []
    for score, snippet, item in results[: args.limit]:
        payload.append({
            "score": score,
            "product": item.get("product"),
            "title": item.get("title"),
            "url": item.get("url"),
            "local_path": item.get("local_path"),
            "snippet": snippet,
        })

    print(json.dumps({
        "status": "ok",
        "query": query,
        "count": len(payload),
        "results": payload,
    }, ensure_ascii=False, indent=2))
    return 0



def command_crawl(args: argparse.Namespace) -> int:
    manifest = write_manifest_if_missing()
    existing_by_url, existing_entries = load_index()
    existing_counts = defaultdict(int)
    for item in existing_entries:
        existing_counts[item.get("product", "unknown")] += 1

    products = manifest.get("products", [])
    if args.product and args.product != "all":
        products = [p for p in products if p.get("slug") == args.product]
        if not products:
            print(f"未知 product: {args.product}")
            return 1

    total_new = 0
    total_seen = 0
    report = []

    for product in products:
        queue = deque(normalize_url(url) for url in product.get("start_urls", []))
        queued = {url for url in queue if url}
        processed = set()
        new_for_product = 0
        seen_for_product = 0
        target_existing = existing_counts.get(product["slug"], 0)

        while queue and total_new < args.max_pages and new_for_product < args.per_product:
            url = queue.popleft()
            if not url or url in processed:
                continue
            processed.add(url)
            seen_for_product += 1
            total_seen += 1

            existing = existing_by_url.get(url)
            if existing:
                for link in existing.get("links", []):
                    if should_follow(link, product) and link not in queued and link not in processed:
                        queue.append(link)
                        queued.add(link)
                continue

            if not should_follow(url, product):
                continue
            if not can_fetch(url):
                continue

            try:
                content_type, html = fetch_url(url, timeout=args.timeout)
            except (HTTPError, URLError, TimeoutError) as exc:
                print(f"[skip] {product['slug']} {url} :: {exc}")
                continue
            except Exception as exc:
                print(f"[skip] {product['slug']} {url} :: {exc}")
                continue

            if "text/html" not in content_type and "application/xhtml+xml" not in content_type and "<html" not in html.lower():
                continue

            title, text, links = parse_document(url, html)
            text = re.sub(r"\n{3,}", "\n\n", text).strip()
            if len(text) < 120:
                text = (title + "\n\n" + text).strip()
            local_path = path_for_url(product["slug"], url)
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_text(render_markdown(product, url, title, text), encoding="utf-8")

            filtered_links = []
            for link in links:
                if should_follow(link, product):
                    filtered_links.append(link)
                    if link not in queued and link not in processed:
                        queue.append(link)
                        queued.add(link)

            entry = {
                "product": product["slug"],
                "product_name": product["name"],
                "url": url,
                "title": title[:300],
                "local_path": str(local_path),
                "fetched_at": now_str(),
                "char_count": len(text),
                "word_count": len(text.split()),
                "snippet": text[:280].replace("\n", " "),
                "search_text": (title + " " + text[:4000]).replace("\n", " "),
                "links": filtered_links[:300],
            }
            append_index(entry)
            existing_by_url[url] = entry
            new_for_product += 1
            total_new += 1
            print(f"[ok] {product['slug']} +1 -> {title[:80]}")
            time.sleep(max(args.delay, 0.0))

        report.append({
            "slug": product["slug"],
            "name": product["name"],
            "existing_before": target_existing,
            "seen_this_run": seen_for_product,
            "new_docs": new_for_product,
            "queued_total": len(queued),
        })

    print(json.dumps({
        "status": "ok",
        "base_dir": str(BASE_DIR),
        "new_docs": total_new,
        "seen_urls": total_seen,
        "report": report,
    }, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="腾讯离线文档管理器")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init")
    sub.add_parser("status")

    p_search = sub.add_parser("search")
    p_search.add_argument("query", nargs="+")
    p_search.add_argument("--product", default="")
    p_search.add_argument("--limit", type=int, default=10)

    p_crawl = sub.add_parser("crawl")
    p_crawl.add_argument("--product", default="all")
    p_crawl.add_argument("--max-pages", type=int, default=1200)
    p_crawl.add_argument("--per-product", type=int, default=220)
    p_crawl.add_argument("--delay", type=float, default=0.8)
    p_crawl.add_argument("--timeout", type=int, default=25)

    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    if args.command == "init":
        return command_init(args)
    if args.command == "status":
        return command_status(args)
    if args.command == "search":
        return command_search(args)
    if args.command == "crawl":
        return command_crawl(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
