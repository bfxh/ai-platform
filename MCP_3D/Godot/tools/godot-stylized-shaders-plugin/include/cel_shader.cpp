#include "cel_shader.hpp"
#include "godot_cpp/classes/compositor_effect.hpp"
#include <godot_cpp/classes/rd_uniform.hpp>
#include <godot_cpp/classes/render_scene_buffers_rd.hpp>
#include <godot_cpp/classes/uniform_set_cache_rd.hpp>

void CelShader::_bind_methods() {}

CelShader::CelShader()
{
    construct();

    queue_callable_on_render_thread(
        callable_mp(this, &CelShader::init_compute).bind("cel.glsl"));
}

CelShader::~CelShader() {}

void CelShader::init_compute(const String &shader_filename)
{
    BaseShader::init_compute(shader_filename);
    // ...
}

void CelShader::_notification(int what)
{
    if (what == NOTIFICATION_PREDELETE && m_device)
    {
        free_shader();
    }
}

void CelShader::_render_callback(int32_t p_effect_callback_type,
                                 RenderData *p_render_data)
{
    Ref<RenderSceneBuffersRD> buffers;
    buffers.instantiate();

    Vector2i size = get_buffers_internal_size(p_render_data, buffers);
    ERR_FAIL_COND_MSG(size.x == 0 || size.y == 0, "Buffer size is 0");

    PackedFloat32Array push_constant = {(float)size.x, (float)size.y,
                                        m_levels->get(), 0.0f};
    ERR_FAIL_COND_MSG(push_constant.is_empty(), "push constant is empty");

    base_compute_update(p_effect_callback_type, p_render_data, buffers,
                        push_constant, size);
}

// void CelShader::_get_property_list(List<PropertyInfo> *p_list) const
// {
//     p_list->push_back(PropertyInfo(Variant::FLOAT, "levels",
//     PROPERTY_HINT_RANGE, "1.0,32.0,1.0"));
// }

// bool CelShader::_get(const StringName &p_name, Variant &r_ret) const
// {

// }

// bool CelShader::_set(const StringName &p_name, const Variant &p_value)
// {

// }