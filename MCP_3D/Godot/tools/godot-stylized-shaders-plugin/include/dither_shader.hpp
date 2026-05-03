#pragma once

#include "base_shader.hpp"
#include "util/encapsulated_data.hpp"
#include <godot_cpp/core/class_db.hpp>

using namespace godot;

class DitherShader : public BaseShader
{
    GDCLASS(DitherShader, BaseShader);

  private:
    void init_compute(const String &shader_filename) override;

  protected:
    static void _bind_methods();

  public:
    DitherShader();
    ~DitherShader();
    EncapsuledData<float> *m_gamma_correction =
        memnew(EncapsuledData<float>(2.2f));

    void _notification(int what) override;
    void _render_callback(int32_t, RenderData *) override;
};