# -*- coding: utf-8 -*-
"""
Skill Reviewer - Skill质量审查与思维导图生成器

功能：
- 审查所有已安装Skill的安全、质量、依赖
- 生成Skill关系思维导图（mermaid / D3.js）
- 分析工作流依赖链
- 输出审美检查报告

用法：
    python /python/MCP_Core/skills/skill_reviewer/skill.py review [skill_name]
    python /python/MCP_Core/skills/skill_reviewer/skill.py mindmap [--output path]
    python /python/MCP_Core/skills/skill_reviewer/skill.py audit
"""

import json as _json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

SKILLS_DIR = Path("/python/MCP_Core/skills")
WORKFLOWS_DIR = Path("/python/MCP_Core/workflow")
OUTPUT_DIR = Path("/python/MCP_Core/docs/skill_review")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class SkillInfo:
    name: str
    path: Path
    description: str = ""
    has_readme: bool = False
    has_skill_md: bool = False
    has_json: bool = False
    lines_of_code: int = 0
    dependencies: List[str] = field(default_factory=list)
    security_flags: List[str] = field(default_factory=list)
    last_modified: Optional[str] = None


@dataclass
class ReviewResult:
    skill_name: str
    status: str
    score: float
    issues: List[Dict[str, str]]
    suggestions: List[str]
    mindmap_node: Optional[Dict] = None


def _get_description(skill_path: Path) -> str:
    for f in ["SKILL.md", "README.md", "skill.json", "skill.py"]:
        fp = skill_path / f
        if fp.exists():
            try:
                content = fp.read_text(encoding="utf-8", errors="ignore")[:500]
                desc = re.search(r'#\s+(.+)|description[:：]\s*(.+)', content, re.IGNORECASE)
                if desc:
                    return (desc.group(1) or desc.group(2)).strip()[:100]
            except Exception:
                pass
    return ""


def _count_lines(skill_path: Path) -> int:
    total = 0
    for ext in ["*.py", "*.js", "*.ts", "*.md"]:
        for f in skill_path.rglob(ext):
            try:
                total += len(f.read_text(encoding="utf-8", errors="ignore").splitlines())
            except Exception:
                pass
    return total


def _extract_dependencies(skill_path: Path) -> List[str]:
    deps = []
    for f in skill_path.rglob("*.py"):
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            for match in re.finditer(r'(?:from|import)\s+([^\s;(]+)', content):
                dep = match.group(1).split('.')[0]
                if not dep.startswith('_') and dep not in ('os', 'sys', 'typing', 'pathlib', 'datetime', 'json', 're'):
                    deps.append(dep)
        except Exception:
            pass
    return list(dict.fromkeys(deps))[:8]


def _security_check(skill_path: Path) -> List[str]:
    flags = []
    patterns = [
        (r"os\.system\s*\(", "shell注入风险: os.system"),
        (r"subprocess\.call\s*\([^,]+shell\s*=\s*True", "shell注入风险: subprocess shell=True"),
        (r"\beval\s*\(", "代码注入风险: eval"),
        (r"\bexec\s*\(", "代码注入风险: exec"),
        (r"__import__\s*\(\s*os\s*\)", "危险导入: __import__ os"),
        (r"ctypes\.", "危险库: ctypes 可调用原生API"),
        (r"shutil\.rmtree", "文件删除风险: shutil.rmtree"),
    ]
    for ext in ["*.py", "*.js"]:
        for f in skill_path.rglob(ext):
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                for pat, msg in patterns:
                    if re.search(pat, content):
                        flags.append(f"{f.name}: {msg}")
            except Exception:
                pass
    return flags


def _get_mtime(skill_path: Path) -> Optional[str]:
    try:
        ts = max(f.stat().st_mtime for f in skill_path.rglob("*") if f.is_file())
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return None


def scan_skills() -> List[SkillInfo]:
    skills = []
    for d in SKILLS_DIR.iterdir():
        if not d.is_dir() or d.name.startswith("_"):
            continue
        info = SkillInfo(
            name=d.name, path=d,
            description=_get_description(d),
            has_readme=(d / "README.md").exists(),
            has_skill_md=(d / "SKILL.md").exists(),
            has_json=(d / "skill.json").exists(),
            lines_of_code=_count_lines(d),
            dependencies=_extract_dependencies(d),
            security_flags=_security_check(d),
            last_modified=_get_mtime(d),
        )
        skills.append(info)
    return skills


