# ============================================================
# AAA Game Development - Godot 项目模板生成器
# 基于 Godot 4.6.1 + 完整插件生态系统
# 生成时间: 2026-05-02
# ============================================================

param(
    [string]$ProjectName = "AAA_Game_Project",
    [string]$OutputDir = "D:\Projects"
)

$ErrorActionPreference = "Stop"
$ProjectPath = Join-Path $OutputDir $ProjectName
$GodotExe = "D:\rj\KF\JM\Godot_v4.6.1-stable_win64.exe"
$Mcp3dRoot = "\MCP_3D"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     AAA 级 Godot 项目模板生成器                      ║" -ForegroundColor Cyan
Write-Host "║     引擎: Godot 4.6.1 | 标准: AAA Photorealistic      ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================
# Step 1: 创建项目目录结构
# ============================================
Write-Host "[1/7] 创建 AAA 项目目录结构..." -ForegroundColor Yellow

$Dirs = @(
    "$ProjectPath",
    "$ProjectPath\assets",
    "$ProjectPath\assets\models\characters",
    "$ProjectPath\assets\models\environment",
    "$ProjectPath\assets\models\props",
    "$ProjectPath\assets\models\weapons",
    "$ProjectPath\assets\models\vehicles",
    "$ProjectPath\assets\textures\pbr",
    "$ProjectPath\assets\textures\ui",
    "$ProjectPath\assets\textures\vfx",
    "$ProjectPath\assets\materials",
    "$ProjectPath\assets\audio\sfx",
    "$ProjectPath\assets\audio\music",
    "$ProjectPath\assets\audio\voice",
    "$ProjectPath\assets\animations\characters",
    "$ProjectPath\assets\animations\props",
    "$ProjectPath\assets\animations\cinematics",
    "$ProjectPath\assets\vfx\particles",
    "$ProjectPath\assets\vfx\shaders",
    "$ProjectPath\assets\ui\screens",
    "$ProjectPath\assets\ui\hud",
    "$ProjectPath\assets\ui\menus",
    "$ProjectPath\assets\ui\fonts",
    "$ProjectPath\assets\data\quests",
    "$ProjectPath\assets\data\dialogue",
    "$ProjectPath\assets\data\items",
    "$ProjectPath\assets\data\skills",
    "$ProjectPath\scenes\levels",
    "$ProjectPath\scenes\prefabs",
    "$ProjectPath\scenes\ui",
    "$ProjectPath\scenes\cinematics",
    "$ProjectPath\scripts\autoload",
    "$ProjectPath\scripts\systems",
    "$ProjectPath\scripts\entities",
    "$ProjectPath\scripts\ui",
    "$ProjectPath\scripts\ai",
    "$ProjectPath\addons",
    "$ProjectPath\shaders",
    "$ProjectPath\docs",
    "$ProjectPath\thirdparty"
)

foreach ($Dir in $Dirs) {
    New-Item -ItemType Directory -Force -Path $Dir | Out-Null
}
Write-Host "  ✓ 创建了 $($Dirs.Count) 个目录" -ForegroundColor Green

# ============================================
# Step 2: 创建 Godot project.godot 项目文件
# ============================================
Write-Host "[2/7] 创建 project.godot 配置文件..." -ForegroundColor Yellow

$ProjectConfig = @"
; Engine configuration file.
; It's best edited using the editor UI and not directly,
; since the parameters that go here are not all obvious.
;
; Format:
;   [section] ; section goes between []
;   param=value ; assign values to parameters

config_version=5

[application]
config/name="$ProjectName"
config/description="AAA Quality Game Project - Godot 4.6.1"
config/icon="res://assets/textures/ui/icon.svg"

[rendering]
renderer/rendering_method="forward_plus"
renderer/rendering_method.mobile="mobile"
textures/canvas_textures/default_texture_filter=5
quality/driver/driver_name="D3D12"
anti_aliasing/quality/msaa_3d=4
anti_aliasing/quality/screen_space_aa=1
anti_aliasing/quality/use_taa=true
anti_aliasing/quality/use_debanding=true
environment/defaults/default_clear_color=Color(0, 0, 0, 1)
environment/defaults/default_environment="res://scenes/levels/default_environment.tres"

