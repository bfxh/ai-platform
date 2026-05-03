#include "crt_shader.hpp"
#include "util/encapsulated_data.hpp"
#include <godot_cpp/classes/compositor_effect.hpp>
#include <godot_cpp/classes/rd_uniform.hpp>
#include <godot_cpp/classes/render_scene_buffers_rd.hpp>
#include <godot_cpp/classes/uniform_set_cache_rd.hpp>

void CRTShader::_bind_methods() {}

CRTShader::CRTShader()
{
    construct();
    queue_callable_on_render_thread(
        callable_mp(this, &CRTShader::init_compute).bind("crt.glsl"));
}

CRTShader::~CRTShader()
{
    try_delete_encapsulated(m_curvature);
    try_delete_encapsulated(m_vignette_mul);
    try_delete_encapsulated(m_brightness);
}

void CRTShader::init_compute(const String &shader_filename)
{
    BaseShader::init_compute(shader_filename);
}

void CRTShader::_notification(int what)
{
    if (what == NOTIFICATION_PREDELETE && m_device)
    {
        free_shader();
    }
}

void CRTShader::_render_callback(int32_t p_effect_callback_type,
                                 RenderData *p_render_data)
{
    Ref<RenderSceneBuffersRD> buffers;
    buffers.instantiate();
    Vector2i size = get_buffers_internal_size(p_render_data, buffers);
    ERR_FAIL_COND_MSG(size.x == 0 || size.y == 0, "Buffer size is 0");

    PackedFloat32Array push_constant = {(float)size.x,
                                        (float)size.y,
                                        0.0f,
                                        0.0f,
                                        m_curvature->get(),
                                        m_vignette_mul->get(),
                                        m_brightness->get(),
                                        0.0f};
    ERR_FAIL_COND_MSG(push_constant.is_empty(),
                      "Push constant is empty/invalid!");

    base_compute_update(p_effect_callback_type, p_render_data, buffers,
                        push_constant, size);
}