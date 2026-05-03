import os
import sys
import json
from pathlib import Path
from datetime import datetime

class GSTACKAnchor:
    def __init__(self):
        self.ai_path = Path("/python")
        self.architecture_file = self.ai_path / "ai_architecture.json"
        self.cc_index = self.ai_path / "CC" / "README.md"
        self.context_file = self.ai_path / "gstack_core" / "state" / "context.json"
    
    def load_architecture(self):
        if not self.architecture_file.exists():
            return {}
        
        try:
            with open(self.architecture_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def load_context(self):
        if not self.context_file.exists():
            return {}
        
        try:
            with open(self.context_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def count_unarchived_files(self):
        cc_path = self.ai_path / "CC"
        if not cc_path.exists():
            return 0
        
        count = 0
        for subdir in ['1_Raw', '2_Old', '3_Unused']:
            subdir_path = cc_path / subdir
            if subdir_path.exists():
                for root, dirs, files in os.walk(subdir_path):
                    for file in files:
                        if not file.endswith('.md') and not file.startswith('.'):
                            count += 1
        return count
    
    def generate_anchor(self):
        architecture = self.load_architecture()
        context = self.load_context()
        
        anchor_lines = []
        anchor_lines.append(f"[GSTACK 记忆锚点 v{datetime.now().strftime('%Y.%m.%d')}]")
        anchor_lines.append("- 根路径: /python")
        
        mcp_categories = architecture.get('mcp', {}).get('categories', {})
        if mcp_categories:
            categories_str = ', '.join([f"{k}({v.get('name', k)})" for k, v in mcp_categories.items()])
            anchor_lines.append(f"- MCP 分类: {categories_str} 禁止混放。")
        else:
            anchor_lines.append("- MCP 分类: JM(建模)/BC(代码)/Tools(工具) 禁止混放。")
        
        unarchived = self.count_unarchived_files()
        anchor_lines.append(f"- CC 缓存: 1_Raw(原)/2_Old(旧)/3_Unused(废) 今日未归档: {unarchived}个。")
        
        current_task = context.get('current_task')
        if current_task:
            task_name = current_task.get('name', '未知任务')
            anchor_lines.append(f"- 当前任务: {task_name}。")
        elif context.get('unfinished_tasks'):
            first_task = context['unfinished_tasks'][0]
            task_name = first_task.get('name', '未知任务')
            anchor_lines.append(f"- 当前任务: 恢复未完成的 {task_name}。")
        else:
            anchor_lines.append("- 当前任务: 无。")
        
        anchor_lines.append("- 保护规则: 严禁直接修改 *.json 核心配置。")
        
        last_error = context.get('last_error')
        if last_error:
            error_msg = last_error.get('message', '未知错误')
            anchor_lines.append(f"- 上次错误: {error_msg[:50]}...")
        
        return '\n'.join(anchor_lines)
    
    def copy_to_clipboard(self, text):
        if sys.platform == 'win32':
            try:
                import win32clipboard
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(text)
                win32clipboard.CloseClipboard()
                return True
            except:
                pass
        return False
    
    def run(self):
        print("🚀 生成 GSTACK 记忆锚点...")
        print("=" * 60)
        
        anchor = self.generate_anchor()
        print(anchor)
        print("=" * 60)
        
        if self.copy_to_clipboard(anchor):
            print("✅ 锚点文本已复制到剪贴板，请粘贴给 AI")
        else:
            print("⚠️ 无法复制到剪贴板，请手动复制上方文本")
        
        return anchor


if __name__ == "__main__":
    anchor = GSTACKAnchor()
    anchor.run()
