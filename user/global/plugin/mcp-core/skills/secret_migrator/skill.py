import os
import sys
import json
import re
from pathlib import Path

class SecretMigrator:
    def __init__(self):
        self.ai_path = Path("/python")
        self.env_file = self.ai_path / ".env"
        self.suspected_secrets = []
        self.patterns = [
            r'(?i)(api[_\s-]?key|token|secret|password|passwd|credential)\s*[:=]\s*["\']?([^"\'\s]+)["\']?',
            r'(?i)(github|openai|api)[_\s-]?(token|key|secret)\s*[:=]\s*["\']?([^"\'\s]+)["\']?',
            r'(?i)password\s*[:=]\s*["\']?([^"\'\s]+)["\']?',
            r'(?i)secret[_\s-]?key\s*[:=]\s*["\']?([^"\'\s]+)["\']?'
        ]
    
    def scan_file(self, file_path):
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            for pattern in self.patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    key = match.group(1) if len(match.groups()) > 1 else 'SECRET'
                    value = match.group(len(match.groups()))
                    
                    if len(value) > 8 and not any(c in value for c in ' \t\n\r'):
                        self.suspected_secrets.append({
                            "file": str(file_path),
                            "key": key.upper().replace(' ', '_'),
                            "value": value,
                            "line": content[:match.start()].count('\n') + 1
                        })
        except Exception as e:
            print(f"❌ 扫描文件失败: {file_path} - {str(e)}")
    
    def scan_directory(self, directory):
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(('.py', '.json', '.yaml', '.yml', '.env.example')):
                    file_path = Path(root) / file
                    self.scan_file(file_path)
    
    def generate_env_content(self):
        env_lines = []
        env_lines.append("# 敏感配置文件")
        env_lines.append("# 此文件已被 .gitignore 忽略，请勿提交到版本控制系统")
        env_lines.append("")
        
        for secret in self.suspected_secrets:
            env_lines.append(f"# 从 {secret['file']} 迁移")
            env_lines.append(f"{secret['key']}={secret['value']}")
            env_lines.append("")
        
        return "\n".join(env_lines)
    
    def run(self):
        print("🔍 开始扫描疑似密钥...")
        print("=" * 60)
        
        scan_dirs = [
            self.ai_path / "MCP",
            self.ai_path / "MCP_Core" / "skills",
            self.ai_path
        ]
        
        for dir_path in scan_dirs:
            if dir_path.exists():
                print(f"扫描目录: {dir_path}")
                self.scan_directory(dir_path)
        
        if not self.suspected_secrets:
            print("✅ 未发现疑似密钥")
            return
        
        print(f"\n🔓 发现 {len(self.suspected_secrets)} 个疑似密钥:")
        for secret in self.suspected_secrets:
            print(f"- {secret['file']}:{secret['line']} -> {secret['key']}")
        
        env_content = self.generate_env_content()
        
        if self.env_file.exists():
            print(f"\n📝 更新 .env 文件: {self.env_file}")
            existing_content = self.env_file.read_text(encoding='utf-8')
            new_content = existing_content + "\n" + env_content
            self.env_file.write_text(new_content, encoding='utf-8')
        else:
            print(f"\n📝 创建 .env 文件: {self.env_file}")
            self.env_file.write_text(env_content, encoding='utf-8')
        
        print("\n📋 迁移建议:")
        print("1. 查看生成的 .env 文件并确认密钥正确")
        print("2. 修改原文件，使用 os.getenv('KEY_NAME') 替代硬编码的密钥")
        print("3. 确保 .env 文件已被 .gitignore 忽略")
        
        print("\n✅ 密钥迁移完成！")


if __name__ == "__main__":
    migrator = SecretMigrator()
    migrator.run()