[display]
window/size/viewport_width=1920
window/size/viewport_height=1080
window/size/mode=2
window/stretch/mode="canvas_items"
window/stretch/aspect="expand"

[input]
jump={
    "deadzone": 0.5,
    "events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":32,"key_label":0,"unicode":0,"location":0,"echo":false,"script":null)
    ]
}
sprint={
    "deadzone": 0.5,
    "events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":4194325,"key_label":0,"unicode":0,"location":0,"echo":false,"script":null)
    ]
}
interact={
    "deadzone": 0.5,
    "events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":69,"key_label":0,"unicode":0,"location":0,"echo":false,"script":null)
    ]
}
ui_cancel={
    "deadzone": 0.5,
    "events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":4194305,"key_label":0,"unicode":0,"location":0,"echo":false,"script":null)
    ]
}

[physics]
3d/physics_engine="JoltPhysics3D"
3d/default_gravity=19.6
3d/run_on_separate_thread=true

[editor_plugins]
enabled=PackedStringArray()

[autoload]
GameManager="*res://scripts/autoload/game_manager.gd"
EventBus="*res://scripts/autoload/event_bus.gd"
AudioManager="*res://scripts/autoload/audio_manager.gd"
SaveSystem="*res://scripts/autoload/save_system.gd"

[dotnet]
project/assembly_name="$ProjectName"
"@

Set-Content -Path "$ProjectPath\project.godot" -Value $ProjectConfig -Encoding UTF8
Write-Host "  ✓ project.godot 已创建" -ForegroundColor Green

# ============================================
# Step 3: 创建核心系统脚本 (Autoloads)
# ============================================
Write-Host "[3/7] 创建核心系统脚本..." -ForegroundColor Yellow

# GameManager
@"
extends Node

var current_scene: String = ""
var game_state: String = "menu"
var player_health: float = 100.0
var player_max_health: float = 100.0
var is_paused: bool = false
var difficulty: String = "normal"

enum GameState {
    MENU,
    LOADING,
    PLAYING,
    PAUSED,
    CINEMATIC,
    GAME_OVER
}

func _ready():
    process_mode = Node.PROCESS_MODE_ALWAYS
    Engine.time_scale = 1.0

func change_scene(scene_path: String):
    current_scene = scene_path
    get_tree().change_scene_to_file(scene_path)

func set_game_state(new_state: GameState):
    game_state = new_state

func pause_game():
    is_paused = true
    Engine.time_scale = 0.0
    get_tree().paused = true

func resume_game():
    is_paused = false
    Engine.time_scale = 1.0
    get_tree().paused = false

func quit_game():
    get_tree().quit()
"@ | Set-Content -Path "$ProjectPath\scripts\autoload\game_manager.gd" -Encoding UTF8

# EventBus
@"
extends Node

signal player_damaged(amount: float, source: Node)
signal player_healed(amount: float)
signal player_died()
signal enemy_killed(enemy_type: String, position: Vector3)
signal item_collected(item_id: String, amount: int)
signal quest_started(quest_id: String)
signal quest_completed(quest_id: String)
signal dialogue_started(npc_id: String)
signal dialogue_ended(npc_id: String)
signal checkpoint_reached(position: Vector3)
signal level_completed(level_name: String)
signal achievement_unlocked(achievement_id: String)
signal ui_event(event_name: String, data: Dictionary)
"@ | Set-Content -Path "$ProjectPath\scripts\autoload\event_bus.gd" -Encoding UTF8

# AudioManager
@"
extends Node

const SFX_DIR = "res://assets/audio/sfx/"
const MUSIC_DIR = "res://assets/audio/music/"
const VOICE_DIR = "res://assets/audio/voice/"

var master_volume: float = 1.0:
    set(v):
        master_volume = v
        AudioServer.set_bus_volume_db(AudioServer.get_bus_index("Master"), linear_to_db(v))
