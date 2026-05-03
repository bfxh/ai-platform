#pragma once

#include "base_shader.hpp"
#include "godot_cpp/classes/wrapped.hpp"
#include <godot_cpp/classes/button.hpp>
#include <godot_cpp/classes/editor_property.hpp>
#include <godot_cpp/classes/h_box_container.hpp>
#include <godot_cpp/classes/line_edit.hpp>
#include <godot_cpp/classes/v_box_container.hpp>
#include <godot_cpp/core/class_db.hpp>

using namespace godot;

class ManualArrayInspector : public VBoxContainer
{
    GDCLASS(ManualArrayInspector, VBoxContainer);

    void _refresh_ui();
    void _on_move_pressed(int from_index, int to_index);

    TypedArray<BaseShader> m_effects;

  protected:
    static void _bind_methods();

  public:
    ManualArrayInspector() = default;
    ~ManualArrayInspector();
    TypedArray<BaseShader> get_effects() const { return m_effects; }
    void set_effects(const TypedArray<BaseShader> &effects);
};