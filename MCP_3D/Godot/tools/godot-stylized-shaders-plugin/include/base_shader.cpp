#include "base_shader.hpp"
#include <godot_cpp/classes/rd_shader_file.hpp>
#include <godot_cpp/classes/rd_shader_spirv.hpp>
#include <godot_cpp/classes/resource_loader.hpp>

#include <godot_cpp/classes/rd_uniform.hpp>
#include <godot_cpp/classes/render_scene_buffers_rd.hpp>
#include <godot_cpp/classes/uniform_set_cache_rd.hpp>

void BaseShader::_bind_methods() {}

void BaseShader::construct()
{
    set_effect_callback_type(
        CompositorEffect::EFFECT_CALLBACK_TYPE_POST_TRANSPARENT);

    m_shader = RID();
    m_pipeline = RID();
    set_enabled(false);
}

void BaseShader::queue_callable_on_render_thread(const Callable &c)
{
    if (auto *rs = RenderingServer::get_singleton())
    {
        rs->call_on_render_thread(c);
    }
}

void BaseShader::init_compute(const String &shader_filename)
{
    m_device = RenderingServer::get_singleton()->get_rendering_device();
    ERR_FAIL_COND_MSG(!m_device, "No device");

    String shader_path = m_addon_path + shader_filename;
    Ref<RDShaderFile> shader_file =
        ResourceLoader::get_singleton()->load(shader_path);
    ERR_FAIL_COND_MSG(!shader_file.is_valid(),
                      "Failed to load shader file from path: " + shader_path);

    String base_error = shader_file->get_base_error();
    ERR_FAIL_COND_MSG(!base_error.is_empty(),
                      "Shader compilation error: " + base_error);

    Ref<RDShaderSPIRV> spirv = shader_file->get_spirv();
    ERR_FAIL_COND_MSG(!spirv.is_valid(),
                      "Failed to get SPIRV from shader file!");

    m_shader = m_device->shader_create_from_spirv(spirv);
    ERR_FAIL_COND_MSG(!m_shader.is_valid(),
                      "Failed to create shader from SPIRV!");

    m_pipeline = m_device->compute_pipeline_create(m_shader);
}

void BaseShader::create_shader(const String &shader_path, RID &shader,
                               RID &pipeline)
{
    Ref<RDShaderFile> shader_file =
        ResourceLoader::get_singleton()->load(shader_path);
    ERR_FAIL_COND_MSG(!shader_file.is_valid(), "Failed to load shader file!");

    String base_error = shader_file->get_base_error();
    ERR_FAIL_COND_MSG(!base_error.is_empty(),
                      "Shader compilation error: " + base_error);

    Ref<RDShaderSPIRV> spirv = shader_file->get_spirv();
    ERR_FAIL_COND_MSG(!spirv.is_valid(),
                      "Failed to get SPIRV from shader file!");

    shader = m_device->shader_create_from_spirv(spirv);
    ERR_FAIL_COND_MSG(!shader.is_valid(),
                      "Failed to create shader from SPIRV!");

    pipeline = m_device->compute_pipeline_create(shader);
}

void BaseShader::free_shader()
{
    if (m_shader.is_valid())
    {
        m_device->free_rid(m_shader);
        m_shader = RID();
    }
}

void BaseShader::free_rid(RID &rid)
{
    if (rid.is_valid())
    {
        m_device->free_rid(rid);
        rid = RID();
    }
}

Ref<RDUniform> BaseShader::get_sampler_uniform(const RID &image,
                                               const RID &sampler,
                                               int32_t binding)
{
    Ref<RDUniform> uniform;
    uniform.instantiate();

    uniform->set_uniform_type(
        RenderingDevice::UNIFORM_TYPE_SAMPLER_WITH_TEXTURE);
    uniform->set_binding(binding);
    uniform->add_id(sampler);
    uniform->add_id(image);

    return uniform;
}

Ref<RDUniform> BaseShader::get_image_uniform(const RID &image, int32_t binding)
{
    Ref<RDUniform> uniform;
    uniform.instantiate();

    uniform->set_uniform_type(RenderingDevice::UNIFORM_TYPE_IMAGE);
    uniform->set_binding(binding);
    uniform->add_id(image);

    return uniform;
}

Ref<RDUniform> BaseShader::get_buffer_uniform(const RID &buffer,
                                              int32_t binding)
{
    Ref<RDUniform> uniform;
    uniform.instantiate();

    uniform->set_uniform_type(RenderingDevice::UNIFORM_TYPE_STORAGE_BUFFER);
    uniform->set_binding(binding);
    uniform->add_id(buffer);

    return uniform;
}

void BaseShader::base_compute_update(int32_t p_effect_callback_type,
                                     RenderData *p_render_data,
                                     Ref<RenderSceneBuffersRD> &buffers,
                                     const PackedFloat32Array &push_constant,
                                     const Vector2i &size)
{
    if (m_device &&
        p_effect_callback_type == EFFECT_CALLBACK_TYPE_POST_TRANSPARENT)
    {
        // Check if shader and pipeline are valid before proceeding
        ERR_FAIL_COND_MSG(push_constant.is_empty(), "push constant is empty");
        ERR_FAIL_COND_MSG(!m_shader.is_valid(),
                          "Shader is invalid in render callback!");
        ERR_FAIL_COND_MSG(!m_pipeline.is_valid(),
                          "Pipeline is invalid in render callback!");

        RenderSceneData *scene_data = p_render_data->get_render_scene_data();
        if (buffers.is_valid() || !scene_data)
        {
            const int x_groups = (size.x + 15) / 16;
            const int y_groups = (size.y + 15) / 16;

            uint32_t view_count = buffers->get_view_count();

            for (int32_t i = 0; i < view_count; i++)
            {
                RID input_image = buffers->get_color_layer(i);
                ERR_CONTINUE_MSG(!input_image.is_valid(),
                                 "Invalid input image for view " +
                                     String::num(i));

                Ref<RDUniform> uniform;
                uniform.instantiate();
                uniform->set_uniform_type(RenderingDevice::UNIFORM_TYPE_IMAGE);
                uniform->set_binding(0);
                uniform->add_id(input_image);

                RID image_uniform_set =
                    UniformSetCacheRD::get_cache(m_shader, 0, {uniform});
                ERR_CONTINUE_MSG(
                    !image_uniform_set.is_valid(),
                    "Failed to create color image uniform set for view " +
                        String::num(i));

                auto compute_list = m_device->compute_list_begin();
                m_device->compute_list_bind_compute_pipeline(compute_list,
                                                             m_pipeline);
                m_device->compute_list_bind_uniform_set(compute_list,
                                                        image_uniform_set, 0);

                for (auto &item : m_uniform_callables)
                {
                    Callable c(item);
                    c.call(m_device, uniform, compute_list, i);
                }

                m_device->compute_list_set_push_constant(
                    compute_list, push_constant.to_byte_array(),
                    push_constant.size() * 4);
                m_device->compute_list_dispatch(compute_list, x_groups,
                                                y_groups, 1);
                m_device->compute_list_end();
            }
        }
    }
}

void BaseShader::push_back_callable(const Callable &c)
{
    m_uniform_callables.push_back(c);
}

Vector2i
BaseShader::get_buffers_internal_size(RenderData *p_render_data,
                                      Ref<RenderSceneBuffersRD> &buffers) const
{
    buffers = p_render_data->get_render_scene_buffers();
    return buffers->get_internal_size();
}