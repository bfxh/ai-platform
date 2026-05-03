#include "vhs_shader.hpp"
#include <godot_cpp/classes/compositor_effect.hpp>
#include <godot_cpp/classes/rd_uniform.hpp>
#include <godot_cpp/classes/render_scene_buffers_rd.hpp>
#include <godot_cpp/classes/uniform_set_cache_rd.hpp>

void VHSShader::_bind_methods() {}

VHSShader::VHSShader()
{
    construct();
    queue_callable_on_render_thread(
        callable_mp(this, &VHSShader::init_compute).bind("vhs.glsl"));
}

VHSShader::~VHSShader()
{
    try_delete_encapsulated(m_scanline_blend_factor);
    try_delete_encapsulated(m_scanline_height);
    try_delete_encapsulated(m_scanline_intensity);
    try_delete_encapsulated(m_scanline_scroll_speed);
    try_delete_encapsulated(m_scanline_enabled);
    try_delete_encapsulated(m_grain_intensity);
    try_delete_encapsulated(m_grain_enabled);
    try_delete_encapsulated(m_vertical_band_speed);
    try_delete_encapsulated(m_vertical_band_height);
    try_delete_encapsulated(m_vertical_band_intensity);
    try_delete_encapsulated(m_vertical_band_choppiness);
    try_delete_encapsulated(m_vertical_band_static_amount);
    try_delete_encapsulated(m_vertical_band_warp_factor);
    try_delete_encapsulated(m_vertical_band_enabled);
    try_delete_encapsulated(m_dt);
}

void VHSShader::init_compute(const String &shader_filename)
{
    BaseShader::init_compute(shader_filename);
}

void VHSShader::_notification(int what)
{
    if (what == NOTIFICATION_PREDELETE && m_device)
    {
        free_shader();
    }
}

void VHSShader::_render_callback(int32_t p_effect_callback_type,
                                 RenderData *p_render_data)
{
    Ref<RenderSceneBuffersRD> buffers;
    buffers.instantiate();
    Vector2i size = get_buffers_internal_size(p_render_data, buffers);
    ERR_FAIL_COND_MSG(size.x == 0 || size.y == 0, "Buffer size is 0");

    PackedFloat32Array push_constant = {(float)size.x,
                                        (float)size.y,
                                        m_scanline_blend_factor->get(),
                                        m_scanline_height->get(),
                                        m_scanline_intensity->get(),
                                        m_scanline_scroll_speed->get(),
                                        (float)m_scanline_enabled->get(),
                                        m_grain_intensity->get(),
                                        (float)m_grain_enabled->get(),
                                        m_vertical_band_speed->get(),
                                        m_vertical_band_height->get(),
                                        m_vertical_band_intensity->get(),
                                        m_vertical_band_choppiness->get(),
                                        m_vertical_band_static_amount->get(),
                                        m_vertical_band_warp_factor->get(),
                                        (float)m_vertical_band_enabled->get(),
                                        m_dt->get(),
                                        0.0f,
                                        0.0f,
                                        0.0f};
    ERR_FAIL_COND_MSG(push_constant.is_empty(),
                      "Push constant is empty/invalid!");

    base_compute_update(p_effect_callback_type, p_render_data, buffers,
                        push_constant, size);
}
