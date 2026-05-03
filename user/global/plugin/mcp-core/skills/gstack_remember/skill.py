import os
import sys
from pathlib import Path
from datetime import datetime

class GSTACKRemember:
    def __init__(self):
        self.ai_path = Path("/python")
        self.user_rules_file = self.ai_path / ".trae" / "user_rules.md"
    
    def add_reminder(self, message):
        print(f"\n📝 记住: {message}")
        
        if not self.user_rules_file.exists():
            print("⚠️ user_rules.md 不存在，创建中...")
            self.user_rules_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.user_rules_file, 'w', encoding='utf-8') as f:
                f.write("# 用户规则\n\n此文件由 GSTACK 自动维护，记录用户偏好和自定义规则。\n\n")
        
        with open(self.user_rules_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        reminder_entry = f"""
## 当前会话备忘录
- **时间**: {timestamp}
- **内容**: {message}
- **来源**: GSTACK remember 命令

"""
        
        if "## 当前会话备忘录" in content:
            lines = content.split('\n')
            new_lines = []
            i = 0
            while i < len(lines):
                if lines[i].startswith("## 当前会话备忘录"):
                    new_lines.append(reminder_entry.strip())
                    while i < len(lines) and not (i > 0 and lines[i].startswith("## ")):
                        i += 1
                    continue
                new_lines.append(lines[i])
                i += 1
            new_content = '\n'.join(new_lines)
        else:
            new_content = content + reminder_entry
        
        try:
            with open(self.user_rules_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("✅ 备忘录已添加到 user_rules.md")
            return True
        except Exception as e:
            print(f"❌ 写入失败: {str(e)}")
            return False
    
    def list_reminders(self):
        if not self.user_rules_file.exists():
            print("❌ user_rules.md 不存在")
            return []
        
        with open(self.user_rules_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        in_memo = False
        reminders = []
        current_memo = []
        
        for line in lines:
            if line.startswith("## 当前会话备忘录"):
                in_memo = True
                current_memo = [line]
            elif in_memo:
                if line.startswith("## "):
                    if current_memo:
                        reminders.append('\n'.join(current_memo))
                    in_memo = False
                else:
                    current_memo.append(line)
        
        if in_memo and current_memo:
            reminders.append('\n'.join(current_memo))
        
        if reminders:
            print("\n📋 会话备忘录:")
            print("=" * 60)
            for i, memo in enumerate(reminders, 1):
                print(f"\n{i}. {memo}")
        else:
            print("\n📋 暂无会话备忘录")
        
        return reminders


if __name__ == "__main__":
    remember = GSTACKRemember()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            remember.list_reminders()
        elif sys.argv[1] == "remember" and len(sys.argv) > 2:
            message = " ".join(sys.argv[2:])
            remember.add_reminder(message)
        else:
            print("用法:")
            print("  python remember.py list - 列出备忘录")
            print('  python remember.py remember "<内容>" - 添加备忘录')
    else:
        print("GSTACK 记忆命令")
        print("用法:")
        print("  python remember.py list - 列出备忘录")
        print('  python remember.py remember "<内容>" - 添加备忘录')
