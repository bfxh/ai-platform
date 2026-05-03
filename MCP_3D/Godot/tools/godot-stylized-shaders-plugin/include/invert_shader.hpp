#pragma once

#include "base_shader.hpp"
#include <godot_cpp/classes/render_data.hpp>
#include <godot_cpp/classes/rendering_server.hpp>
#include <godot_cpp/core/class_db.hpp>

using namespace godot;

class InvertShader : public BaseShader
{
    GDCLASS(InvertShader, BaseShader);

  private:
    void init_compute(const String &shader_filename) override;

  protected:
    static void _bind_methods();

  public:
    InvertShader();
    ~InvertShader();

    void _render_callback(int32_t p_effect_callback_type,
                          RenderData *p_render_data) override;
    void _notification(int what) override;
};