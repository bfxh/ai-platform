#pragma once

#include "base_shader.hpp"
#include "util/encapsulated_data.hpp"
#include <godot_cpp/classes/render_data.hpp>
#include <godot_cpp/classes/rendering_server.hpp>
#include <godot_cpp/core/class_db.hpp>

using namespace godot;

class OutlineShader : public BaseShader
{
    GDCLASS(OutlineShader, BaseShader);

  private:
    void init_compute(const String &shader_filename) override;

    RID m_depth_sampler;

    Color m_outline_color = Color(0.0f, 0.0f, 0.0f);

  protected:
    static void _bind_methods();

  public:
    OutlineShader();
    ~OutlineShader();
    EncapsuledData<float> *m_outline_width =
        memnew(EncapsuledData<float>(.002f));
    EncapsuledData<float> *m_outline_mul = memnew(EncapsuledData<float>(.04f));
    EncapsuledData<float> *m_jitter_amp = memnew(EncapsuledData<float>(.01f));
    EncapsuledData<float> *m_jitter_freq = memnew(EncapsuledData<float>(.002f));
    EncapsuledData<float> *m_dt = memnew(EncapsuledData<float>(.0f));
    EncapsuledData<bool> *m_jitter_toggle = memnew(EncapsuledData<bool>(false));

    void _notification(int what) override;
    void _render_callback(int32_t, RenderData *) override;

    void set_outline_color(Color color);
    Color get_outline_color() const;
};