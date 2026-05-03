#pragma once

#include <godot_cpp/classes/button.hpp>
#include <godot_cpp/classes/editor_plugin.hpp>
#include <godot_cpp/core/class_db.hpp>

#include "tool_panel.hpp"

using namespace godot;

class PluginUI : public EditorPlugin
{
    GDCLASS(PluginUI, EditorPlugin);

  private:
    ToolPanel *m_panel = nullptr;

  protected:
    static void _bind_methods();

  public:
    PluginUI() {}
    ~PluginUI();

    void _enter_tree() override;
    void _exit_tree() override;
    void _on_scene_changed(Node *scene_root);
};