var sfx_volume: float = 1.0:
    set(v):
        sfx_volume = v
        AudioServer.set_bus_volume_db(AudioServer.get_bus_index("SFX"), linear_to_db(v))
var music_volume: float = 1.0:
    set(v):
        music_volume = v
        AudioServer.set_bus_volume_db(AudioServer.get_bus_index("Music"), linear_to_db(v))
var voice_volume: float = 1.0:
    set(v):
        voice_volume = v
        AudioServer.set_bus_volume_db(AudioServer.get_bus_index("Voice"), linear_to_db(v))

var music_player: AudioStreamPlayer
var current_music: String = ""

func _ready():
    music_player = AudioStreamPlayer.new()
    add_child(music_player)
    music_player.bus = "Music"

func play_sfx(sfx_name: String, position_3d: Vector3 = Vector3.ZERO):
    var path = SFX_DIR + sfx_name
    if ResourceLoader.exists(path):
        if position_3d != Vector3.ZERO:
            var player = AudioStreamPlayer3D.new()
            get_tree().root.add_child(player)
            player.global_position = position_3d
            player.stream = load(path)
            player.finished.connect(player.queue_free)
            player.play()
        else:
            var player = AudioStreamPlayer.new()
            add_child(player)
            player.stream = load(path)
            player.finished.connect(player.queue_free)
            player.play()

func play_music(music_name: String, fade_duration: float = 1.0):
    if current_music == music_name:
        return
    var path = MUSIC_DIR + music_name
    if ResourceLoader.exists(path):
        current_music = music_name
        var tween = create_tween()
        tween.tween_property(music_player, "volume_db", -80, fade_duration)
        tween.tween_callback(func():
            music_player.stream = load(path)
            music_player.play()
        )
        tween.tween_property(music_player, "volume_db", 0, fade_duration)

func stop_music(fade_duration: float = 1.0):
    var tween = create_tween()
    tween.tween_property(music_player, "volume_db", -80, fade_duration)
    tween.tween_callback(func():
        music_player.stop()
        current_music = ""
        music_player.volume_db = 0
    )
"@ | Set-Content -Path "$ProjectPath\scripts\autoload\audio_manager.gd" -Encoding UTF8

# SaveSystem
@"
extends Node

const SAVE_DIR = "user://saves/"
const SAVE_EXTENSION = ".save"
const META_EXTENSION = ".meta"

var current_save_slot: int = 0

func _ready():
    if not DirAccess.dir_exists_absolute(SAVE_DIR):
        DirAccess.make_dir_absolute(SAVE_DIR)

func save_game(slot: int = 0):
    current_save_slot = slot
    var save_path = SAVE_DIR + "slot_" + str(slot) + SAVE_EXTENSION
    var meta_path = SAVE_DIR + "slot_" + str(slot) + META_EXTENSION
    
    var save_data = {
        "timestamp": Time.get_unix_time_from_system(),
        "scene": GameManager.current_scene,
        "player_health": GameManager.player_health,
        "difficulty": GameManager.difficulty,
    }
    
    var save_file = FileAccess.open(save_path, FileAccess.WRITE)
    save_file.store_string(JSON.stringify(save_data, "\t"))
    save_file.close()
    
    var meta_data = {
        "slot": slot,
        "date": Time.get_datetime_string_from_system(),
        "play_time": 0
    }
    
    var meta_file = FileAccess.open(meta_path, FileAccess.WRITE)
    meta_file.store_string(JSON.stringify(meta_data, "\t"))
    meta_file.close()

func load_game(slot: int = 0) -> Dictionary:
    var save_path = SAVE_DIR + "slot_" + str(slot) + SAVE_EXTENSION
    if not FileAccess.file_exists(save_path):
        return {}
    
    var save_file = FileAccess.open(save_path, FileAccess.READ)
    var json_string = save_file.get_as_text()
    save_file.close()
    
    var json = JSON.new()
    var error = json.parse(json_string)
    if error == OK:
        return json.data
    return {}

