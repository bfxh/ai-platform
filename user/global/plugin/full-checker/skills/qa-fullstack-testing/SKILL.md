---
name: "qa-fullstack-testing"
description: "全栈QA自动化测试框架，基于Playwright+Cucumber，包含API/E2E/移动/性能测试。适用于项目结束前的完整测试流程验证。"
---

# QA Fullstack Testing Skill

## 概述

本技能基于 [kit-qa-outsera](https://github.com/tiagonline/kit-qa-outsera) 项目，提供完整的全栈自动化测试解决方案。

## 功能特性

- **API测试**：使用 Playwright + Faker + ZOD 进行功能和契约测试
- **E2E测试**：使用 Cucumber BDD 风格编写测试场景
- **移动测试**：使用 Playwright 进行响应式测试
- **性能测试**：使用 K6 + Docker + Grafana 进行负载测试
- **可访问性测试**：WACG 标准测试

## 技术栈

- TypeScript / JavaScript (Node.js v18+)
- Playwright v1.40+
- CucumberJS v10+
- K6 (性能测试)
- GitHub Actions CI/CD

## 项目结构

```
kit-qa-outsera/
├── .github/workflows/   # CI/CD Pipeline
├── envs/                # 环境配置
├── pages/               # Page Objects
├── tests/
│   ├── api/             # API测试
│   ├── e2e/             # E2E测试 (Cucumber)
│   ├── mobile/          # 移动测试
│   ├── accessibility/   # 可访问性测试
│   └── k6-load/         # 性能测试
└── playwright.config.ts
```

## 使用方法

### 本地运行

```bash
# 安装依赖
npm install
npx playwright install --with-deps

# 运行所有测试 (CI模式)
npm run test:all

# 运行API测试
npm run test:api

# 运行E2E测试
npm run test:e2e

# 运行移动测试
npm run test:mobile

# 运行性能测试 (需要Docker)
npm run test:load
```

### 在项目中使用

1. 将 `\python\kit-qa-outsera` 复制到目标项目
2. 根据项目需求修改 `envs/.env.dev` 配置
3. 在项目的 GitHub Actions 中集成测试流程

## 适用场景

- 项目结束前的完整测试验证
- 需要 API + UI + 性能综合测试的项目
- CI/CD 流程需要并行测试的任务
- 需要 BDD 风格测试文档的团队

## 集成到总检查

本skill作为总检查plugin的一部分，在项目结束时自动被调用进行完整测试验证。
