using UnityEngine;
using UnityEditor;
using System.IO;
using System.Collections.Generic;
using System.Text.RegularExpressions;

namespace EngineImporter
{
    public class EngineImporterWindow : EditorWindow
    {
        private int _sourceEngine = 0;
        private string _sourcePath = "";
        private string _importPath = "Assets/Imported";
        private bool _importMeshes = true;
        private bool _importTextures = true;
        private bool _importMaterials = true;
        private bool _importScripts = false;
        private bool _importAudio = true;
        private bool _importScenes = true;
        private float _scaleFactor = 1.0f;
        private Vector2 _scrollPos;
        private string _log = "";

        [MenuItem("Tools/Engine Importer")]
        public static void ShowWindow()
        {
            var window = GetWindow<EngineImporterWindow>("Engine Importer");
            window.minSize = new Vector2(400, 600);
        }

        void OnGUI()
        {
            _scrollPos = EditorGUILayout.BeginScrollView(_scrollPos);

            EditorGUILayout.LabelField("Engine Importer", EditorStyles.boldLabel);
            EditorGUILayout.Space(10);

            EditorGUILayout.LabelField("Source Engine:", EditorStyles.miniLabel);
            _sourceEngine = GUILayout.SelectionGrid(_sourceEngine,
                new[] { "Unreal Engine", "Godot", "Blender" }, 3);

            EditorGUILayout.Space(5);

            EditorGUILayout.LabelField("Source Path:");
            EditorGUILayout.BeginHorizontal();
            _sourcePath = EditorGUILayout.TextField(_sourcePath);
            if (GUILayout.Button("Browse", GUILayout.Width(80)))
            {
                _sourcePath = EditorUtility.OpenFolderPanel("Select Source Project", "", "");
            }
            EditorGUILayout.EndHorizontal();

            EditorGUILayout.Space(5);

            EditorGUILayout.LabelField("Import To:");
            _importPath = EditorGUILayout.TextField(_importPath);

            EditorGUILayout.Space(10);
            EditorGUILayout.LabelField("Import Options:", EditorStyles.boldLabel);

            _importMeshes = EditorGUILayout.Toggle("Import Meshes", _importMeshes);
            _importTextures = EditorGUILayout.Toggle("Import Textures", _importTextures);
            _importMaterials = EditorGUILayout.Toggle("Import Materials", _importMaterials);
            _importAudio = EditorGUILayout.Toggle("Import Audio", _importAudio);
            _importScenes = EditorGUILayout.Toggle("Import Scenes", _importScenes);
            _importScripts = EditorGUILayout.Toggle("Convert Scripts", _importScripts);

            EditorGUILayout.Space(5);
            _scaleFactor = EditorGUILayout.FloatField("Scale Factor", _scaleFactor);

            EditorGUILayout.Space(15);

            if (GUILayout.Button("Import", GUILayout.Height(40)))
            {
                DoImport();
            }

            if (GUILayout.Button("Batch Import Folder", GUILayout.Height(30)))
            {
                BatchImport();
            }

            if (GUILayout.Button("Generate Report", GUILayout.Height(30)))
            {
                GenerateReport();
            }

            EditorGUILayout.Space(10);
            EditorGUILayout.LabelField("Log:", EditorStyles.boldLabel);
            EditorGUILayout.TextArea(_log, GUILayout.ExpandHeight(true));

            EditorGUILayout.EndScrollView();
        }

        void DoImport()
        {
            if (string.IsNullOrEmpty(_sourcePath) || !Directory.Exists(_sourcePath))
            {
                _log += "[ERROR] Invalid source path\n";
                return;
            }

            _log += $"[INFO] Starting import from {_sourceEngine switch { 0 => "UE", 1 => "Godot", 2 => "Blender", _ => "Unknown" }}\n";

            switch (_sourceEngine)
            {
                case 0: ImportUEAssets(_sourcePath); break;
                case 1: ImportGodotAssets(_sourcePath); break;
                case 2: ImportBlenderAssets(_sourcePath); break;
            }

            AssetDatabase.Refresh();
            _log += "[DONE] Import complete\n";
        }