def review_skill(skill_name: str) -> ReviewResult:
    skill_path = SKILLS_DIR / skill_name
    if not skill_path.exists():
        return ReviewResult(
            skill_name=skill_name, status="fail", score=0,
            issues=[{"severity": "error", "msg": f"Skill不存在: {skill_name}"}],
            suggestions=["检查Skill名称是否正确"],
        )

    info = SkillInfo(
        name=skill_name, path=skill_path,
        description=_get_description(skill_path),
        has_readme=(skill_path / "README.md").exists(),
        has_skill_md=(skill_path / "SKILL.md").exists(),
        has_json=(skill_path / "skill.json").exists(),
        lines_of_code=_count_lines(skill_path),
        dependencies=_extract_dependencies(skill_path),
        security_flags=_security_check(skill_path),
        last_modified=_get_mtime(skill_path),
    )

    issues = []
    suggestions = []
    score = 100.0

    if not info.has_skill_md:
        issues.append({"severity": "warn", "msg": "缺少 SKILL.md"})
        score -= 20
    if not info.has_readme:
        issues.append({"severity": "warn", "msg": "缺少 README.md"})
        score -= 10
    if not info.has_json:
        issues.append({"severity": "warn", "msg": "缺少 skill.json"})
        score -= 10
    if info.lines_of_code == 0:
        issues.append({"severity": "error", "msg": "Skill无代码"})
        score -= 50
    for flag in info.security_flags:
        issues.append({"severity": "error", "msg": f"[安全] {flag}"})
        score -= 15
    if score < 0:
        score = 0

    if not info.has_skill_md:
        suggestions.append("添加 SKILL.md 描述功能、用法、示例")
    if not info.description:
        suggestions.append("在描述中添功能说明")
    if not info.security_flags:
        suggestions.append("考虑添加安全边界注释")
    if info.lines_of_code > 2000:
        suggestions.append("代码超过2000行，建议拆分子模块")

    return ReviewResult(
        skill_name=skill_name,
        status="pass" if score >= 60 else "warn" if score >= 30 else "fail",
        score=round(score, 1),
        issues=issues,
        suggestions=suggestions,
        mindmap_node={
            "id": skill_name, "label": skill_name, "type": "skill",
            "status": "pass" if score >= 60 else "warn" if score >= 30 else "fail",
            "score": round(score, 1), "children": [],
            "metadata": {
                "description": info.description,
                "lines": info.lines_of_code,
                "security_issues": len(info.security_flags),
                "last_modified": info.last_modified,
            }
        }
    )


def generate_mindmap(skill_name: Optional[str] = None) -> Dict[str, Any]:
    workflows = []
    if WORKFLOWS_DIR.exists():
        for wf in WORKFLOWS_DIR.glob("*.json"):
            try:
                data = _json.loads(wf.read_text(encoding="utf-8"))
                workflows.append({"name": wf.stem, "steps": data.get("steps", [])})
            except Exception:
                pass

    if skill_name:
        result = review_skill(skill_name)
        node = result.mindmap_node or {}
        node["children"] = []
        for dim, status in [
            ("文档完整性", "pass" if result.score >= 80 else "warn"),
            ("代码质量", "pass" if result.score >= 70 else "warn"),
            ("安全性", "pass" if not any(i.get("severity") == "error" for i in result.issues) else "fail"),
            ("性能", "pass"),
        ]:
            node["children"].append({
                "id": f"{skill_name}_{dim}", "label": dim, "type": "dimension",
                "status": status, "children": [],
            })
        return {
            "title": f"Skill审查报告: {result.skill_name}",
            "generated_at": datetime.now().isoformat(),
            "root": node, "score": result.score,
            "status": result.status,
            "issues": result.issues, "suggestions": result.suggestions,
        }

    skills = scan_skills()
    nodes = []
    for s in skills:
        result = review_skill(s.name)
        nodes.append({
            "id": s.name, "label": s.name, "type": "skill",
            "status": result.status, "score": result.score, "children": [],
            "metadata": {
                "description": s.description, "lines": s.lines_of_code,
                "security": len(s.security_flags), "deps": s.dependencies[:5],
            }
        })

    for wf in workflows:
        wf_node = {
            "id": f"wf_{wf['name']}", "label": wf["name"], "type": "workflow",
            "status": "running", "children": [
                {"id": f"wf_{wf['name']}_s{i}", "label": step.get("name", f"Step{i+1}"),
                 "type": "workflow_step", "status": "pending", "children": []}
                for i, step in enumerate(wf.get("steps", []))
            ], "metadata": wf,
        }
        nodes.append(wf_node)

    return {
        "title": "MCP Skills & Workflows 全局思维导图",
        "generated_at": datetime.now().isoformat(),
        "nodes": nodes,
        "stats": {
            "total_skills": len([n for n in nodes if n["type"] == "skill"]),
            "total_workflows": len([n for n in nodes if n["type"] == "workflow"]),
            "pass": len([n for n in nodes if n["status"] == "pass"]),
            "warn": len([n for n in nodes if n["status"] == "warn"]),
            "fail": len([n for n in nodes if n["status"] == "fail"]),
        }
    }


