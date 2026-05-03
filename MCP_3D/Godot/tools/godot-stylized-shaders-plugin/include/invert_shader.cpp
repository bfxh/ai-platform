#include "invert_shader.hpp"
#include "godot_cpp/classes/compositor_effect.hpp"
#include "godot_cpp/core/error_macros.hpp"
#include "godot_cpp/variant/packed_float32_array.hpp"
#include "godot_cpp/variant/utility_functions.hpp"
#include <godot_cpp/classes/file_access.hpp>
#include <godot_cpp/classes/rd_shader_file.hpp>
#include <godot_cpp/classes/rd_shader_source.hpp>
#include <godot_cpp/classes/rd_shader_spirv.hpp>
#include <godot_cpp/classes/rd_uniform.hpp>
#include <godot_cpp/classes/render_scene_buffers_rd.hpp>
#include <godot_cpp/classes/render_scene_data_rd.hpp>
#include <godot_cpp/classes/rendering_device.hpp>
#include <godot_cpp/classes/resource_loader.hpp>
#include <godot_cpp/classes/uniform_set_cache_rd.hpp>

// Converted to C++ GDExtension from:
// https://docs.godotengine.org/en/latest/tutorials/rendering/compositor.html

void InvertShader::_bind_methods()
{
    ClassDB::bind_method(D_METHOD("init_compute"), &InvertShader::init_compute);
}

InvertShader::InvertShader()
{
    construct();
    queue_callable_on_render_thread(
        callable_mp(this, &InvertShader::init_compute)
            .bind("compute_template.glsl"));
}

InvertShader::~InvertShader() {}

void InvertShader::_notification(int what)
{
    if (what == NOTIFICATION_PREDELETE && m_device)
    {
        free_shader();
    }
}

void InvertShader::_render_callback(int32_t p_effect_callback_type,
                                    RenderData *p_render_data)
{
    Ref<RenderSceneBuffersRD> buffers;
    buffers.instantiate();

    Vector2i size = get_buffers_internal_size(p_render_data, buffers);
    ERR_FAIL_COND_MSG(size.x == 0 || size.y == 0, "Buffer size is 0");

    PackedFloat32Array push_constant = {(float)size.x, (float)size.y, 0, 0};
    ERR_FAIL_COND_MSG(push_constant.is_empty(), "push constant is empty");

    base_compute_update(p_effect_callback_type, p_render_data, buffers,
                        push_constant, size);
}

void InvertShader::init_compute(const String &shader_filename)
{
    BaseShader::init_compute(shader_filename);
}