        void ImportUEAssets(string sourcePath)
        {
            if (_importMeshes)
            {
                var meshFiles = FindFiles(sourcePath, new[] { ".fbx", ".obj" });
                _log += $"[SCAN] Found {meshFiles.Count} mesh files\n";
                CopyAssetsToUnity(meshFiles, "Meshes");
            }

            if (_importTextures)
            {
                var texFiles = FindFiles(sourcePath, new[] { ".png", ".jpg", ".tga", ".bmp", ".hdr" });
                _log += $"[SCAN] Found {texFiles.Count} texture files\n";
                CopyAssetsToUnity(texFiles, "Textures");
            }

            if (_importAudio)
            {
                var audioFiles = FindFiles(sourcePath, new[] { ".wav", ".mp3", ".ogg" });
                _log += $"[SCAN] Found {audioFiles.Count} audio files\n";
                CopyAssetsToUnity(audioFiles, "Audio");
            }

            if (_importMaterials)
            {
                _log += "[INFO] UE materials need manual recreation in Unity\n";
                _log += "[INFO] Use PBR texture maps (Albedo/Normal/Metallic/Roughness) directly\n";
            }
        }

        void ImportGodotAssets(string sourcePath)
        {
            if (_importMeshes)
            {
                var meshFiles = FindFiles(sourcePath, new[] { ".fbx", ".obj", ".glb", ".gltf" });
                _log += $"[SCAN] Found {meshFiles.Count} mesh files\n";
                CopyAssetsToUnity(meshFiles, "Meshes");
            }

            if (_importTextures)
            {
                var texFiles = FindFiles(sourcePath, new[] { ".png", ".jpg", ".hdr" });
                _log += $"[SCAN] Found {texFiles.Count} texture files\n";
                CopyAssetsToUnity(texFiles, "Textures");
            }

            if (_importAudio)
            {
                var audioFiles = FindFiles(sourcePath, new[] { ".wav", ".ogg", ".mp3" });
                _log += $"[SCAN] Found {audioFiles.Count} audio files\n";
                CopyAssetsToUnity(audioFiles, "Audio");
            }

            if (_importScenes)
            {
                var sceneFiles = FindFiles(sourcePath, new[] { ".tscn" });
                _log += $"[SCAN] Found {sceneFiles.Count} Godot scenes\n";
                foreach (var sf in sceneFiles)
                {
                    ConvertGodotScene(sf);
                }
            }

            if (_importMaterials)
            {
                var matFiles = FindFiles(sourcePath, new[] { ".tres" });
                _log += $"[SCAN] Found {matFiles.Count} Godot resources\n";
                foreach (var mf in matFiles)
                {
                    ConvertGodotMaterial(mf);
                }
            }

            if (_importScripts)
            {
                var scriptFiles = FindFiles(sourcePath, new[] { ".gd" });
                _log += $"[SCAN] Found {scriptFiles.Count} GDScript files\n";
                foreach (var sf in scriptFiles)
                {
                    ConvertGDScript(sf);
                }
            }
        }

        void ImportBlenderAssets(string sourcePath)
        {
            var blendFiles = FindFiles(sourcePath, new[] { ".blend" });
            _log += $"[SCAN] Found {blendFiles.Count} Blender files\n";

            foreach (var blend in blendFiles)
            {
                string destDir = Path.Combine(_importPath, "Blender", Path.GetFileNameWithoutExtension(blend));
                if (!Directory.Exists(destDir))
                    Directory.CreateDirectory(destDir);

                string destPath = Path.Combine(destDir, Path.GetFileName(blend));
                File.Copy(blend, destPath, true);
                _log += $"[COPY] {Path.GetFileName(blend)}\n";
            }

            var exportedFiles = FindFiles(sourcePath, new[] { ".fbx", ".obj", ".glb", ".gltf" });
            CopyAssetsToUnity(exportedFiles, "Blender");

            _log += "[INFO] .blend files copied - Unity can import them directly with Blender installed\n";
        }

