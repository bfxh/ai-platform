import os
import shutil
from pathlib import Path

env = SConscript("godot-cpp/SConstruct")

env.Append(CPPPATH=["include/", "include/util/"])

sources = Glob("include/*.cpp") + Glob("include/util/*.cpp")

addon_folder = "demo/addons/GodotStylizedShadersPlugin"

platform = env["platform"]
target = env["target"]

suffix = env['suffix'].replace(".dev", "").replace(".universal", "")

if env["target"] in ["editor", "template_debug"]:
    try:
        doc_data = env.GodotCPPDocData("include/gen/doc_data.gen.cpp", source=Glob("doc_classes/*.xml"))
        sources.append(doc_data)
    except AttributeError:
        print("Not including class reference as we're targeting a pre-4.3 baseline.")

def get_library_path():
    """Generate the correct library path based on platform"""
    if platform == "macos":
        lib_name = f"libGodotStylizedShadersPlugin.{platform}.{target}"
        return f"{addon_folder}/{lib_name}.framework/{lib_name}"
    elif platform == "ios":
        lib_name = f"libGodotStylizedShadersPlugin.{platform}.{target}"
        return f"{addon_folder}/{lib_name}.framework/{lib_name}"
    else:
        # Windows, Linux, Android
        lib_name = f"libGodotStylizedShadersPlugin{env['suffix']}{env['SHLIBSUFFIX']}"
        return f"{addon_folder}/{lib_name}"

def clean_old_libraries(target, source, env):
    """Remove ONLY old library files, preserve shaders/scenes/gdextension"""
    if not os.path.exists(addon_folder):
        return None
    
    library_extensions = ['.so', '.dll', '.dylib', '.pdb', '.exp', '.lib', '.a']
    
    for item in os.listdir(addon_folder):
        item_path = os.path.join(addon_folder, item)
        
        if os.path.isdir(item_path):
            if item_path.endswith('.framework'):
                try:
                    shutil.rmtree(item_path)
                    print(f"Cleaned old framework: {item}")
                except Exception as e:
                    print(f"Warning: Could not remove {item}: {e}")
            continue
        
        if item.endswith('.gdextension'):
            continue
        
        if any(item.endswith(ext) for ext in library_extensions):
            try:
                os.remove(item_path)
                print(f"Cleaned old library: {item}")
            except Exception as e:
                print(f"Warning: Could not remove {item}: {e}")
    
    return None

def copy_directory(target, source, env):
    """SCons-friendly directory copy that preserves existing files"""
    src_dir = str(source[0])
    tgt_dir = str(target[0])
    
    if os.path.exists(src_dir):
        shutil.copytree(src_dir, tgt_dir, dirs_exist_ok=True)
    
    return None

clean_marker = env.Command(
    target=".clean_marker",
    source=[],
    action=clean_old_libraries
)

library = env.SharedLibrary(
    target=get_library_path(),
    source=sources
)

env.Depends(library, clean_marker)

gdextension_copy = env.Command(
    target=f"{addon_folder}/GodotStylizedShadersPlugin.gdextension",
    source="GodotStylizedShadersPlugin.gdextension",
    action=Copy("$TARGET", "$SOURCE")
)

shaders_copy = env.Command(
    target=Dir(f"{addon_folder}/shaders"),
    source=Dir("include/shaders"),
    action=copy_directory
)

scenes_copy = env.Command(
    target=Dir(f"{addon_folder}/scenes"),
    source=Dir("scenes"),
    action=copy_directory
)

env.Depends(gdextension_copy, library)
env.AlwaysBuild(shaders_copy)
env.AlwaysBuild(scenes_copy)

env.CacheDir(".scons_cache")

Default([library, gdextension_copy, shaders_copy, scenes_copy])

env.Alias('install', [library, gdextension_copy, shaders_copy, scenes_copy])