func delete_save(slot: int = 0):
    var save_path = SAVE_DIR + "slot_" + str(slot) + SAVE_EXTENSION
    var meta_path = SAVE_DIR + "slot_" + str(slot) + META_EXTENSION
    
    if FileAccess.file_exists(save_path):
        DirAccess.remove_absolute(save_path)
    if FileAccess.file_exists(meta_path):
        DirAccess.remove_absolute(meta_path)

func save_exists(slot: int = 0) -> bool:
    return FileAccess.file_exists(SAVE_DIR + "slot_" + str(slot) + SAVE_EXTENSION)

func get_all_saves() -> Array:
    var saves = []
    for slot in range(10):
        var meta_path = SAVE_DIR + "slot_" + str(slot) + META_EXTENSION
        if FileAccess.file_exists(meta_path):
            var file = FileAccess.open(meta_path, FileAccess.READ)
            var json = JSON.new()
            var error = json.parse(file.get_as_text())
            file.close()
            if error == OK:
                saves.append(json.data)
    return saves
"@ | Set-Content -Path "$ProjectPath\scripts\autoload\save_system.gd" -Encoding UTF8

Write-Host "  ✓ 4 个核心系统脚本已创建" -ForegroundColor Green

# ============================================
# Step 4: 复制插件 (从 MCP_3D 生态)
# ============================================
Write-Host "[4/7] 安装 Godot 插件..." -ForegroundColor Yellow

# Fuku AI 编辑器插件
$FukuSrc = "$Mcp3dRoot\Godot\addons\fuku"
$FukuDst = "$ProjectPath\addons\fuku"
if (Test-Path $FukuSrc) {
    Copy-Item -Path $FukuSrc -Destination $FukuDst -Recurse -Force
    Write-Host "  ✓ Fuku AI 编辑器助手" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Fuku 插件未找到，跳过" -ForegroundColor DarkYellow
}

# AI Coding Assistant
$AiCodeSrc = "$Mcp3dRoot\Godot\addons\ai_coding_assistant"
$AiCodeDst = "$ProjectPath\addons\ai_coding_assistant"
if (Test-Path $AiCodeSrc) {
    Copy-Item -Path $AiCodeSrc -Destination $AiCodeDst -Recurse -Force
    Write-Host "  ✓ AI Coding Assistant" -ForegroundColor Green
} else {
    Write-Host "  ⚠ AI Coding Assistant 未找到，跳过" -ForegroundColor DarkYellow
}

# AI Assistant Hub
$AiHubSrc = "$Mcp3dRoot\Godot\addons\ai_assistant_hub"
$AiHubDst = "$ProjectPath\addons\ai_assistant_hub"
if (Test-Path $AiHubSrc) {
    Copy-Item -Path $AiHubSrc -Destination $AiHubDst -Recurse -Force
    Write-Host "  ✓ AI Assistant Hub" -ForegroundColor Green
} else {
    Write-Host "  ⚠ AI Assistant Hub 未找到，跳过" -ForegroundColor DarkYellow
}

# ============================================
# Step 5: 创建默认环境资源
# ============================================
Write-Host "[5/7] 创建默认 3D 环境..." -ForegroundColor Yellow

# default_environment.tres
@"
[gd_resource type="Environment" load_steps=2 format=3]

[sub_resource type="ProceduralSkyMaterial" id="1"]
sky_top_color = Color(0.2, 0.4, 0.8, 1)
sky_horizon_color = Color(0.6, 0.7, 0.8, 1)
sky_curve = 0.15
sky_energy_multiplier = 2.0
sky_cover = 0.0
sky_cover_modulate = Color(0.6, 0.6, 0.6, 1)
ground_bottom_color = Color(0.15, 0.12, 0.1, 1)
ground_horizon_color = Color(0.3, 0.28, 0.25, 1)
ground_curve = 0.02
ground_energy_multiplier = 3.0
sun_angle_max = 100.0
sun_curve = 0.05
use_debanding = true
texture_size = 2

