import os
import sys
import json
import uuid
from pathlib import Path
from datetime import datetime

class AuditLogger:
    def __init__(self):
        self.ai_path = Path("/python")
        self.log_dir = self.ai_path / "logs"
        self.audit_file = self.log_dir / "gstack_audit.jsonl"
        self.session_id = str(uuid.uuid4())
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def log(self, command, files_modified=None, mcp_calls=None, result="success", details=None):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "command": command,
            "files_modified": files_modified or [],
            "mcp_calls": mcp_calls or [],
            "result": result,
            "details": details or {},
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "os": os.name
        }
        
        try:
            with open(self.audit_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            return True
        except Exception as e:
            print(f"❌ 写入审计日志失败: {str(e)}")
            return False
    
    def log_mcp_call(self, mcp_name, action, params=None, response=None, duration_ms=None):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "command": f"mcp:{mcp_name}:{action}",
            "mcp_calls": [{
                "mcp": mcp_name,
                "action": action,
                "params": params,
                "response": response,
                "duration_ms": duration_ms
            }],
            "result": "success" if response else "error",
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        }
        
        try:
            with open(self.audit_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            return True
        except Exception as e:
            print(f"❌ 写入 MCP 调用日志失败: {str(e)}")
            return False
    
    def get_logs(self, limit=100):
        logs = []
        try:
            if self.audit_file.exists():
                with open(self.audit_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            logs.append(json.loads(line))
            return logs[-limit:]
        except Exception as e:
            print(f"❌ 读取审计日志失败: {str(e)}")
            return []
    
    def generate_report(self, days=7):
        logs = self.get_logs()
        cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)
        
        recent_logs = []
        for log in logs:
            log_time = datetime.fromisoformat(log['timestamp']).timestamp()
            if log_time >= cutoff_time:
                recent_logs.append(log)
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "time_range": f"最近 {days} 天",
            "total_logs": len(recent_logs),
            "success_count": sum(1 for log in recent_logs if log.get('result') == 'success'),
            "error_count": sum(1 for log in recent_logs if log.get('result') == 'error'),
            "commands": {}
        }
        
        for log in recent_logs:
            command = log.get('command', 'unknown')
            if command not in report['commands']:
                report['commands'][command] = {
                    "count": 0,
                    "success": 0,
                    "error": 0
                }
            report['commands'][command]['count'] += 1
            if log.get('result') == 'success':
                report['commands'][command]['success'] += 1
            else:
                report['commands'][command]['error'] += 1
        
        return report


if __name__ == "__main__":
    logger = AuditLogger()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "report":
            report = logger.generate_report()
            print(json.dumps(report, ensure_ascii=False, indent=2))
        elif sys.argv[1] == "test":
            logger.log(
                command="test:audit",
                files_modified=["/python/test.txt"],
                mcp_calls=["blender_mcp:render"],
                result="success",
                details={"test": "audit logger"}
            )
            print("✅ 测试日志写入成功")
    else:
        print("用法:")
        print("  python audit_logger.py report - 生成审计报告")
        print("  python audit_logger.py test - 测试日志写入")