def generate_mermaid(mindmap_data: Dict[str, Any]) -> str:
    lines = ["mindmap"]

    def render(n: Dict, indent: int = 2) -> List[str]:
        prefix = " " * indent
        icon = {"pass": "OK", "warn": "WARN", "fail": "FAIL"}.get(n.get("status", ""), "")
        label = f"{icon} {n.get('label', n.get('id', ''))}" if icon else n.get("label", n.get("id", ""))
        out = [f"{prefix}{label}"]
        for c in n.get("children", []):
            out.extend(render(c, indent + 2))
        return out

    if "root" in mindmap_data and mindmap_data["root"]:
        lines.extend(render(mindmap_data["root"]))
    else:
        for node in mindmap_data.get("nodes", []):
            lines.extend(render(node))

    return "\n".join(lines)


def run_full_audit() -> Dict[str, Any]:
    skills = scan_skills()
    results = []
    total_score = 0
    for s in skills:
        result = review_skill(s.name)
        results.append({
            "name": result.skill_name, "status": result.status, "score": result.score,
            "issues_count": len(result.issues),
            "issues": result.issues, "suggestions": result.suggestions,
        })
        total_score += result.score

    avg = total_score / len(results) if results else 0
    report = {
        "audit_time": datetime.now().isoformat(),
        "total_skills": len(results),
        "average_score": round(avg, 1),
        "pass": len([r for r in results if r["status"] == "pass"]),
        "warn": len([r for r in results if r["status"] == "warn"]),
        "fail": len([r for r in results if r["status"] == "fail"]),
        "results": results,
        "mindmap": generate_mindmap(),
    }
    out = OUTPUT_DIR / f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out, "w", encoding="utf-8") as f:
        _json.dump(report, f, ensure_ascii=False, indent=2)
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("audit")
    r = sub.add_parser("review"); r.add_argument("skill_name")
    m = sub.add_parser("mindmap")
    m.add_argument("--skill", "-s")
    m.add_argument("--format", "-f", choices=["json", "mermaid"], default="json")
    m.add_argument("--output", "-o")
    args = parser.parse_args()

    if args.cmd == "audit":
        r = run_full_audit()
        print(f"审查: {r['total_skills']}个Skill 平均{r['average_score']}分 "
              f"通过/警告/失败 {r['pass']}/{r['warn']}/{r['fail']}")

    elif args.cmd == "review":
        res = review_skill(args.skill_name)
        print(_json.dumps({"skill": res.skill_name, "status": res.status,
                           "score": res.score, "issues": res.issues,
                           "suggestions": res.suggestions}, ensure_ascii=False, indent=2))

    elif args.cmd == "mindmap":
        data = generate_mindmap(args.skill)
        out = generate_mermaid(data) if args.format == "mermaid" else _json.dumps(data, ensure_ascii=False, indent=2)
        if args.output:
            Path(args.output).write_text(out, encoding="utf-8")
            print(f"已保存: {args.output}")
        else:
            print(out[:4000])

    else:
        parser.print_help()
