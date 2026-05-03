#!/usr/bin/env python
"""Phase 1: Preliminary Analysis - 初步分析阶段

职责:
- 项目结构扫描 (目录树、文件类型分布)
- 代码语言/框架识别
- 依赖关系映射 (import/require/use)
- 架构模式识别 (MVC/微服务/单体/插件式)
- 入口点发现
- 特性/功能清单提取
"""

import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).parent.parent.parent  # \python\
sys.path.insert(0, str(ROOT / "core"))

# 延迟导入 pipeline_engine 避免循环
from pipeline_engine import GateReport, GateStatus
from pipeline_engine import Phase as PipelinePhase


def analyze_phase(
    project_path: Path, project_name: str, run_id: str, prev_reports: dict = None, **kwargs
) -> GateReport:
    """执行初步分析阶段"""

    if isinstance(project_path, str):
        project_path = Path(project_path)
    if not project_path.exists():
        return GateReport(
            phase=PipelinePhase.ANALYSIS,
            status=GateStatus.FAILED,
            summary=f"项目路径不存在: {project_path}",
            risk_level="high",
        )

    # 1. 目录结构扫描
    tree = _scan_directory(project_path)
    file_stats = _analyze_file_types(project_path)

    # 2. 代码语言和框架识别
    languages = _detect_languages(project_path)
    frameworks = _detect_frameworks(project_path, languages)

    # 3. 依赖关系映射
    dependencies = _map_dependencies(project_path, languages)

    # 4. 架构模式识别
    architecture = _detect_architecture(project_path, languages)

    # 5. 入口点发现
    entry_points = _find_entry_points(project_path, languages)

    # 6. 特性提取
    features = _extract_features(project_path, languages)

    # 综合风险
    risk = "low"
    if not entry_points:
        risk = "medium"
    if not any(languages.values()):
        risk = "high"

    details = {
        "project_path": str(project_path),
        "directory_structure": tree,
        "file_statistics": file_stats,
        "languages_detected": {k: v for k, v in languages.items() if v},
        "frameworks_detected": frameworks,
        "dependencies": {k: v[:10] for k, v in dependencies.items()},
        "architecture_patterns": architecture,
        "entry_points": entry_points[:10],
        "features_identified": features[:20],
        "total_files": file_stats.get("total", 0),
        "scan_timestamp": datetime.now().isoformat(),
    }

    summary = []
    if languages:
        main_lang = max(languages, key=languages.get)
        summary.append(f"主语言: {main_lang} ({languages[main_lang]} 文件)")
    if frameworks:
        summary.append(f"框架: {', '.join(frameworks[:5])}")
    if entry_points:
        summary.append(f"入口点: {len(entry_points)} 个")
    if architecture:
        summary.append(f"架构: {', '.join(architecture[:3])}")

    return GateReport(
        phase=PipelinePhase.ANALYSIS,
        status=GateStatus.PASSED if languages else GateStatus.WARNING,
        summary=" | ".join(summary) if summary else "分析完成",
        details=details,
        risk_level=risk,
    )


# ─── 扫描工具函数 ──────────────────────────────────────


def _scan_directory(root: Path, max_depth: int = 3) -> dict:
    """扫描目录结构"""
    tree = {}
    for item in sorted(root.iterdir())[:50]:
        if item.name.startswith(".") or item.name.startswith("__"):
            continue
        if item.is_dir():
            sub_count = len(list(item.rglob("*"))) if max_depth > 0 else 0
            tree[item.name] = {
                "type": "directory",
                "count": min(sub_count, 999),
            }
            if max_depth > 0:
                tree[item.name]["children"] = _scan_directory(item, max_depth - 1)
        else:
            tree[item.name] = {
                "type": "file",
                "ext": item.suffix,
                "size_kb": round(item.stat().st_size / 1024, 1),
            }
    return tree


def _analyze_file_types(root: Path) -> dict:
    """分析文件类型分布"""
    stats = defaultdict(int)
    total = 0
    ext_map = {}
    for f in root.rglob("*"):
        if f.is_file() and not any(p.startswith(".") for p in f.parts):
            total += 1
            ext = f.suffix.lower()
            stats[ext] += 1
            if ext not in ext_map:
                ext_map[ext] = f.suffix

    return {
        "total": total,
        "extensions": dict(sorted(stats.items(), key=lambda x: x[1], reverse=True)[:20]),
    }


def _detect_languages(root: Path) -> dict:
    """检测编程语言"""
    ext_to_lang = {
        ".py": "Python",
        ".js": "JavaScript",
        ".mjs": "JavaScript",
        ".jsx": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".java": "Java",
        ".kt": "Kotlin",
        ".go": "Go",
        ".rs": "Rust",
        ".cpp": "C++",
        ".c": "C",
        ".h": "C/C++ Header",
        ".cs": "C#",
        ".rb": "Ruby",
        ".php": "PHP",
        ".swift": "Swift",
        ".r": "R",
        ".toml": "TOML Config",
        ".yaml": "YAML Config",
        ".yml": "YAML Config",
        ".json": "JSON",
        ".xml": "XML",
        ".sh": "Shell",
        ".ps1": "PowerShell",
        ".bat": "Batch",
        ".md": "Markdown",
        ".html": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",
        ".sql": "SQL",
        ".dockerfile": "Docker",
    }

    counts = defaultdict(int)
    for f in root.rglob("*"):
        if f.is_file():
            ext = f.suffix.lower()
            lang = ext_to_lang.get(ext)
            if lang:
                counts[lang] += 1
            elif f.name.lower() == "dockerfile":
                counts["Docker"] += 1
            elif f.name.lower() == "makefile":
                counts["Makefile"] += 1
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))


