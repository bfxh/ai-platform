# Tasks

- [x] Task 1: 设计108+虫族起源完整列表
  - [x] 1.1: 设计5级进化体系（基础30+寄生35+变异20+进化15+终极8）
  - [x] 1.2: 为每个起源定义：ID、中文名、描述、图标、影响等级、能力组合
  - [x] 1.3: 确保能力组合全部使用已注册的122个能力

- [x] Task 2: 修复现有中文翻译
  - [x] 2.1: 修复Origins JAR的zh_cn.json，统一为虫族名称
  - [x] 2.2: 修复swarm_origins JAR的zh_cn.json中的乱码/错字
  - [x] 2.3: 确保origin.origins.*的name和description一致

- [x] Task 3: 扩展swarm_origins JAR至108+起源
  - [x] 3.1: 创建Python脚本生成108+个origin JSON文件
  - [x] 3.2: 每个起源分配3-7个已注册能力的组合
  - [x] 3.3: 生成完整的zh_cn.json和en_us.json翻译文件
  - [x] 3.4: 更新origin layer配置支持108+起源
  - [x] 3.5: 重新打包swarm_origins JAR

- [x] Task 4: 验证游戏加载
  - [x] 4.1: 启动游戏检查108+起源是否全部加载
  - [x] 4.2: 确认0个ERROR/unregistered power
  - [x] 4.3: 验证中文翻译在游戏内正确显示

# Task Dependencies
- [Task 2] depends on [Task 1] (需要知道所有起源的名称才能写翻译)
- [Task 3] depends on [Task 1] (需要完整起源列表才能生成JSON)
- [Task 4] depends on [Task 2, Task 3] (需要翻译和起源都完成后才能验证)
