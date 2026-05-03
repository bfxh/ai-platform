import os
import sys
import json
from pathlib import Path
from datetime import datetime

class ContextMemory:
    def __init__(self):
        self.ai_path = Path("/python")
        self.state_dir = self.ai_path / "gstack_core" / "state"
        self.context_file = self.state_dir / "context.json"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        self.context = self.load_context()
    
    def load_context(self):
        if self.context_file.exists():
            try:
                with open(self.context_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "session_id": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "current_task": None,
            "unfinished_tasks": [],
            "last_error": None,
            "active_branch": None,
            "checkpoint": None,
            "pending_recoveries": []
        }
    
    def save_context(self):
        self.context["updated_at"] = datetime.now().isoformat()
        
        try:
            with open(self.context_file, 'w', encoding='utf-8') as f:
                json.dump(self.context, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ 保存上下文失败: {str(e)}")
            return False
    
    def start_session(self, session_id=None):
        if session_id:
            self.context["session_id"] = session_id
        else:
            import uuid
            self.context["session_id"] = str(uuid.uuid4())
        
        self.context["created_at"] = datetime.now().isoformat()
        self.save_context()
        print(f"✅ 会话已启动: {self.context['session_id']}")
        return self.context["session_id"]
    
    def set_current_task(self, task_name, description=None, priority="medium"):
        self.context["current_task"] = {
            "name": task_name,
            "description": description,
            "priority": priority,
            "started_at": datetime.now().isoformat(),
            "status": "in_progress"
        }
        self.save_context()
        print(f"📌 当前任务: {task_name}")
    
    def add_unfinished_task(self, task_name, description=None, checkpoint=None):
        task = {
            "name": task_name,
            "description": description,
            "checkpoint": checkpoint,
            "added_at": datetime.now().isoformat()
        }
        self.context["unfinished_tasks"].append(task)
        self.save_context()
        print(f"⏸️ 任务已暂停: {task_name}")
    
    def complete_task(self, task_name):
        for i, task in enumerate(self.context["unfinished_tasks"]):
            if task["name"] == task_name:
                self.context["unfinished_tasks"].pop(i)
                print(f"✅ 任务已完成: {task_name}")
                break
        
        if self.context["current_task"] and self.context["current_task"]["name"] == task_name:
            self.context["current_task"]["status"] = "completed"
            self.context["current_task"] = None
        
        self.save_context()
    
    def set_error(self, error_message, stack_trace=None):
        self.context["last_error"] = {
            "message": error_message,
            "stack_trace": stack_trace,
            "occurred_at": datetime.now().isoformat()
        }
        self.save_context()
        print(f"❌ 错误已记录: {error_message}")
    
    def set_checkpoint(self, checkpoint_data):
        self.context["checkpoint"] = {
            "data": checkpoint_data,
            "created_at": datetime.now().isoformat()
        }
        self.save_context()
        print(f"💾 检查点已保存")
    
    def check_unfinished_tasks(self):
        if self.context["unfinished_tasks"]:
            print("\n🔔 检测到未完成任务:")
            for i, task in enumerate(self.context["unfinished_tasks"]):
                print(f"  {i+1}. {task['name']}")
                if task.get('description'):
                    print(f"     - {task['description']}")
                if task.get('checkpoint'):
                    print(f"     - 检查点: {task['checkpoint']}")
            return True
        return False
    
    def recover_task(self, task_name):
        for task in self.context["unfinished_tasks"]:
            if task["name"] == task_name:
                print(f"\n🔄 恢复任务: {task_name}")
                if task.get('description'):
                    print(f"   描述: {task['description']}")
                if task.get('checkpoint'):
                    print(f"   检查点: {task['checkpoint']}")
                if self.context.get('last_error'):
                    print(f"   上次错误: {self.context['last_error']['message']}")
                return task
        print(f"❌ 未找到任务: {task_name}")
        return None
    
    def add_feedback(self, feedback_type, feedback_content):
        if "feedback" not in self.context:
            self.context["feedback"] = []
        
        self.context["feedback"].append({
            "type": feedback_type,
            "content": feedback_content,
            "received_at": datetime.now().isoformat()
        })
        self.save_context()
        print(f"📝 反馈已记录: [{feedback_type}] {feedback_content[:50]}...")
    
    def get_status(self):
        status = {
            "session_id": self.context.get("session_id"),
            "has_current_task": self.context.get("current_task") is not None,
            "unfinished_count": len(self.context.get("unfinished_tasks", [])),
            "has_error": self.context.get("last_error") is not None,
            "has_checkpoint": self.context.get("checkpoint") is not None,
            "feedback_count": len(self.context.get("feedback", []))
        }
        return status
    
    def print_status(self):
        status = self.get_status()
        print("\n📊 记忆晶体状态:")
        print(f"  会话 ID: {status['session_id'] or '未启动'}")
        print(f"  当前任务: {'有' if status['has_current_task'] else '无'}")
        print(f"  未完成任务: {status['unfinished_count']} 个")
        print(f"  错误: {'有' if status['has_error'] else '无'}")
        print(f"  检查点: {'有' if status['has_checkpoint'] else '无'}")
        print(f"  反馈记录: {status['feedback_count']} 条")
        
        if status['has_error']:
            error = self.context['last_error']
            print(f"\n  ❌ 上次错误 ({error['occurred_at']}):")
            print(f"     {error['message']}")


if __name__ == "__main__":
    memory = ContextMemory()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "status":
            memory.print_status()
        elif cmd == "start":
            session_id = sys.argv[2] if len(sys.argv) > 2 else None
            memory.start_session(session_id)
        elif cmd == "task" and len(sys.argv) > 2:
            task_name = sys.argv[2]
            desc = sys.argv[3] if len(sys.argv) > 3 else None
            memory.set_current_task(task_name, desc)
        elif cmd == "pause" and len(sys.argv) > 2:
            task_name = sys.argv[2]
            checkpoint = sys.argv[3] if len(sys.argv) > 3 else None
            memory.add_unfinished_task(task_name, checkpoint=checkpoint)
        elif cmd == "complete" and len(sys.argv) > 2:
            task_name = sys.argv[2]
            memory.complete_task(task_name)
        elif cmd == "recover" and len(sys.argv) > 2:
            task_name = sys.argv[2]
            memory.recover_task(task_name)
        elif cmd == "check":
            if memory.check_unfinished_tasks():
                print("💡 使用 'recover <task_name>' 恢复任务")
        elif cmd == "feedback" and len(sys.argv) > 3:
            feedback_type = sys.argv[2]
            content = sys.argv[3]
            memory.add_feedback(feedback_type, content)
        else:
            print("未知命令")
    else:
        memory.print_status()