[resource]
background_mode = 2
sky = SubResource("1")
ambient_light_source = 1
ambient_light_color = Color(0.3, 0.35, 0.45, 1)
ambient_light_sky_contribution = 0.5
ambient_light_energy = 1.5
reflected_light_source = 0
tonemap_mode = 0
tonemap_exposure = 1.2
tonemap_white = 6.0
glow_enabled = true
glow_levels/1 = true
glow_levels/3 = true
glow_levels/5 = true
glow_intensity = 0.6
glow_strength = 1.0
glow_bloom = 0.2
glow_blend_mode = 2
glow_hdr_bleed_threshold = 1.2
glow_hdr_bleed_scale = 2.0
adjustments_enabled = true
adjustments_brightness = 1.05
adjustments_contrast = 1.1
adjustments_saturation = 1.05
ssr_enabled = true
ssr_max_steps = 64
ssr_fade_in = 0.15
ssr_fade_out = 2.0
ssr_depth_tolerance = 0.2
ssao_enabled = true
ssao_radius = 2.0
ssao_intensity = 1.5
ssao_power = 1.5
ssao_detail = 0.5
ssao_horizon = 0.06
ssao_sharpness = 0.98
ssao_direct_light_affect = 0.0
ssil_enabled = true
ssil_radius = 5.0
ssil_intensity = 1.0
ssil_sharpness = 0.98
ssil_normal_rejection = 1.0
volumetric_fog_enabled = true
volumetric_fog_gi_inject = 1.0
volumetric_fog_density = 0.01
volumetric_fog_albedo = Color(0.9, 0.9, 1.0, 1)
volumetric_fog_emission = Color(0, 0, 0, 1)
volumetric_fog_emission_energy = 1.0
volumetric_fog_anisotropy = 0.2
volumetric_fog_length = 64.0
volumetric_fog_detail_spread = 2.0
volumetric_fog_ambient_inject = 1.0
volumetric_fog_sky_affect = 1.0
sdfgi_enabled = true
sdfgi_bounce_feedback = 0.5
sdfgi_cascade0_distance = 12.0
sdfgi_read_sky_light = true
sdfgi_min_cell_size = 0.2
fog_enabled = false
"@ | Set-Content -Path "$ProjectPath\scenes\levels\default_environment.tres" -Encoding UTF8
Write-Host "  ✓ default_environment.tres (PBR HDR 环境光 + GI + 体积雾)" -ForegroundColor Green

# ============================================
# Step 6: 创建 README
# ============================================
Write-Host "[6/7] 创建项目说明..." -ForegroundColor Yellow

@"
# $ProjectName — AAA Quality Game Project

## 技术栈
- Godot 4.6.1 (Forward+ 渲染管线)
- Jolt Physics (第三方物理引擎)
- Direct3D 12 驱动
- MSAA 4x + TAA + Debanding
- SDFGI 全局光照 + SSIL 间接光
- SSR 屏幕空间反射
- 体积雾 (Volumetric Fog)

## 目录结构
```
$ProjectName/
├── assets/
│   ├── models/          # 3D 模型 (角色/环境/道具/武器/载具)
│   ├── textures/        # PBR 贴图 / UI素材 / VFX贴图
│   ├── materials/       # Godot材质资源
│   ├── audio/           # SFX / 音乐 / 配音
│   ├── animations/      # 角色动画 / 道具动画 / 过场
│   ├── vfx/             # 粒子 / Shader
│   ├── ui/              # 界面素材
│   └── data/            # 任务/对话/物品/技能数据
├── scenes/
│   ├── levels/          # 关卡场景
│   ├── prefabs/         # 预制体
│   ├── ui/              # UI场景
│   └── cinematics/      # 过场动画
├── scripts/
│   ├── autoload/        # 全局单例 (GameManager/EventBus/Audio/Save)
│   ├── systems/         # 系统脚本
│   ├── entities/        # 实体脚本
│   ├── ui/              # UI脚本
│   └── ai/              # AI脚本
├── addons/              # Godot插件
│   ├── fuku/            # AI编辑器助手
│   ├── ai_coding_assistant/
│   └── ai_assistant_hub/
├── shaders/             # 自定义Shader
└── docs/                # 设计文档
```

