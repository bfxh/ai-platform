#include "outline_shader.hpp"
#include "ext/callable_lambda.hpp"
#include "util/encapsulated_data.hpp"
#include <godot_cpp/classes/compositor_effect.hpp>
#include <godot_cpp/classes/engine.hpp>
#include <godot_cpp/classes/file_access.hpp>
#include <godot_cpp/classes/rd_sampler_state.hpp>
#include <godot_cpp/classes/rd_shader_file.hpp>
#include <godot_cpp/classes/rd_shader_source.hpp>
#include <godot_cpp/classes/rd_shader_spirv.hpp>
#include <godot_cpp/classes/rd_uniform.hpp>
#include <godot_cpp/classes/render_scene_buffers_rd.hpp>
#include <godot_cpp/classes/render_scene_data_rd.hpp>
#include <godot_cpp/classes/rendering_device.hpp>
#include <godot_cpp/classes/resource_loader.hpp>
#include <godot_cpp/classes/uniform_set_cache_rd.hpp>
#include <godot_cpp/core/error_macros.hpp>
#include <godot_cpp/variant/array.hpp>
#include <godot_cpp/variant/packed_float32_array.hpp>
#include <godot_cpp/variant/projection.hpp>
#include <godot_cpp/variant/utility_functions.hpp>

void OutlineShader::_bind_methods()
{
    ClassDB::bind_method(D_METHOD("set_outline_color", "color"),
                         &OutlineShader::set_outline_color);
    ClassDB::bind_method(D_METHOD("get_outline_color"),
                         &OutlineShader::get_outline_color);
}

OutlineShader::OutlineShader()
{
    construct();
    m_depth_sampler = RID();
    queue_callable_on_render_thread(
        callable_mp(this, &OutlineShader::init_compute).bind("outline.glsl"));
}

OutlineShader::~OutlineShader()
{
    try_delete_encapsulated(m_outline_width);
    try_delete_encapsulated(m_outline_mul);
    try_delete_encapsulated(m_jitter_amp);
    try_delete_encapsulated(m_jitter_freq);
    try_delete_encapsulated(m_dt);
    try_delete_encapsulated(m_jitter_toggle);
}

void OutlineShader::_notification(int what)
{
    if (what == NOTIFICATION_PREDELETE && m_device)
    {
        free_shader();

        if (m_depth_sampler.is_valid())
        {
            m_device->free_rid(m_depth_sampler);
            m_depth_sampler = RID();
        }
    }
}

void OutlineShader::_render_callback(int32_t p_effect_callback_type,
                                     RenderData *p_render_data)
{
    Ref<RenderSceneBuffersRD> buffers;
    buffers.instantiate();
    Vector2i size = get_buffers_internal_size(p_render_data, buffers);
    ERR_FAIL_COND_MSG(size.x == 0 || size.y == 0, "Buffer size is 0");

    auto inv_proj_mat =
        p_render_data->get_render_scene_data()->get_cam_projection().inverse();
    PackedFloat32Array push_constant = {m_outline_color.r,
                                        m_outline_color.g,
                                        m_outline_color.b,
                                        m_jitter_amp->get(),
                                        (float)size.x,
                                        (float)size.y,
                                        (float)inv_proj_mat[2].w,
                                        (float)inv_proj_mat[3].w,
                                        m_outline_width->get(),
                                        m_outline_mul->get(),
                                        m_dt->get(),
                                        (float)UtilityFunctions::randf(),
                                        (float)m_jitter_toggle->get(),
                                        m_jitter_freq->get(),
                                        0.0f,
                                        0.0f};
    ERR_FAIL_COND_MSG(push_constant.is_empty(), "push constant is empty");

    push_back_callable(create_custom_callable_lambda(
        this,
        [&, buffers](RenderingDevice *device, Ref<RDUniform> uniform,
                     const int64_t &compute_list, int32_t i)
        {
            RID depth_texture = buffers->get_depth_layer(i);
            ERR_FAIL_COND_MSG(!depth_texture.is_valid(),
                              "Invalid depth texture for view " +
                                  String::num(i));
            uniform.instantiate();
            uniform->set_uniform_type(
                RenderingDevice::UNIFORM_TYPE_SAMPLER_WITH_TEXTURE);
            uniform->set_binding(0);
            uniform->add_id(m_depth_sampler);
            uniform->add_id(depth_texture);

            RID depth_uniform_set =
                UniformSetCacheRD::get_cache(m_shader, 1, {uniform});
            ERR_FAIL_COND_MSG(!depth_uniform_set.is_valid(),
                              "Failed to create depth uniform set for view " +
                                  String::num(i));
            device->compute_list_bind_uniform_set(compute_list,
                                                  depth_uniform_set, 1);
        }));

    base_compute_update(p_effect_callback_type, p_render_data, buffers,
                        push_constant, size);
}

void OutlineShader::init_compute(const String &shader_filename)
{
    BaseShader::init_compute(shader_filename);

    ERR_FAIL_COND_MSG(!m_device, "No device in OutlineShader::init_compute");

    Ref<RDSamplerState> state;
    state.instantiate();
    state->set_min_filter(RenderingDevice::SAMPLER_FILTER_LINEAR);
    state->set_mag_filter(RenderingDevice::SAMPLER_FILTER_LINEAR);
    m_depth_sampler = m_device->sampler_create(state);
    ERR_FAIL_COND_MSG(!m_depth_sampler.is_valid(), "Failed to create sampler!");
}

void OutlineShader::set_outline_color(Color color) { m_outline_color = color; }
Color OutlineShader::get_outline_color() const { return m_outline_color; }