import os
import sys
import shutil
import json
from pathlib import Path

class SkillForker:
    def __init__(self):
        self.ai_path = Path("/python")
        self.skills_path = self.ai_path / "MCP_Core" / "skills"
    
    def fork_skill(self, skill_name, target_project):
        skill_source = self.skills_path / skill_name
        if not skill_source.exists():
            print(f"❌ 技能不存在: {skill_name}")
            return False
        
        target_path = Path(target_project) / ".gstack" / "skills" / skill_name
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"🔄 克隆技能 {skill_name} 到 {target_path}")
        
        for item in skill_source.iterdir():
            if item.is_file():
                dest_file = target_path / item.name
                shutil.copy2(item, dest_file)
                print(f"✅ 复制: {item.name}")
                
                if item.name == "skill.py":
                    self.update_paths(dest_file, target_project)
            elif item.is_dir():
                dest_dir = target_path / item.name
                shutil.copytree(item, dest_dir)
                print(f"✅ 复制目录: {item.name}")
        
        print(f"\n✅ 技能 {skill_name} 克隆完成！")
        print(f"📁 位置: {target_path}")
        print("💡 提示: 项目本地技能优先级高于全局技能")
        return True
    
    def update_paths(self, skill_file, project_path):
        try:
            content = skill_file.read_text(encoding='utf-8')
            
            project_path_abs = str(Path(project_path).absolute())
            ai_path_abs = str(self.ai_path.absolute())
            
            updated_content = content.replace(ai_path_abs, project_path_abs)
            
            skill_file.write_text(updated_content, encoding='utf-8')
            print(f"✅ 更新路径引用: {skill_file.name}")
        except Exception as e:
            print(f"⚠️ 更新路径失败: {str(e)}")
    
    def list_skills(self):
        print("📋 可用技能列表:")
        print("=" * 60)
        
        for skill_dir in self.skills_path.iterdir():
            if skill_dir.is_dir():
                skill_name = skill_dir.name
                skill_json = skill_dir / "skill.json"
                
                if skill_json.exists():
                    try:
                        with open(skill_json, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        description = config.get('description', '无描述')
                        print(f"- {skill_name}: {description}")
                    except:
                        print(f"- {skill_name}: 配置文件错误")
                else:
                    print(f"- {skill_name}: 缺少 skill.json")
    
    def check_project_skills(self, project_path):
        project_skills_path = Path(project_path) / ".gstack" / "skills"
        
        if not project_skills_path.exists():
            print(f"❌ 项目 {project_path} 没有本地技能")
            return
        
        print(f"📋 项目 {project_path} 的本地技能:")
        print("=" * 60)
        
        for skill_dir in project_skills_path.iterdir():
            if skill_dir.is_dir():
                skill_name = skill_dir.name
                print(f"- {skill_name}")


if __name__ == "__main__":
    forker = SkillForker()
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python skill_forker.py list - 列出可用技能")
        print("  python skill_forker.py fork <skill_name> <project_path> - 克隆技能到项目")
        print("  python skill_forker.py check <project_path> - 检查项目本地技能")
    elif sys.argv[1] == "list":
        forker.list_skills()
    elif sys.argv[1] == "fork" and len(sys.argv) == 4:
        forker.fork_skill(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "check" and len(sys.argv) == 3:
        forker.check_project_skills(sys.argv[2])
    else:
        print("❌ 参数错误")
