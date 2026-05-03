#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《游戏也太真实了》小说奉献者3D角色生成工作流

为所有为这部小说奉献的创作者们创建3D纪念角色
体现"为事业奉献自身"的崇高艺术感
"""

import os
import sys
import subprocess
import json
from pathlib import Path

# Blender路径配置
BLENDER_PATH = "%SOFTWARE_DIR%/KF/JM/blender/blender.exe"
SCRIPTS_DIR = Path("/python/MCP/blender_scripts")
OUTPUT_DIR = Path("/python/Output/Characters/3D")
INPUT_DIR = Path("/python/Input/Characters")

# 确保目录存在
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
INPUT_DIR.mkdir(parents=True, exist_ok=True)

def run_blender_script(script_path, args=None, background=True):
    """运行Blender脚本"""
    cmd = [BLENDER_PATH]
    if background:
        cmd.append("--background")
    cmd.extend(["--python", str(script_path)])
    
    if args:
        cmd.append("--")
        cmd.extend(args)
    
    print(f"🚀 执行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            encoding='utf-8'
        )
        
        # 过滤Blender启动信息
        output_lines = []
        for line in result.stdout.split('\n'):
            if line.strip() and not line.startswith('Read') and not line.startswith('Info'):
                output_lines.append(line)
        
        if result.stderr:
            error_lines = []
            for line in result.stderr.split('\n'):
                if line.strip() and 'ERROR' in line:
                    error_lines.append(line)
            if error_lines:
                print(f"⚠️ 错误信息:\n{chr(10).join(error_lines)}")
        
        return {
            "success": result.returncode == 0,
            "output": '\n'.join(output_lines),
            "error": result.stderr if result.returncode != 0 else None,
            "return_code": result.returncode
        }
    
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "执行超时", "return_code": -1}
    except Exception as e:
        return {"success": False, "error": str(e), "return_code": -2}

def generate_single_character(image_path, character_name):
    """生成单个角色"""
    print(f"\n{'='*60}")
    print(f"🎨 正在生成角色: {character_name}")
    print(f"📷 参考图片: {image_path}")
    print(f"{'='*60}")
    
    script_path = SCRIPTS_DIR / "image_to_3d_character.py"
    
    args = [str(image_path), character_name]
    result = run_blender_script(script_path, args)
    
    if result["success"]:
        print("✅ 角色生成成功!")
        print(f"输出:\n{result['output']}")
    else:
        print("❌ 角色生成失败!")
        print(f"错误: {result['error']}")
    
    return result

def generate_all_contributors():
    """为所有奉献者生成3D角色"""
    print(f"\n{'='*70}")
    print("🌟 《游戏也太真实了》小说奉献者3D角色生成项目")
    print(f"{'='*70}")
    print("🎯 艺术主题: 为事业奉献自身的崇高精神")
    print(f"{'='*70}")
    
    # 奉献者列表（根据用户提供的图片）
    contributors = [
        {
            "name": "创作先驱",
            "description": "为小说奠定基石的创作者",
            "role": "核心策划",
            "image": "contributor1"
        },
        {
            "name": "艺术团队",
            "description": "三位共同奉献的艺术家",
            "role": "美术设计",
            "image": "contributor2"
        },
        {
            "name": "幕后英雄",
            "description": "默默付出的幕后工作者",
            "role": "技术支持",
            "image": "contributor3"
        }
    ]
    
    results = []
    
    for i, contributor in enumerate(contributors):
        print(f"\n📌 第 {i+1} 位奉献者: {contributor['name']}")
        print(f"   角色: {contributor['role']}")
        print(f"   描述: {contributor['description']}")
        
        # 构建图片路径
        image_path = INPUT_DIR / f"{contributor['image']}.png"
        
        # 如果图片不存在，使用默认生成
        if not image_path.exists():
            print(f"   ⚠️ 未找到图片: {image_path}")
            print(f"   🔄 使用默认角色生成")
            image_path = None
        
        # 生成角色
        character_name = f"Dedication_{contributor['name'].replace(' ', '_')}"
        
        if image_path and image_path.exists():
            result = generate_single_character(str(image_path), character_name)
        else:
            # 使用Blender脚本生成默认角色
            script_path = SCRIPTS_DIR / "image_to_3d_character.py"
            result = run_blender_script(script_path, [character_name])
        
        result["contributor"] = contributor
        results.append(result)
    
    # 生成项目报告
    generate_report(results, contributors)
    
    return results

def generate_report(results, contributors):
    """生成项目报告"""
    report = {
        "project": "《游戏也太真实了》奉献者3D角色项目",
        "theme": "为事业奉献自身的崇高精神",
        "generated_at": "2026年4月12日",
        "contributors": contributors,
        "results": results,
        "summary": {
            "total": len(results),
            "successful": sum(1 for r in results if r.get("success")),
            "failed": sum(1 for r in results if not r.get("success"))
        }
    }
    
    report_file = OUTPUT_DIR / "project_report.json"
    report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    
    # 生成HTML报告
    html_report = generate_html_report(report)
    html_file = OUTPUT_DIR / "project_report.html"
    html_file.write_text(html_report, encoding='utf-8')
    
    print(f"\n📊 生成项目报告")
    print(f"   JSON报告: {report_file}")
    print(f"   HTML报告: {html_file}")

def generate_html_report(report):
    """生成HTML报告"""
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report['project']}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Microsoft YaHei', sans-serif; 
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            color: white;
            padding: 40px 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ text-align: center; margin-bottom: 50px; }}
        .header h1 {{ 
            font-size: 2.5em; 
            background: linear-gradient(90deg, #e94560, #ff6b6b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
        }}
        .header .subtitle {{ color: #aaa; font-size: 1.2em; }}
        .theme-badge {{
            display: inline-block;
            background: linear-gradient(135deg, #e94560, #c70039);
            padding: 8px 20px;
            border-radius: 30px;
            margin-top: 20px;
            font-weight: bold;
        }}
        .stats {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-bottom: 50px;
        }}
        .stat-item {{
            text-align: center;
            padding: 20px 40px;
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }}
        .stat-item .number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #e94560;
        }}
        .stat-item .label {{ color: #aaa; }}
        .contributors {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; }}
        .card {{
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            padding: 30px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            transition: transform 0.3s;
        }}
        .card:hover {{ transform: translateY(-5px); }}
        .card .name {{
            font-size: 1.5em;
            margin-bottom: 10px;
            color: #e94560;
        }}
        .card .role {{
            display: inline-block;
            background: rgba(233, 69, 96, 0.2);
            padding: 5px 15px;
            border-radius: 20px;
            margin-bottom: 15px;
            font-size: 0.9em;
        }}
        .card .description {{ color: #aaa; margin-bottom: 15px; }}
        .card .status {{
            padding: 10px;
            border-radius: 10px;
            font-weight: bold;
        }}
        .status.success {{ background: rgba(46, 213, 115, 0.2); color: #2ed573; }}
        .status.failed {{ background: rgba(239, 83, 80, 0.2); color: #ef5350; }}
        .output-files {{ margin-top: 15px; }}
        .output-files a {{
            display: block;
            color: #4cc9f0;
            text-decoration: none;
            margin-bottom: 5px;
        }}
        .output-files a:hover {{ text-decoration: underline; }}
        .footer {{
            text-align: center;
            margin-top: 50px;
            color: #666;
            font-size: 0.9em;
        }}
        .dedication {{
            background: linear-gradient(135deg, rgba(233,69,96,0.1), rgba(15,52,96,0.2));
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .dedication quote {{
            font-size: 1.5em;
            font-style: italic;
            color: #e94560;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{report['project']}</h1>
            <p class="subtitle">3D角色生成项目</p>
            <div class="theme-badge">🎨 {report['theme']}</div>
        </div>
        
        <div class="dedication">
            <quote>"为了热爱的事业，奉献一切"</quote>
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="number">{report['summary']['total']}</div>
                <div class="label">奉献者总数</div>
            </div>
            <div class="stat-item">
                <div class="number">{report['summary']['successful']}</div>
                <div class="label">生成成功</div>
            </div>
            <div class="stat-item">
                <div class="number">{report['summary']['failed']}</div>
                <div class="label">生成失败</div>
            </div>
        </div>
        
        <h2 style="margin-bottom: 20px; color: #e94560;">🎭 奉献者角色列表</h2>
        <div class="contributors">
"""
    
    for result in report['results']:
        contributor = result.get('contributor', {})
        status_class = "success" if result.get('success') else "failed"
        status_text = "生成成功" if result.get('success') else "生成失败"
        
        html += f"""
            <div class="card">
                <div class="name">🌟 {contributor.get('name', '未知')}</div>
                <div class="role">{contributor.get('role', '未知角色')}</div>
                <div class="description">📝 {contributor.get('description', '')}</div>
                <div class="status {status_class}">{'✅' if result.get('success') else '❌'} {status_text}</div>
                <div class="output-files">
                    <a href="{contributor.get('name', 'character').replace(' ', '_')}.blend" target="_blank">📁 Blender文件</a>
                    <a href="{contributor.get('name', 'character').replace(' ', '_')}.png" target="_blank">🖼️ 渲染图片</a>
                </div>
            </div>
"""
    
    html += """
        </div>
        
        <div class="footer">
            <p>生成时间: 2026年4月12日</p>
            <p>献给所有为《游戏也太真实了》奉献的创作者们</p>
        </div>
    </div>
</body>
</html>
"""
    return html

