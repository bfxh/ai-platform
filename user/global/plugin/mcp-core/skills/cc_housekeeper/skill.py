import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta

class CCHousekeeper:
    def __init__(self):
        self.ai_path = Path("/python")
        self.cc_path = self.ai_path / "CC"
        self.archive_path = self.ai_path / "Archive"
        self.config_file = self.ai_path / "ai_architecture.json"
        self.dry_run = False
        self.results = {
            "to_archive": [],
            "to_delete": [],
            "kept": []
        }
        self.archive_path.mkdir(parents=True, exist_ok=True)
    
    def get_file_age_days(self, file_path):
        mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        return (datetime.now() - mtime).days
    
    def get_file_access_days(self, file_path):
        try:
            atime = datetime.fromtimestamp(os.path.getatime(file_path))
            return (datetime.now() - atime).days
        except:
            return self.get_file_age_days(file_path)
    
    def scan_3_unused(self):
        unused_path = self.cc_path / "3_Unused"
        if not unused_path.exists():
            return
        
        print("🔍 扫描 3_Unused 目录...")
        
        for root, dirs, files in os.walk(unused_path):
            for filename in files:
                if filename.startswith('.') or filename.endswith('.md'):
                    continue
                
                file_path = Path(root) / filename
                access_days = self.get_file_access_days(file_path)
                
                if access_days > 90:
                    rel_path = file_path.relative_to(self.cc_path)
                    archive_dest = self.archive_path / rel_path
                    self.results["to_archive"].append({
                        "path": str(file_path),
                        "age": access_days,
                        "dest": str(archive_dest)
                    })
                else:
                    self.results["kept"].append({
                        "path": str(file_path),
                        "age": access_days
                    })
    
    def scan_2_old(self):
        old_path = self.cc_path / "2_Old"
        if not old_path.exists():
            return
        
        print("🔍 扫描 2_Old 目录...")
        
        for root, dirs, files in os.walk(old_path):
            for filename in files:
                if filename.startswith('.') or filename.endswith('.md'):
                    continue
                
                file_path = Path(root) / filename
                age_days = self.get_file_age_days(file_path)
                
                if age_days > 60:
                    self.results["to_delete"].append({
                        "path": str(file_path),
                        "age": age_days
                    })
                else:
                    self.results["kept"].append({
                        "path": str(file_path),
                        "age": age_days
                    })
    
    def execute_archive(self):
        for item in self.results["to_archive"]:
            src = Path(item["path"])
            dest = Path(item["dest"])
            
            if self.dry_run:
                print(f"📋 预览: 归档 {src} -> {dest}")
            else:
                try:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(src), str(dest))
                    print(f"✅ 已归档: {src} -> {dest}")
                except Exception as e:
                    print(f"❌ 归档失败: {src} - {str(e)}")
    
    def execute_delete(self):
        for item in self.results["to_delete"]:
            file_path = Path(item["path"])
            
            if self.dry_run:
                print(f"📋 预览: 删除 {file_path}")
            else:
                try:
                    file_path.unlink()
                    print(f"✅ 已删除: {file_path}")
                except Exception as e:
                    print(f"❌ 删除失败: {file_path} - {str(e)}")
    
    def update_index(self):
        for category in ["1_Raw", "2_Old", "3_Unused"]:
            index_file = self.cc_path / category / "INDEX.md"
            if not index_file.exists():
                continue
            
            try:
                lines = index_file.read_text(encoding='utf-8').split('\n')
                for i, line in enumerate(lines):
                    if line.startswith("## 最后更新"):
                        lines[i] = f"## 最后更新\n{datetime.now().strftime('%Y-%m-%d')}\n"
                        break
                
                if not self.dry_run:
                    index_file.write_text('\n'.join(lines), encoding='utf-8')
                    print(f"✅ 更新索引: {index_file}")
            except Exception as e:
                print(f"❌ 更新索引失败: {index_file} - {str(e)}")
    
    def generate_report(self):
        report = []
        report.append("# CC 目录清理报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"模式: {'预览' if self.dry_run else '执行'}")
        report.append("")
        
        report.append("## 统计")
        report.append(f"- 待归档: {len(self.results['to_archive'])}")
        report.append(f"- 待删除: {len(self.results['to_delete'])}")
        report.append(f"- 保留: {len(self.results['kept'])}")
        report.append("")
        
        if self.results['to_archive']:
            report.append("## 待归档文件")
            for item in self.results['to_archive']:
                report.append(f"- {item['path']} (访问时间: {item['age']} 天)")
            report.append("")
        
        if self.results['to_delete']:
            report.append("## 待删除文件")
            for item in self.results['to_delete']:
                report.append(f"- {item['path']} (修改时间: {item['age']} 天)")
            report.append("")
        
        return "\n".join(report)
    
    def run(self, dry_run=True):
        self.dry_run = dry_run
        print("🚀 开始 CC 目录清理...")
        print(f"模式: {'预览' if dry_run else '执行'}")
        print("=" * 60)
        
        self.scan_3_unused()
        self.scan_2_old()
        
        print("\n📊 清理计划:")
        print(f"- 归档到 Archive: {len(self.results['to_archive'])} 个文件")
        print(f"- 删除: {len(self.results['to_delete'])} 个文件")
        print(f"- 保留: {len(self.results['kept'])} 个文件")
        
        if not dry_run:
            print("\n🔄 执行清理操作...")
            self.execute_archive()
            self.execute_delete()
            self.update_index()
        
        report = self.generate_report()
        print("\n" + "=" * 60)
        print(report)
        
        return report


if __name__ == "__main__":
    housekeeper = CCHousekeeper()
    dry_run = len(sys.argv) > 1 and sys.argv[1] == "--dry-run"
    housekeeper.run(dry_run=dry_run)
