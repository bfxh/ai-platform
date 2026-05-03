#include "bloom_shader.hpp"
#include "godot_cpp/classes/rd_sampler_state.hpp"
#include "godot_cpp/classes/render_scene_buffers_rd.hpp"
#include "godot_cpp/core/error_macros.hpp"
#include "godot_cpp/core/method_bind.hpp"
#include "godot_cpp/variant/packed_float32_array.hpp"
#include "util/encapsulated_data.hpp"

#include <godot_cpp/classes/compositor_effect.hpp>
#include <godot_cpp/classes/display_server.hpp>
#include <godot_cpp/classes/rd_shader_file.hpp>
#include <godot_cpp/classes/rd_shader_spirv.hpp>
#include <godot_cpp/classes/rd_uniform.hpp>
#include <godot_cpp/classes/render_scene_data_rd.hpp>
#include <godot_cpp/classes/rendering_device.hpp>
#include <godot_cpp/classes/rendering_server.hpp>
#include <godot_cpp/classes/resource_loader.hpp>
#include <godot_cpp/classes/uniform_set_cache_rd.hpp>

void BloomShader::_bind_methods() {}

BloomShader::BloomShader()
{
    set_effect_callback_type(
        CompositorEffect::EFFECT_CALLBACK_TYPE_POST_TRANSPARENT);
    set_enabled(false);

    m_downsample_shader = RID();
    m_upsample_shader = RID();
    m_add_shader = RID();
    m_downsample_pipeline = RID();
    m_upsample_pipeline = RID();
    m_add_pipeline = RID();
    m_bilinear_sampler = RID();

    queue_callable_on_render_thread(
        callable_mp(this, &BloomShader::init_compute));
}

BloomShader::~BloomShader()
{
    try_delete_encapsulated(m_threshold);
    try_delete_encapsulated(m_radius);
    try_delete_encapsulated(m_strength);
}

void BloomShader::init_compute()
{
    m_device = RenderingServer::get_singleton()->get_rendering_device();
    ERR_FAIL_COND_MSG(!m_device, "No device");

    String addon_path = get_addon_path();
    String downsample_path = addon_path + "bloom_downsample.glsl";
    String upsample_path = addon_path + "bloom_upsample.glsl";
    String add_path = addon_path + "bloom_add.glsl";

    create_shader(downsample_path, m_downsample_shader, m_downsample_pipeline);
    create_shader(upsample_path, m_upsample_shader, m_upsample_pipeline);
    create_shader(add_path, m_add_shader, m_add_pipeline);

    Ref<RDSamplerState> sampler_state;
    sampler_state.instantiate();
    sampler_state->set_min_filter(RenderingDevice::SAMPLER_FILTER_LINEAR);
    sampler_state->set_mag_filter(RenderingDevice::SAMPLER_FILTER_LINEAR);
    m_bilinear_sampler = m_device->sampler_create(sampler_state);
    ERR_FAIL_COND_MSG(!m_bilinear_sampler.is_valid(),
                      "Failed to create bilinear sampler!");

    int32_t num_max_mips = 0;
    int32_t w = DisplayServer::get_singleton()->screen_get_size().x;
    while (w >= 2)
        w /= 2, num_max_mips++;

    m_num_sampled_mips = std::min(num_max_mips, 8);

    m_mip_resolutions.resize(m_num_sampled_mips);
}

void BloomShader::_notification(int what)
{
    if (!m_device)
        return;
    if (what == NOTIFICATION_PREDELETE)
    {
        free_shader();
        free_rid(m_bilinear_sampler);  // 4
        free_rid(m_add_shader);        // 3
        free_rid(m_upsample_shader);   // 2
        free_rid(m_downsample_shader); // 1
    }
}

