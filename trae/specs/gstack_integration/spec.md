# GSTACK 架构集成与强化 - 产品需求文档

## Overview
- **Summary**: 集成和强化 GSTACK 架构的核心功能，包括 Blender MCP 自然语言控制、n8n 工作流自动化和 Narsil MCP 代码分析能力，实现完整的自动化工作流系统。
- **Purpose**: 解决 AI 工作流自动化问题，提供一个统一的架构来管理和执行各种 AI 任务，特别是 3D 建模、工作流自动化和代码分析。
- **Target Users**: 需要使用 AI 进行 3D 建模、自动化工作流和代码分析的开发者和内容创作者。

## Goals
- 强化 Blender MCP 核心功能，支持自然语言控制 Blender
- 实现 n8n 工作流的自动启动和监控
- 完善 Narsil MCP 的代码分析能力
- 集成所有服务到 GSTACK 自检流程，确保自动拉起
- 提供统一的命令行接口管理所有服务

## Non-Goals (Out of Scope)
- 不开发新的 AI 模型或算法
- 不修改 Blender 核心功能
- 不实现完整的 Docker 管理系统
- 不开发 Web 界面（仅命令行接口）

## Background & Context
- GSTACK 是一个 AI 工作流架构，旨在管理和自动化各种 AI 任务
- 已有的 MCP（Model Control Protocol）架构需要更强大的功能和更好的集成
- 现有的系统缺乏自动启动和监控能力
- 需要更强大的代码分析工具来确保代码质量

## Functional Requirements
- **FR-1**: Blender MCP 支持自然语言命令控制 Blender
- **FR-2**: Blender MCP 提供 HTTP API 接口
- **FR-3**: n8n 工作流系统自动启动和监控
- **FR-4**: Narsil MCP 提供深度代码分析能力
- **FR-5**: 所有服务集成到 GSTACK 自检流程
- **FR-6**: 统一的命令行接口管理所有服务

## Non-Functional Requirements
- **NFR-1**: 服务启动时间不超过 10 秒
- **NFR-2**: 系统稳定性，能够自动恢复服务
- **NFR-3**: 代码分析速度不超过 5 秒/文件
- **NFR-4**: 安全性，避免路径注入等安全问题
- **NFR-5**: 可扩展性，易于添加新的 MCP 服务

## Constraints
- **Technical**: Python 3.7+, PowerShell 5+, Docker (for n8n)
- **Business**: 基于现有 GSTACK 架构，不重新设计核心架构
- **Dependencies**: Blender 4.0+ (for Blender MCP), Docker (for n8n)

## Assumptions
- Blender 已安装在标准路径或配置文件中指定路径
- Docker 已安装并运行
- Python 环境已配置好必要的依赖
- 端口 8400 (Blender MCP), 5678 (n8n), 8401 (Narsil MCP) 未被占用

## Acceptance Criteria

### AC-1: Blender MCP 自然语言控制
- **Given**: Blender MCP 服务已启动
- **When**: 发送自然语言命令 "创建立方体"
- **Then**: Blender 中应创建一个立方体对象
- **Verification**: `programmatic`

### AC-2: Blender MCP HTTP API
- **Given**: Blender MCP 服务已启动
- **When**: 发送 POST 请求到 / 端点
- **Then**: 应返回正确的命令执行结果
- **Verification**: `programmatic`

### AC-3: n8n 自动启动
- **Given**: n8n 服务未运行
- **When**: 运行 gstack 自检
- **Then**: n8n 服务应自动启动
- **Verification**: `programmatic`

### AC-4: Narsil MCP 代码分析
- **Given**: Narsil MCP 客户端已安装
- **When**: 运行 gstack lint --deep <file>
- **Then**: 应返回详细的代码分析结果
- **Verification**: `programmatic`

### AC-5: 服务自动拉起
- **Given**: 服务已停止
- **When**: 运行 gstack anchor
- **Then**: 所有服务应自动启动
- **Verification**: `programmatic`

### AC-6: 命令行接口
- **Given**: GSTACK 已配置
- **When**: 运行 gstack 命令
- **Then**: 应显示正确的帮助信息和执行结果
- **Verification**: `human-judgment`

## Open Questions
- [ ] Blender 的具体安装路径是否需要更灵活的配置？
- [ ] n8n 工作流模板是否需要更多定制化？
- [ ] Narsil MCP 的性能优化策略？