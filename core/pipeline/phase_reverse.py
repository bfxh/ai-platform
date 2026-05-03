#!/usr/bin/env python
"""Phase 3: Reverse Engineering - 逆向工程与许可证检测阶段

职责:
- 许可证类型检测 (MIT/Apache/GPL/BSD/Proprietary)
- 开源状态验证
- 二进制/编译产物检测 (.exe/.jar/.dll/.so)
- 反编译可行性评估
- 知识产权风险评估
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).parent.parent.parent  # \python\
sys.path.insert(0, str(ROOT / "core"))
from pipeline_engine import GateReport, GateStatus
from pipeline_engine import Phase as PipelinePhase

# ─── 许可证类型定义 ────────────────────────────────────

LICENSE_PATTERNS = {
    "MIT": {
        "keywords": ["mit license", "permission is hereby granted", "without restriction"],
        "file_names": ["LICENSE", "LICENSE.MIT", "LICENSE.txt", "COPYING"],
        "is_opensource": True,
    },
    "Apache-2.0": {
        "keywords": ["apache license", "version 2.0", "apache software foundation"],
        "file_names": ["LICENSE", "LICENSE.APACHE", "NOTICE"],
        "is_opensource": True,
    },
    "GPL-2.0": {
        "keywords": ["gnu general public license", "version 2", "free software foundation"],
        "file_names": ["LICENSE", "COPYING", "COPYING.GPL"],
        "is_opensource": True,
    },
    "GPL-3.0": {
        "keywords": ["gnu general public license", "version 3", "gplv3"],
        "file_names": ["LICENSE", "COPYING", "COPYING.GPL3"],
        "is_opensource": True,
    },
    "BSD": {
        "keywords": ["bsd license", "redistribution and use in source", "all rights reserved"],
        "file_names": ["LICENSE", "LICENSE.BSD"],
        "is_opensource": True,
    },
    "LGPL": {
        "keywords": ["gnu lesser general public license", "lgpl"],
        "file_names": ["LICENSE", "COPYING.LGPL"],
        "is_opensource": True,
    },
    "Proprietary": {
        "keywords": [
            "proprietary",
            "all rights reserved",
            "confidential",
            "trade secret",
            "no part of this",
            "未经许可不得",
        ],
        "file_names": [],
        "is_opensource": False,
    },
}

OPENSOURCE_INDICATORS = [
    "LICENSE",
    "license",
    "COPYING",
    "copying",
    "NOTICE",
    "notice",
    "AUTHORS",
    "CONTRIBUTING",
]

PROPRIETARY_INDICATORS = [
    "proprietary",
    "confidential",
    "trade secret",
    "all rights reserved",
    "commercial license",
    "未经许可不得",
    "商业授权",
    "版权所有",
]


def reverse_phase(
    project_path: Path, project_name: str, run_id: str, prev_reports: dict = None, **kwargs
) -> GateReport:
    """执行逆向工程/许可证检测"""

    if isinstance(project_path, str):
        project_path = Path(project_path)

    # 1. 许可证文件检测
    license_files_found = []
    license_type = "Unknown"
    is_opensource = None

    for pattern in OPENSOURCE_INDICATORS + list(
        {name for lic in LICENSE_PATTERNS.values() for name in lic.get("file_names", [])}
    ):
        for f in project_path.rglob(pattern):
            if f.is_file() and f.stat().st_size < 100000:
                license_files_found.append(str(f.relative_to(project_path)))

    license_files_found = list(dict.fromkeys(license_files_found))[:10]

    # 2. 许可证内容分析
    for lf_path in license_files_found[:5]:
        full_path = project_path / lf_path
        try:
            content = full_path.read_text(encoding="utf-8", errors="ignore")[:5000].lower()
            for lic_name, lic_data in LICENSE_PATTERNS.items():
                for kw in lic_data["keywords"]:
                    if kw in content:
                        license_type = lic_name
                        is_opensource = lic_data["is_opensource"]
                        break
                if license_type != "Unknown":
                    break
        except Exception:
            continue

    # 如果没找到 LICENSE 文件，检查 package.json / pyproject.toml
    if license_type == "Unknown":
        pkg_json = project_path / "package.json"
        if pkg_json.exists():
            try:
                pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
                pkg_license = pkg.get("license", "")
                if pkg_license:
                    license_type = pkg_license
                    is_opensource = license_type.lower() not in ("proprietary", "unlicensed")
            except Exception:
                pass

        pyproject = project_path / "pyproject.toml"
        if pyproject.exists() and license_type == "Unknown":
            try:
                content = pyproject.read_text(encoding="utf-8", errors="ignore")
                lic_match = re.search(r'license\s*=\s*["\']([^"\']+)["\']', content)
                if lic_match:
                    license_type = lic_match.group(1)
            except Exception:
                pass

    # 3. 二进制/编译产物检测
    binary_patterns = {
        ".exe": "Windows可执行",
        ".dll": "Windows动态库",
        ".so": "Linux共享库",
        ".jar": "Java归档",
        ".class": "Java字节码",
        ".pyc": "Python字节码",
        ".o": "编译目标",
        ".a": "静态库",
        ".bin": "二进制",
        ".dat": "数据文件",
        ".pak": "游戏资源包",
        ".unity3d": "Unity资源",
        ".wasm": "WebAssembly",
    }
    binaries_found = []
    for f in project_path.rglob("*"):
        if f.is_file() and f.suffix.lower() in binary_patterns:
            rel = str(f.relative_to(project_path))
            size_mb = round(f.stat().st_size / 1024 / 1024, 2)
            binaries_found.append(
                {
                    "file": rel,
                    "type": binary_patterns.get(f.suffix.lower(), "unknown"),
                    "size_mb": size_mb,
                }
            )
            if len(binaries_found) >= 50:
                break

    # 4. 反编译评估
    decompilable = []
    if binaries_found:
        for b in binaries_found[:10]:
            ext = Path(b["file"]).suffix.lower()
            if ext == ".jar":
                decompilable.append({"file": b["file"], "method": "JD-GUI / CFR", "difficulty": "easy"})
            elif ext == ".pyc":
                decompilable.append({"file": b["file"], "method": "uncompyle6 / pycdc", "difficulty": "easy"})
            elif ext == ".exe" or ext == ".dll":
                decompilable.append({"file": b["file"], "method": "IDA Pro / Ghidra", "difficulty": "medium"})
            elif ext == ".class":
                decompilable.append({"file": b["file"], "method": "JD-GUI / javap", "difficulty": "easy"})
            elif ext in (".unity3d", ".pak"):
                decompilable.append({"file": b["file"], "method": "AssetRipper / UModel", "difficulty": "medium"})

    # 5. 风险评估
    risk = "low"
    if license_type == "Proprietary":
        risk = "high"
    elif license_type == "Unknown" and binaries_found and not license_files_found:
        risk = "medium"

    if license_type in ("GPL-2.0", "GPL-3.0"):
        risk = "medium"  # GPL 传染性风险

    # 6. 状态判定
    if license_type == "Proprietary" or (license_type == "Unknown" and binaries_found and not license_files_found):
        status = GateStatus.BLOCKED
        summary = f"许可证: {license_type} — 非开源项目，需要授权"
    elif license_type != "Unknown":
        status = GateStatus.PASSED
        summary = f"许可证: {license_type} | 开源: {'✓' if is_opensource else '✗'}"
    else:
        status = GateStatus.PASSED
        summary = "许可证: 未明确声明 (可能开源)"

    details = {
        "license_detected": license_type,
        "is_opensource": is_opensource,
        "license_files": license_files_found,
        "binaries_count": len(binaries_found),
        "binary_types": list(set(b.get("type", "") for b in binaries_found)),
        "decompilable_targets": decompilable[:10],
        "total_binary_size_mb": round(sum(b.get("size_mb", 0) for b in binaries_found), 2),
        "scan_timestamp": datetime.now().isoformat(),
        "recommendation": _get_recommendation(license_type, binaries_found),
    }

    if binaries_found:
        summary += f" | 二进制: {len(binaries_found)} 个 ({details['total_binary_size_mb']:.1f}MB)"

    return GateReport(
        phase=PipelinePhase.REVERSE,
        status=status,
        summary=summary,
        details=details,
        risk_level=risk,
    )


def _get_recommendation(license_type: str, binaries: list) -> str:
    """根据许可证类型生成建议"""
    if license_type == "Proprietary":
        return "⚠ 专有软件 — 仅可在授权范围内分析，禁止分发修改"
    elif license_type == "MIT":
        return "✓ MIT 许可证 — 自由使用、修改、分发，仅需保留版权声明"
    elif license_type in ("GPL-2.0", "GPL-3.0"):
        return "⚠ GPL 许可证 — 修改后分发需开源（传染性），内部使用无限制"
    elif license_type == "Apache-2.0":
        return "✓ Apache 许可证 — 自由使用，需保留版权和专利声明"
    elif binaries:
        return "⚠ 存在二进制文件 — 建议先确认许可证再处理"
    return "✓ 无已知许可证限制"


if __name__ == "__main__":
    report = reverse_phase(Path("/python"), "AI-Platform", "test_run")
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
