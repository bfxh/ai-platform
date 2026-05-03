#include "register_types.hpp"

#include <gdextension_interface.h>
#include <godot_cpp/core/class_db.hpp>
#include <godot_cpp/core/defs.hpp>
#include <godot_cpp/godot.hpp>

#include "base_shader.hpp"
#include "bloom_shader.hpp"
#include "cel_shader.hpp"
#include "crt_shader.hpp"
#include "dither_shader.hpp"
#include "effect_array.hpp"
#include "godot_cpp/classes/editor_plugin.hpp"
#include "invert_shader.hpp"
#include "kuwahara_shader.hpp"
#include "manual_array_inspector.hpp"
#include "outline_shader.hpp"
#include "pixel_shader.hpp"
#include "plugin_ui.hpp"
#include "slider_container.hpp"
#include "tool_panel.hpp"
#include "util/encapsulated_data.hpp"
#include "vhs_shader.hpp"

using namespace godot;

void initialize_shader_plugin(ModuleInitializationLevel p_level)
{
    if (p_level == MODULE_INITIALIZATION_LEVEL_EDITOR)
    {
        GDREGISTER_CLASS(ManualArrayInspector);
        GDREGISTER_CLASS(EffectArray);
        GDREGISTER_CLASS(EncapsuledData<int>);
        GDREGISTER_CLASS(EncapsuledData<float>);
        GDREGISTER_CLASS(EncapsuledData<bool>);
        GDREGISTER_CLASS(SliderContainer);
        GDREGISTER_CLASS(ToolPanel);
        GDREGISTER_INTERNAL_CLASS(PluginUI);
        EditorPlugins::add_by_type<PluginUI>();
    }

    if (p_level != MODULE_INITIALIZATION_LEVEL_SCENE)
    {
        return;
    }

    GDREGISTER_ABSTRACT_CLASS(BaseShader);

    GDREGISTER_CLASS(InvertShader);
    GDREGISTER_CLASS(OutlineShader);
    GDREGISTER_CLASS(CelShader);
    GDREGISTER_CLASS(CRTShader);
    GDREGISTER_CLASS(DitherShader);
    GDREGISTER_CLASS(PixelShader);
    GDREGISTER_CLASS(VHSShader);
    GDREGISTER_CLASS(BloomShader);
    GDREGISTER_CLASS(KuwaharaShader);
}

void uninitialize_shader_plugin(ModuleInitializationLevel p_level)
{
    if (p_level == MODULE_INITIALIZATION_LEVEL_EDITOR)
    {
        EditorPlugins::remove_by_type<PluginUI>();
    }
    if (p_level != MODULE_INITIALIZATION_LEVEL_SCENE)
    {
        return;
    }
}

extern "C"
{
    auto GDE_EXPORT godot_stylized_shaders_plugin_entry(
        GDExtensionInterfaceGetProcAddress p_get_proc_address,
        const GDExtensionClassLibraryPtr p_library,
        GDExtensionInitialization *r_initialization) -> GDExtensionBool
    {
        godot::GDExtensionBinding::InitObject init_obj(
            p_get_proc_address, p_library, r_initialization);

        init_obj.register_initializer(initialize_shader_plugin);
        init_obj.register_terminator(uninitialize_shader_plugin);

        init_obj.set_minimum_library_initialization_level(
            MODULE_INITIALIZATION_LEVEL_SCENE);

        return init_obj.init();
    }
}