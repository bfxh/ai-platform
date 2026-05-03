#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unity MCP - Unity引擎自动化工具

用法：
    python unity_mcp.py hub                          # 打开Unity Hub
    python unity_mcp.py open [project_path]          # 打开项目
    python unity_mcp.py projects                     # 列出项目
    python unity_mcp.py versions                     # 已安装Unity版本
    python unity_mcp.py create <name> [template]     # 创建项目
    python unity_mcp.py build <project> <platform>   # 打包
    python unity_mcp.py extract <game_path>          # 提取Unity游戏资产
    python unity_mcp.py decompile <dll_path>         # 反编译DLL信息
    python unity_mcp.py mod_init <name> <game>       # 初始化模组项目
    python unity_mcp.py script <type> <name>         # 生成C#脚本模板
    python unity_mcp.py info <project_path>          # 项目信息
    python unity_mcp.py packages <project_path>      # 列出包
    python unity_mcp.py scenes <project_path>        # 列出场景
    python unity_mcp.py prefabs <project_path>       # 列出Prefab
"""

import json
import sys
import os
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

# 本地路径
UNITY_HUB = Path("D:/UnityHub/Unity Hub.exe")
UNITY_EDITOR = Path("E:/76767/786/Unity/Editor/Unity.exe")
UNITY_VERSION = "2018.4.13c1"
ASSET_RIPPER = Path("%DEVTOOLS_DIR%/AssetRipper.GUI.Free.exe")
PROJECT_DIR = Path("D:/50")
TERRATECH_PATH = Path("%STEAM_DIR%/steamapps/common/TerraTech")
TERRATECH_MOD = Path("D:/泰拉科技")

# C#脚本模板
SCRIPT_TEMPLATES = {
    "mono": '''using UnityEngine;

public class {name} : MonoBehaviour
{{
    [Header("Settings")]
    [SerializeField] private float speed = 5f;
    
    private void Awake()
    {{
        
    }}
    
    private void Start()
    {{
        
    }}
    
    private void Update()
    {{
        
    }}
    
    private void OnDestroy()
    {{
        
    }}
}}
''',

    "singleton": '''using UnityEngine;

public class {name} : MonoBehaviour
{{
    public static {name} Instance {{ get; private set; }}
    
    private void Awake()
    {{
        if (Instance != null && Instance != this)
        {{
            Destroy(gameObject);
            return;
        }}
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }}
}}
''',

    "so": '''using UnityEngine;

[CreateAssetMenu(fileName = "New{name}", menuName = "Data/{name}")]
public class {name} : ScriptableObject
{{
    [Header("Data")]
    public string displayName;
    public string description;
    public Sprite icon;
    public int value;
}}
''',

    "editor": '''#if UNITY_EDITOR
using UnityEngine;
using UnityEditor;

[CustomEditor(typeof({target}))]
public class {name} : Editor
{{
    public override void OnInspectorGUI()
    {{
        DrawDefaultInspector();
        
        var script = ({target})target;
        
        if (GUILayout.Button("Execute"))
        {{
            // 按钮逻辑
        }}
    }}
}}
#endif
''',

    "state": '''using System;
using System.Collections.Generic;

public class {name}
{{
    private Dictionary<string, Action> _states = new Dictionary<string, Action>();
    private Dictionary<string, Action> _enters = new Dictionary<string, Action>();
    private Dictionary<string, Action> _exits = new Dictionary<string, Action>();
    private string _current;
    
    public string Current => _current;
    
    public void AddState(string name, Action update, Action enter = null, Action exit = null)
    {{
        _states[name] = update;
        if (enter != null) _enters[name] = enter;
        if (exit != null) _exits[name] = exit;
    }}
    
    public void ChangeState(string name)
    {{
        if (_current != null && _exits.ContainsKey(_current))
            _exits[_current]();
        _current = name;
        if (_enters.ContainsKey(_current))
            _enters[_current]();
    }}
    
    public void Update()
    {{
        if (_current != null && _states.ContainsKey(_current))
            _states[_current]();
    }}
}}
''',

    "pool": '''using System.Collections.Generic;
using UnityEngine;

public class {name}<T> where T : MonoBehaviour
{{
    private readonly Queue<T> _pool = new Queue<T>();
    private readonly T _prefab;
    private readonly Transform _parent;
    
    public {name}(T prefab, int initialSize, Transform parent = null)
    {{
        _prefab = prefab;
        _parent = parent;
        for (int i = 0; i < initialSize; i++)
            _pool.Enqueue(CreateNew());
    }}
    
    public T Get(Vector3 pos, Quaternion rot)
    {{
        var obj = _pool.Count > 0 ? _pool.Dequeue() : CreateNew();
        obj.transform.SetPositionAndRotation(pos, rot);
        obj.gameObject.SetActive(true);
        return obj;
    }}
    
    public void Release(T obj)
    {{
        obj.gameObject.SetActive(false);
        _pool.Enqueue(obj);
    }}
    
    private T CreateNew()
    {{
        var obj = Object.Instantiate(_prefab, _parent);
        obj.gameObject.SetActive(false);
        return obj;
    }}
}}
''',

    "patch": '''using HarmonyLib;
using UnityEngine;

// Harmony Patch for {target}
[HarmonyPatch(typeof({target}), "{method}")]
public class {name}
{{
    [HarmonyPrefix]
    static bool Prefix({target} __instance)
    {{
        // 在原方法前执行
        // return false 跳过原方法
        return true;
    }}
    
    [HarmonyPostfix]
    static void Postfix({target} __instance)
    {{
        // 在原方法后执行
    }}
}}
''',

    "event": '''using System;
using System.Collections.Generic;

public static class {name}
{{
    private static Dictionary<string, List<Action<object>>> _listeners 
        = new Dictionary<string, List<Action<object>>>();
    
    public static void Subscribe(string eventName, Action<object> callback)
    {{
        if (!_listeners.ContainsKey(eventName))
            _listeners[eventName] = new List<Action<object>>();
        _listeners[eventName].Add(callback);
    }}
    
    public static void Unsubscribe(string eventName, Action<object> callback)
    {{
        if (_listeners.ContainsKey(eventName))
            _listeners[eventName].Remove(callback);
    }}
    
    public static void Publish(string eventName, object data = null)
    {{
        if (_listeners.ContainsKey(eventName))
            foreach (var cb in _listeners[eventName])
                cb?.Invoke(data);
    }}
}}
''',
}


def cmd_hub():
    subprocess.Popen([str(UNITY_HUB)])
    print(f"opened: {UNITY_HUB}")

def cmd_open(project_path=None):
    if project_path is None:
        project_path = str(PROJECT_DIR)
    if UNITY_EDITOR.exists():
        subprocess.Popen([str(UNITY_EDITOR), "-projectPath", project_path])
        print(f"opening: {project_path}")
    else:
        print(f"Unity Editor not found: {UNITY_EDITOR}")

def cmd_versions():
    print(f"已安装Unity版本:")
    print(f"  {UNITY_VERSION}  {UNITY_EDITOR}")
    # 检查Hub配置
    editors_file = Path("C:/Users/abc/AppData/Roaming/UnityHub/editors-v2.json")
    if editors_file.exists():
        data = json.loads(editors_file.read_text())
        for editor in data.get("data", []):
            ver = editor.get("version", "?")
            loc = editor.get("location", ["?"])
            loc_str = loc[0] if loc else "?"
            print(f"  {ver}  {loc_str}")

def cmd_projects():
    print(f"项目目录: {PROJECT_DIR}")
    if PROJECT_DIR.exists():
        for d in PROJECT_DIR.iterdir():
            if d.is_dir():
                uproject = d / "Assets"
                if uproject.exists():
                    # 读取ProjectSettings
                    ps = d / "ProjectSettings" / "ProjectSettings.asset"
                    version = "?"
                    if ps.exists():
                        for line in ps.read_text(errors='ignore').split('\n'):
                            if 'm_EditorVersion' in line:
                                version = line.split(':')[-1].strip()
                                break
                    print(f"  {d.name:30s} Unity {version}")
                else:
                    print(f"  {d.name:30s} (非Unity项目)")

def cmd_info(project_path):
    p = Path(project_path)
    print(f"项目: {p.name}")
    print(f"路径: {p}")
    
    # Assets
    assets = p / "Assets"
    if assets.exists():
        cs_files = list(assets.rglob("*.cs"))
        scenes = list(assets.rglob("*.unity"))
        prefabs = list(assets.rglob("*.prefab"))
        materials = list(assets.rglob("*.mat"))
        textures = list(assets.rglob("*.png")) + list(assets.rglob("*.jpg"))
        print(f"  C#脚本: {len(cs_files)}")
        print(f"  场景: {len(scenes)}")
        print(f"  Prefab: {len(prefabs)}")
        print(f"  材质: {len(materials)}")
        print(f"  贴图: {len(textures)}")
    
    # Packages
    manifest = p / "Packages" / "manifest.json"
    if manifest.exists():
        data = json.loads(manifest.read_text())
        deps = data.get("dependencies", {})
        print(f"  包: {len(deps)}")

def cmd_packages(project_path):
    manifest = Path(project_path) / "Packages" / "manifest.json"
    if manifest.exists():
        data = json.loads(manifest.read_text())
        deps = data.get("dependencies", {})
        print(f"包 ({len(deps)}):")
        for name, ver in sorted(deps.items()):
            print(f"  {name:45s} {ver}")
    else:
        print("manifest.json not found")

def cmd_scenes(project_path):
    assets = Path(project_path) / "Assets"
    scenes = list(assets.rglob("*.unity")) if assets.exists() else []
    print(f"场景 ({len(scenes)}):")
    for s in scenes:
        print(f"  {s.relative_to(assets)}")

def cmd_prefabs(project_path):
    assets = Path(project_path) / "Assets"
    prefabs = list(assets.rglob("*.prefab")) if assets.exists() else []
    print(f"Prefab ({len(prefabs)}):")
    for p in prefabs[:30]:
        print(f"  {p.relative_to(assets)}")
    if len(prefabs) > 30:
        print(f"  ... 还有 {len(prefabs)-30} 个")

def cmd_extract(game_path):
    if ASSET_RIPPER.exists():
        subprocess.Popen([str(ASSET_RIPPER)])
        print(f"opened AssetRipper")
        print(f"请手动: File > Open Folder > {game_path}")
    else:
        print(f"AssetRipper not found: {ASSET_RIPPER}")

def cmd_decompile(dll_path):
    """分析DLL基本信息"""
    p = Path(dll_path)
    if not p.exists():
        print(f"不存在: {dll_path}")
        return
    
    size = p.stat().st_size
    print(f"DLL: {p.name}")
    print(f"大小: {size/1024:.1f}KB")
    
    # 读取PE头
    with open(p, 'rb') as f:
        data = f.read(min(size, 4096))
    
    if data[:2] == b'MZ':
        print(f"类型: .NET Assembly (PE)")
        # 搜索版本字符串
        import re
        versions = re.findall(rb'(\d+\.\d+\.\d+\.\d+)', data)
        if versions:
            print(f"版本: {versions[0].decode()}")
    
    print(f"\n反编译建议:")
    print(f"  dnSpy: 打开 {dll_path}")
    print(f"  ILSpy: 打开 {dll_path}")
    print(f"  dotPeek: 打开 {dll_path}")

def cmd_script(script_type, name, **kwargs):
    if script_type not in SCRIPT_TEMPLATES:
        print(f"可用模板: {', '.join(SCRIPT_TEMPLATES.keys())}")
        return
    
    template = SCRIPT_TEMPLATES[script_type]
    defaults = {"name": name, "target": "TargetClass", "method": "TargetMethod"}
    defaults.update(kwargs)
    
    code = template.format(**defaults)
    
    output = Path(f"D:/搞阶跃的/{name}.cs")
    output.write_text(code, encoding='utf-8')
    print(f"生成: {output}")
    print(f"类型: {script_type}")

def cmd_mod_init(mod_name, game_name="TerraTech"):
    """初始化模组项目结构"""
    mod_dir = Path(f"D:/搞阶跃的/Mods/{mod_name}")
    mod_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建目录结构
    (mod_dir / "src").mkdir(exist_ok=True)
    (mod_dir / "assets").mkdir(exist_ok=True)
    (mod_dir / "lib").mkdir(exist_ok=True)
    
    # 主入口
    entry_code = f'''using HarmonyLib;
using UnityEngine;

namespace {mod_name}
{{
    public class {mod_name}Mod
    {{
        private static Harmony _harmony;
        
        public static void Init()
        {{
            Debug.Log("[{mod_name}] Initializing...");
            _harmony = new Harmony("com.{mod_name.lower()}.mod");
            _harmony.PatchAll();
            Debug.Log("[{mod_name}] Loaded!");
        }}
    }}
}}
'''
    (mod_dir / "src" / f"{mod_name}Mod.cs").write_text(entry_code, encoding='utf-8')
    
    # README
    readme = f'''# {mod_name}

## 简介
{game_name} 模组

## 安装
1. 将DLL复制到游戏Mods目录
2. 启动游戏

## 开发
- 引用: Assembly-CSharp.dll, UnityEngine.dll, 0Harmony.dll
- 编译: dotnet build
- 测试: 复制DLL到游戏目录启动
'''
    (mod_dir / "README.md").write_text(readme, encoding='utf-8')
    
    print(f"模组项目已创建: {mod_dir}")
    print(f"  src/{mod_name}Mod.cs  - 主入口")
    print(f"  assets/              - 资产目录")
    print(f"  lib/                 - 依赖库(放0Harmony.dll等)")
    print(f"  README.md            - 说明")

def cmd_build(project_path, platform="StandaloneWindows64"):
    if not UNITY_EDITOR.exists():
        print(f"Unity Editor not found")
        return
    
    output = Path(project_path) / "Build" / platform
    output.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        str(UNITY_EDITOR),
        "-batchmode", "-nographics",
        "-projectPath", project_path,
        "-buildTarget", platform,
        "-executeMethod", "BuildScript.Build",
        "-quit"
    ]
    print(f"打包: {' '.join(cmd)}")
    subprocess.Popen(cmd)


def main():
    if len(sys.argv) < 2:
        print("""Unity MCP - Unity引擎工具

