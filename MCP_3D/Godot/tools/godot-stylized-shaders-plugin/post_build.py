import os

folder = "demo/addons/GodotStylizedShadersPlugin"
script_dir = os.path.dirname(os.path.abspath(__file__))

for filename in os.listdir(folder):
    if "dev" in filename and not filename.endswith(".pdb"):
        new_name = filename.replace(".dev", "")
        old_path = os.path.join(folder, filename)
        new_path = os.path.join(folder, new_name)

        if os.path.exists(new_path):
            print(f'Skipping "{filename}" → "{new_name}" (already exists)')
        else:
            os.rename(old_path, new_path)
            print(f'Renamed: "{filename}" → "{new_name}"')
