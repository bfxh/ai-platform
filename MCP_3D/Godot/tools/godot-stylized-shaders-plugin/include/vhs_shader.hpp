#pragma once

#include "base_shader.hpp"
#include "godot_cpp/classes/wrapped.hpp"
#include "util/encapsulated_data.hpp"
#include <godot_cpp/core/class_db.hpp>

using namespace godot;

class VHSShader : public BaseShader
{
    GDCLASS(VHSShader, BaseShader);

  private:
    void init_compute(const String &shader_filename) override;

  protected:
    static void _bind_methods();

  public:
    VHSShader();
    ~VHSShader();
    EncapsuledData<float> *m_scanline_blend_factor =
        memnew(EncapsuledData<float>(.1f));
    EncapsuledData<float> *m_scanline_height =
        memnew(EncapsuledData<float>(4.f));
    EncapsuledData<float> *m_scanline_intensity =
        memnew(EncapsuledData<float>(.25f));
    EncapsuledData<float> *m_scanline_scroll_speed =
        memnew(EncapsuledData<float>(16.f));
    EncapsuledData<bool> *m_scanline_enabled =
        memnew(EncapsuledData<bool>(true));
    EncapsuledData<float> *m_grain_intensity =
        memnew(EncapsuledData<float>(2.f));
    EncapsuledData<bool> *m_grain_enabled = memnew(EncapsuledData<bool>(true));
    EncapsuledData<float> *m_vertical_band_speed =
        memnew(EncapsuledData<float>(.2f));
    EncapsuledData<float> *m_vertical_band_height =
        memnew(EncapsuledData<float>(.01f));
    EncapsuledData<float> *m_vertical_band_intensity =
        memnew(EncapsuledData<float>(.2f));
    EncapsuledData<float> *m_vertical_band_choppiness =
        memnew(EncapsuledData<float>(.2f));
    EncapsuledData<float> *m_vertical_band_static_amount =
        memnew(EncapsuledData<float>(.02f));
    EncapsuledData<float> *m_vertical_band_warp_factor =
        memnew(EncapsuledData<float>(.005f));
    EncapsuledData<bool> *m_vertical_band_enabled =
        memnew(EncapsuledData<bool>(true));
    EncapsuledData<float> *m_dt = memnew(EncapsuledData<float>(0.f));

    void _notification(int what) override;
    void _render_callback(int32_t, RenderData *) override;
};