        void CopyAssetsToUnity(List<string> files, string subDir)
        {
            string destBase = Path.Combine(_importPath, subDir);
            if (!Directory.Exists(destBase))
                Directory.CreateDirectory(destBase);

            int copied = 0;
            foreach (var file in files)
            {
                try
                {
                    string dest = Path.Combine(destBase, Path.GetFileName(file));
                    if (!File.Exists(dest))
                    {
                        File.Copy(file, dest, false);
                        copied++;
                    }
                }
                catch (System.Exception e)
                {
                    _log += $"[WARN] Copy failed: {Path.GetFileName(file)} - {e.Message}\n";
                }
            }
            _log += $"[COPY] {copied}/{files.Count} files copied to {subDir}\n";
        }

        void ConvertGodotScene(string tscnPath)
        {
            try
            {
                var lines = File.ReadAllLines(tscnPath);
                var sceneData = new GodotSceneData { Name = Path.GetFileNameWithoutExtension(tscnPath) };

                foreach (var line in lines)
                {
                    if (line.StartsWith("[node name="))
                    {
                        var match = Regex.Match(line, @"name=""([^""]+)"".*type=""([^""]+)""");
                        if (match.Success)
                        {
                            sceneData.Nodes.Add(new GodotNodeData
                            {
                                Name = match.Groups[1].Value,
                                Type = match.Groups[2].Value
                            });
                        }
                    }
                    else if (line.StartsWith("transform ="))
                    {
                        var lastNode = sceneData.Nodes.Count > 0 ? sceneData.Nodes[sceneData.Nodes.Count - 1] : null;
                        if (lastNode != null)
                        {
                            var posMatch = Regex.Match(line, @"Transform3D\([^)]+,([^,]+),([^,]+),([^,]+)\)");
                            if (posMatch.Success)
                            {
                                lastNode.Position = new Vector3(
                                    float.Parse(posMatch.Groups[1].Value),
                                    float.Parse(posMatch.Groups[2].Value),
                                    float.Parse(posMatch.Groups[3].Value)
                                );
                            }
                        }
                    }
                }

                string jsonPath = Path.Combine(_importPath, "Scenes", sceneData.Name + ".json");
                if (!Directory.Exists(Path.GetDirectoryName(jsonPath)))
                    Directory.CreateDirectory(Path.GetDirectoryName(jsonPath));
                File.WriteAllText(jsonPath, JsonUtility.ToJson(sceneData, true));
                _log += $"[CONVERT] Scene: {sceneData.Name} ({sceneData.Nodes.Count} nodes)\n";
            }
            catch (System.Exception e)
            {
                _log += $"[ERROR] Scene conversion failed: {e.Message}\n";
            }
        }

        void ConvertGodotMaterial(string tresPath)
        {
            try
            {
                var lines = File.ReadAllLines(tresPath);
                var matData = new Dictionary<string, string>();

                foreach (var line in lines)
                {
                    if (line.Contains("=") && !line.StartsWith("["))
                    {
                        var parts = line.Split(new[] { '=' }, 2);
                        if (parts.Length == 2)
                            matData[parts[0].Trim()] = parts[1].Trim().Trim('"');
                    }
                }

                string jsonPath = Path.Combine(_importPath, "Materials", Path.GetFileNameWithoutExtension(tresPath) + ".json");
                if (!Directory.Exists(Path.GetDirectoryName(jsonPath)))
                    Directory.CreateDirectory(Path.GetDirectoryName(jsonPath));
                File.WriteAllText(jsonPath, JsonUtility.ToJson(matData, true));
                _log += $"[CONVERT] Material: {Path.GetFileNameWithoutExtension(tresPath)}\n";
            }
            catch (System.Exception e)
            {
                _log += $"[ERROR] Material conversion failed: {e.Message}\n";
            }
        }

        void ConvertGDScript(string gdPath)
        {
            try
            {
                var content = File.ReadAllText(gdPath);
                var className = Path.GetFileNameWithoutExtension(gdPath);
                var csContent = ConvertGDToCS(content, className);

                string csDir = Path.Combine(_importPath, "Scripts");
                if (!Directory.Exists(csDir))
                    Directory.CreateDirectory(csDir);
                File.WriteAllText(Path.Combine(csDir, className + ".cs"), csContent);
                _log += $"[CONVERT] Script: {className}.gd → {className}.cs\n";
            }
            catch (System.Exception e)
            {
                _log += $"[ERROR] Script conversion failed: {e.Message}\n";
            }
        }

