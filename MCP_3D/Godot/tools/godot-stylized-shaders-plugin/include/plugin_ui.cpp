#include "plugin_ui.hpp"
#include "godot_cpp/core/class_db.hpp"
#include "godot_cpp/core/error_macros.hpp"
#include <godot_cpp/classes/editor_inspector.hpp>
#include <godot_cpp/classes/editor_interface.hpp>
#include <godot_cpp/classes/packed_scene.hpp>
#include <godot_cpp/classes/resource_loader.hpp>
#include <godot_cpp/classes/resource_preloader.hpp>

void PluginUI::_bind_methods()
{
    ClassDB::bind_method(D_METHOD("_on_scene_changed"),
                         &PluginUI::_on_scene_changed);
}

PluginUI::~PluginUI()
{
    if (m_panel)
        m_panel->queue_free();
}

void PluginUI::_enter_tree()
{
    Ref<PackedScene> ui_scene = ResourceLoader::get_singleton()->load(
        "res://addons/GodotStylizedShadersPlugin/scenes/ui_toolbar.tscn");
    Node *instance = ui_scene->instantiate();
    m_panel = Object::cast_to<ToolPanel>(instance);

    ERR_FAIL_COND_MSG(!ui_scene.is_valid(), "UI scene is invalid or not found");
    ERR_FAIL_COND_MSG(!instance, "Failed to instantiate scene");

    if (!m_panel)
    {
        UtilityFunctions::push_error("Failed to cast to ToolPanel");
        instance->queue_free();
        return;
    }

    Node *edited_scene_root =
        EditorInterface::get_singleton()->get_edited_scene_root();
    if (edited_scene_root)
        m_panel->set_edited_scene_root(edited_scene_root);

    add_control_to_dock(EditorPlugin::DOCK_SLOT_LEFT_BL, m_panel);
    connect("scene_changed", Callable(this, "_on_scene_changed"));
}

void PluginUI::_exit_tree()
{
    if (m_panel)
    {
        remove_control_from_docks(m_panel);
        m_panel->queue_free();
    }
}

void PluginUI::_on_scene_changed(Node *scene_root)
{
    if (m_panel && scene_root)
        m_panel->set_edited_scene_root(scene_root);
}