# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '/python/MCP_Core')
from ironclaw_observer import get_observer

obs = get_observer()
obs.new_session()
obs.record_workflow_start('系统验证', {'source': 'cli_test'})
obs.record_thinking('验证IronClaw Observer是否正常工作')
obs.record_action('tool_call', {'tool': 'test', 'status': 'ok'})
obs.record_workflow_end('success', {'verified': True})
print('OK:', obs.get_stats())
print('Mindmap nodes:', len(obs.get_mind_map_data().get('children', [])))
