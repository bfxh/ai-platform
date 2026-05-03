import os
import sys
import json
from pathlib import Path
from datetime import datetime

class MemoryMCP:
    def __init__(self):
        self.ai_path = Path("/python")
        self.memory_file = self.ai_path / "gstack_core" / "state" / "memory.json"
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self.memory = self.load_memory()
    
    def load_memory(self):
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            "session_id": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "memories": {}
        }
    
    def save_memory(self):
        self.memory["updated_at"] = datetime.now().isoformat()
        
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ 保存记忆失败: {str(e)}")
            return False
    
    def remember(self, key, value):
        self.memory["memories"][key] = {
            "value": value,
            "created_at": datetime.now().isoformat()
        }
        self.save_memory()
        print(f"✅ 记忆已保存: {key} = {value}")
        return True
    
    def recall(self, key=None):
        if key:
            memory = self.memory["memories"].get(key)
            if memory:
                print(f"📝 记忆: {key} = {memory['value']}")
                return memory['value']
            else:
                print(f"❌ 未找到记忆: {key}")
                return None
        else:
            print("📋 所有记忆:")
            for key, memory in self.memory["memories"].items():
                print(f"  {key}: {memory['value']} (保存于: {memory['created_at']})")
            return self.memory["memories"]
    
    def forget(self, key):
        if key in self.memory["memories"]:
            del self.memory["memories"][key]
            self.save_memory()
            print(f"✅ 记忆已删除: {key}")
            return True
        else:
            print(f"❌ 未找到记忆: {key}")
            return False
    
    def clear(self):
        self.memory["memories"] = {}
        self.save_memory()
        print("✅ 所有记忆已清除")
        return True
    
    def get_session_id(self):
        if not self.memory["session_id"]:
            import uuid
            self.memory["session_id"] = str(uuid.uuid4())
            self.save_memory()
        return self.memory["session_id"]


if __name__ == "__main__":
    memory_mcp = MemoryMCP()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "remember" and len(sys.argv) > 3:
            key = sys.argv[2]
            value = " ".join(sys.argv[3:])
            memory_mcp.remember(key, value)
        elif cmd == "recall" and len(sys.argv) > 2:
            key = sys.argv[2]
            memory_mcp.recall(key)
        elif cmd == "recall":
            memory_mcp.recall()
        elif cmd == "forget" and len(sys.argv) > 2:
            key = sys.argv[2]
            memory_mcp.forget(key)
        elif cmd == "clear":
            memory_mcp.clear()
        elif cmd == "session":
            session_id = memory_mcp.get_session_id()
            print(f"会话 ID: {session_id}")
        else:
            print("用法:")
            print("  python memory_mcp.py remember <key> <value> - 保存记忆")
            print("  python memory_mcp.py recall [key] - 回忆记忆")
            print("  python memory_mcp.py forget <key> - 删除记忆")
            print("  python memory_mcp.py clear - 清除所有记忆")
            print("  python memory_mcp.py session - 获取会话 ID")
    else:
        print("记忆 MCP 服务器")
        print("用法:")
        print("  python memory_mcp.py remember <key> <value> - 保存记忆")
        print("  python memory_mcp.py recall [key] - 回忆记忆")
        print("  python memory_mcp.py forget <key> - 删除记忆")
        print("  python memory_mcp.py clear - 清除所有记忆")
        print("  python memory_mcp.py session - 获取会话 ID")
