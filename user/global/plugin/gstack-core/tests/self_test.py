import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

class GStackSelfTest:
    def __init__(self):
        self.ai_path = Path("/python")
        self.gstack_path = self.ai_path / "gstack_core"
        self.tests_path = self.gstack_path / "tests"
        self.results = []
        
        self.tests_path.mkdir(parents=True, exist_ok=True)
    
    def test_mcp_directory_structure(self):
        print("🔍 测试 MCP 目录结构...")
        
        required_dirs = {
            "JM": self.ai_path / "MCP" / "JM",
            "BC": self.ai_path / "MCP" / "BC",
            "Tools": self.ai_path / "MCP" / "Tools"
        }
        
        all_pass = True
        for name, path in required_dirs.items():
            if path.exists():
                file_count = len(list(path.rglob("*.py")))
                self.results.append({
                    "test": f"mcp_dir_{name}",
                    "status": "pass",
                    "message": f"{name} 目录正常 ({file_count} 个 Python 文件)"
                })
                print(f"  ✅ {name}: {file_count} 个文件")
            else:
                self.results.append({
                    "test": f"mcp_dir_{name}",
                    "status": "fail",
                    "message": f"{name} 目录缺失: {path}"
                })
                print(f"  ❌ {name} 目录缺失")
                all_pass = False
        
        return all_pass
    
    def test_skills_structure(self):
        print("\n🔍 测试 Skills 结构...")
        
        skills_path = self.ai_path / "MCP_Core" / "skills"
        if not skills_path.exists():
            self.results.append({
                "test": "skills_dir",
                "status": "fail",
                "message": "Skills 目录缺失"
            })
            return False
        
        skill_count = 0
        valid_skills = 0
        
        for skill_dir in skills_path.iterdir():
            if skill_dir.is_dir():
                skill_count += 1
                skill_py = skill_dir / "skill.py"
                skill_json = skill_dir / "skill.json"
                
                if skill_py.exists() and skill_json.exists():
                    valid_skills += 1
        
        self.results.append({
            "test": "skills_structure",
            "status": "pass" if valid_skills > 0 else "fail",
            "message": f"Skills: {valid_skills}/{skill_count} 个结构完整"
        })
        
        print(f"  📊 Skills 总数: {skill_count}")
        print(f"  ✅ 结构完整: {valid_skills} 个")
        
        return valid_skills > 0
    
    def test_architecture_config(self):
        print("\n🔍 测试架构配置文件...")
        
        config_file = self.ai_path / "ai_architecture.json"
        if not config_file.exists():
            self.results.append({
                "test": "architecture_config",
                "status": "fail",
                "message": "ai_architecture.json 不存在"
            })
            return False
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            required_fields = ["version", "gstack", "mcp", "skills", "cc"]
            missing = []
            
            for field in required_fields:
                if field not in config:
                    missing.append(field)
            
            if missing:
                self.results.append({
                    "test": "architecture_config",
                    "status": "fail",
                    "message": f"缺少字段: {', '.join(missing)}"
                })
                return False
            
            self.results.append({
                "test": "architecture_config",
                "status": "pass",
                "message": f"架构配置正常 (v{config.get('version', '?')})"
            })
            print(f"  ✅ 架构配置正常 (v{config.get('version', '?')})")
            return True
            
        except Exception as e:
            self.results.append({
                "test": "architecture_config",
                "status": "fail",
                "message": f"配置文件错误: {str(e)}"
            })
            return False
    
    def test_project_rules(self):
        print("\n🔍 测试 TRAE 规则文件...")
        
        rules_dir = self.ai_path / ".trae"
        required_rules = ["project_rules.md", "user_rules.md"]
        
        all_pass = True
        for rule_file in required_rules:
            path = rules_dir / rule_file
            if path.exists():
                self.results.append({
                    "test": f"rule_{rule_file}",
                    "status": "pass",
                    "message": f"{rule_file} 存在"
                })
                print(f"  ✅ {rule_file}")
            else:
                self.results.append({
                    "test": f"rule_{rule_file}",
                    "status": "fail",
                    "message": f"{rule_file} 缺失"
                })
                print(f"  ❌ {rule_file} 缺失")
                all_pass = False
        
        return all_pass
    
    def test_cc_directory(self):
        print("\n🔍 测试 CC 缓存目录...")
        
        cc_path = self.ai_path / "CC"
        required_subdirs = ["1_Raw", "2_Old", "3_Unused"]
        
        all_exist = True
        for subdir in required_subdirs:
            path = cc_path / subdir
            if path.exists():
                print(f"  ✅ {subdir} 存在")
            else:
                print(f"  ⚠️ {subdir} 不存在 (可选)")
        
        self.results.append({
            "test": "cc_directory",
            "status": "pass",
            "message": "CC 目录结构正常"
        })
        
        return True
    
    def test_protection_marker(self):
        print("\n🔍 测试架构保护标记...")
        
        marker = self.ai_path / ".gstack_protected"
        if marker.exists():
            self.results.append({
                "test": "protection_marker",
                "status": "pass",
                "message": "保护标记文件存在"
            })
            print(f"  ✅ .gstack_protected 存在")
        else:
            self.results.append({
                "test": "protection_marker",
                "status": "warn",
                "message": "保护标记文件不存在"
            })
            print(f"  ⚠️ .gstack_protected 不存在")
        
        return True
    
    def run_all_tests(self):
        print("🚀 开始 GSTACK 自举测试...")
        print("=" * 60)
        
        self.test_mcp_directory_structure()
        self.test_skills_structure()
        self.test_architecture_config()
        self.test_project_rules()
        self.test_cc_directory()
        self.test_protection_marker()
        
        print("\n" + "=" * 60)
        print("📊 测试结果汇总:")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if r['status'] == 'pass')
        failed = sum(1 for r in self.results if r['status'] == 'fail')
        warnings = sum(1 for r in self.results if r['status'] == 'warn')
        total = len(self.results)
        
        print(f"总测试数: {total}")
        print(f"通过: {passed} ✅")
        print(f"失败: {failed} ❌")
        print(f"警告: {warnings} ⚠️")
        
        if failed > 0:
            print("\n❌ 失败的测试:")
            for r in self.results:
                if r['status'] == 'fail':
                    print(f"  - {r['test']}: {r['message']}")
        
        if warnings > 0:
            print("\n⚠️ 警告:")
            for r in self.results:
                if r['status'] == 'warn':
                    print(f"  - {r['test']}: {r['message']}")
        
        return failed == 0
    
    def save_results(self):
        result_file = self.tests_path / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "results": self.results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 测试结果已保存: {result_file}")


if __name__ == "__main__":
    tester = GStackSelfTest()
    success = tester.run_all_tests()
    tester.save_results()
    
    sys.exit(0 if success else 1)