用法: python unity_mcp.py <action> [args...]

  hub                          打开Unity Hub
  open [project]               打开项目
  versions                     已安装版本
  projects                     列出项目
  info <project>               项目信息
  packages <project>           列出包
  scenes <project>             列出场景
  prefabs <project>            列出Prefab
  extract <game_path>          提取Unity游戏资产
  decompile <dll>              DLL信息
  script <type> <name>         生成C#脚本
    类型: mono|singleton|so|editor|state|pool|patch|event
  mod_init <name> [game]       初始化模组项目
  build <project> [platform]   打包""")
        return
    
    action = sys.argv[1]
    args = sys.argv[2:]
    
    if action == "hub": cmd_hub()
    elif action == "open": cmd_open(args[0] if args else None)
    elif action == "versions": cmd_versions()
    elif action == "projects": cmd_projects()
    elif action == "info": cmd_info(args[0] if args else str(PROJECT_DIR))
    elif action == "packages": cmd_packages(args[0] if args else str(PROJECT_DIR))
    elif action == "scenes": cmd_scenes(args[0] if args else str(PROJECT_DIR))
    elif action == "prefabs": cmd_prefabs(args[0] if args else str(PROJECT_DIR))
    elif action == "extract": cmd_extract(args[0] if args else "")
    elif action == "decompile": cmd_decompile(args[0] if args else "")
    elif action == "script":
        kwargs = {}
        for a in args[2:]:
            if '=' in a:
                k, v = a.split('=', 1)
                kwargs[k] = v
        cmd_script(args[0] if args else "", args[1] if len(args) > 1 else "MyScript", **kwargs)
    elif action == "mod_init": cmd_mod_init(args[0] if args else "MyMod", args[1] if len(args) > 1 else "TerraTech")
    elif action == "build": cmd_build(args[0] if args else "", args[1] if len(args) > 1 else "StandaloneWindows64")
    else: print(f"未知: {action}")


if __name__ == '__main__':
    main()
