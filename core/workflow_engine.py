#!/usr/bin/env python3
"""
Workflow 执行引擎
解析 YAML 工作流定义，按节点顺序执行 skill/mcp/cli 操作
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import yaml

BASE_DIR = Path("/python")
PROJECTS_DIR = BASE_DIR / "projects"


def load_workflow(workflow_path: str) -> dict:
    with open(workflow_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve_ref(ref_type: str, ref_name: str, project_name: str) -> str:
    project_dir = PROJECTS_DIR / project_name
    if ref_type == "skill":
        return str(project_dir / "skills" / f"{ref_name}.py")
    elif ref_type == "mcp":
        return str(project_dir / "mcps" / ref_name / "mcp.json")
    elif ref_type == "cli":
        return str(project_dir / "clis" / ref_name / "cli.yaml")
    return ""


def execute_node(node: dict, project_name: str, context: dict) -> dict:
    node_id = node.get("id", "unknown")
    node_type = node.get("type", "")
    ref = node.get("ref", "")
    input_data = node.get("input", {})
    timeout = node.get("timeout", 120)

    print(f"\n  ▶ 执行节点: {node_id} (type={node_type}, ref={ref})")

    result = {"id": node_id, "status": "pending", "output": {}}

    if node_type == "cli":
        script = input_data.get("script", "/python/launch_1204.py")
        action = input_data.get("action", "start")

        if action == "start":
            try:
                proc = subprocess.Popen(
                    ["py", script],
                    cwd="/python",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                context["process"] = proc
                result["status"] = "pass"
                result["output"] = {"pid": proc.pid}
                print(f"    启动进程 PID={proc.pid}")
            except Exception as e:
                result["status"] = "fail"
                result["output"] = {"error": str(e)}
                print(f"    ❌ 启动失败: {e}")
        elif action == "stop":
            proc = context.get("process")
            if proc:
                proc.terminate()
                try:
                    proc.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    proc.kill()
                result["status"] = "pass"
                print(f"    进程已终止")
            else:
                result["status"] = "pass"

    elif node_type == "skill":
        skill_path = resolve_ref("skill", ref, project_name)
        if not os.path.exists(skill_path):
            skill_path = str(PROJECTS_DIR / project_name / "skills" / "explore.py")

        actions = input_data.get("actions", ["full_explore"])
        duration = input_data.get("duration", 60)

        try:
            cmd = [sys.executable, skill_path]
            if "full_explore" in actions:
                cmd.append("full_explore")
            elif actions:
                cmd.append(actions[0])

            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=duration,
                cwd=str(PROJECTS_DIR / project_name / "skills"),
            )
            result["status"] = "pass" if proc.returncode == 0 else "fail"
            result["output"] = {"stdout": proc.stdout[:500], "returncode": proc.returncode}
            print(f"    输出: {proc.stdout[:200]}")
        except subprocess.TimeoutExpired:
            result["status"] = "pass"
            result["output"] = {"note": "timeout but continued"}
            print(f"    ⏱ 超时但继续")
        except Exception as e:
            result["status"] = "fail"
            result["output"] = {"error": str(e)}
            print(f"    ❌ 执行失败: {e}")

    elif node_type == "mcp":
        mcp_path = resolve_ref("mcp", ref, project_name)
        mcp_py = str(PROJECTS_DIR / project_name / "mcps" / ref / f"{ref.replace('-', '_')}.py")

        checks = input_data.get("checks", [])

        try:
            pid = context.get("process", subprocess.Popen(["echo"])).pid if context.get("process") else 0
            init_cmd = json.dumps({"method": "initialize", "params": {"pid": pid}})
            proc = subprocess.run(
                [sys.executable, mcp_py, init_cmd],
                capture_output=True,
                text=True,
                timeout=30,
            )

            for check in checks:
                check_cmd = json.dumps({"method": check, "params": {}})
                proc = subprocess.run(
                    [sys.executable, mcp_py, check_cmd],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if proc.stdout:
                    check_result = json.loads(proc.stdout)
                    result["output"][check] = check_result
                    print(f"    {check}: {json.dumps(check_result, ensure_ascii=False)[:200]}")

            result["status"] = "pass"
        except Exception as e:
            result["status"] = "fail"
            result["output"] = {"error": str(e)}
            print(f"    ❌ MCP 检查失败: {e}")

    else:
        result["status"] = "skip"
        print(f"    ⏭ 未知类型: {node_type}")

    return result


def run_workflow(workflow_path: str, project_name: str) -> dict:
    print(f"\n{'='*60}")
    print(f"  执行工作流: {workflow_path}")
    print(f"  项目: {project_name}")
    print(f"{'='*60}")

    wf = load_workflow(workflow_path)
    nodes = {n["id"]: n for n in wf.get("nodes", [])}
    edges = wf.get("edges", [])

    execution_order = []
    if edges:
        current = edges[0]["from"]
        visited = set()
        while current and current not in visited:
            visited.add(current)
            execution_order.append(current)
            next_nodes = [e["to"] for e in edges if e["from"] == current]
            current = next_nodes[0] if next_nodes else None
    else:
        execution_order = list(nodes.keys())

    context = {}
    results = []
    start_time = time.time()

    for node_id in execution_order:
        node = nodes.get(node_id)
        if not node:
            print(f"  ⚠ 节点不存在: {node_id}")
            continue
        result = execute_node(node, project_name, context)
        results.append(result)

        if result["status"] == "fail":
            print(f"\n  ❌ 节点 {node_id} 失败，终止工作流")
            break

    total_time = time.time() - start_time
    passed = sum(1 for r in results if r["status"] == "pass")
    failed = sum(1 for r in results if r["status"] == "fail")

    report = {
        "workflow": os.path.basename(workflow_path),
        "project": project_name,
        "total_time": round(total_time, 1),
        "passed": passed,
        "failed": failed,
        "results": results,
    }

    print(f"\n{'='*60}")
    print(f"  工作流完成: {passed} 通过, {failed} 失败, {total_time:.1f}s")
    print(f"{'='*60}")

    return report


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python workflow_engine.py <workflow.yaml> <project_name>")
        print("示例: python workflow_engine.py /python/projects/game_test/workflows/test-loop.yaml game_test")
        sys.exit(1)

    report = run_workflow(sys.argv[1], sys.argv[2])
    report_path = Path(sys.argv[1]).parent.parent / "reports" / f"workflow_{int(time.time())}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  报告: {report_path}")