void BloomShader::_render_callback(int32_t p_effect_callback_type,
                                   RenderData *p_render_data)
{
    ERR_FAIL_COND_MSG(
        !m_downsample_pipeline.is_valid(),
        "Downsample pipeline invalid in KuwaharaShader::_render_callback");
    ERR_FAIL_COND_MSG(
        !m_upsample_pipeline.is_valid(),
        "Upsample pipeline invalid in KuwaharaShader::_render_callback");
    ERR_FAIL_COND_MSG(
        !m_add_pipeline.is_valid(),
        "Add pipeline invalid in KuwaharaShader::_render_callback");

    if (m_device &&
        p_effect_callback_type == EFFECT_CALLBACK_TYPE_POST_TRANSPARENT)
    {
        Ref<RenderSceneBuffersRD> buffers =
            p_render_data->get_render_scene_buffers();
        ERR_FAIL_COND_MSG(!buffers.is_valid(), "BloomShader: buffers invalid!");

        Vector2i size = get_buffers_internal_size(p_render_data, buffers);
        ERR_FAIL_COND_MSG(size.x == 0 || size.y == 0, "Buffer size is 0");
        RenderSceneData *scene_data = p_render_data->get_render_scene_data();
        if (buffers.is_valid() || !scene_data)
        {
            const int x_groups = (size.x + 15) / 16;
            const int y_groups = (size.y + 15) / 16;
            auto usage = RenderingDevice::TEXTURE_USAGE_SAMPLING_BIT |
                         RenderingDevice::TEXTURE_USAGE_STORAGE_BIT |
                         RenderingDevice::TEXTURE_USAGE_CAN_UPDATE_BIT |
                         RenderingDevice::TEXTURE_USAGE_CAN_COPY_TO_BIT;
            if (!m_mip_finished) // run this only once, but i need size which is
                                 // gotten from p_render_data..
            {
                Vector2i resolution = size;
                for (int32_t i = 0; i < m_num_sampled_mips; ++i)
                {
                    m_mip_resolutions[i] = resolution;
                    resolution /= 2;
                }

                for (int32_t i = 0; i < m_num_sampled_mips; ++i)
                {
                    String downsample_name = "Downsample" + String::num(i, 0);
                    String upsample_name = "Upsample" + String::num(i, 0);
                    buffers->create_texture(
                        "Bloom", downsample_name,
                        RenderingDevice::DATA_FORMAT_R16G16B16A16_SFLOAT, usage,
                        RenderingDevice::TEXTURE_SAMPLES_1,
                        m_mip_resolutions[i], 1, 1, true, false);
                    buffers->create_texture(
                        "Bloom", upsample_name,
                        RenderingDevice::DATA_FORMAT_R16G16B16A16_SFLOAT, usage,
                        RenderingDevice::TEXTURE_SAMPLES_1,
                        m_mip_resolutions[i], 1, 1, true, false);
                }
                m_mip_finished = true;
            }

            PackedFloat32Array add_push_constant = {
                float(size.x), float(size.y), m_strength->get(), 0.0f};

            auto view_count = buffers->get_view_count();
            for (auto i = 0; i < view_count; ++i)
            {
                RID input_image = buffers->get_color_layer(i);
                // downsample
                for (int32_t mip = 0; mip < m_num_sampled_mips; ++mip)
                {
                    Vector2i resolution = m_mip_resolutions[mip];
                    int gx = (resolution.x + 15) / 16;
                    int gy = (resolution.y + 15) / 16;
                    auto downsample_texture = buffers->get_texture_slice(
                        "Bloom", "Downsample" + String::num(mip, 0), i, 0, 1,
                        1);
                    auto compute_list = m_device->compute_list_begin();
                    m_device->compute_list_bind_compute_pipeline(
                        compute_list, m_downsample_pipeline);
                    auto downsample_in =
                        get_sampler_uniform(input_image, m_bilinear_sampler, 0);
                    auto downsample_out =
                        get_image_uniform(downsample_texture, 1);
                    RID uniform_set = UniformSetCacheRD::get_cache(
                        m_downsample_shader, 0,
                        {downsample_in, downsample_out});

                    m_device->compute_list_bind_uniform_set(compute_list,
                                                            uniform_set, 0);

                    PackedFloat32Array downsample_push_constant = {
                        float(resolution.x), float(resolution.y),
                        m_threshold->get(),
                        0.0f}; // replace 1.0f with bloom threshold
                    m_device->compute_list_set_push_constant(
                        compute_list, downsample_push_constant.to_byte_array(),
                        downsample_push_constant.size() * 4);

                    m_device->compute_list_dispatch(compute_list, gx, gy, 1);
                    m_device->compute_list_end();

                    input_image = downsample_texture;
                }

                // Upsample
                for (int32_t mip = m_num_sampled_mips - 1; mip >= 0; --mip)
                {
                    if (mip == m_num_sampled_mips - 1)
                    {
                        continue;
                    }

                    Vector2i resolution = m_mip_resolutions[mip];
                    int gx = (resolution.x + 15) / 16;
                    int gy = (resolution.y + 15) / 16;

                    // upsampling src (higher mip)
                    RID src_texture;
                    if (mip == m_num_sampled_mips - 2)
                    {
                        src_texture = buffers->get_texture_slice(
                            "Bloom", "Downsample" + String::num(mip + 1, 0), i,
                            0, 1, 1);
                    }
                    else
                    {
                        src_texture = buffers->get_texture_slice(
                            "Bloom", "Upsample" + String::num(mip + 1, 0), i, 0,
                            1, 1);
                    }

                    auto downsample_texture = buffers->get_texture_slice(
                        "Bloom", "Downsample" + String::num(mip, 0), i, 0, 1,
                        1);

                    auto dst_texture = buffers->get_texture_slice(
                        "Bloom", "Upsample" + String::num(mip, 0), i, 0, 1, 1);

                    auto compute_list = m_device->compute_list_begin();
                    m_device->compute_list_bind_compute_pipeline(
                        compute_list, m_upsample_pipeline);

                    auto upsample_in =
                        get_sampler_uniform(src_texture, m_bilinear_sampler, 0);
                    auto downsample_in = get_sampler_uniform(
                        downsample_texture, m_bilinear_sampler, 1);
                    auto upsample_out = get_image_uniform(dst_texture, 2);

                    RID uniform_set = UniformSetCacheRD::get_cache(
                        m_upsample_shader, 0,
                        {upsample_in, downsample_in, upsample_out});

                    m_device->compute_list_bind_uniform_set(compute_list,
                                                            uniform_set, 0);
                    PackedFloat32Array upsample_push_constant = {
                        float(resolution.x), float(resolution.y),
                        m_radius->get(), 0.0f};
                    m_device->compute_list_set_push_constant(
                        compute_list, upsample_push_constant.to_byte_array(),
                        upsample_push_constant.size() * 4);
                    m_device->compute_list_dispatch(compute_list, gx, gy, 1);
                    m_device->compute_list_end();
                }

                // Add
                {
                    auto compute_list = m_device->compute_list_begin();
                    m_device->compute_list_bind_compute_pipeline(
                        compute_list, m_add_pipeline);
                    auto add_in1 =
                        get_image_uniform(buffers->get_color_layer(i), 0);
                    auto add_in2 = get_sampler_uniform(
                        buffers->get_texture_slice("Bloom", "Upsample0", i, 0,
                                                   1, 1),
                        m_bilinear_sampler, 1);
                    RID uniform_set = UniformSetCacheRD::get_cache(
                        m_add_shader, 0, {add_in1, add_in2});
                    m_device->compute_list_bind_uniform_set(compute_list,
                                                            uniform_set, 0);
                    m_device->compute_list_set_push_constant(
                        compute_list, add_push_constant.to_byte_array(),
                        add_push_constant.size() * 4);
                    m_device->compute_list_dispatch(compute_list, x_groups,
                                                    y_groups, 1);
                    m_device->compute_list_end();
                }
            }
        }
    }
}