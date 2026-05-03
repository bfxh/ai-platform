# godot-stylized-shaders-plugin

This is a **Godot 4.4 plugin** made with *GDExtension C++* as part of a *university project*. This plugin aims to provide a variety of **stylized shaders** that the user can customize to their liking, being able to **layer/stack** the shaders and **change the order of appliance** (to change the overall look).

# Features

This plugin makes heavy usage of Godot's `Compositor` and `CompositorEffect`. I've implemented the following post-process effects using `CompositorEffect`:
- Invert color shader (first shader implemented in the project for testing purposes)
- Posterization shader
- Outline shader
- CRT shader
- Pixelization shader
- Dithering shader
- VHS shader
- HDR Bloom shader
- Anisotropic Kuwahara Filter shader

Additionally, the editor UI was created with C++ and implements heavy customizability for the shader effects. (Unfortunately due to time constraints, getting the changes from the editor UI to apply in-game is a broken feature at the moment)
Since I could not find a way to implement the array inspector into the editor UI, I made a "manual array inspector" that shows up in the UI which allows you to change the order in which the currently enabled effects are applied.

# Demo video

https://github.com/user-attachments/assets/2394674a-c7c5-4b61-9202-71cb9a43299a

# Important Disclaimer

This was my first experience working with the Godot Engine, as well as using GDExtension. Some parts are more complete than others, some parts should really be refactored, and so on. This project was made during the duration of 8 weeks (as I've mentioned before, it's a university assignment), and learning about the engine and the bindings while also making the plugin wasn't that easy. Any feedback is welcome though! :)

# Compiling the plugin yourself

Requirements:
- a version of Python and pip
- SCons (`pip install scons`) & SCons being declared in your PATH [("how-to" here)](https://stackoverflow.com/a/63925889)
- Godot 4.4+

Commands for cloning the repository (with the `godot-cpp` submodule included) and building the plugin with **SCons**:
```
git clone --recursive https://github.com/alexstn18/godot-stylized-shaders-plugin/
cd godot-stylized-shaders-plugin/
scons
```

The build is currently being outputted to `demo/addons/`, but you can easily change this in the `SCons` configuration file (`folder = your_path_here`)
