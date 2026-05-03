#include "pixel_shader.hpp"
#include "util/encapsulated_data.hpp"

void PixelShader::_bind_methods() {}

PixelShader::PixelShader()
{
    construct();

    queue_callable_on_render_thread(
        callable_mp(this, &PixelShader::init_compute).bind("pixel.glsl"));
}

PixelShader::~PixelShader()
{
    try_delete_encapsulated(target_width);
    try_delete_encapsulated(target_height);
}

void PixelShader::init_compute(const String &shader_filename)
{
    BaseShader::init_compute(shader_filename);
}

void PixelShader::_notification(int what)
{
    if (what == NOTIFICATION_PREDELETE && m_device)
    {
        free_shader();
    }
}

void PixelShader::_render_callback(int32_t p_effect_callback_type,
                                   RenderData *p_render_data)
{
    Ref<RenderSceneBuffersRD> buffers;
    buffers.instantiate();

    Vector2i size = get_buffers_internal_size(p_render_data, buffers);
    ERR_FAIL_COND_MSG(size.x == 0 || size.y == 0, "Buffer size is 0");

    PackedFloat32Array push_constant = {(float)size.x, (float)size.y,
                                        (float)target_width->get(),
                                        (float)target_height->get()};
    ERR_FAIL_COND_MSG(push_constant.is_empty(), "push constant is empty");

    base_compute_update(p_effect_callback_type, p_render_data, buffers,
                        push_constant, size);
}