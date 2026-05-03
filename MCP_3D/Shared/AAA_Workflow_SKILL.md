# AAA 概念设计 → 成品 完整工作流

## 总览
本工作流教 AI 如何驱动 AAA 级游戏的完整生产管线。
所有环节默认使用 photorealism/PBR 标准，杜绝像素/方块/低模风格。

---

## 管线阶段

### Phase 1: 概念设计 (AI图像生成)
**工具: ComfyUI MCP / Stable Diffusion MCP**
```
输入: 文字描述
输出: AAA 级概念图/氛围图/角色设计稿/场景概念

AI提示词模板:
"photorealistic concept art, [主题], 8k, highly detailed, AAA quality,
 cinematic lighting, volumetric fog, ray tracing, subsurface scattering,
 trending on artstation, sharp focus, professional game concept"

负面提示词 (必加):
"pixel art, voxel, blocky, low poly, cartoon, toon, 8-bit, 16-bit,
 blurry, bad anatomy, deformed, ugly"
```

### Phase 2: UI/UX 设计
**工具: Figma MCP / ComfyUI MCP**
```
1. Figma 中设计界面布局/交互原型
2. AI 生成 UI 元素素材 (按钮/图标/面板/槽位)
3. Figma MCP 导出设计规范和资源

UI设计标准:
- HUD: 极简透明背景 + 关键信息高亮
- 菜单: 半透明毛玻璃 + 动画过渡
- 背包: 网格布局 + 物品3D预览
- 对话: 底部字幕条 + 角色头像
```

### Phase 3: 3D 建模管线
**工具: Blender MCP (+ ZBrush/Substance等外部)**
```
高模阶段:
  1. Blender sculpt mode 初雕大型
  2. ZBrush 精细雕刻 (百万~千万面)
  3. 导出高模作为烘焙源

低模阶段:
  1. 高模基础上重拓扑 (TopoGun/Blender)
  2. 目标面数: 角色 30k~100k, 武器 5k~20k, 道具 1k~10k
  3. UV 展开 (RizomUV/Blender)

PBR 贴图制作:
  1. 高模烘焙到低模 (Marmoset Toolbag)
  2. Substance Painter 制作 PBR 贴图集
     - Albedo/BaseColor
     - Normal Map (DirectX)
     - Roughness
     - Metallic
     - Ambient Occlusion
     - Height/Displacement

导出: glTF 2.0 (.glb) → Godot / Unreal / Unity
```

### Phase 4: 地形 & 植被
**工具: Terrain3D (Godot GDExtension) / SpeedTree**
```
Terrain3D 工作流:
  1. 导入高度图 (或程序化噪声生成)
  2. 配置贴图层 (最多32层，2k/4k分辨率)
  3. 雕刻/挖洞/纹理绘制
  4. 植被实例化 (GPU Instancing, 10级LOD)

SpeedTree 工作流:
  1. 程序化生成树木几何 + LOD
  2. 导出 .glb 到 Godot
  3. Terrain3D 植被系统实例化
```

### Phase 5: 材质 & Shader
**工具: Godot Shader Material / Substance Designer**
```
PBR Standard Shader:
  - Metallic/Roughness 工作流
  - Albedo + Normal + ORM 纹理
  - Emission 自发光
  - Subsurface Scattering (皮肤/树叶)

高级 Shader 效果:
  - Wetness/Water (湿润表面)
  - Parallax Occlusion Mapping
  - Detail Normal 叠加
  - Triplanar Mapping (地形)
  - Dither Fading (LOD过渡)
```

### Phase 6: 动画管线
**工具: Blender MCP / Maya MCP / Mixamo**
```
角色动画:
  1. Rigify/Auto-Rig Pro 绑定骨架
  2. IK/FK 控制系统
  3. 关键帧动画 (走/跑/跳/攻击/受击/死亡)
  4. 动画重定向 (Retargeting)

过场动画:
  1. 动作捕捉 (Mocap) 或手K
  2. 摄像机动画 (Cinemachine式)
  3. 面部表情 (Blend Shapes/Morph Targets)

导出: glTF 2.0 带骨骼动画
```

### Phase 7: VFX 特效
**工具: Godot GPUParticles3D / Houdini (Niagara)**
```
粒子系统:
  - GPU Particles (百万级粒子)
  - 子发射器
  - 吸引/碰撞/湍流
  - Shader材质粒子

Houdini 程序化:
  - 破坏/碎裂 (Voronoi)
  - 流体/烟雾/火焰
  - HDA 工具链到 Godot
```

### Phase 8: 关卡设计
**工具: Godot Editor + Godot MCP**
```
流程:
  1. Terrain3D 创建地形
  2. 放置建筑/植被/道具
  3. 设置光照 (方向光+点光源+区域光)
  4. 后期处理 + 体积雾
  5. 碰撞/导航网格生成
  6. 性能分析 (LOD/遮挡剔除)

AI 辅助:
  使用 Godot MCP 让 AI 批量放置资产/调整属性/检查关卡
```

### Phase 9: 音频设计
**工具: ElevenLabs MCP (配音) + Wwise/FMOD + ComfyUI Audio**
```
NPC配音: ElevenLabs MCP
  - 生成多角色对白
  - 情绪变化 (愤怒/悲伤/高兴)

SFX音效: 
  - Foley 音效层叠
  - 空间音频 (3D Audio)
  
BGM音乐:
  - 动态音乐系统
  - 战斗/探索/剧情 状态切换
```

### Phase 10: 系统开发
**工具: Godot MCP + Fuku AI**
```
ECS 架构 (GECS):
  - Entity: 游戏对象
  - Component: 数据 (血量/位置/速度)
  - System: 逻辑 (移动/战斗/AI)

任务系统 (Questify):
  - 图形化任务编辑
  - 分支/条件/奖励
  - 序列化/本地化

AI系统:
  - 行为树 (BehaviorTree)
  - 导航/NavMesh
  - 感知系统 (视觉/听觉)
  - godot-llm 本地 NPC 对话
```

---

## AI 工作指令模板

### 生成概念图时:
"用 ComfyUI 生成 AAA photorealism 概念图: [主题], 
8k, cinematic lighting, volumetric fog, no pixel/voxel/cartoon style"

### 生成 3D 模型时:
"用 Blender 创建 AAA photorealism [物体], PBR材质,
high-poly sculpt, correct real-world proportions, 
game-ready topology, 目标面数 [数字]k"

### 生成材质时:
"生成 [材质名] PBR 材质, 4k, seamless tileable, 
AAA Subsurface scattering, surface imperfections, 
photorealistic wear and tear"

### 编辑关卡时:
"用 Godot MCP 在场景中放置 [类型] 资产,
position [x,y,z], rotation [x,y,z], scale [x,y,z],
设置 PBR 材质, 生成碰撞体"
