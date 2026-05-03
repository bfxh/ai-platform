#pragma once

#include "base_shader.hpp"
#include <godot_cpp/core/class_db.hpp>

using namespace godot;

class PixelShader : public BaseShader
{
    GDCLASS(PixelShader, BaseShader);

  private:
    void init_compute(const String &shader_filename) override;

  protected:
    static void _bind_methods();

  public:
    PixelShader();
    ~PixelShader();
    EncapsuledData<int> *target_width = memnew(EncapsuledData<int>(320));
    EncapsuledData<int> *target_height = memnew(EncapsuledData<int>(180));

    void _notification(int what) override;
    void _render_callback(int32_t, RenderData *) override;
};