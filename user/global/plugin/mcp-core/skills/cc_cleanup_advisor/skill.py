import os
import sys
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path

class CCCleanupAdvisor:
    def __init__(self):
        self.ai_path = Path("/python")
        self.cc_path = self.ai_path / "CC"
        self.architecture_file = self.ai_path / "ai_architecture.json"
        self.threshold_days = 30
        self.scan_results = {
            "1_Raw": [],
            "2_Old": [],
            "3_Unused": []
        }
        
    def load_architecture_config(self):
        with open(self.architecture_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_file_age_days(self, file_path):
        mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        return (datetime.now() - mtime).days
    
    def scan_directory(self, dir_path, category):
        files = []
        dir_path = Path(dir_path)
        
        if not dir_path.exists():
            return files
            
        for root, dirs, filenames in os.walk(dir_path):
            for filename in filenames:
                file_path = Path(root) / filename
                if filename.startswith('.') or filename.endswith('.md'):
                    continue
                    
                age_days = self.get_file_age_days(file_path)
                files.append({
                    "path": str(file_path),
                    "name": filename,
                    "age_days": age_days,
                    "size": os.path.getsize(file_path),
                    "category": category,
                    "recommendation": "review" if age_days > self.threshold_days else "keep"
                })
        
        return files
    
    def scan(self):
        print("🔍 开始扫描 CC 目录...")
        
        categories = {
            "1_Raw": self.cc_path / "1_Raw",
            "2_Old": self.cc_path / "2_Old",
            "3_Unused": self.cc_path / "3_Unused"
        }
        
        for cat_name, cat_path in categories.items():
            print(f"  扫描 {cat_name}...")
            self.scan_results[cat_name] = self.scan_directory(cat_path, cat_name)
        
        return self.scan_results
    
    def generate_report(self):
        report = []
        report.append("# CC 清理扫描报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"阈值: 超过 {self.threshold_days} 天未修改的文件建议清理")
        report.append("")
        
        total_files = 0
        files_to_cleanup = 0
        
        for cat_name, files in self.scan_results.items():
            if not files:
                continue
                
            report.append(f"## {cat_name}")
            report.append("")
            report.append("| 文件名 | 路径 | 存在天数 | 大小 | 建议 |")
            report.append("|--------|------|----------|------|------|")
            
            for f in files:
                total_files += 1
                size_kb = f['size'] / 1024
                if f['recommendation'] == 'review':
                    files_to_cleanup += 1
                report.append(f"| {f['name']} | {f['path']} | {f['age_days']} | {size_kb:.1f} KB | {f['recommendation']} |")
            
            report.append("")
        
        report.append(f"## 统计")
        report.append(f"- 总文件数: {total_files}")
        report.append(f"- 建议清理: {files_to_cleanup}")
        report.append(f"- 可保留: {total_files - files_to_cleanup}")
        
        return "\n".join(report)
    
    def update_index(self, category, files):
        index_file = self.cc_path / category / "INDEX.md"
        if not index_file.exists():
            return False
        
        lines = []
        with open(index_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines):
            if line.startswith("## 最后更新"):
                lines[i] = f"## 最后更新\n{datetime.now().strftime('%Y-%m-%d')}\n"
                break
        
        with open(index_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        return True
    
    def execute(self, command="scan"):
        if command == "scan":
            self.scan()
            return self.generate_report()
        elif command == "report":
            self.scan()
            return self.generate_report()
        else:
            return f"未知命令: {command}"


if __name__ == "__main__":
    advisor = CCCleanupAdvisor()
    
    if len(sys.argv) > 1:
        result = advisor.execute(sys.argv[1])
    else:
        result = advisor.execute("scan")
    
    print(result)
