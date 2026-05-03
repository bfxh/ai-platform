#include "dither_shader.hpp"
#include "util/encapsulated_data.hpp"

void DitherShader::_bind_methods() {}

DitherShader::DitherShader()
{
    construct();
    queue_callable_on_render_thread(
        callable_mp(this, &DitherShader::init_compute).bind("dither.glsl"));
}

DitherShader::~DitherShader() { try_delete_encapsulated(m_gamma_correction); }

void DitherShader::init_compute(const String &shader_filename)
{
    BaseShader::init_compute(shader_filename);
}

void DitherShader::_notification(int what)
{
    if (what == NOTIFICATION_PREDELETE && m_device)
    {
        free_shader();
    }
}

void DitherShader::_render_callback(int32_t p_effect_callback_type,
                                    RenderData *p_render_data)
{
    Ref<RenderSceneBuffersRD> buffers;
    buffers.instantiate();
    Vector2i size = get_buffers_internal_size(p_render_data, buffers);

    ERR_FAIL_COND_MSG(size.x == 0 || size.y == 0, "Buffer size is 0");

    PackedFloat32Array push_constant = {(float)size.x, (float)size.y,
                                        m_gamma_correction->get(), 0.0f};
    ERR_FAIL_COND_MSG(push_constant.is_empty(),
                      "Push constant is empty/invalid!");

    base_compute_update(p_effect_callback_type, p_render_data, buffers,
                        push_constant, size);
}