## MCP 生态 (AI驱动全管线)
| 软件 | MCP Server | 用途 |
|------|-----------|------|
| Blender 4.4 | blender-mcp | 3D建模/材质/动画/几何节点 |
| Godot 4.6 | godot-mcp ×5 | 编辑器控制/调试/资产管理 |
| Unreal 5.6 | uemcp + unreal-mcp | 关卡编辑/Actor/材质 |
| Unity | unity-mcp | 脚本/资源/构建 |
| Maya | maya-mcp | 建模/动画/API (29工具) |
| Houdini | houdini-mcp | 程序化/VFX/HDA |
| Rhino | rhino3d-mcp | NURBS建模 (135+工具) |
| Figma | figma-mcp | UI/UX设计/原型 |
| ComfyUI | comfyui-mcp | AI文生图/概念设计 |
| ElevenLabs | elevenlabs-mcp | AI配音 |
| FFmpeg | video-editor-mcp | 视频/过场编辑 |

## 开发规范
- 材质: PBR Standard (Metallic/Roughness/Albedo)
- 纹理格式: BC7 (DDS) / WebP
- 模型格式: glTF 2.0 (.glb/.gltf)
- 音频: OGG Vorbis
- 代码: GDScript 2.0 + C# (可选)
- LOD: 自动生成 + 手动配置
- 物理: Jolt Physics 3D (多线程)

## 快捷键
- W/A/S/D: 移动
- Space: 跳跃
- Shift: 冲刺
- E: 交互
- ESC: UI取消/暂停
"@ | Set-Content -Path "$ProjectPath\docs\README.txt" -Encoding UTF8
Write-Host "  ✓ 项目文档已创建" -ForegroundColor Green

# ============================================
# Step 7: 生成 .gitignore
# ============================================
Write-Host "[7/7] 创建 .gitignore..." -ForegroundColor Yellow

@"
# Godot
.godot/
*.import
*.translation
export_presets.cfg
.editor/

# Build
build/
bin/
.vs/

# IDE
.idea/
.vscode/
*.code-workspace

# OS
Thumbs.db
.DS_Store

# Addons (第三方插件不提交)
addons/

# User data
user://
"@ | Set-Content -Path "$ProjectPath\.gitignore" -Encoding UTF8
Write-Host "  ✓ .gitignore 已创建" -ForegroundColor Green

# ============================================
# 完成
# ============================================
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║           项目模板创建完成！                        ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  项目路径: $ProjectPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "  下一步操作:" -ForegroundColor White
Write-Host "  1. 用 Godot 打开项目:" -ForegroundColor Gray
Write-Host "     & $GodotExe --path $ProjectPath --editor" -ForegroundColor Yellow
Write-Host ""
Write-Host "  2. 进入项目后在 AssetLib 搜索安装:" -ForegroundColor Gray
Write-Host "     - Terrain3D (GDExtension 地形系统)" -ForegroundColor DarkCyan
Write-Host "     - Questify (图形化任务编辑器)" -ForegroundColor DarkCyan
Write-Host "     - Dither3D (表面稳定抖动)" -ForegroundColor DarkCyan
Write-Host "     - godot-ai (AssetLib安装 120+工具MCP)" -ForegroundColor DarkCyan
Write-Host ""
Write-Host "  3. 外部工具 (手动安装):" -ForegroundColor Gray
Write-Host "     - Substance Painter/Designer (PBR材质)" -ForegroundColor DarkCyan
Write-Host "     - ZBrush (高模雕刻)" -ForegroundColor DarkCyan
Write-Host "     - SpeedTree (植被程序化生成)" -ForegroundColor DarkCyan
Write-Host "     - Marvelous Designer (布料模拟)" -ForegroundColor DarkCyan
Write-Host "     - Wwise / FMOD (音频中间件)" -ForegroundColor DarkCyan
Write-Host "     - Quixel Megascans (照片级扫描素材库)" -ForegroundColor DarkCyan
Write-Host ""
