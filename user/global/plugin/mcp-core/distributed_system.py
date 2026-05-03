#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - 分布式部署系统

功能:
- 多节点部署支持
- 技能分布式执行
- 负载均衡
- 故障转移
"""

import asyncio
import hashlib
import json
import random
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Callable, Any
import aiohttp


class NodeStatus(Enum):
    """节点状态"""
    HEALTHY = "healthy"
    BUSY = "busy"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


@dataclass
class Node:
    """集群节点"""
    node_id: str
    host: str
    port: int
    status: NodeStatus = NodeStatus.HEALTHY
    last_heartbeat: float = field(default_factory=time.time)
    load: float = 0.0  # CPU 负载
    memory_usage: float = 0.0  # 内存使用率
    active_tasks: int = 0
    total_tasks: int = 0
    capabilities: List[str] = field(default_factory=list)

    @property
    def address(self) -> str:
        return f"http://{self.host}:{self.port}"

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "host": self.host,
            "port": self.port,
            "status": self.status.value,
            "last_heartbeat": self.last_heartbeat,
            "load": self.load,
            "memory_usage": self.memory_usage,
            "active_tasks": self.active_tasks,
            "total_tasks": self.total_tasks,
            "capabilities": self.capabilities,
        }


@dataclass
class Task:
    """分布式任务"""
    task_id: str
    skill_name: str
    params: dict
    priority: int = 5  # 1-10, 10为最高
    created_at: float = field(default_factory=time.time)
    assigned_node: Optional[str] = None
    status: str = "pending"  # pending, running, completed, failed
    result: Any = None
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "skill_name": self.skill_name,
            "params": self.params,
            "priority": self.priority,
            "created_at": self.created_at,
            "assigned_node": self.assigned_node,
            "status": self.status,
            "result": self.result,
            "error": self.error,
        }


class LoadBalancer:
    """负载均衡器"""

    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.algorithm: str = "round_robin"
        self._round_robin_index: int = 0

    def add_node(self, node: Node):
        """添加节点"""
        self.nodes[node.node_id] = node

    def remove_node(self, node_id: str):
        """移除节点"""
        if node_id in self.nodes:
            del self.nodes[node_id]

    def get_healthy_nodes(self) -> List[Node]:
        """获取健康节点"""
        return [
            node for node in self.nodes.values()
            if node.status in [NodeStatus.HEALTHY, NodeStatus.BUSY]
        ]

    def select_node(self, task: Task) -> Optional[Node]:
        """选择执行节点"""
        healthy_nodes = self.get_healthy_nodes()

        if not healthy_nodes:
            return None

        if self.algorithm == "round_robin":
            return self._round_robin_select(healthy_nodes)
        elif self.algorithm == "least_connections":
            return self._least_connections_select(healthy_nodes)
        elif self.algorithm == "least_load":
            return self._least_load_select(healthy_nodes)
        elif self.algorithm == "hash":
            return self._hash_select(healthy_nodes, task)
        else:
            return random.choice(healthy_nodes)

    def _round_robin_select(self, nodes: List[Node]) -> Node:
        """轮询选择"""
        node = nodes[self._round_robin_index % len(nodes)]
        self._round_robin_index += 1
        return node

    def _least_connections_select(self, nodes: List[Node]) -> Node:
        """最少连接数选择"""
        return min(nodes, key=lambda n: n.active_tasks)

    def _least_load_select(self, nodes: List[Node]) -> Node:
        """最低负载选择"""
        return min(nodes, key=lambda n: n.load)

    def _hash_select(self, nodes: List[Node], task: Task) -> Node:
        """哈希选择"""
        hash_value = int(hashlib.md5(task.task_id.encode()).hexdigest(), 16)
        return nodes[hash_value % len(nodes)]

    def update_node_status(self, node_id: str, status: NodeStatus):
        """更新节点状态"""
        if node_id in self.nodes:
            self.nodes[node_id].status = status

    def get_node_stats(self) -> dict:
        """获取节点统计"""
        healthy = len([n for n in self.nodes.values() if n.status == NodeStatus.HEALTHY])
        busy = len([n for n in self.nodes.values() if n.status == NodeStatus.BUSY])
        unhealthy = len([n for n in self.nodes.values() if n.status == NodeStatus.UNHEALTHY])
        offline = len([n for n in self.nodes.values() if n.status == NodeStatus.OFFLINE])

        return {
            "total": len(self.nodes),
            "healthy": healthy,
            "busy": busy,
            "unhealthy": unhealthy,
            "offline": offline,
        }


class FailoverManager:
    """故障转移管理器"""

    def __init__(self, load_balancer: LoadBalancer):
        self.load_balancer = load_balancer
        self.max_retries: int = 3
        self.retry_delay: float = 1.0
        self.failed_tasks: Dict[str, int] = {}  # task_id -> retry_count
        self.circuit_breakers: Dict[str, dict] = {}  # node_id -> breaker state

    async def execute_with_failover(self, task: Task, execute_func: Callable) -> dict:
        """带故障转移的执行"""
        retry_count = 0
        last_error = None

        while retry_count < self.max_retries:
            # 选择节点
            node = self.load_balancer.select_node(task)

            if not node:
                return {
                    "success": False,
                    "error": "没有可用的节点",
                    "task_id": task.task_id,
                }

            # 检查断路器
            if self._is_circuit_open(node.node_id):
                await asyncio.sleep(self.retry_delay)
                retry_count += 1
                continue

            try:
                # 执行任务
                result = await execute_func(node, task)

                # 成功，重置断路器
                self._record_success(node.node_id)

                return {
                    "success": True,
                    "result": result,
                    "node_id": node.node_id,
                    "task_id": task.task_id,
                }

            except Exception as e:
                last_error = str(e)
                self._record_failure(node.node_id)

                # 更新节点状态
                if self.circuit_breakers.get(node.node_id, {}).get("failures", 0) >= 5:
                    self.load_balancer.update_node_status(node.node_id, NodeStatus.UNHEALTHY)

                retry_count += 1
                await asyncio.sleep(self.retry_delay * retry_count)

        return {
            "success": False,
            "error": f"执行失败（重试{retry_count}次）: {last_error}",
            "task_id": task.task_id,
        }

    def _is_circuit_open(self, node_id: str) -> bool:
        """检查断路器是否打开"""
        breaker = self.circuit_breakers.get(node_id, {})
        if breaker.get("state") == "open":
            # 检查是否应该尝试半开
            last_failure = breaker.get("last_failure", 0)
            if time.time() - last_failure > 30:  # 30秒后尝试半开
                breaker["state"] = "half_open"
                return False
            return True
        return False

    def _record_success(self, node_id: str):
        """记录成功"""
        if node_id in self.circuit_breakers:
            self.circuit_breakers[node_id] = {
                "state": "closed",
                "failures": 0,
                "successes": self.circuit_breakers[node_id].get("successes", 0) + 1,
            }

    def _record_failure(self, node_id: str):
        """记录失败"""
        if node_id not in self.circuit_breakers:
            self.circuit_breakers[node_id] = {"state": "closed", "failures": 0}

        self.circuit_breakers[node_id]["failures"] += 1
        self.circuit_breakers[node_id]["last_failure"] = time.time()

        if self.circuit_breakers[node_id]["failures"] >= 5:
            self.circuit_breakers[node_id]["state"] = "open"


class DistributedTaskManager:
    """分布式任务管理器"""

    def __init__(self):
        self.load_balancer = LoadBalancer()
        self.failover_manager = FailoverManager(self.load_balancer)
        self.tasks: Dict[str, Task] = {}
        self.task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.running = False
        self.session: Optional[aiohttp.ClientSession] = None

    async def start(self):
        """启动任务管理器"""
        self.running = True
        self.session = aiohttp.ClientSession()
        self._tasks: set = set()

        task1 = asyncio.create_task(self._heartbeat_check())
        self._tasks.add(task1)
        task1.add_done_callback(self._tasks.discard)

        task2 = asyncio.create_task(self._process_tasks())
        self._tasks.add(task2)
        task2.add_done_callback(self._tasks.discard)

    async def stop(self):
        """停止任务管理器"""
        self.running = False
        if self.session:
            await self.session.close()

    def add_node(self, node_id: str, host: str, port: int, capabilities: List[str] = None):
        """添加节点"""
        node = Node(
            node_id=node_id,
            host=host,
            port=port,
            capabilities=capabilities or [],
        )
        self.load_balancer.add_node(node)

    def remove_node(self, node_id: str):
        """移除节点"""
        self.load_balancer.remove_node(node_id)

    async def submit_task(self, skill_name: str, params: dict, priority: int = 5) -> str:
        """提交任务"""
        task_id = f"task_{int(time.time() * 1000)}_{secrets.randbelow(9000) + 1000}"

        task = Task(
            task_id=task_id,
            skill_name=skill_name,
            params=params,
            priority=priority,
        )

        self.tasks[task_id] = task

        # 添加到队列（优先级队列，数值越小优先级越高）
        await self.task_queue.put((-priority, task_id))

        return task_id

    async def get_task_result(self, task_id: str, timeout: float = 30.0) -> Optional[dict]:
        """获取任务结果"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            task = self.tasks.get(task_id)

            if not task:
                return None

            if task.status == "completed":
                return {
                    "success": True,
                    "result": task.result,
                    "node_id": task.assigned_node,
                }

            if task.status == "failed":
                return {
                    "success": False,
                    "error": task.error,
                    "node_id": task.assigned_node,
                }

            await asyncio.sleep(0.1)

        return {"success": False, "error": "获取结果超时"}

    async def _process_tasks(self):
        """处理任务队列"""
        while self.running:
            try:
                # 获取任务（带超时）
                priority, task_id = await asyncio.wait_for(
                    self.task_queue.get(), timeout=1.0
                )

                task = self.tasks.get(task_id)
                if not task:
                    continue

                t = asyncio.create_task(self._execute_task(task))
                self._tasks.add(t)
                t.add_done_callback(self._tasks.discard)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"任务处理错误: {e}")

    async def _execute_task(self, task: Task):
        """执行单个任务"""
        task.status = "running"

        async def execute_on_node(node: Node, task: Task):
            """在节点上执行任务"""
            url = f"{node.address}/api/skills/{task.skill_name}/execute"

            async with self.session.post(url, json=task.params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"HTTP {response.status}")

        result = await self.failover_manager.execute_with_failover(task, execute_on_node)

        if result["success"]:
            task.status = "completed"
            task.result = result.get("result")
            task.assigned_node = result.get("node_id")
        else:
            task.status = "failed"
            task.error = result.get("error", "未知错误")
            task.assigned_node = result.get("node_id")

    async def _heartbeat_check(self):
        """心跳检测"""
        while self.running:
            await asyncio.sleep(10)  # 每10秒检测一次

            current_time = time.time()

            for node in list(self.load_balancer.nodes.values()):
                # 检查心跳超时
                if current_time - node.last_heartbeat > 30:
                    if node.status != NodeStatus.OFFLINE:
                        print(f"节点 {node.node_id} 心跳超时")
                        self.load_balancer.update_node_status(node.node_id, NodeStatus.OFFLINE)

    async def update_node_heartbeat(self, node_id: str, stats: dict):
        """更新节点心跳"""
        if node_id in self.load_balancer.nodes:
            node = self.load_balancer.nodes[node_id]
            node.last_heartbeat = time.time()
            node.load = stats.get("load", 0.0)
            node.memory_usage = stats.get("memory_usage", 0.0)
            node.active_tasks = stats.get("active_tasks", 0)

            # 根据负载更新状态
            if node.load < 0.7 and node.memory_usage < 0.8:
                node.status = NodeStatus.HEALTHY
            elif node.load < 0.9 and node.memory_usage < 0.9:
                node.status = NodeStatus.BUSY
            else:
                node.status = NodeStatus.UNHEALTHY

    def get_cluster_status(self) -> dict:
        """获取集群状态"""
        return {
            "nodes": self.load_balancer.get_node_stats(),
            "tasks": {
                "total": len(self.tasks),
                "pending": len([t for t in self.tasks.values() if t.status == "pending"]),
                "running": len([t for t in self.tasks.values() if t.status == "running"]),
                "completed": len([t for t in self.tasks.values() if t.status == "completed"]),
                "failed": len([t for t in self.tasks.values() if t.status == "failed"]),
            },
            "load_balancer": {
                "algorithm": self.load_balancer.algorithm,
            },
        }