        string ConvertGDToCS(string gdContent, string className)
        {
            string extends = "MonoBehaviour";
            if (gdContent.Contains("extends RigidBody3D") || gdContent.Contains("extends RigidBody2D"))
                extends = "MonoBehaviour";
            else if (gdContent.Contains("extends Resource"))
                extends = "ScriptableObject";
            else if (gdContent.Contains("extends Node"))
                extends = "MonoBehaviour";

            var sb = new System.Text.StringBuilder();
            sb.AppendLine("// 从 Godot GDScript 自动转换 - 需手动调整");
            sb.AppendLine("using UnityEngine;");
            sb.AppendLine();
            sb.AppendLine($"public class {className} : {extends}");
            sb.AppendLine("{");

            var exportMatch = Regex.Matches(gdContent, @"@export\s+var\s+(\w+)\s*:\s*(\w+)");
            foreach (Match m in exportMatch)
            {
                string varName = m.Groups[1].Value;
                string gdType = m.Groups[2].Value;
                string csType = GdTypeToCs(gdType);
                sb.AppendLine($"    [SerializeField] private {csType} {varName};");
            }

            if (gdContent.Contains("_ready"))
                sb.AppendLine("\n    private void Awake() { /* from _ready() */ }");
            if (gdContent.Contains("_process"))
                sb.AppendLine("    private void Update() { /* from _process() */ }");
            if (gdContent.Contains("_physics_process"))
                sb.AppendLine("    private void FixedUpdate() { /* from _physics_process() */ }");

            sb.AppendLine("}");
            return sb.ToString();
        }

        string GdTypeToCs(string gdType)
        {
            return gdType switch
            {
                "int" => "int",
                "float" => "float",
                "bool" => "bool",
                "String" => "string",
                "Vector2" => "Vector2",
                "Vector3" => "Vector3",
                "Color" => "Color",
                "Node3D" => "GameObject",
                "RigidBody3D" => "Rigidbody",
                "AudioStreamPlayer3D" => "AudioSource",
                "AnimationPlayer" => "Animator",
                _ => "object"
            };
        }

        List<string> FindFiles(string path, string[] extensions)
        {
            var result = new List<string>();
            if (!Directory.Exists(path)) return result;

            foreach (var ext in extensions)
            {
                result.AddRange(Directory.GetFiles(path, "*" + ext, SearchOption.AllDirectories));
            }
            return result;
        }

        void BatchImport()
        {
            string folder = EditorUtility.OpenFolderPanel("Select Folder to Batch Import", "", "");
            if (!string.IsNullOrEmpty(folder))
            {
                _sourcePath = folder;
                DoImport();
            }
        }

        void GenerateReport()
        {
            _log += "[REPORT] Generating conversion report...\n";
            var report = new ConversionReport();

            if (Directory.Exists(_importPath))
            {
                report.Meshes = Directory.GetFiles(_importPath, "*.fbx", SearchOption.AllDirectories).Length
                    + Directory.GetFiles(_importPath, "*.obj", SearchOption.AllDirectories).Length;
                report.Textures = Directory.GetFiles(_importPath, "*.png", SearchOption.AllDirectories).Length
                    + Directory.GetFiles(_importPath, "*.jpg", SearchOption.AllDirectories).Length;
                report.Scripts = Directory.GetFiles(_importPath, "*.cs", SearchOption.AllDirectories).Length;
                report.Materials = Directory.GetFiles(_importPath, "*.mat", SearchOption.AllDirectories).Length;
            }

            _log += $"[REPORT] Meshes: {report.Meshes}, Textures: {report.Textures}, Scripts: {report.Scripts}, Materials: {report.Materials}\n";
        }

        [System.Serializable]
        class GodotSceneData
        {
            public string Name;
            public List<GodotNodeData> Nodes = new List<GodotNodeData>();
        }

        [System.Serializable]
        class GodotNodeData
        {
            public string Name;
            public string Type;
            public Vector3 Position;
        }

        [System.Serializable]
        class ConversionReport
        {
            public int Meshes;
            public int Textures;
            public int Scripts;
            public int Materials;
        }
    }
}
