#pragma once

#include "base_shader.hpp"
#include <godot_cpp/core/class_db.hpp>

using namespace godot;

class CRTShader : public BaseShader
{
    GDCLASS(CRTShader, BaseShader);

  private:
    void init_compute(const String &shader_filename) override;

  protected:
    static void _bind_methods();

  public:
    CRTShader();
    ~CRTShader();
    EncapsuledData<float> *m_curvature = memnew(EncapsuledData<float>(7.0f));
    EncapsuledData<float> *m_vignette_mul = memnew(EncapsuledData<float>(2.0f));
    EncapsuledData<float> *m_brightness = memnew(EncapsuledData<float>(0.9f));

    void _notification(int what) override;
    void _render_callback(int32_t, RenderData *) override;
};