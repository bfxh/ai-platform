#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASK (Agent Skill Kit) - TRAE Skill

本地执行的AI技能系统，支持多种AI技能
"""

import os
import sys
import json
import importlib.util
from pathlib import Path


class ASKSkill:
    """ASK Skill 主类"""

    def __init__(self, config=None):
        self.config = config or {}
        self.ask_dir = self.config.get("ask_dir") or Path(r"\python\MCP\Tools\ask")
        self.skills_dir = self.config.get("skills_dir") or self.ask_dir / "skills"
        self.skills = {}
        self._load_skills()

    def _load_skills(self):
        """加载所有技能"""
        if not self.skills_dir.exists():
            self.skills_dir.mkdir(parents=True, exist_ok=True)
            self._create_default_skills()

        for skill_file in self.skills_dir.glob("*.py"):
            skill_name = skill_file.stem
            try:
                spec = importlib.util.spec_from_file_location(skill_name, skill_file)
                skill_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(skill_module)
                if hasattr(skill_module, "run"):
                    self.skills[skill_name] = skill_module
                    print(f"Loaded skill: {skill_name}")
            except Exception as e:
                print(f"Failed to load skill {skill_name}: {e}")

    def _create_default_skills(self):
        """创建默认技能"""
        tech_pulse_content = "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n\"\"\"\n技术脉搏技能\n获取最新的技术新闻和趋势\n\"\"\"\n\ndef run():\n    \"\"\"运行技术脉搏技能\"\"\"\n    try:\n        news = [\n            {\"title\": \"GitHub Fake Star Economy\", \"source\": \"HackerNews\"},\n            {\"title\": \"OpenClaw Review\", \"source\": \"HackerNews\"},\n            {\"title\": \"Bees Underground Network\", \"source\": \"HackerNews\"},\n            {\"title\": \"SDF Public Access Unix\", \"source\": \"HackerNews\"},\n            {\"title\": \"Vercel Security Incident\", \"source\": \"HackerNews\"}\n        ]\n        print(\"Tech Pulse - Latest Tech News\")\n        for i, item in enumerate(news, 1):\n            print(f\"#{i}. {item['title']} - {item['source']}\")\n        return {\"success\": True, \"data\": news}\n    except Exception as e:\n        return {\"success\": False, \"error\": str(e)}\n"

        repo_visualizer_content = "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n\"\"\"\n仓库可视化技能\n分析GitHub仓库结构\n\"\"\"\n\nimport os\nfrom pathlib import Path\n\ndef run(repo_path=None):\n    \"\"\"运行仓库可视化技能\"\"\"\n    try:\n        if not repo_path:\n            repo_path = os.getcwd()\n        repo_path = Path(repo_path)\n        if not repo_path.exists():\n            return {\"success\": False, \"error\": \"Path does not exist\"}\n        print(f\"Repo Visualizer - {repo_path.name}\")\n        print(\"=\" * 50)\n        file_types = {}\n        total_files = 0\n        for file in repo_path.rglob(\"*.*\"):\n            if file.is_file():\n                ext = file.suffix.lower()\n                file_types[ext] = file_types.get(ext, 0) + 1\n                total_files += 1\n        print(f\"Total files: {total_files}\")\n        print(\"File types:\")\n        for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:10]:\n            print(f\"  {ext}: {count}\")\n        return {\"success\": True, \"data\": {\"total_files\": total_files, \"file_types\": file_types}}\n    except Exception as e:\n        return {\"success\": False, \"error\": str(e)}\n"

        architect_content = "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n\"\"\"\n架构师技能\n从自然语言描述生成新技能\n\"\"\"\n\nimport os\nfrom pathlib import Path\n\ndef run(description):\n    \"\"\"运行架构师技能\"\"\"\n    try:\n        if not description:\n            return {\"success\": False, \"error\": \"Please provide description\"}\n        print(f\"Architect - Generate skill: {description}\")\n        skill_name = description.lower().replace(\" \", \"_\").replace(\"-\", \"_\").strip()\n        skill_name = \"\".join(c for c in skill_name if c.isalnum() or c == \"_\")\n        skill_template = \"#!/usr/bin/env python3\\n# -*- coding: utf-8 -*-\\n\\\"\\\"\\\"\\nDESCRIPTION\\n\\\"\\\"\\\"\\n\\ndef run():\\n    \\\"\\\"\\\"Run skill\\\"\\\"\\\"\\n    try:\\n        print(\\\"Running skill\\\")\\n        return {\\\"success\\\": True, \\\"data\\\": {\\\"message\\\": \\\"Skill executed\\\"}}\\n    except Exception as e:\\n        return {\\\"success\\\": False, \\\"error\\\": str(e)}\\n\"\n        skill_code = skill_template.replace(\"DESCRIPTION\", description)\n        skills_dir = Path(__file__).parent\n        (skills_dir / f\"{skill_name}.py\").write_text(skill_code, encoding=\"utf-8\")\n        print(f\"Skill generated: {skill_name}.py\")\n        print(f\"Location: {skills_dir}/{skill_name}.py\")\n        return {\"success\": True, \"data\": {\"skill_name\": skill_name, \"path\": str(skills_dir / f\"{skill_name}.py\")}}\n    except Exception as e:\n        return {\"success\": False, \"error\": str(e)}\n"

        (self.skills_dir / "tech_pulse.py").write_text(tech_pulse_content, encoding='utf-8')
        (self.skills_dir / "repo_visualizer.py").write_text(repo_visualizer_content, encoding='utf-8')
        (self.skills_dir / "architect.py").write_text(architect_content, encoding='utf-8')

    def list_skills(self):
        """列出所有可用技能"""
        print("Available skills:")
        for skill_name in sorted(self.skills.keys()):
            print(f"  - {skill_name}")
        return list(self.skills.keys())

    def run_skill(self, skill_name, *args, **kwargs):
        """运行指定技能"""
        if skill_name not in self.skills:
            print(f"Skill not found: {skill_name}")
            return {"success": False, "error": f"Skill not found: {skill_name}"}

        try:
            skill_module = self.skills[skill_name]
            import inspect
            sig = inspect.signature(skill_module.run)
            params = list(sig.parameters.keys())

            if len(params) == 0:
                result = skill_module.run()
            else:
                result = skill_module.run(*args, **kwargs)
            return result
        except Exception as e:
            print(f"Skill execution failed: {e}")
            return {"success": False, "error": str(e)}


def execute(command, **kwargs):
    """执行ASK命令"""
    ask_skill = ASKSkill(kwargs.get("config", {}))

    if command == "dashboard":
        return {
            "success": True,
            "data": {
                "skills": ask_skill.list_skills()
            }
        }
    elif command == "run":
        skill_name = kwargs.get("skill_name")
        skill_args = kwargs.get("skill_args", [])
        if not skill_name:
            return {"success": False, "error": "Please specify skill name"}
        result = ask_skill.run_skill(skill_name, *skill_args)
        return result
    else:
        return {"success": False, "error": f"Unknown command: {command}"}


if __name__ == "__main__":
    ask_skill = ASKSkill()
    ask_skill.list_skills()
