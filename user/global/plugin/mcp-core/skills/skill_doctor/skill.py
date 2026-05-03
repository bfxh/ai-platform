import os
import json
import shutil
from pathlib import Path
from datetime import datetime

class SkillDoctor:
    def __init__(self):
        self.ai_path = Path("/python")
        self.skills_path = self.ai_path / "MCP_Core" / "skills"
        self.cc_old_path = self.ai_path / "CC" / "2_Old" / "Skills"
        self.config_file = self.ai_path / "MCP" / "mcp-config.json"
        self.issues = []
        self.fixed = []
        
    def check_skill_dependencies(self, skill_path):
        try:
            with open(skill_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            issues = []
            
            if "import" in content:
                for line in content.split('\n'):
                    if line.strip().startswith("import ") or line.strip().startswith("from "):
                        module = line.strip().split()[1].split('.')[0]
                        try:
                            __import__(module)
                        except ImportError:
                            issues.append(f"Missing dependency: {module}")
            
            return issues
        except Exception as e:
            return [f"Error checking dependencies: {str(e)}"]
    
    def check_skill_exists(self, skill_name):
        skill_dir = self.skills_path / skill_name
        skill_file = skill_dir / "skill.py"
        return skill_file.exists(), skill_file
    
    def run_diagnostics(self):
        print("🔍 开始 Skills 自检...")
        print("=" * 50)
        
        results = {
            "total": 0,
            "working": 0,
            "broken": 0,
            "details": []
        }
        
        if not self.skills_path.exists():
            print(f"❌ Skills 目录不存在: {self.skills_path}")
            return results
        
        for skill_dir in self.skills_path.iterdir():
            if not skill_dir.is_dir():
                continue
                
            skill_name = skill_dir.name
            results["total"] += 1
            
            skill_file = skill_dir / "skill.py"
            skill_json = skill_dir / "skill.json"
            
            status = "✅"
            issues = []
            
            if not skill_file.exists():
                status = "❌"
                issues.append("skill.py 不存在")
            else:
                deps = self.check_skill_dependencies(skill_file)
                if deps:
                    status = "⚠️"
                    issues.extend(deps)
            
            if not skill_json.exists():
                issues.append("skill.json 不存在")
            
            detail = {
                "name": skill_name,
                "status": status,
                "issues": issues,
                "path": str(skill_dir)
            }
            results["details"].append(detail)
            
            if issues:
                results["broken"] += 1
            else:
                results["working"] += 1
            
            if status == "❌":
                self.issues.append(f"❌ {skill_name}: {', '.join(issues)}")
            elif status == "⚠️":
                self.issues.append(f"⚠️ {skill_name}: {', '.join(issues)}")
        
        return results
    
    def print_report(self, results):
        print(f"\n📊 自检报告")
        print("=" * 50)
        print(f"总 Skills 数: {results['total']}")
        print(f"正常: {results['working']} ✅")
        print(f"异常: {results['broken']} ⚠️")
        print()
        
        if self.issues:
            print("🔎 发现问题:")
            for issue in self.issues:
                print(f"  {issue}")
        else:
            print("✅ 所有 Skills 检查通过!")
        
        print()
        
        for detail in results["details"]:
            if detail["issues"]:
                print(f"{detail['status']} {detail['name']}")
                for issue in detail["issues"]:
                    print(f"   - {issue}")
        
        return len(self.issues) == 0
    
    def rollback_skill(self, skill_name):
        print(f"\n🔄 尝试回滚 {skill_name}...")
        
        skill_source = self.skills_path / skill_name
        skill_backup = self.cc_old_path / skill_name
        
        if not skill_source.exists():
            print(f"❌ 源技能不存在: {skill_source}")
            return False
        
        skill_source.mkdir(parents=True, exist_ok=True)
        skill_backup.mkdir(parents=True, exist_ok=True)
        
        for item in skill_source.iterdir():
            if item.is_file():
                shutil.copy2(item, skill_backup / item.name)
        
        print(f"✅ 已备份当前版本到: {skill_backup}")
        print(f"💡 可手动从 CC/2_Old/Skills/{skill_name} 恢复旧版本")
        
        return True
    
    def execute(self, command="diagnose"):
        if command == "diagnose":
            results = self.run_diagnostics()
            self.print_report(results)
            return results
        elif command == "doctor":
            results = self.run_diagnostics()
            self.print_report(results)
            if results["broken"] > 0:
                print("\n💡 提示: 可使用 skill:rollback <name> 回滚问题技能")
            return results
        else:
            return f"未知命令: {command}"


if __name__ == "__main__":
    import sys
    doctor = SkillDoctor()
    
    cmd = sys.argv[1] if len(sys.argv) > 1 else "diagnose"
    doctor.execute(cmd)
