#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GStackCore Web界面

简洁的Web界面，提供GitHub操作功能
"""

import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path

from gstack_core import GStackCore


class GStackHTTPHandler(BaseHTTPRequestHandler):
    """HTTP请求处理器"""

    core = GStackCore()

    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)

        if path == "/" or path == "/index.html":
            self.send_html(self.get_index_page())
        elif path == "/api/status":
            self.send_json(self.core.get_status())
        elif path == "/api/history":
            limit = int(query.get("limit", [10])[0])
            self.send_json({"success": True, "tasks": self.core.get_task_history(limit)})
        elif path.startswith("/api/"):
            action = path[5:]  # 去掉 /api/
            params = {k: v[0] if len(v) == 1 else v for k, v in query.items()}
            
            # 特殊处理自然语言任务
            if action == "natural_language":
                task_description = params.get("query")
                if task_description:
                    result = self.core.process_natural_language(task_description)
                    self.send_json(result)
                else:
                    self.send_json({"success": False, "error": "缺少query参数"})
            else:
                result = self.core.execute(action, params)
                self.send_json(result)
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        """处理POST请求"""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        try:
            data = json.loads(body)
            action = data.get("action")
            params = data.get("params", {})

            result = self.core.execute(action, params)
            self.send_json(result)
        except json.JSONDecodeError:
            self.send_json({"success": False, "error": "无效的JSON格式"})
        except Exception as e:
            self.send_json({"success": False, "error": str(e)})

    def send_json(self, data):
        """发送JSON响应"""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "http://localhost")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def send_html(self, html):
        """发送HTML响应"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def get_index_page(self):
        """首页HTML"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GStackCore - GitHub智能助手</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .header h1 { color: #333; margin-bottom: 10px; }
        .header p { color: #666; }
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .card h2 { color: #333; margin-bottom: 15px; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; color: #666; font-weight: 500; }
        .form-group input, .form-group select, .form-group textarea {
            width: 100%;
            padding: 10px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        .form-group textarea {
            height: 100px;
            resize: vertical;
        }
        .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn {
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            transition: transform 0.2s;
        }
        .btn:hover { transform: translateY(-2px); }
        .result {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
            font-family: monospace;
            font-size: 13px;
            white-space: pre-wrap;
            max-height: 400px;
            overflow-y: auto;
        }
        .status-bar {
            display: flex;
            gap: 20px;
            margin-top: 15px;
        }
        .status-item {
            padding: 10px 20px;
            background: #e7f3ff;
            border-radius: 8px;
            color: #0066cc;
            font-size: 14px;
        }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
        .chat-container {
            max-width: 800px;
            margin: 0 auto;
        }
        .chat-message {
            margin-bottom: 15px;
            padding: 15px;
            border-radius: 10px;
        }
        .user-message {
            background: #e3f2fd;
            margin-left: 20%;
            border-top-right-radius: 0;
        }
        .system-message {
            background: #f3e5f5;
            margin-right: 20%;
            border-top-left-radius: 0;
        }
        .message-content {
            font-size: 14px;
            line-height: 1.4;
        }
        .message-time {
            font-size: 11px;
            color: #666;
            margin-top: 5px;
            text-align: right;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>[AI] GStackCore - GitHub智能助手</h1>
            <p>智能理解自然语言，自动规划和执行GitHub任务</p>
            <div class="status-bar" id="statusBar">
                <div class="status-item">加载中...</div>
            </div>
        </div>

        <!-- 智能自然语言界面 -->
        <div class="card">
            <h2>💬 智能对话</h2>
            <div class="form-group">
                <label>输入自然语言任务</label>
                <textarea id="nlpInput" placeholder="例如：查找GitHub上最受欢迎的Python Web框架，分析microsoft/vscode仓库的活跃度，比较facebook/react和vuejs/vue"></textarea>
            </div>
            <button class="btn" onclick="processNaturalLanguage()">发送</button>
            <div id="chatContainer" class="chat-container">
                <!-- 对话消息将显示在这里 -->
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <h2>👤 获取用户信息</h2>
                <div class="form-group">
                    <label>用户名</label>
                    <input type="text" id="username" placeholder="octocat">
                </div>
                <button class="btn" onclick="getUser()">查询</button>
                <div class="result" id="userResult">结果将显示在这里...</div>
            </div>

            <div class="card">
                <h2>📦 获取仓库信息</h2>
                <div class="form-group">
                    <label>所有者</label>
                    <input type="text" id="repoOwner" placeholder="microsoft">
                </div>
                <div class="form-group">
                    <label>仓库名</label>
                    <input type="text" id="repoName" placeholder="vscode">
                </div>
                <button class="btn" onclick="getRepo()">查询</button>
                <div class="result" id="repoResult">结果将显示在这里...</div>
            </div>
        </div>

        <div class="card">
            <h2>🔍 搜索仓库</h2>
            <div class="form-group">
                <label>搜索关键词</label>
                <input type="text" id="searchQuery" placeholder="python web framework">
            </div>
            <button class="btn" onclick="searchRepos()">搜索</button>
            <div class="result" id="searchResult">结果将显示在这里...</div>
        </div>

        <div class="card">
            <h2>📊 分析仓库</h2>
            <div class="form-group">
                <label>所有者/仓库</label>
                <input type="text" id="analyzeInput" placeholder="microsoft/vscode">
            </div>
            <button class="btn" onclick="analyzeRepo()">分析</button>
            <div class="result" id="analyzeResult">结果将显示在这里...</div>
        </div>

        <div class="card">
            <h2>📜 任务历史</h2>
            <button class="btn" onclick="loadHistory()">刷新</button>
            <div class="result" id="historyResult">结果将显示在这里...</div>
        </div>
    </div>

    <script>
        async function api(action, params = {}) {
            try {
                const response = await fetch(`/api/${action}?${new URLSearchParams(params)}`);
                return await response.json();
            } catch (error) {
                return { success: false, error: error.message };
            }
        }

        async function apiPost(action, data) {
            try {
                const response = await fetch(`/api/${action}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                return await response.json();
            } catch (error) {
                return { success: false, error: error.message };
            }
        }

        async function loadStatus() {
            const result = await api('status');
            if (result.success) {
                document.getElementById('statusBar').innerHTML = `
                    <div class="status-item">任务: ${result.tasks_completed}/${result.tasks_total}</div>
                    <div class="status-item">API限制: ${result.rate_limit?.remaining || '?'}/${result.rate_limit?.limit || '?'}</div>
                `;
            }
        }

        async function getUser() {
            const username = document.getElementById('username').value;
            if (!username) { alert('请输入用户名'); return; }
            const result = await api('get_user', { username });
            document.getElementById('userResult').textContent = JSON.stringify(result, null, 2);
        }

        async function getRepo() {
            const owner = document.getElementById('repoOwner').value;
            const repo = document.getElementById('repoName').value;
            if (!owner || !repo) { alert('请输入所有者和仓库名'); return; }
            const result = await api('get_repo', { owner, repo });
            document.getElementById('repoResult').textContent = JSON.stringify(result, null, 2);
        }

        async function searchRepos() {
            const query = document.getElementById('searchQuery').value;
            if (!query) { alert('请输入搜索关键词'); return; }
            const result = await api('search_repos', { query, limit: 10 });
            document.getElementById('searchResult').textContent = JSON.stringify(result, null, 2);
        }

        async function analyzeRepo() {
            const input = document.getElementById('analyzeInput').value;
            if (!input) { alert('请输入所有者/仓库'); return; }
            const [owner, repo] = input.split('/');
            if (!owner || !repo) { alert('格式错误，请使用 owner/repo 格式'); return; }
            const result = await api('analyze_repo', { owner, repo });
            document.getElementById('analyzeResult').textContent = JSON.stringify(result, null, 2);
        }

        async function processNaturalLanguage() {
            const input = document.getElementById('nlpInput').value;
            if (!input) { alert('请输入任务描述'); return; }

            // 添加用户消息
            addMessage('user', input);
            document.getElementById('nlpInput').value = '';

            // 显示加载中
            addMessage('system', '正在处理...');

            try {
                const result = await api('natural_language', { query: input });
                
                // 清空加载消息
                const chatContainer = document.getElementById('chatContainer');
                chatContainer.removeChild(chatContainer.lastChild);

                if (result.success) {
                    const data = result.data;
                    let response = '';

                    // 构建响应消息
                    response += `**分析结果:**\n`;
                    response += `- 意图: ${data.analysis.intent}\n`;
                    response += `- 实体: ${JSON.stringify(data.analysis.entities)}\n`;
                    response += `- 置信度: ${(data.confidence * 100).toFixed(1)}%\n\n`;

                    response += `**执行计划:**\n`;
                    data.scheduled_tasks.forEach((task, index) => {
                        response += `${index + 1}. ${task.action}: ${JSON.stringify(task.params)}\n`;
                    });

                    response += `\n**执行结果:**\n`;
                    data.results.forEach((res, index) => {
                        const status = res.success ? '✅' : '❌';
                        response += `${status} ${res.action}: ${res.success ? '成功' : res.error}\n`;
                    });

                    response += `\n**总结:**\n${data.summary}`;

                    addMessage('system', response);
                } else {
                    addMessage('system', `错误: ${result.error}`);
                }
            } catch (error) {
                addMessage('system', `处理失败: ${error.message}`);
            }
        }

        function addMessage(type, content) {
            const chatContainer = document.getElementById('chatContainer');
            const messageDiv = document.createElement('div');
            messageDiv.className = `chat-message ${type}-message`;

            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.innerHTML = content.replace(/\n/g, '<br>').replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>');

            const timeDiv = document.createElement('div');
            timeDiv.className = 'message-time';
            timeDiv.textContent = new Date().toLocaleTimeString();

            messageDiv.appendChild(contentDiv);
            messageDiv.appendChild(timeDiv);
            chatContainer.appendChild(messageDiv);

            // 滚动到底部
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        async function loadHistory() {
            const result = await api('history', { limit: 10 });
            document.getElementById('historyResult').textContent = JSON.stringify(result, null, 2);
        }

        loadStatus();
        setInterval(loadStatus, 30000);
    </script>
</body>
</html>
"""


def run(port=8000):
    """启动服务器"""
    server = HTTPServer(('localhost', port), GStackHTTPHandler)
    print(f"🚀 GStackCore Web界面已启动")
    print(f"   访问地址: http://localhost:{port}")
    print(f"   按 Ctrl+C 停止")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
        server.shutdown()


if __name__ == "__main__":
    run()