def _detect_frameworks(root: Path, languages: dict) -> list:
    """检测框架"""
    frameworks = set()
    framework_indicators = {
        # Python
        "requirements.txt": ["Python Project"],
        "setup.py": ["Python Package"],
        "pyproject.toml": ["Python (Poetry/Hatch)"],
        "Pipfile": ["Python (Pipenv)"],
        # JS/TS
        "package.json": ["Node.js"],
        "next.config.js": ["Next.js"],
        "next.config.ts": ["Next.js"],
        "nuxt.config.js": ["Nuxt.js"],
        "angular.json": ["Angular"],
        "vue.config.js": ["Vue.js"],
        "svelte.config.js": ["Svelte"],
        # Java
        "pom.xml": ["Maven"],
        "build.gradle": ["Gradle"],
        "gradlew": ["Gradle Wrapper"],
        # Rust
        "Cargo.toml": ["Rust (Cargo)"],
        # Go
        "go.mod": ["Go Modules"],
        # .NET
        "*.csproj": [".NET"],
        "*.sln": [".NET Solution"],
        # Docker
        "Dockerfile": ["Docker"],
        "docker-compose.yml": ["Docker Compose"],
        # CI/CD
        ".github/workflows/": ["GitHub Actions"],
        ".gitlab-ci.yml": ["GitLab CI"],
    }

    for indicator, names in framework_indicators.items():
        pattern = f"**/{indicator}" if "*" in indicator else f"**/{indicator}"
        matches = list(root.glob(pattern))
        if matches:
            for name in names:
                frameworks.add(name)

    return sorted(frameworks)


def _map_dependencies(root: Path, languages: dict) -> dict:
    """映射依赖关系"""
    deps = defaultdict(list)

    # Python imports
    for py_file in list(root.rglob("*.py"))[:100]:
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            imports = re.findall(r"^(?:from|import)\s+(\S+)", content, re.MULTILINE)
            for imp in imports[:5]:
                deps["python"].append(imp.split(".")[0])
        except Exception:
            pass

    # JS requires/imports
    for js_file in list(root.rglob("*.js"))[:50]:
        try:
            content = js_file.read_text(encoding="utf-8", errors="ignore")
            reqs = re.findall(r'(?:require|import).*?[\'"]([^\'"]+)[\'"]', content)
            for r in reqs[:5]:
                deps["javascript"].append(r)
        except Exception:
            pass

    # JSON dependencies
    pkg_json = root / "package.json"
    if pkg_json.exists():
        try:
            pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
            for dep_type in ("dependencies", "devDependencies"):
                if dep_type in pkg:
                    deps["npm"].extend(list(pkg[dep_type].keys())[:20])
        except Exception:
            pass

    # Python requirements
    req_file = root / "requirements.txt"
    if req_file.exists():
        try:
            for line in req_file.read_text(encoding="utf-8").split("\n")[:30]:
                line = line.strip().split("#")[0].strip()
                if line and not line.startswith("-"):
                    req_name = re.split(r"[>=<~!]", line)[0].strip()
                    deps["python_requirements"].append(req_name)
        except Exception:
            pass

    return dict(deps)


def _detect_architecture(root: Path, languages: dict) -> list:
    """检测架构模式"""
    patterns = set()
    dirs = [d.name.lower() for d in root.iterdir() if d.is_dir()]

    # MVC 模式
    if all(d in dirs for d in ("models", "views", "controllers")):
        patterns.add("MVC")
    elif all(d in dirs for d in ("models", "controllers")):
        patterns.add("MC-like")

    # 微服务
    svc_dirs = [d for d in root.iterdir() if d.is_dir() and "service" in d.name.lower()]
    if len(svc_dirs) >= 2:
        patterns.add("Microservices")

    # 插件架构
    if "plugins" in dirs or "plugin" in dirs:
        patterns.add("Plugin Architecture")

    # 分层架构
    layer_dirs = {"core", "adapter", "storage", "user"}
    if len(layer_dirs & set(dirs)) >= 3:
        patterns.add("Layered Architecture")

    # 单体
    if not patterns:
        patterns.add("Monolithic")

    return sorted(patterns)


def _find_entry_points(root: Path, languages: dict) -> list:
    """查找入口点"""
    entries = []

    entry_names = {"main", "index", "app", "server", "run", "start", "entry", "launch", "main", "管理", "启动", "入口"}

    for f in root.rglob("*"):
        if f.is_file() and f.suffix in (".py", ".js", ".ts", ".go", ".rs", ".java"):
            stem = f.stem.lower()
            if stem in entry_names or "main" in stem or "启动" in stem:
                entries.append(str(f.relative_to(root)))
                if len(entries) >= 20:
                    break

    return sorted(entries)


def _extract_features(root: Path, languages: dict) -> list:
    """从文档/注释中提取特性清单"""
    features = []

    # 从 README 提取
    readme_files = list(root.glob("README*")) + list(root.glob("readme*"))
    for rf in readme_files[:3]:
        try:
            content = rf.read_text(encoding="utf-8", errors="ignore")[:5000]
            # 提取标题行和特性描述
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("## ") or line.startswith("# ") or line.startswith("* ") or line.startswith("- "):
                    features.append(line.lstrip("#*- ").strip())
        except Exception:
            pass

    # 从 AGENTS.md 提取
    agents_file = root / "AGENTS.md"
    if agents_file.exists():
        try:
            content = agents_file.read_text(encoding="utf-8", errors="ignore")[:3000]
            for line in content.split("\n"):
                if "- " in line and len(line) > 30:
                    features.append(line.strip("- ").strip())
        except Exception:
            pass

    return list(dict.fromkeys(features))[:30]  # 去重去序


if __name__ == "__main__":
    report = analyze_phase(Path("/python"), "AI-Platform", "test_run")
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
