---
name: "cypress-qa-testing"
description: "Cypress QA自动化框架，基于TypeScript+Cucumber，包含UI和API测试、完整BDD流程。适用于Web应用项目的端到端测试验证。"
---

# Cypress QA Testing Skill

## 概述

本技能基于 [cypress-qa-automation](https://github.com/ricardoisgood/cypress-qa-automation) 项目，提供专业的 Cypress 自动化测试解决方案。

## 功能特性

- **UI自动化**：完整的Web界面自动化测试
- **BDD支持**：使用 Cucumber Gherkin 语法编写测试
- **API测试**：RESTful API 完整CRUD测试
- **丰富场景**：覆盖表格、表单、弹窗、动态属性、上传下载等
- **Mochawesome报告**：生成美观的HTML测试报告
- **CI/CD集成**：支持 GitHub Actions

## 技术栈

- Cypress 13+
- TypeScript
- Cucumber (@badeball/cypress-cucumber-preprocessor)
- esbuild bundler
- Mochawesome reporter
- Node.js (LTS)

## 项目结构

```
cypress-qa-automation/
├── cypress/
│   ├── e2e/
│   │   └── features/     # Gherkin feature文件
│   └── step_definitions/
│       └── steps.ts      # 步骤定义
├── cypress.config.ts
├── package.json
└── tsconfig.json
```

## 已实现的测试场景

### UI测试
- **Web Tables**：CRUD操作、字段边界、搜索、分页
- **Forms**：必填字段、特殊字符、邮箱、手机、日期选择器、图片上传
- **Alerts & Frames**：弹窗处理、框架切换、新标签页
- **Dynamic Properties**：动态属性验证
- **Upload & Download**：文件上传下载
- **Widgets**：手风琴、自动完成、标签页、工具提示

### API测试
- GET端点验证
- 完整CRUD操作
- 错误处理（404等）
- 性能验证（响应时间<1500ms）

## 使用方法

### 本地运行

```bash
# 安装依赖
npm install

# 打开Cypress测试运行器
npm run cypress:open

# 无头模式运行并生成报告
npm run cypress:run
```

### 报告查看

Mochawesome 报告生成在：`cypress/reports/html/index.html`

## 适用场景

- Web应用项目的端到端测试
- 需要BDD风格测试文档的项目
- 需要详细测试报告的CI/CD流程
- 表单验证、UI交互测试

## 集成到总检查

本skill作为总检查plugin的一部分，在项目结束时被调用进行Web UI测试验证。