#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - TRAE 技能统一包装器
TRAE Skill Unified Wrapper

功能:
- 整合所有 Skills 到统一接口
- 强化错误处理和重试机制
- 性能优化和资源管理
- 统一输出格式
- 支持并行执行

用法:
    python trae_skill_wrapper.py list                    # 列出所有技能
    python trae_skill_wrapper.py execute <skill> <action> # 执行技能
    python trae_skill_wrapper.py mcp                    # MCP 模式运行
"""

import asyncio
import json
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from functools import wraps
import threading
import hashlib

sys.path.insert(0, str(Path(__file__).parent.parent))

from skills.base import Skill, get_registry, SkillRegistry


@dataclass
class SkillResult:
    """技能执行结果"""
    success: bool
    skill_name: str
    action: str
    result: Any = None
    error: str = ""
    execution_time: float = 0
    timestamp: str = ""
    retry_count: int = 0
    cache_hit: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "skill_name": self.skill_name,
            "action": self.action,
            "result": self.result,
            "error": self.error,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp,
            "retry_count": self.retry_count,
            "cache_hit": self.cache_hit
        }


class TRAESkillWrapper:
    """TRAE 技能包装器 - 强化版"""

    def __init__(self):
        self.registry = get_registry()
        self._cache: Dict[str, Any] = {}
        self._cache_lock = threading.RLock()
        self._max_cache_size = 1000
        self._max_retries = 3
        self._retry_delay = 0.5
        self._executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="trae_skill_")
        self._skill_metadata: Dict[str, Dict] = {}
        self._load_all_skills()

    def _load_all_skills(self):
        """加载所有技能并构建元数据"""
        print("=" * 70)
        print("TRAE 技能包装器初始化")
        print("=" * 70)

        skills = self.registry.list()
        print(f"\n发现 {len(skills)} 个技能:\n")

        for skill_info in skills:
            name = skill_info['name']
            actions = skill_info.get('actions', [])
            self._skill_metadata[name] = {
                'description': skill_info.get('description', ''),
                'version': skill_info.get('version', '1.0'),
                'author': skill_info.get('author', 'Unknown'),
                'actions': actions,
                'is_loaded': skill_info.get('is_loaded', False)
            }
            print(f"  [{name}]")
            print(f"    描述: {skill_info.get('description', 'N/A')}")
            print(f"    版本: {skill_info.get('version', '1.0')}")
            print(f"    动作: {', '.join(actions) if actions else 'N/A'}")
            print()

        print("=" * 70)

    def _get_cache_key(self, skill_name: str, action: str, params: Dict) -> str:
        """生成缓存键"""
        cache_data = f"{skill_name}:{action}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(cache_data.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """从缓存获取"""
        with self._cache_lock:
            if cache_key in self._cache:
                entry = self._cache[cache_key]
                if time.time() - entry['timestamp'] < 300:
                    return entry['result']
                else:
                    del self._cache[cache_key]
        return None

    def _save_to_cache(self, cache_key: str, result: Any):
        """保存到缓存"""
        with self._cache_lock:
            if len(self._cache) >= self._max_cache_size:
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]['timestamp'])
                del self._cache[oldest_key]
            self._cache[cache_key] = {
                'result': result,
                'timestamp': time.time()
            }

    def _retry_with_backoff(self, func: Callable, *args, **kwargs) -> Any:
        """指数退避重试"""
        last_exception = None
        for attempt in range(self._max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self._max_retries - 1:
                    delay = self._retry_delay * (2 ** attempt)
                    time.sleep(delay)
        raise last_exception

    def execute(self, skill_name: str, action: str = "", params: Optional[Dict] = None) -> SkillResult:
        """执行技能 - 强化版"""
        params = params or {}
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        retry_count = 0

        cache_key = self._get_cache_key(skill_name, action, params)
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return SkillResult(
                success=True,
                skill_name=skill_name,
                action=action,
                result=cached_result,
                execution_time=time.time() - start_time,
                timestamp=timestamp,
                cache_hit=True
            )

        try:
            skill = self.registry.get(skill_name)
            if not skill:
                raise ValueError(f"技能不存在: {skill_name}")

            execute_params = {'action': action, **params} if action else params

            def _execute_with_retry():
                nonlocal retry_count
                for attempt in range(self._max_retries):
                    try:
                        retry_count = attempt
                        return skill.execute(execute_params)
                    except Exception as e:
                        if attempt < self._max_retries - 1:
                            time.sleep(self._retry_delay * (2 ** attempt))
                        else:
                            raise

            result = _execute_with_retry()

            if result.get('success', False):
                self._save_to_cache(cache_key, result)
                return SkillResult(
                    success=True,
                    skill_name=skill_name,
                    action=action,
                    result=result,
                    execution_time=time.time() - start_time,
                    timestamp=timestamp,
                    retry_count=retry_count
                )
            else:
                return SkillResult(
                    success=False,
                    skill_name=skill_name,
                    action=action,
                    error=result.get('error', 'Unknown error'),
                    execution_time=time.time() - start_time,
                    timestamp=timestamp,
                    retry_count=retry_count
                )

        except Exception as e:
            return SkillResult(
                success=False,
                skill_name=skill_name,
                action=action,
                error=f"{str(e)}\n{traceback.format_exc()}",
                execution_time=time.time() - start_time,
                timestamp=timestamp,
                retry_count=retry_count
            )

    def execute_parallel(self, tasks: List[Dict[str, Any]]) -> List[SkillResult]:
        """并行执行多个技能"""
        futures = []
        for task in tasks:
            skill_name = task.get('skill_name')
            action = task.get('action', '')
            params = task.get('params', {})
            future = self._executor.submit(self.execute, skill_name, action, params)
            futures.append(future)

        results = []
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                results.append(SkillResult(
                    success=False,
                    skill_name="unknown",
                    action="",
                    error=str(e)
                ))
        return results

    def list_skills(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出所有技能"""
        skills = self.registry.list()
        if category:
            skills = [s for s in skills if s.get('category') == category]
        return skills

    def get_skill_info(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """获取技能详细信息"""
        return self._skill_metadata.get(skill_name)

    def search_skills(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索技能"""
        keyword = keyword.lower()
        results = []
        for skill_name, metadata in self._skill_metadata.items():
            if keyword in skill_name.lower():
                results.append({'name': skill_name, **metadata})
            elif keyword in metadata.get('description', '').lower():
                results.append({'name': skill_name, **metadata})
        return results

    def validate_skill(self, skill_name: str) -> Dict[str, Any]:
        """验证技能可用性"""
        skill = self.registry.get(skill_name)
        if not skill:
            return {'valid': False, 'error': f"技能不存在: {skill_name}"}

        try:
            result = skill.execute({'action': 'test'})
            return {'valid': True, 'skill_name': skill_name, 'test_result': result}
        except Exception as e:
            return {'valid': False, 'skill_name': skill_name, 'error': str(e)}

    def get_all_actions(self) -> Dict[str, List[str]]:
        """获取所有技能的动作"""
        actions = {}
        for skill_name, metadata in self._skill_metadata.items():
            actions[skill_name] = metadata.get('actions', [])
        return actions

    def shutdown(self):
        """关闭包装器"""
        self._executor.shutdown(wait=True)
        self._cache.clear()


class TRAEMCPInterface:
    """TRAE MCP 接口"""

    def __init__(self):
        self.wrapper = TRAESkillWrapper()

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理 MCP 请求"""
        action = request.get('action', '')
        params = request.get('params', {})

        if action == 'list':
            return {'success': True, 'skills': self.wrapper.list_skills()}

        elif action == 'execute':
            skill_name = params.get('skill_name')
            skill_action = params.get('action', '')
            skill_params = params.get('params', {})
            result = self.wrapper.execute(skill_name, skill_action, skill_params)
            return result.to_dict()

        elif action == 'parallel':
            tasks = params.get('tasks', [])
            results = self.wrapper.execute_parallel(tasks)
            return {'success': True, 'results': [r.to_dict() for r in results]}

        elif action == 'search':
            keyword = params.get('keyword', '')
            results = self.wrapper.search_skills(keyword)
            return {'success': True, 'results': results}

        elif action == 'info':
            skill_name = params.get('skill_name')
            info = self.wrapper.get_skill_info(skill_name)
            return {'success': True, 'info': info} if info else {'success': False, 'error': 'Skill not found'}

        elif action == 'validate':
            skill_name = params.get('skill_name')
            result = self.wrapper.validate_skill(skill_name)
            return {'success': True, 'validation': result}

        elif action == 'all_actions':
            actions = self.wrapper.get_all_actions()
            return {'success': True, 'actions': actions}

        else:
            return {'success': False, 'error': f'Unknown action: {action}'}

    def run_mcp_server(self):
        """运行 MCP 服务器"""
        print("\n" + "=" * 70)
        print("TRAE Skill MCP Server 已启动")
        print("=" * 70)
        print("\n等待请求...\n")

        import select
        while True:
            if select.select([sys.stdin], [], [], 0.1)[0]:
                line = sys.stdin.readline()
                if not line:
                    break
                try:
                    request = json.loads(line)
                    response = self.handle_request(request)
                    print(json.dumps(response, ensure_ascii=False))
                    sys.stdout.flush()
                except json.JSONDecodeError:
                    print(json.dumps({'success': False, 'error': 'Invalid JSON'}))
                    sys.stdout.flush()


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    wrapper = TRAESkillWrapper()

    if cmd == 'list':
        print("\n所有可用技能:")
        for skill_name, metadata in wrapper._skill_metadata.items():
            print(f"\n  [{skill_name}]")
            print(f"    描述: {metadata.get('description', 'N/A')}")
            print(f"    版本: {metadata.get('version', '1.0')}")
            print(f"    作者: {metadata.get('author', 'Unknown')}")
            print(f"    动作: {', '.join(metadata.get('actions', []))}")

    elif cmd == 'execute':
        if len(sys.argv) < 4:
            print("用法: execute <skill_name> <action> [params_json]")
            return
        skill_name = sys.argv[2]
        action = sys.argv[3]
        params = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
        result = wrapper.execute(skill_name, action, params)
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))

    elif cmd == 'search':
        if len(sys.argv) < 3:
            print("用法: search <keyword>")
            return
        keyword = sys.argv[2]
        results = wrapper.search_skills(keyword)
        print(json.dumps(results, ensure_ascii=False, indent=2))

    elif cmd == 'validate':
        if len(sys.argv) < 3:
            print("用法: validate <skill_name>")
            return
        skill_name = sys.argv[2]
        result = wrapper.validate_skill(skill_name)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif cmd == 'mcp':
        mcp = TRAEMCPInterface()
        mcp.run_mcp_server()

    elif cmd == 'parallel':
        print("并行执行示例:")
        tasks = [
            {'skill_name': 'system_optimizer', 'action': 'status'},
            {'skill_name': 'github_opensource', 'action': 'templates'},
        ]
        results = wrapper.execute_parallel(tasks)
        for r in results:
            print(f"\n{r.skill_name}: {'成功' if r.success else '失败'}")
            if r.result:
                print(f"  结果: {str(r.result)[:200]}...")

    else:
        print(f"未知命令: {cmd}")
        print(__doc__)

    wrapper.shutdown()


if __name__ == '__main__':
    main()
