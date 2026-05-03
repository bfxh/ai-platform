import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

class FullChecker:
    def __init__(self):
        self.plugin_dir = Path(__file__).parent
        self.skills_dir = self.plugin_dir / "skills"
        self.config_file = self.plugin_dir / "config.json"
        self.project_configs_dir = self.plugin_dir / "project_configs"
        self.load_config()

    def load_config(self):
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = {
                "enabled_skills": [],
                "project_configs": {},
                "check_history": []
            }
            self.save_config()

    def save_config(self):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def get_available_skills(self) -> List[str]:
        skills = []
        if self.skills_dir.exists():
            for skill_dir in self.skills_dir.iterdir():
                if skill_dir.is_dir():
                    skill_file = skill_dir / "SKILL.md"
                    if skill_file.exists():
                        skills.append(skill_dir.name)
        return skills

    def register_skill(self, skill_name: str, skill_path: str):
        if skill_name not in self.config["enabled_skills"]:
            self.config["enabled_skills"].append(skill_name)
            self.save_config()

    def get_project_config(self, project_name: str) -> Optional[Dict]:
        project_name_lower = project_name.lower()
        if project_name_lower in self.config["project_configs"]:
            return self.config["project_configs"][project_name_lower]
        return None

    def set_project_config(self, project_name: str, config: Dict):
        project_name_lower = project_name.lower()
        self.config["project_configs"][project_name_lower] = config
        self.save_config()

    def get_project_type(self, project_path: str) -> str:
        project_path_obj = Path(project_path)
        if (project_path_obj / "package.json").exists():
            return "nodejs"
        elif (project_path_obj / "requirements.txt").exists() or (project_path_obj / "pyproject.toml").exists():
            return "python"
        elif (project_path_obj / "Cargo.toml").exists():
            return "rust"
        elif (project_path_obj / "pom.xml").exists() or (project_path_obj / "build.gradle").exists():
            return "java"
        elif (project_path_obj / "go.mod").exists():
            return "go"
        elif (project_path_obj / ".git").exists():
            return "generic"
        return "unknown"

    def run_check(self, project_path: str, project_name: str = None, check_types: List[str] = None) -> Dict[str, Any]:
        result = {
            "success": True,
            "project_path": project_path,
            "project_name": project_name or Path(project_path).name,
            "project_type": self.get_project_type(project_path),
            "checks": {},
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }

        project_config = self.get_project_config(project_name) if project_name else None

        if check_types is None:
            check_types = ["code_quality", "testing", "documentation", "security", "dependencies"]

        for check_type in check_types:
            check_result = self._run_check_by_type(check_type, project_path, project_config)
            result["checks"][check_type] = check_result

            result["summary"]["total"] += 1
            if check_result["status"] == "passed":
                result["summary"]["passed"] += 1
            elif check_result["status"] == "failed":
                result["summary"]["failed"] += 1
            elif check_result["status"] == "warning":
                result["summary"]["warnings"] += 1

        self.config["check_history"].append({
            "project": result["project_name"],
            "timestamp": str(Path().cwd()),
            "result": result["summary"]
        })
        self.save_config()

        return result

    def _run_check_by_type(self, check_type: str, project_path: str, project_config: Optional[Dict]) -> Dict:
        check_map = {
            "code_quality": self._check_code_quality,
            "testing": self._check_testing,
            "documentation": self._check_documentation,
            "security": self._check_security,
            "dependencies": self._check_dependencies
        }

        if check_type in check_map:
            return check_map[check_type](project_path, project_config)
        return {"status": "skipped", "message": f"Unknown check type: {check_type}"}

    def _check_code_quality(self, project_path: str, project_config: Optional[Dict]) -> Dict:
        issues = []
        path_obj = Path(project_path)

        for pattern in ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx"]:
            for file in path_obj.rglob(pattern):
                if "node_modules" in str(file) or "__pycache__" in str(file):
                    continue
                try:
                    with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if len(content) > 10000 and "def " not in content and "class " not in content:
                            issues.append(f"Large file without functions: {file.name}")
                except:
                    pass

        return {
            "status": "passed" if len(issues) == 0 else "warning",
            "message": f"Code quality check completed. Found {len(issues)} issues.",
            "issues": issues
        }

    def _check_testing(self, project_path: str, project_config: Optional[Dict]) -> Dict:
        path_obj = Path(project_path)
        has_tests = False
        test_files = []

        test_patterns = ["test_*.py", "*_test.py", "*.spec.js", "*.test.js", "*.spec.ts", "*.test.ts"]
        for pattern in test_patterns:
            test_files.extend(path_obj.rglob(pattern))

        if test_files:
            has_tests = True

        return {
            "status": "passed" if has_tests else "warning",
            "message": f"Testing check completed. Found {len(test_files)} test files.",
            "test_files": [str(f) for f in test_files[:10]]
        }

    def _check_documentation(self, project_path: str, project_config: Optional[Dict]) -> Dict:
        path_obj = Path(project_path)
        docs_found = []

        for doc_name in ["README.md", "README.txt", "docs", "documentation"]:
            if (path_obj / doc_name).exists():
                docs_found.append(doc_name)

        return {
            "status": "passed" if len(docs_found) > 0 else "warning",
            "message": f"Documentation check completed. Found {len(docs_found)} documentation items.",
            "docs": docs_found
        }

    def _check_security(self, project_path: str, project_config: Optional[Dict]) -> Dict:
        path_obj = Path(project_path)
        issues = []

        for secret_file in [".env", ".env.local", ".env.production"]:
            if (path_obj / secret_file).exists():
                with open(path_obj / secret_file, 'r') as f:
                    content = f.read()
                    if "PASSWORD" in content or "SECRET" in content or "API_KEY" in content:
                        if ".gitignore" in [f.name for f in path_obj.iterdir()]:
                            pass
                        else:
                            issues.append(f"Potential secrets in {secret_file} without .gitignore protection")

        return {
            "status": "passed" if len(issues) == 0 else "warning",
            "message": f"Security check completed. Found {len(issues)} potential issues.",
            "issues": issues
        }

    def _check_dependencies(self, project_path: str, project_config: Optional[Dict]) -> Dict:
        path_obj = Path(project_path)
        outdated = []
        missing_lock = False

        if (path_obj / "package.json").exists() and not (path_obj / "package-lock.json").exists():
            missing_lock = True

        if (path_obj / "requirements.txt").exists() and not (path_obj / "requirements.lock").exists():
            missing_lock = True

        return {
            "status": "warning" if missing_lock else "passed",
            "message": f"Dependency check completed. Missing lock file: {missing_lock}",
            "outdated": outdated
        }

    def list_skills(self) -> List[Dict[str, str]]:
        skills = []
        for skill_name in self.get_available_skills():
            skill_dir = self.skills_dir / skill_name
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                with open(skill_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    description = ""
                    for line in lines[1:]:
                        if line.startswith('##'):
                            break
                        if line.strip():
                            description = line.strip()
                            break
                    skills.append({
                        "name": skill_name,
                        "description": description
                    })
        return skills

    def invoke_skill(self, skill_name: str, project_path: str, params: Dict = None) -> Dict:
        if skill_name not in self.get_available_skills():
            return {"success": False, "error": f"Skill {skill_name} not found"}

        skill_dir = self.skills_dir / skill_name
        skill_file = skill_dir / "SKILL.md"

        return {
            "success": True,
            "skill": skill_name,
            "project_path": project_path,
            "params": params or {},
            "message": f"Skill {skill_name} invoked for project {project_path}"
        }

full_checker_instance = FullChecker()

def get_checker():
    return full_checker_instance