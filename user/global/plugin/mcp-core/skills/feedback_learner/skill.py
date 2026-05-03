import os
import sys
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime

class FeedbackLearner:
    def __init__(self):
        self.ai_path = Path("/python")
        self.user_rules_file = self.ai_path / ".trae" / "user_rules.md"
        self.rules_dir = self.ai_path / ".trae"
        self.rules_dir.mkdir(parents=True, exist_ok=True)
    
    def add_rule(self, feedback_text):
        print(f"\n📝 处理用户反馈...")
        print(f"   反馈内容: {feedback_text}")
        
        pattern_match = self._extract_pattern(feedback_text)
        
        if pattern_match:
            rule_entry = self._create_rule_entry(pattern_match, feedback_text)
            
            if self._append_to_user_rules(rule_entry):
                print(f"✅ 规则已添加: {pattern_match}")
                return True
            else:
                print(f"❌ 规则添加失败")
                return False
        else:
            print(f"⚠️ 无法从反馈中提取明确规则")
            return False
    
    def _extract_pattern(self, feedback_text):
        patterns = {
            r"(不要|禁止|别把|不要把)\s*(.+?)\s*归为?\s*(未使用|3_Unused|旧版本)": r"\2 保护规则",
            r"(不要|禁止|别把|不要把)\s*(.+?)\s*自动": r"\2 手动操作规则",
            r"(应该|需要|必须)\s*(.+?)\s*(存放在|放在|归类到)": r"\2 分类规则",
            r"优先\s*(.+?)": r"\1 优先级规则",
            r"保护\s*(.+?)": r"\1 保护规则"
        }
        
        for pattern, rule_type in patterns.items():
            match = re.search(pattern, feedback_text)
            if match:
                return {
                    "type": rule_type,
                    "matched": match.group(0),
                    "subject": match.group(2) if len(match.groups()) > 1 else None,
                    "pattern": pattern
                }
        
        return None
    
    def _create_rule_entry(self, pattern_match, original_feedback):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""
### 用户反馈规则 ({timestamp})
- **原始反馈**: {original_feedback}
- **规则类型**: {pattern_match['type']}
- **匹配内容**: {pattern_match.get('matched', 'N/A')}
- **添加方式**: 自动从用户反馈学习

**具体规则**:
根据上述反馈，已将此规则添加到 user_rules.md 中。
"""
    
    def _append_to_user_rules(self, rule_entry):
        try:
            if self.user_rules_file.exists():
                existing_content = self.user_rules_file.read_text(encoding='utf-8')
            else:
                existing_content = "# 用户规则\n\n此文件由 GSTACK 自动维护，记录用户偏好和自定义规则。\n\n"
            
            new_content = existing_content + "\n" + rule_entry
            
            self.user_rules_file.write_text(new_content, encoding='utf-8')
            return True
        except Exception as e:
            print(f"❌ 写入规则失败: {str(e)}")
            return False
    
    def commit_to_git(self, commit_message=None):
        try:
            if not commit_message:
                commit_message = f"learn: 用户偏好规则更新 - {datetime.now().strftime('%Y-%m-%d')}"
            
            result = subprocess.run(
                ["git", "add", str(self.user_rules_file)],
                cwd=str(self.ai_path),
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                result = subprocess.run(
                    ["git", "commit", "-m", commit_message],
                    cwd=str(self.ai_path),
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    print(f"✅ Git 提交成功: {commit_message}")
                    return True
                else:
                    print(f"⚠️ Git 提交失败: {result.stderr}")
                    return False
            else:
                print(f"⚠️ Git add 失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"⚠️ Git 操作失败: {str(e)}")
            return False
    
    def list_rules(self):
        if not self.user_rules_file.exists():
            print("❌ user_rules.md 不存在")
            return []
        
        content = self.user_rules_file.read_text(encoding='utf-8')
        
        sections = re.split(r'### ', content)
        rules = []
        
        for section in sections:
            if '用户反馈规则' in section or '反馈规则' in section:
                rules.append(section.strip())
        
        print(f"\n📋 用户规则列表 ({len(rules)} 条):")
        print("=" * 60)
        
        for i, rule in enumerate(rules, 1):
            print(f"\n{i}. {rule[:200]}...")
        
        return rules
    
    def process_feedback(self, feedback_text, auto_commit=False):
        print("🚀 处理用户反馈")
        print("=" * 60)
        
        success = self.add_rule(feedback_text)
        
        if success and auto_commit:
            print("\n🔄 尝试提交到 Git...")
            self.commit_to_git()
        
        return success


if __name__ == "__main__":
    learner = FeedbackLearner()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            learner.list_rules()
        elif sys.argv[1] == "commit":
            learner.commit_to_git()
        elif sys.argv[1] == "feedback" and len(sys.argv) > 2:
            feedback = " ".join(sys.argv[2:])
            auto_commit = "--commit" in sys.argv
            learner.process_feedback(feedback, auto_commit=auto_commit)
        else:
            print("用法:")
            print("  python feedback_learner.py list - 列出已有规则")
            print('  python feedback_learner.py feedback "<反馈内容>" - 处理反馈')
            print('  python feedback_learner.py feedback "<反馈内容>" --commit - 处理反馈并提交')
            print("  python feedback_learner.py commit - 提交规则到 Git")
    else:
        print("GSTACK 反馈学习系统")
        print("用法:")
        print("  python feedback_learner.py list - 列出已有规则")
        print('  python feedback_learner.py feedback "<反馈内容>" - 处理反馈')