def main():
    """主函数"""
    print(f"\n{'='*70}")
    print("🚀 《游戏也太真实了》奉献者3D角色生成器")
    print(f"{'='*70}")
    
    # 检查Blender是否存在
    if not os.path.exists(BLENDER_PATH):
        print(f"❌ Blender未找到: {BLENDER_PATH}")
        print("请检查Blender安装路径")
        return
    
    print(f"✅ Blender路径: {BLENDER_PATH}")
    print(f"📁 输出目录: {OUTPUT_DIR}")
    
    # 生成所有奉献者角色
    results = generate_all_contributors()
    
    # 输出汇总
    successful = sum(1 for r in results if r.get("success"))
    failed = len(results) - successful
    
    print(f"\n{'='*70}")
    print("📊 生成结果汇总")
    print(f"{'='*70}")
    print(f"✅ 成功生成: {successful} 个角色")
    print(f"❌ 生成失败: {failed} 个角色")
    print(f"📁 输出目录: {OUTPUT_DIR}")
    print(f"{'='*70}")
    
    if successful > 0:
        print("\n🎉 角色生成项目完成!")
        print("查看输出目录获取生成的3D角色文件和渲染图片")
    else:
        print("\n⚠️ 所有角色生成失败，请检查错误信息")

if __name__ == "__main__":
    main()
