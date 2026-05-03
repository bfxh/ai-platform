import os
import sys
import subprocess
import re
from pathlib import Path

class DependencyChecker:
    def __init__(self):
        self.ai_path = Path("/python")
        self.skills_path = self.ai_path / "MCP_Core" / "skills"
    
    def parse_requirements(self, requirements_file):
        requirements = []
        try:
            content = requirements_file.read_text(encoding='utf-8')
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    requirements.append(line)
        except Exception as e:
            print(f"❌ 解析依赖文件失败: {requirements_file} - {str(e)}")
        return requirements
    
    def check_python_version(self, required_version):
        current_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        print(f"当前 Python 版本: {current_version}")
        
        if required_version.startswith('python'):
            version_spec = required_version.split('>=')[1].strip() if '>=' in required_version else required_version.split('==')[1].strip()
            req_major, req_minor = map(int, version_spec.split('.')[:2])
            cur_major, cur_minor = sys.version_info.major, sys.version_info.minor
            
            if cur_major > req_major or (cur_major == req_major and cur_minor >= req_minor):
                print(f"✅ Python 版本满足要求: {required_version}")
                return True
            else:
                print(f"❌ Python 版本不满足要求: 需要 {required_version}, 当前 {current_version}")
                return False
        return True
    
    def check_package(self, package_spec):
        try:
            if '==' in package_spec:
                package, version = package_spec.split('==')
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'show', package],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if line.startswith('Version:'):
                            installed_version = line.split(':', 1)[1].strip()
                            if installed_version == version:
                                print(f"✅ {package}=={version} 已安装")
                                return True
                            else:
                                print(f"❌ {package} 版本不匹配: 已安装 {installed_version}, 需要 {version}")
                                return False
                else:
                    print(f"❌ {package} 未安装")
                    return False
            elif '>=' in package_spec:
                package, version = package_spec.split('>=')
                version = version.split(',')[0].strip()
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'show', package],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if line.startswith('Version:'):
                            installed_version = line.split(':', 1)[1].strip()
                            if self.version_greater_or_equal(installed_version, version):
                                print(f"✅ {package}>={version} 已安装")
                                return True
                            else:
                                print(f"❌ {package} 版本过低: 已安装 {installed_version}, 需要 >= {version}")
                                return False
                else:
                    print(f"❌ {package} 未安装")
                    return False
            else:
                package = package_spec
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'show', package],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print(f"✅ {package} 已安装")
                    return True
                else:
                    print(f"❌ {package} 未安装")
                    return False
        except Exception as e:
            print(f"❌ 检查包失败: {package_spec} - {str(e)}")
            return False
    
    def version_greater_or_equal(self, v1, v2):
        v1_parts = list(map(int, re.findall(r'\d+', v1)))
        v2_parts = list(map(int, re.findall(r'\d+', v2)))
        return v1_parts >= v2_parts
    
    def check_skill_dependencies(self, skill_name):
        skill_path = self.skills_path / skill_name
        requirements_file = skill_path / "requirements.gstack"
        
        if not requirements_file.exists():
            print(f"⚠️ {skill_name} 缺少 requirements.gstack 文件")
            return True
        
        print(f"\n🔍 检查 {skill_name} 依赖...")
        requirements = self.parse_requirements(requirements_file)
        
        all_met = True
        for req in requirements:
            if req.startswith('python'):
                if not self.check_python_version(req):
                    all_met = False
            else:
                if not self.check_package(req):
                    all_met = False
        
        if all_met:
            print(f"✅ {skill_name} 所有依赖满足")
        else:
            print(f"❌ {skill_name} 依赖不满足")
        
        return all_met
    
    def check_all_skills(self):
        print("🚀 开始检查所有 Skills 依赖...")
        print("=" * 60)
        
        results = {}
        for skill_dir in self.skills_path.iterdir():
            if skill_dir.is_dir():
                skill_name = skill_dir.name
                results[skill_name] = self.check_skill_dependencies(skill_name)
        
        print("\n📊 依赖检查结果:")
        print("=" * 60)
        
        met_count = sum(1 for v in results.values() if v)
        total_count = len(results)
        
        print(f"- 满足依赖: {met_count}/{total_count} ✅")
        print(f"- 依赖缺失: {total_count - met_count}/{total_count} ❌")
        
        if total_count - met_count > 0:
            print("\n❌ 依赖缺失的 Skills:")
            for skill, met in results.items():
                if not met:
                    print(f"- {skill}")
        
        return met_count == total_count


if __name__ == "__main__":
    checker = DependencyChecker()
    if len(sys.argv) > 1:
        checker.check_skill_dependencies(sys.argv[1])
    else:
        checker.check_all_skills()
