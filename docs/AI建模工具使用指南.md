# AI建模工具使用指南 - TripoSR ComfyUI

## 1. 环境准备

### 1.1 安装Python 3.10+
1. 访问官网：https://www.python.org/downloads/
2. 下载Windows 64位版本（推荐3.10或3.11）
3. 运行安装程序，**必须勾选"Add Python to PATH"**
4. 点击"Install Now"

### 1.2 验证Python安装
- 打开命令提示符（Win+R → cmd → 回车）
- 输入 `python --version` 查看版本
- 输入 `pip --version` 查看pip版本

## 2. 安装依赖包

### 2.1 打开命令提示符
- 进入ComfyUI目录：`cd %SOFTWARE_DIR%\AI\ComfyUI`

### 2.2 安装基础依赖
```bash
pip install -r requirements.txt
```

### 2.3 安装TripoSR额外依赖
```bash
pip install einops==0.7.0 trimesh==4.0.5 huggingface-hub imageio[ffmpeg]
```

## 3. 启动ComfyUI

### 3.1 运行启动脚本
- 双击 `%SOFTWARE_DIR%\AI\ComfyUI\启动ComfyUI.bat`
- 或在命令提示符中运行：`python main.py`

### 3.2 访问ComfyUI
- 打开浏览器，访问 http://localhost:8188
- 首次启动可能需要下载额外的模型文件

## 4. 使用TripoSR生成3D模型

### 4.1 加载工作流
1. 点击"Load"按钮
2. 选择 `%SOFTWARE_DIR%\AI\ComfyUI\workflows\workflow_simple.json`

### 4.2 配置参数
1. **Load Image** 节点：点击上传一张2D图像
2. **TripoSR Sampler** 节点：
   - geometry_resolution: 256（默认，可根据需要调整）
   - threshold: 25.0（默认，可根据需要调整）

### 4.3 生成模型
1. 点击"Queue Prompt"按钮
2. 等待生成完成（可能需要几分钟）
3. 在 **TripoSR Viewer** 节点中查看生成的3D模型
4. 点击"Save"按钮保存模型

## 5. 模型格式说明

| 格式 | 用途 | 特点 |
|------|------|------|
| GLB | 通用3D格式 | 单文件包含所有数据 |
| GLTF | 通用3D格式 | 文本格式，支持外部资源 |
| OBJ | 传统3D格式 | 通用性强，文件小 |
| FBX | 游戏引擎格式 | 支持动画、骨骼 |

## 6. 常见问题解决

### 6.1 Python未找到
- 确保Python已安装且添加到PATH
- 重启电脑后再尝试

### 6.2 依赖安装失败
- 确保网络连接正常
- 尝试升级pip：`python -m pip install --upgrade pip`
- 尝试使用国内镜像：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

### 6.3 模型生成失败
- 确保图像质量清晰
- 确保显卡驱动已更新
- 尝试降低geometry_resolution值

### 6.4 CUDA内存不足
- 降低geometry_resolution值
- 关闭其他占用GPU内存的程序
- 考虑使用CPU模式（速度会慢很多）

## 7. 推荐硬件配置

- **CPU**：至少4核心
- **内存**：至少8GB RAM
- **GPU**：建议NVIDIA GeForce RTX 2060或更高
- **存储空间**：至少10GB可用空间

## 8. 相关工具推荐

### 8.1 3D建模软件
- **Blender**：开源3D软件
- **MeshLab**：模型查看和修复
- **Open3D**：3D数据处理

### 8.2 游戏引擎
- **Unity**：跨平台游戏引擎
- **Unreal Engine**：AAA级游戏引擎
- **Godot**：开源轻量级引擎

### 8.3 AI生成工具
- **Stable Diffusion**：AI图像生成
- **TripoSR**：2D到3D模型生成
- **ComfyUI**：节点式AI工作流

## 9. 目录结构

```
%SOFTWARE_DIR%\AI\ComfyUI\
├── custom_nodes\           # 自定义节点（插件）
│   ├── ComfyUI-Flowty-TripoSR\  # TripoSR 插件
│   └── ComfyUI_essentials-main\ # 基础插件
├── models\                # 模型文件
│   ├── hub\               # Hugging Face 模型
│   ├── rembg\             # 背景移除模型
│   └── triposrmodel.ckpt   # TripoSR 主模型
├── workflows\             # 工作流文件
│   ├── workflow_simple.json     # 简单工作流
│   └── workflow_rembg.json      # 带背景移除的工作流
├── main.py                # ComfyUI 主程序
├── requirements.txt       # 依赖包列表
├── 启动ComfyUI.bat        # 启动脚本
└── 安装使用指南.md         # 本指南
```

## 10. 联系支持

如果遇到问题，请参考以下资源：
- ComfyUI 官方 GitHub：https://github.com/comfyanonymous/ComfyUI
- TripoSR 官方 GitHub：https://github.com/Flowty-ai/ComfyUI-Flowty-TripoSR
- 本指南由 AI 助手生成，如有问题请联系相关技术支持
