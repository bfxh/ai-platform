#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Unified Core System v9 - 终极整合版

架构层级：
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: API Gateway (HTTP/TCP/WebSocket)                  │
│  - 统一入口 /api/v1/*                                       │
│  - 认证/限流/路由                                           │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Service Mesh (内嵌服务网格)                        │
│  - 服务注册/发现/健康检查                                    │
│  - 负载均衡/熔断/重试                                       │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: MCP Services (34+ 服务)                           │
│  - Core: Brain, Prompts, Network, Reader, Collector         │
│  - Dev: CodeInspect, CodeForge, DevKit                      │
│  - Data: Bilibili, Douyin, Downloader                       │
│  - Ext: Browser, Extensions, IronClaw, Installer            │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: Resource Manager (资源管理层)                      │
│  - 进程优先级动态调整                                        │
│  - 内存/CPU监控与限制                                        │
│  - 存储配额管理                                              │
├─────────────────────────────────────────────────────────────┤
│  Layer 0: Kernel (系统内核适配)                              │
│  - Windows进程管理                                           │
│  - 文件系统监控                                              │
│  - 网络栈优化                                                │
└─────────────────────────────────────────────────────────────┘

启动顺序：
  1. Kernel初始化 (日志/配置/路径)
  2. Resource Manager启动 (优先级管理)
  3. Service Mesh初始化 (注册表/路由表)
  4. MCP Services按依赖顺序启动
  5. API Gateway启动 (HTTP/TCP)
  6. 系统自检与报告

设计原则：
  - 单一进程，多线程架构
  - 零外部依赖（纯Python标准库）
  - 服务热插拔（动态加载/卸载）
  - 自动故障恢复
  - 资源自适应（根据系统负载调整）
"""

__version__ = "9.0.0"
__author__ = "AI Assistant"
__all__ = [
    "MCPCore", "ServiceRegistry", "ResourceManager",
    "APIGateway", "ServiceMesh", "Kernel"
]
