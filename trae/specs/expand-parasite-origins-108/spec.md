# 虫族起源扩展至108+种族 Spec

## Why
当前整合包仅有22个起源（11个swarm_origins + 10个Origins原版改造），远低于用户要求的108+种族。且中文翻译混乱——Origins原版的zh_cn.json中同时存在旧名（人类、羽人族）和新名（寄生原体、寄生蜂），游戏内显示不一致。

## What Changes
- 将虫族起源从22个扩展到108+个，全部为虫族/寄生虫主题变体
- 修复所有中文翻译，确保游戏内显示统一的虫族名称
- 每个起源拥有独特的能力组合和中文描述
- 按寄生虫进化体系分类：基础型、寄生型、变异型、进化型、终极型
- **BREAKING**: 完全替换Origins原版起源层(origin layer)，所有可选起源均为虫族

## Impact
- Affected specs: swarm_origins-5.0.0.jar, Origins-1.13.0-alpha.4+mc.1.20.4.jar
- Affected code: 
  - swarm_origins JAR 内所有 origin JSON + power JSON + lang JSON
  - Origins JAR 内 origin JSON + lang JSON
  - origin layer 配置

## ADDED Requirements

### Requirement: 108+虫族起源体系
系统 SHALL 提供108个以上虫族/寄生虫主题起源，按以下进化体系分类：

#### 进化体系分类
1. **基础型 (影响1)** — 约30个：幼虫、蛹体、寄生原体等低级形态
2. **寄生型 (影响2)** — 约35个：各种寄生方式（空中、水中、地下、精神等）
3. **变异型 (影响2)** — 约20个：适应特定环境的变异体
4. **进化型 (影响3)** — 约15个：高级进化形态
5. **终极型 (影响3)** — 约8个：虫群女王、虫神等终极形态

#### Scenario: 玩家选择起源
- **WHEN** 玩家首次进入世界看到起源选择界面
- **THEN** 显示108+个虫族起源，全部有中文名称和描述
- **AND** 每个起源有独特图标和影响等级

### Requirement: 统一中文翻译
系统 SHALL 确保所有起源和能力在游戏内显示正确的中文名称和描述。

#### Scenario: 中文显示
- **WHEN** 玩家在起源选择界面查看任意起源
- **THEN** 显示中文名称（如"血吸虫"）而非英文名（如"Blood Fluke"）
- **AND** 描述文本完整且符合虫族主题

### Requirement: 能力复用与组合
系统 SHALL 通过组合现有122个能力来创建新起源，而非创建新能力类型。

#### Scenario: 能力组合
- **WHEN** 创建新起源时
- **THEN** 从现有能力池中选择3-7个能力组合
- **AND** 确保所有引用的能力都已注册且无错误

### Requirement: 起源层配置
系统 SHALL 配置origin layer以支持108+个起源的选择。

#### Scenario: 起源选择
- **WHEN** 玩家打开起源选择GUI
- **THEN** 可以滚动浏览所有108+个起源
- **AND** 每个起源可正常选择

## MODIFIED Requirements

### Requirement: Origins原版起源替换
原版10个起源已被替换为虫族变体，但翻译不一致。需要统一修复zh_cn.json，移除旧名（人类、羽人族等），只保留虫族名称。

## REMOVED Requirements

### Requirement: 旧版22起源体系
**Reason**: 不足以满足用户需求，需要扩展到108+
**Migration**: 保留现有11个swarm_origins起源作为基础，扩展新起源
