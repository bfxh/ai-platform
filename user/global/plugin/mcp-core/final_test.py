import sys, json
sys.path.insert(0,'/python/MCP_Core')

from mcp_skill_server import (
    tool_system_check, tool_nl_route, tool_skill_list,
    tool_kb_search, tool_memory_read
)
from knowledge_base import bootstrap_knowledge

bootstrap_knowledge()

print('=== 最终系统验证 ===\n')

s = tool_system_check()['status']
print('系统状态:')
print(f'  NL路由: {s["nl_router"]}')
print(f'  知识库: {s["knowledge_base"]}')
print(f'  知识条目数: {s["knowledge_base_count"]}')
print(f'  MCP Core Skills: {s["mcp_core_skill_count"]}')
print(f'  WorkBuddy Skills: {s["workbuddy_skill_count"]}')
print()

test_cases = [
    '帮我备份D盘的AI文件夹',
    '天气怎么样',
    '记住：我的项目在D:/Projects/MyApp',
    '优化一下系统内存',
    '搜索GitHub上有没有向量数据库项目',
    '生成一张科技感的壁纸',
    '把文件发到另一台电脑',
    'a股最新行情',
]
print('自然语言路由测试:')
for q in test_cases:
    r = tool_nl_route(q)
    conf = r['confidence']
    skill = r['skill_name']
    stype = r['skill_type']
    print(f'  [{conf:.1f}] {q[:30]:<30} -> {skill}')
print()

print('知识库搜索:')
for kw in ['路径', 'API', 'Python', '工作区']:
    r = tool_kb_search(kw)
    print(f'  "{kw}" -> {r["count"]}条')

print('\n验证完成!')
