#include "manual_array_inspector.hpp"
#include <godot_cpp/classes/editor_interface.hpp>

void ManualArrayInspector::_bind_methods()
{
    ClassDB::bind_method(D_METHOD("set_effects", "effects"),
                         &ManualArrayInspector::set_effects);
    ClassDB::bind_method(D_METHOD("get_effects"),
                         &ManualArrayInspector::get_effects);
    ClassDB::bind_method(D_METHOD("_on_move_pressed", "from_index", "to_index"),
                         &ManualArrayInspector::_on_move_pressed);

    ADD_SIGNAL(
        MethodInfo("order_changed", PropertyInfo(Variant::ARRAY, "effects")));
}

ManualArrayInspector::~ManualArrayInspector()
{
    queue_free();
}

void ManualArrayInspector::_refresh_ui()
{
    for (auto &child : get_children())
    {
        if (Node *child_as_node = Object::cast_to<Node>(child))
        {
            child_as_node->queue_free();
        }
    }

    if (m_effects.size() > 0)
    {
        Label *label = memnew(Label);
        label->set_text("Effect Order");
        label->set_horizontal_alignment(godot::HORIZONTAL_ALIGNMENT_CENTER);
        add_child(label);
    }

    for (int32_t i = 0; i < m_effects.size(); ++i)
    {
        if (BaseShader *obj = Object::cast_to<BaseShader>(m_effects[i]))
        {
            HBoxContainer *hbox = memnew(HBoxContainer);
            LineEdit *line_edit = memnew(LineEdit);
            line_edit->set_text(obj->get_class());
            line_edit->set_editable(false);
            hbox->add_child(line_edit);

            Button *up_btn = memnew(Button);
            up_btn->set_text("Move Up");
            up_btn->set_focus_mode(Control::FOCUS_NONE);
            up_btn->set_disabled(i == 0);
            up_btn->connect(
                "pressed",
                callable_mp(this, &ManualArrayInspector::_on_move_pressed)
                    .bind(i, i - 1));
            hbox->add_child(up_btn);

            Button *down_btn = memnew(Button);
            down_btn->set_text("Move Down");
            down_btn->set_focus_mode(Control::FOCUS_NONE);
            down_btn->set_disabled(i == m_effects.size() - 1);
            down_btn->connect(
                "pressed",
                callable_mp(this, &ManualArrayInspector::_on_move_pressed)
                    .bind(i, i + 1));
            hbox->add_child(down_btn);

            add_child(hbox);
        }
    }
}

void ManualArrayInspector::set_effects(const TypedArray<BaseShader> &effects)
{
    m_effects = effects;
    _refresh_ui();
}

void ManualArrayInspector::_on_move_pressed(int from_index, int to_index)
{
    if (to_index < 0 || to_index >= m_effects.size())
        return;

    Ref<BaseShader> temp = m_effects[from_index];
    m_effects.set(from_index, m_effects[to_index]);
    m_effects.set(to_index, temp);

    _refresh_ui();

    emit_signal("order_changed", m_effects);

    if (EditorInterface *editor = EditorInterface::get_singleton())
    {
        editor->mark_scene_as_unsaved();
    }
}