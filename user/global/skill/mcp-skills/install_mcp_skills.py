import os
import json
import shutil
from pathlib import Path

print("=" * 80)
print("泰拉瑞亚模组优化 - MCP技能安装脚本")
print("=" * 80)
print()

skills_source = Path("/python/MCP_Skills")
workflows_source = Path("/python/MCP_Workflows")

install_base = Path("/python/.mcp")
skills_target = install_base / "skills"
workflows_target = install_base / "workflows"

print("步骤1: 创建安装目录...")
print()

for dir_path in [install_base, skills_target, workflows_target]:
    if not dir_path.exists():
        dir_path.mkdir(parents=True)
        print(f"✓ 创建目录: {dir_path}")
    else:
        print(f"✓ 目录已存在: {dir_path}")

print()
print("步骤2: 安装技能文件...")
print()

skill_files = list(skills_source.glob("*.json"))
skill_count = 0

for skill_file in skill_files:
    if skill_file.name == "registry.json":
        continue
    
    target_file = skills_target / skill_file.name
    shutil.copy2(skill_file, target_file)
    print(f"✓ 安装技能: {skill_file.stem}")
    skill_count += 1

print()
print("步骤3: 安装工作流文件...")
print()

workflow_files = list(workflows_source.glob("*.json"))
workflow_count = 0

for workflow_file in workflow_files:
    target_file = workflows_target / workflow_file.name
    shutil.copy2(workflow_file, target_file)
    print(f"✓ 安装工作流: {workflow_file.stem}")
    workflow_count += 1

print()
print("步骤4: 安装注册表...")
print()

registry_source = skills_source / "registry.json"
registry_target = install_base / "registry.json"
shutil.copy2(registry_source, registry_target)
print(f"✓ 安装注册表: registry.json")

print()
print("步骤5: 安装执行器...")
print()

executor_source = skills_source / "mcp_skills.py"
executor_target = install_base / "mcp_skills.py"
shutil.copy2(executor_source, executor_target)
print(f"✓ 安装执行器: mcp_skills.py")

print()
print("步骤6: 创建配置文件...")
print()

config = {
    "version": "1.0.0",
    "install_path": str(install_base),
    "skills_path": str(skills_target),
    "workflows_path": str(workflows_target),
    "registry_path": str(registry_target),
    "installed_skills": skill_count,
    "installed_workflows": workflow_count,
    "install_date": "2026-04-05"
}

config_file = install_base / "config.json"
with open(config_file, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
print(f"✓ 创建配置文件: config.json")

print()
print("=" * 80)
print("安装完成！")
print()
print(f"已安装技能: {skill_count} 个")
print(f"已安装工作流: {workflow_count} 个")
print()
print("使用方法:")
print("  cd /python\\.mcp")
print("  python mcp_skills.py list              # 列出所有技能")
print("  python mcp_skills.py workflows         # 列出所有工作流")
print("  python mcp_skills.py execute <skill>   # 执行技能")
print("  python mcp_skills.py run <workflow>    # 运行工作流")
print("  python mcp_skills.py help <skill>      # 查看帮助")
print()
print("快速开始:")
print("  python mcp_skills.py run terraria-gpu-optimization-workflow")
print("=" * 80)
