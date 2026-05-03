#!/usr/bin/env python3
"""
统一游戏技能接口 - 整合所有游戏相关技能
"""

import sys
import json
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler

class GameSkillManager:
    def __init__(self):
        self.game_servers = {
            'minecraft': {
                'name': '我的世界',
                'server': 'localhost',
                'port': 8890,
                'description': '服务器管理、插件开发等'
            },
            'terraria': {
                'name': '泰拉瑞亚',
                'server': 'localhost',
                'port': 8891,
                'description': '模组开发和管理'
            }
        }
    
    def call_game_skill(self, game_name, command, params=None):
        """调用特定游戏技能"""
        if params is None:
            params = {}
        
        if game_name not in self.game_servers:
            return {
                'status': 'error',
                'message': f'未知游戏: {game_name}，支持的游戏: {list(self.game_servers.keys())}'
            }
        
        game_config = self.game_servers[game_name]
        try:
            # 构建MCP命令
            mcp_command = {
                'command': command,
                'params': params
            }
            
            # 发送请求到游戏技能服务器
            url = f"http://{game_config['server']}:{game_config['port']}"
            response = requests.post(url, json=mcp_command, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'status': 'error',
                    'message': f'请求失败，状态码: {response.status_code}'
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'连接失败: {str(e)}'
            }
    
    def list_supported_games(self):
        """列出支持的游戏"""
        return {
            'status': 'success',
            'result': {
                'games': [
                    {
                        'name': game_name,
                        'display_name': game_info['name'],
                        'description': game_info['description'],
                        'server': f"http://{game_info['server']}:{game_info['port']}"
                    }
                    for game_name, game_info in self.game_servers.items()
                ]
            }
        }
    
    def get_game_info(self, game_name):
        """获取游戏信息"""
        if game_name not in self.game_servers:
            return {
                'status': 'error',
                'message': f'未知游戏: {game_name}'
            }
        
        game_config = self.game_servers[game_name]
        return {
            'status': 'success',
            'result': {
                'name': game_name,
                'display_name': game_config['name'],
                'description': game_config['description'],
                'server': f"http://{game_config['server']}:{game_config['port']}"
            }
        }

class MCPHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, manager=None, **kwargs):
        self.manager = manager
        super().__init__(*args, **kwargs)
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        # 处理MCP命令
        response = self.handle_command(data)
        
        # 发送响应
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    def handle_command(self, data):
        command = data.get('command', '')
        params = data.get('params', {})
        
        if command == 'call_game_skill':
            game_name = params.get('game_name', '')
            game_command = params.get('game_command', '')
            game_params = params.get('game_params', {})
            
            if not game_name or not game_command:
                return {'status': 'error', 'message': '请提供游戏名称和命令'}
            
            return self.manager.call_game_skill(game_name, game_command, game_params)
        
        elif command == 'list_supported_games':
            return self.manager.list_supported_games()
        
        elif command == 'get_game_info':
            game_name = params.get('game_name', '')
            if not game_name:
                return {'status': 'error', 'message': '请提供游戏名称'}
            
            return self.manager.get_game_info(game_name)
        
        elif command == 'list_functions':
            return {
                'status': 'success',
                'result': {
                    'functions': [
                        'call_game_skill',
                        'list_supported_games',
                        'get_game_info',
                        'list_functions'
                    ]
                }
            }
        
        else:
            return {
                'status': 'error',
                'message': f'未知命令: {command}'
            }

def main():
    manager = GameSkillManager()
    
    def handler(*args, **kwargs):
        return MCPHandler(*args, manager=manager, **kwargs)
    
    if len(sys.argv) > 1 and sys.argv[1] == 'mcp':
        # 启动MCP服务器
        server_address = ('', 8899)
        httpd = HTTPServer(server_address, handler)
        print('统一游戏技能接口MCP服务器启动在端口 8899')
        httpd.serve_forever()
    else:
        # 直接运行时的测试
        print('统一游戏技能接口 - 整合所有游戏相关技能')
        print('使用: python skill.py mcp 启动MCP服务器')

if __name__ == '__main__':
    main()
