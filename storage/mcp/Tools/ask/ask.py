#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent Skill Kit (ASK) - 集成到 GSTACK

功能:
- 本地执行的AI agent skill框架
- 无API密钥依赖
- 与GSTACK架构集成
- 支持多种AI平台
"""

import os
import sys
import json
import importlib.util
from pathlib import Path


class ASK:
    """Agent Skill Kit 主类"""

    def __init__(self, root_dir=None):
        # 确保路径正确，避免控制字符
        self.root_dir = root_dir or Path(r"\python\MCP\Tools\ask")
        self.skills_dir = self.root_dir / "skills"
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
                    print(f"✅ 加载技能: {skill_name}")
            except Exception as e:
                print(f"❌ 加载技能失败 {skill_name}: {e}")

    def _create_default_skills(self):
        """创建默认技能"""
        # 技术脉搏技能
        tech_pulse_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术脉搏技能
获取最新的技术新闻和趋势
"""

import requests
import json

def run():
    """运行技术脉搏技能"""
    try:
        # 使用免费的新闻API
        url = "https://newsapi.org/v2/top-headlines?category=technology&pageSize=5&apiKey=YOUR_API_KEY"
        # 注意：这里需要替换为真实的API密钥
        # 或者使用其他免费的新闻源
        
        # 模拟数据
        news = [
            {"title": "GitHub's Fake Star Economy", "source": "HackerNews"},
            {"title": "OpenClaw isn't fooling me. I remember MS-DOS", "source": "HackerNews"},
            {"title": "Up to 8M Bees Are Living in an Underground Network Beneath This Cemetery", "source": "HackerNews"},
            {"title": "SDF Public Access Unix System", "source": "HackerNews"},
            {"title": "Vercel April 2026 security incident", "source": "HackerNews"}
        ]
        
        print("📊 技术脉搏 - 最新技术新闻")
        for i, item in enumerate(news, 1):
            print(f"#{i}. {item['title']} - {item['source']}")
        
        return {"success": True, "data": news}
    except Exception as e:
        return {"success": False, "error": str(e)}
'''
        
        # 仓库可视化技能
        repo_visualizer_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仓库可视化技能
分析GitHub仓库结构
"""

import os
from pathlib import Path

def run(repo_path=None):
    """运行仓库可视化技能"""
    try:
        if not repo_path:
            repo_path = os.getcwd()
        
        repo_path = Path(repo_path)
        if not repo_path.exists():
            return {"success": False, "error": "仓库路径不存在"}
        
        print(f"📁 仓库可视化 - {repo_path.name}")
        print("=" * 50)
        
        # 统计文件类型
        file_types = {}
        total_files = 0
        
        for file in repo_path.rglob("*.*"):
            if file.is_file():
                ext = file.suffix.lower()
                file_types[ext] = file_types.get(ext, 0) + 1
                total_files += 1
        
        print(f"📊 总文件数: {total_files}")
        print("📋 文件类型分布:")
        for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {ext}: {count}")
        
        # 查找主要文件
        main_files = []
        for pattern in ["README*", "setup.*", "requirements.*", "package.*", "Makefile"]:
            for file in repo_path.glob(pattern):
                main_files.append(file.name)
        
        if main_files:
            print("\n🔍 主要文件:")
            for file in main_files:
                print(f"  - {file}")
        
        return {"success": True, "data": {"total_files": total_files, "file_types": file_types}}
    except Exception as e:
        return {"success": False, "error": str(e)}
'''
        
        # 架构师技能
        architect_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
架构师技能
从自然语言描述生成新技能
"""

import os
from pathlib import Path

def run(description):
    """运行架构师技能"""
    try:
        if not description:
            return {"success": False, "error": "请提供技能描述"}
        
        print(f"🏗️  架构师 - 生成技能: {description}")
        
        # 生成技能名称
        skill_name = description.lower().replace(" ", "_").replace("-", "_").strip()
        skill_name = ''.join(c for c in skill_name if c.isalnum() or c == '_')
        
        # 生成技能代码
        skill_code = f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{description}
"""

def run():
    """运行技能"""
    try:
        print("运行 {description} 技能")
        # 实现技能逻辑
        return {"success": True, "data": {"message": "技能执行成功"}}
    except Exception as e:
        return {"success": False, "error": str(e)}
"""
        
        # 保存技能文件
        skills_dir = self.skills_dir
        (skills_dir / f"{skill_name}.py").write_text(skill_code)
        
        print(f"✅ 技能生成成功: {skill_name}.py")
        print(f"📁 保存位置: {skills_dir}/{skill_name}.py")
        
        return {"success": True, "data": {"skill_name": skill_name, "path": str(skills_dir / f"{skill_name}.py")}}
    except Exception as e:
        return {"success": False, "error": str(e)}
'''
        
        # 写入默认技能文件，指定utf-8编码
        (self.skills_dir / "tech_pulse.py").write_text(tech_pulse_content, encoding='utf-8')
        (self.skills_dir / "repo_visualizer.py").write_text(repo_visualizer_content, encoding='utf-8')
        (self.skills_dir / "architect.py").write_text(architect_content, encoding='utf-8')

    def list_skills(self):
        """列出所有可用技能"""
        print("📋 可用技能:")
        for skill_name in sorted(self.skills.keys()):
            print(f"  - {skill_name}")
        return list(self.skills.keys())

    def run_skill(self, skill_name, *args, **kwargs):
        """运行指定技能"""
        if skill_name not in self.skills:
            print(f"❌ 技能不存在: {skill_name}")
            return {"success": False, "error": f"技能不存在: {skill_name}"}
        
        try:
            skill_module = self.skills[skill_name]
            # 检查run函数的参数数量
            import inspect
            sig = inspect.signature(skill_module.run)
            params = list(sig.parameters.keys())
            
            if len(params) == 0:
                # 无参数函数
                result = skill_module.run()
            else:
                # 有参数函数
                result = skill_module.run(*args, **kwargs)
            return result
        except Exception as e:
            print(f"❌ 技能执行失败: {e}")
            return {"success": False, "error": str(e)}


def main():
    """主函数"""
    ask = ASK()
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  ask dashboard   - 查看可用技能")
        print("  ask run <skill> [args]   - 运行指定技能")
        return
    
    command = sys.argv[1]
    
    if command == "dashboard":
        ask.list_skills()
    elif command == "run":
        if len(sys.argv) < 3:
            print("请指定技能名称")
            return
        skill_name = sys.argv[2]
        args = sys.argv[3:]
        # 处理技能参数
        skill_args = " " .join(args) if args else None
        result = ask.run_skill(skill_name, skill_args)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"未知命令: {command}")


if __name__ == "__main__":
    main()
