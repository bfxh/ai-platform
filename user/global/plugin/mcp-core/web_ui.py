#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - Web UI 界面

功能:
- 技能管理界面
- 实时监控面板
- 配置管理
- 日志查看
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

sys.path.insert(0, str(Path(__file__).parent))

from skills.base import Skill, SkillRegistry
from config_manager import get_config_manager
from performance_monitor import get_performance_monitor

# IronClaw Observer
try:
    from ironclaw_observer import get_observer
    HAS_OBSERVER = True
except ImportError:
    HAS_OBSERVER = False

# 创建 FastAPI 应用
app = FastAPI(
    title="MCP Core Web UI",
    description="MCP Core 技能管理系统 Web 界面",
    version="1.0.0",
)

# 创建模板目录
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)

# 创建静态文件目录
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)

# 初始化模板
templates = Jinja2Templates(directory=str(templates_dir))

# 技能注册表
skill_registry = SkillRegistry()


# HTML 模板
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Core - 技能管理面板</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            color: #333;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 1.5rem;
            font-weight: 600;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        
        .stat-card:hover {
            transform: translateY(-2px);
        }
        
        .stat-card h3 {
            color: #666;
            font-size: 0.875rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
        }
        
        .stat-card .value {
            font-size: 2rem;
            font-weight: 700;
            color: #667eea;
        }
        
        .section {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .section h2 {
            font-size: 1.25rem;
            margin-bottom: 1rem;
            color: #333;
        }
        
        .skill-list {
            display: grid;
            gap: 1rem;
        }
        
        .skill-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        
        .skill-info h4 {
            font-size: 1rem;
            margin-bottom: 0.25rem;
        }
        
        .skill-info p {
            font-size: 0.875rem;
            color: #666;
        }
        
        .skill-actions {
            display: flex;
            gap: 0.5rem;
        }
        
        .btn {
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.875rem;
            transition: all 0.2s;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
        }
        
        .btn-primary:hover {
            background: #5a6fd6;
        }
        
        .btn-secondary {
            background: #e0e0e0;
            color: #333;
        }
        
        .btn-secondary:hover {
            background: #d0d0d0;
        }
        
        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 500;
        }
        
        .status-active {
            background: #d4edda;
            color: #155724;
        }
        
        .status-inactive {
            background: #f8d7da;
            color: #721c24;
        }
        
        .log-container {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 1rem;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 0.875rem;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .log-entry {
            margin-bottom: 0.5rem;
            padding: 0.25rem 0;
        }
        
        .log-time {
            color: #858585;
        }
        
        .log-level-info {
            color: #4fc1ff;
        }
        
        .log-level-error {
            color: #f48771;
        }
        
        .refresh-btn {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: #667eea;
            color: white;
            border: none;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
            font-size: 1.5rem;
            transition: all 0.2s;
        }
        
        .refresh-btn:hover {
            transform: scale(1.1);
            background: #5a6fd6;
        }
    </style>
</head>
<body>
    <header class="header">
        <h1>🚀 MCP Core 技能管理面板</h1>
    </header>
    
    <div class="container">
        <!-- 统计卡片 -->
        <div class="stats-grid">
            <div class="stat-card">
                <h3>总技能数</h3>
                <div class="value" id="total-skills">{{ total_skills }}</div>
            </div>
            <div class="stat-card">
                <h3>活跃技能</h3>
                <div class="value" id="active-skills">{{ active_skills }}</div>
            </div>
            <div class="stat-card">
                <h3>今日执行</h3>
                <div class="value" id="today-executions">{{ today_executions }}</div>
            </div>
            <div class="stat-card">
                <h3>成功率</h3>
                <div class="value" id="success-rate">{{ success_rate }}%</div>
            </div>
        </div>
        
        <!-- 技能列表 -->
        <div class="section">
            <h2>📦 技能列表</h2>
            <div class="skill-list" id="skill-list">
                {% for skill in skills %}
                <div class="skill-item">
                    <div class="skill-info">
                        <h4>{{ skill.name }}</h4>
                        <p>{{ skill.description }}</p>
                        <span class="status-badge status-active">{{ skill.version }}</span>
                    </div>
                    <div class="skill-actions">
                        <button class="btn btn-secondary" onclick="viewSkill('{{ skill.name }}')">查看</button>
                        <button class="btn btn-primary" onclick="executeSkill('{{ skill.name }}')">执行</button>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <!-- 系统日志 -->
        <div class="section">
            <h2>📋 系统日志</h2>
            <div class="log-container" id="log-container">
                {% for log in logs %}
                <div class="log-entry">
                    <span class="log-time">{{ log.time }}</span>
                    <span class="log-level-{{ log.level }}">[{{ log.level.upper() }}]</span>
                    {{ log.message }}
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
    
    <button class="refresh-btn" onclick="refreshData()">🔄</button>
    
    <script>
        function refreshData() {
            location.reload();
        }
        
        function viewSkill(skillName) {
            alert('查看技能: ' + skillName);
        }
        
        function executeSkill(skillName) {
            fetch('/api/skills/' + skillName + '/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({action: 'default'})
            })
            .then(response => response.json())
            .then(data => {
                alert('执行结果: ' + JSON.stringify(data, null, 2));
            })
            .catch(error => {
                alert('执行失败: ' + error);
            });
        }
        
        // 自动刷新（每30秒）
        setInterval(refreshData, 30000);
    </script>
