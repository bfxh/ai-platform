# Tasks

- [ ] Task 1: 安装安全扫描工具链
  - [ ] SubTask 1.1: pip install bandit detect-secrets pip-audit safety ruff semgrep
  - [ ] SubTask 1.2: 验证所有工具安装成功 (bandit --version, ruff --version, etc.)
  - [ ] SubTask 1.3: 更新 requirements.txt 添加安全工具依赖

- [ ] Task 2: 创建 pyproject.toml 统一配置
  - [ ] SubTask 2.1: 创建 pyproject.toml，配置 [tool.bandit] [tool.ruff] [tool.mypy] 段
  - [ ] SubTask 2.2: 配置 Ruff S 系列安全规则 + 项目特有忽略
  - [ ] SubTask 2.3: 配置 Bandit 排除目录和严重级别

- [ ] Task 3: 配置 pre-commit 安全 hooks
  - [ ] SubTask 3.1: 创建/更新 .pre-commit-config.yaml，添加 bandit/ruff/detect-secrets/hooks
  - [ ] SubTask 3.2: 生成 .secrets.baseline 基线文件
  - [ ] SubTask 3.3: 运行 pre-commit install 注册钩子
  - [ ] SubTask 3.4: 测试 pre-commit 是否正常拦截安全问题

- [ ] Task 4: 创建 Semgrep 自定义规则
  - [ ] SubTask 4.1: 创建 .semgrep.yml 自定义规则文件
  - [ ] SubTask 4.2: 编写规则: 检测 asyncio.create_task 不保存引用
  - [ ] SubTask 4.3: 编写规则: 检测 0.0.0.0 绑定
  - [ ] SubTask 4.4: 编写规则: 检测 pickle.loads 无校验
  - [ ] SubTask 4.5: 编写规则: 检测 WebSocket 无 Origin 验证
  - [ ] SubTask 4.6: 编写规则: 检测 Access-Control-Allow-Origin: *
  - [ ] SubTask 4.7: 运行 semgrep --config .semgrep.yml 验证规则有效

- [ ] Task 5: 创建一键安全扫描脚本
  - [ ] SubTask 5.1: 创建 scripts/check/security_scan.py
  - [ ] SubTask 5.2: 实现 --quick 模式 (Ruff S + Bandit)
  - [ ] SubTask 5.3: 实现 --full 模式 (全部工具)
  - [ ] SubTask 5.4: 实现 --fix 模式 (自动修复裸 except 等)
  - [ ] SubTask 5.5: 实现 JSON 报告输出到 logs/security/
  - [ ] SubTask 5.6: 测试三种模式均正常工作

- [ ] Task 6: 运行全量安全扫描并生成基线
  - [ ] SubTask 6.1: 运行 security_scan.py --full 生成首次全量报告
  - [ ] SubTask 6.2: 将已知残留问题 (17个 ⚠️) 添加到 Bandit/Semgrep 忽略列表
  - [ ] SubTask 6.3: 生成 bandit-baseline.json
  - [ ] SubTask 6.4: 确认扫描结果中不再有未知的严重/高危问题

# Task Dependencies
- [Task 2] depends on [Task 1] (需要工具安装后才能配置)
- [Task 3] depends on [Task 1, Task 2] (需要工具和配置)
- [Task 4] depends on [Task 1] (需要 Semgrep 安装)
- [Task 5] depends on [Task 1, Task 2] (需要工具和配置)
- [Task 6] depends on [Task 1, Task 2, Task 3, Task 4, Task 5] (需要全部工具就绪)