class DistributedNode:
    """分布式节点（工作节点）"""

    def __init__(self, node_id: str, host: str, port: int, master_address: str):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.master_address = master_address
        self.running = False
        self.session: Optional[aiohttp.ClientSession] = None
        self.skills: Dict[str, Any] = {}

    async def start(self):
        """启动节点"""
        self.running = True
        self.session = aiohttp.ClientSession()

        # 注册到主节点
        await self._register()

        t = asyncio.create_task(self._heartbeat_loop())
        self._tasks.add(t)
        t.add_done_callback(self._tasks.discard)

        # 启动服务
        from aiohttp import web

        app = web.Application()
        app.router.add_post("/api/skills/{skill_name}/execute", self._handle_execute)
        app.router.add_get("/health", self._handle_health)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()

        print(f"节点 {self.node_id} 启动在 {self.host}:{self.port}")

    async def stop(self):
        """停止节点"""
        self.running = False
        if self.session:
            await self.session.close()

    async def _register(self):
        """注册到主节点"""
        url = f"{self.master_address}/api/nodes/register"
        data = {
            "node_id": self.node_id,
            "host": self.host,
            "port": self.port,
            "capabilities": list(self.skills.keys()),
        }

        try:
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    print(f"节点 {self.node_id} 注册成功")
                else:
                    print(f"节点 {self.node_id} 注册失败: HTTP {response.status}")
        except Exception as e:
            print(f"节点 {self.node_id} 注册错误: {e}")

    async def _heartbeat_loop(self):
        """心跳循环"""
        while self.running:
            await asyncio.sleep(5)  # 每5秒发送一次心跳

            url = f"{self.master_address}/api/nodes/heartbeat"
            stats = {
                "node_id": self.node_id,
                "load": self._get_system_load(),
                "memory_usage": self._get_memory_usage(),
                "active_tasks": 0,  # TODO: 实现任务计数
            }

            try:
                async with self.session.post(url, json=stats):
                    pass
            except Exception as e:
                print(f"心跳发送失败: {e}")

    async def _handle_execute(self, request):
        """处理执行请求"""
        skill_name = request.match_info["skill_name"]
        params = await request.json()

        # TODO: 实际执行技能
        result = {"success": True, "message": f"技能 {skill_name} 执行成功", "params": params}

        return aiohttp.web.json_response(result)

    async def _handle_health(self, request):
        """健康检查"""
        return aiohttp.web.json_response({
            "status": "healthy",
            "node_id": self.node_id,
            "timestamp": datetime.now().isoformat(),
        })

    def _get_system_load(self) -> float:
        """获取系统负载"""
        try:
            import psutil
            return psutil.cpu_percent() / 100.0
        except ImportError:
            return 0.0

    def _get_memory_usage(self) -> float:
        """获取内存使用率"""
        try:
            import psutil
            return psutil.virtual_memory().percent / 100.0
        except ImportError:
            return 0.0

    def register_skill(self, skill_name: str, skill_instance: Any):
        """注册技能"""
        self.skills[skill_name] = skill_instance


# 使用示例
async def main():
    """示例用法"""
    # 创建分布式任务管理器（主节点）
    manager = DistributedTaskManager()

    # 添加工作节点
    manager.add_node("node1", "localhost", 9001, ["file_backup", "github_download"])
    manager.add_node("node2", "localhost", 9002, ["ai_toolkit_manager", "notification"])
    manager.add_node("node3", "localhost", 9003, ["system_config", "plugin_manager"])

    # 启动管理器
    await manager.start()

    print("集群状态:", json.dumps(manager.get_cluster_status(), indent=2))

    # 提交任务
    task_id = await manager.submit_task("file_backup", {"action": "backup", "path": "/data"}, priority=8)
    print(f"提交任务: {task_id}")

    # 等待结果
    result = await manager.get_task_result(task_id, timeout=10.0)
    print(f"任务结果: {result}")

    # 停止管理器
    await manager.stop()


if __name__ == "__main__":
    asyncio.run(main())