</body>
</html>
"""

# 保存模板
(templates_dir / "dashboard.html").write_text(DASHBOARD_TEMPLATE, encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """主面板"""
    # 获取所有技能
    skills = skill_registry.list_skills()

    # 模拟统计数据
    stats = {
        "total_skills": len(skills),
        "active_skills": len(skills),
        "today_executions": 42,
        "success_rate": 95,
        "skills": skills,
        "logs": [
            {
                "time": datetime.now().strftime("%H:%M:%S"),
                "level": "info",
                "message": "系统启动成功",
            },
            {
                "time": datetime.now().strftime("%H:%M:%S"),
                "level": "info",
                "message": f"加载了 {len(skills)} 个技能",
            },
        ],
    }

    return templates.TemplateResponse("dashboard.html", {"request": request, **stats})


@app.get("/api/skills")
async def get_skills():
    """获取所有技能列表"""
    skills = skill_registry.list_skills()
    return {"skills": skills, "total": len(skills)}


@app.get("/api/skills/{skill_name}")
async def get_skill(skill_name: str):
    """获取技能详情"""
    skill = skill_registry.get_skill(skill_name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"技能不存在: {skill_name}")

    return {
        "name": skill.name,
        "description": skill.description,
        "version": skill.version,
        "parameters": skill.get_parameters(),
    }


@app.post("/api/skills/{skill_name}/execute")
async def execute_skill(skill_name: str, params: dict):
    """执行技能"""
    skill = skill_registry.get_skill(skill_name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"技能不存在: {skill_name}")

    try:
        result = skill.execute(params)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="执行失败，请检查日志获取详细信息")


@app.get("/api/stats")
async def get_stats():
    """获取系统统计信息"""
    skills = skill_registry.list_skills()

    return {
        "total_skills": len(skills),
        "active_skills": len(skills),
        "system_status": "running",
        "uptime": "1h 23m",
    }


@app.get("/api/config")
async def get_config():
    """获取系统配置"""
    config_manager = get_config_manager()
    return config_manager.get_all_configs()


@app.post("/api/config/{config_name}")
async def update_config(config_name: str, config: dict):
    """更新配置"""
    config_manager = get_config_manager()
    success = config_manager.save_config(config_name, config)

    if success:
        return {"success": True, "message": "配置已更新"}
    else:
        raise HTTPException(status_code=500, detail="配置更新失败")


@app.get("/api/performance")
async def get_performance():
    """获取性能指标"""
    monitor = get_performance_monitor()
    return {
        "metrics": [m.to_dict() for m in monitor.get_metrics()],
        "stats": monitor.get_skill_statistics(),
    }


# ─── IronClaw Observer API ─────────────────────────────────

@app.get("/api/observer/dashboard")
async def observer_dashboard():
    """获取小龙虾行为追踪仪表盘数据"""
    if not HAS_OBSERVER:
        return {"error": "Observer未安装", "stats": {}}
    obs = get_observer()
    return obs.get_dashboard_data()


@app.get("/api/observer/mindmap")
async def observer_mindmap():
    """获取思维导图数据"""
    if not HAS_OBSERVER:
        return {"error": "Observer未安装"}
    obs = get_observer()
    return obs.get_mind_map_data()


@app.get("/api/observer/actions")
async def observer_actions(limit: int = 50):
    """获取最近行为记录"""
    if not HAS_OBSERVER:
        return []
    obs = get_observer()
    return obs.get_recent_actions(limit)


@app.post("/api/observer/session")
async def observer_new_session():
    """开启新会话"""
    if not HAS_OBSERVER:
        return {"error": "Observer未安装"}
    obs = get_observer()
    new_id = obs.new_session()
    return {"session_id": new_id}


@app.get("/mindmap")
async def mindmap_page():
    """思维导图可视化页面"""
    mindmap_path = Path(__file__).parent / "web" / "mindmap_viewer.html"
    if mindmap_path.exists():
        return HTMLResponse(mindmap_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>思维导图页面未找到</h1>")


def start_web_ui(host: str = "127.0.0.1", port: int = 8080):
    """启动 Web UI"""
    import uvicorn

    print(f"🚀 启动 MCP Core Web UI...")
    print(f"📍 访问地址: http://{host}:{port}")
    print(f"🛑 按 Ctrl+C 停止服务")

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_web_ui()
