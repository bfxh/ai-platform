#include "kuwahara_shader.hpp"
#include "util/encapsulated_data.hpp"
#include <godot_cpp/classes/rd_sampler_state.hpp>
#include <godot_cpp/classes/rd_uniform.hpp>
#include <godot_cpp/classes/uniform_set_cache_rd.hpp>

void KuwaharaShader::_bind_methods() {}

KuwaharaShader::KuwaharaShader()
{
    set_effect_callback_type(
        CompositorEffect::EFFECT_CALLBACK_TYPE_POST_TRANSPARENT);
    set_enabled(false);

    m_structure_tensor_shader = RID();
    m_horizontal_blur_shader = RID();
    m_vertical_blur_shader = RID();
    m_composite_shader = RID();
    m_downsample_shader = RID();
    m_upsample_shader = RID();
    m_structure_tensor_pipeline = RID();
    m_horizontal_blur_pipeline = RID();
    m_vertical_blur_pipeline = RID();
    m_composite_pipeline = RID();
    m_downsample_pipeline = RID();
    m_upsample_pipeline = RID();
    m_billinear_sampler = RID();

    queue_callable_on_render_thread(
        callable_mp(this, &KuwaharaShader::init_compute));

    m_preset_configs.push_back({"Fast", 3.0F, 7.0F, 1.0F, 4.0F, 8.0F});
    m_preset_configs.push_back({"Subtle", 3.0F, 7.0F, 1.0F, 8.0F, 8.0F});
    m_preset_configs.push_back({"Oil", 5.0F, 13.0F, 1.5F, 8.0F, 10.0F});
    m_preset_configs.push_back({"Anime", 4.0F, 9.0F, 0.8F, 4.0F, 12.0F});
}

KuwaharaShader::~KuwaharaShader()
{
    try_delete_encapsulated(downsample_factor);
    try_delete_encapsulated(radius);
    try_delete_encapsulated(kernel_size);
    try_delete_encapsulated(alpha);
    try_delete_encapsulated(sectors);
    try_delete_encapsulated(sharpness);
}

void KuwaharaShader::init_compute()
{
    m_device = RenderingServer::get_singleton()->get_rendering_device();
    ERR_FAIL_COND_MSG(!m_device, "No device");

    String addon_path = get_addon_path();
    String tensor_path = addon_path + "structure_tensor.glsl";
    String horizontal_blur_path = addon_path + "kuwahara_blur_horizontal.glsl";
    String vertical_blur_path = addon_path + "kuwahara_blur_vertical.glsl";
    String comp_path = addon_path + "kuwahara_comp.glsl";
    String downsample_path = addon_path + "kuwahara_downsample.glsl";
    String upsample_path = addon_path + "kuwahara_upsample.glsl";

    create_shader(tensor_path, m_structure_tensor_shader,
                  m_structure_tensor_pipeline);
    create_shader(horizontal_blur_path, m_horizontal_blur_shader,
                  m_horizontal_blur_pipeline);
    create_shader(vertical_blur_path, m_vertical_blur_shader,
                  m_vertical_blur_pipeline);
    create_shader(comp_path, m_composite_shader, m_composite_pipeline);
    create_shader(downsample_path, m_downsample_shader, m_downsample_pipeline);
    create_shader(upsample_path, m_upsample_shader, m_upsample_pipeline);

    Ref<RDSamplerState> sampler_state;
    sampler_state.instantiate();
    sampler_state->set_min_filter(RenderingDevice::SAMPLER_FILTER_LINEAR);
    sampler_state->set_mag_filter(RenderingDevice::SAMPLER_FILTER_LINEAR);
    m_billinear_sampler = m_device->sampler_create(sampler_state);
    ERR_FAIL_COND_MSG(!m_billinear_sampler.is_valid(),
                      "Failed to create billinear sampler!");
}

void KuwaharaShader::_notification(int what)
{
    if (!m_device)
        return;
    if (what == NOTIFICATION_PREDELETE)
    {
        free_shader();
        free_rid(m_upsample_shader);         // 6
        free_rid(m_downsample_shader);       // 5
        free_rid(m_composite_shader);        // 4
        free_rid(m_vertical_blur_shader);    // 3
        free_rid(m_horizontal_blur_shader);  // 2
        free_rid(m_structure_tensor_shader); // 1
    }
}

void KuwaharaShader::_render_callback(int32_t p_effect_callback_type,
                                      RenderData *p_render_data)
{
    ERR_FAIL_COND_MSG(!m_device,
                      "No device in KuwaharaShader::_render_callback");
    ERR_FAIL_COND_MSG(
        !m_structure_tensor_pipeline.is_valid(),
        "No structure tensor pipeline in KuwaharaShader::_render_callback");
    ERR_FAIL_COND_MSG(
        !m_horizontal_blur_pipeline.is_valid(),
        "No horizontal blur pipeline in KuwaharaShader::_render_callback");
    ERR_FAIL_COND_MSG(
        !m_vertical_blur_pipeline.is_valid(),
        "No vertical blur pipeline in KuwaharaShader::_render_callback");
    ERR_FAIL_COND_MSG(
        !m_composite_pipeline.is_valid(),
        "No weighting pipeline in KuwaharaShader::_render_callback");
    ERR_FAIL_COND_MSG(
        !m_downsample_pipeline.is_valid(),
        "No downsample pipeline in KuwaharaShader::_render_callback");
    ERR_FAIL_COND_MSG(
        !m_upsample_pipeline.is_valid(),
        "No upsample pipeline in KuwaharaShader::_render_callback");

    if (p_effect_callback_type == EFFECT_CALLBACK_TYPE_POST_TRANSPARENT)
    {
        Ref<RenderSceneBuffersRD> buffers =
            p_render_data->get_render_scene_buffers();
        ERR_FAIL_COND_MSG(!buffers.is_valid(),
                          "KuwaharaShader: buffers invalid!");

        Vector2i full_size = get_buffers_internal_size(p_render_data, buffers);
        ERR_FAIL_COND_MSG(full_size.x == 0 || full_size.y == 0,
                          "Buffer size is 0");
        Vector2i work_size =
            Vector2i(Math::max(1, int(full_size.x / downsample_factor->get())),
                     Math::max(1, int(full_size.y / downsample_factor->get())));
        RenderSceneData *scene_data = p_render_data->get_render_scene_data();
        if (buffers.is_valid() && scene_data)
        {
            const int full_x_groups = (full_size.x + 15) / 16;
            const int full_y_groups = (full_size.y + 15) / 16;
            const int work_x_groups = (work_size.x + 15) / 16;
            const int work_y_groups = (work_size.y + 15) / 16;

            auto view_count = buffers->get_view_count();
            auto usage = RenderingDevice::TEXTURE_USAGE_SAMPLING_BIT |
                         RenderingDevice::TEXTURE_USAGE_STORAGE_BIT |
                         RenderingDevice::TEXTURE_USAGE_CAN_UPDATE_BIT |
                         RenderingDevice::TEXTURE_USAGE_CAN_COPY_TO_BIT;

            // TODO: fix runtime change of downsample_factor scaling bug
            bool size_changed = (m_last_work_size != work_size);
            if (size_changed)
            {
                buffers->create_texture(
                    "Kuwahara", "Downsample",
                    RenderingDevice::DATA_FORMAT_R16G16B16A16_SFLOAT, usage,
                    RenderingDevice::TEXTURE_SAMPLES_1, work_size, 1, 1, true,
                    false);
                buffers->create_texture(
                    "Kuwahara", "Tensor",
                    RenderingDevice::DATA_FORMAT_R16G16B16A16_SFLOAT, usage,
                    RenderingDevice::TEXTURE_SAMPLES_1, work_size, 1, 1, true,
                    false);
                buffers->create_texture(
                    "Kuwahara", "BlurH",
                    RenderingDevice::DATA_FORMAT_R16G16B16A16_SFLOAT, usage,
                    RenderingDevice::TEXTURE_SAMPLES_1, work_size, 1, 1, true,
                    false);
                buffers->create_texture(
                    "Kuwahara", "BlurV",
                    RenderingDevice::DATA_FORMAT_R16G16B16A16_SFLOAT, usage,
                    RenderingDevice::TEXTURE_SAMPLES_1, work_size, 1, 1, true,
                    false);
                buffers->create_texture(
                    "Kuwahara", "Output",
                    RenderingDevice::DATA_FORMAT_R16G16B16A16_SFLOAT, usage,
                    RenderingDevice::TEXTURE_SAMPLES_1, work_size, 1, 1, true,
                    false);
                m_last_work_size = work_size;
            }

            for (uint32_t i = 0; i < view_count; ++i)
            {
                RID input_image = buffers->get_color_layer(i);

                RID downsample_tex = buffers->get_texture_slice(
                    "Kuwahara", "Downsample", i, 0, 1, 1);
                RID tensor_tex = buffers->get_texture_slice(
                    "Kuwahara", "Tensor", i, 0, 1, 1);
                RID blur_h_tex =
                    buffers->get_texture_slice("Kuwahara", "BlurH", i, 0, 1, 1);
                RID blur_v_tex =
                    buffers->get_texture_slice("Kuwahara", "BlurV", i, 0, 1, 1);
                RID output_tex = buffers->get_texture_slice(
                    "Kuwahara", "Output", i, 0, 1, 1);

                // downsample
                {
                    auto list = m_device->compute_list_begin();
                    m_device->compute_list_bind_compute_pipeline(
                        list, m_downsample_pipeline);

                    auto u_in = get_sampler_uniform(input_image,
                                                    m_billinear_sampler, 0);
                    auto u_out = get_image_uniform(downsample_tex, 1);
                    RID set = UniformSetCacheRD::get_cache(m_downsample_shader,
                                                           0, {u_in, u_out});
                    m_device->compute_list_bind_uniform_set(list, set, 0);

                    PackedFloat32Array pc = {
                        float(full_size.x), float(full_size.y),
                        float(work_size.x), float(work_size.y)};
                    m_device->compute_list_set_push_constant(
                        list, pc.to_byte_array(), pc.size() * 4);
                    m_device->compute_list_dispatch(list, work_x_groups,
                                                    work_y_groups, 1);
                    m_device->compute_list_end();
                }

                // structure tensor pass
                {
                    auto compute_list = m_device->compute_list_begin();
                    m_device->compute_list_bind_compute_pipeline(
                        compute_list, m_structure_tensor_pipeline);

                    auto u_in = get_sampler_uniform(downsample_tex,
                                                    m_billinear_sampler, 0);
                    auto u_out = get_image_uniform(tensor_tex, 1);
                    RID set = UniformSetCacheRD::get_cache(
                        m_structure_tensor_shader, 0, {u_in, u_out});
                    m_device->compute_list_bind_uniform_set(compute_list, set,
                                                            0);

                    PackedFloat32Array push_constant = {
                        float(work_size.x), float(work_size.y), 0.0f, 0.0f};
                    m_device->compute_list_set_push_constant(
                        compute_list, push_constant.to_byte_array(),
                        push_constant.size() * 4);
                    m_device->compute_list_dispatch(compute_list, work_x_groups,
                                                    work_y_groups, 1);
                    m_device->compute_list_end();
                }

                // horiz blur pass
                {
                    auto list = m_device->compute_list_begin();
                    m_device->compute_list_bind_compute_pipeline(
                        list, m_horizontal_blur_pipeline);

                    auto u_in =
                        get_sampler_uniform(tensor_tex, m_billinear_sampler, 0);
                    auto u_out = get_image_uniform(blur_h_tex, 1);
                    RID set = UniformSetCacheRD::get_cache(
                        m_horizontal_blur_shader, 0, {u_in, u_out});
                    m_device->compute_list_bind_uniform_set(list, set, 0);

                    PackedFloat32Array pc = {float(work_size.x),
                                             float(work_size.y), radius->get(),
                                             0.0f};
                    m_device->compute_list_set_push_constant(
                        list, pc.to_byte_array(), pc.size() * 4);
                    m_device->compute_list_dispatch(list, work_x_groups,
                                                    work_y_groups, 1);
                    m_device->compute_list_end();
                }

                // vert blur pass
                {
                    auto list = m_device->compute_list_begin();
                    m_device->compute_list_bind_compute_pipeline(
                        list, m_vertical_blur_pipeline);

                    auto u_in =
                        get_sampler_uniform(blur_h_tex, m_billinear_sampler, 0);
                    auto u_out = get_image_uniform(blur_v_tex, 1);
                    RID set = UniformSetCacheRD::get_cache(
                        m_vertical_blur_shader, 0, {u_in, u_out});
                    m_device->compute_list_bind_uniform_set(list, set, 0);

                    PackedFloat32Array pc = {float(work_size.x),
                                             float(work_size.y), radius->get(),
                                             0.0f};
                    m_device->compute_list_set_push_constant(
                        list, pc.to_byte_array(), pc.size() * 4);
                    m_device->compute_list_dispatch(list, work_x_groups,
                                                    work_y_groups, 1);
                    m_device->compute_list_end();
                }

                // weighting pass
                {
                    auto list = m_device->compute_list_begin();
                    m_device->compute_list_bind_compute_pipeline(
                        list, m_composite_pipeline);

                    auto u_color = get_sampler_uniform(downsample_tex,
                                                       m_billinear_sampler, 0);
                    auto u_blur =
                        get_sampler_uniform(blur_v_tex, m_billinear_sampler, 1);
                    auto u_out = get_image_uniform(output_tex, 2);
                    RID set = UniformSetCacheRD::get_cache(
                        m_composite_shader, 0, {u_color, u_blur, u_out});
                    m_device->compute_list_bind_uniform_set(list, set, 0);

                    PackedFloat32Array pc = {
                        float(work_size.x), float(work_size.y),
                        kernel_size->get(), alpha->get(),
                        ZERO_CROSSING,      sectors->get(),
                        sharpness->get(),   0.0f};
                    m_device->compute_list_set_push_constant(
                        list, pc.to_byte_array(), pc.size() * 4);
                    m_device->compute_list_dispatch(list, work_x_groups,
                                                    work_y_groups, 1);
                    m_device->compute_list_end();
                }

                // final pass
                {
                    auto list = m_device->compute_list_begin();
                    m_device->compute_list_bind_compute_pipeline(
                        list, m_upsample_pipeline);

                    auto u_in =
                        get_sampler_uniform(output_tex, m_billinear_sampler, 0);
                    auto u_out = get_image_uniform(input_image, 1);
                    RID set = UniformSetCacheRD::get_cache(m_upsample_shader, 0,
                                                           {u_in, u_out});
                    m_device->compute_list_bind_uniform_set(list, set, 0);

                    PackedFloat32Array pc = {
                        float(work_size.x), float(work_size.y),
                        float(full_size.x), float(full_size.y)};
                    m_device->compute_list_set_push_constant(
                        list, pc.to_byte_array(), pc.size() * 4);
                    m_device->compute_list_dispatch(list, full_x_groups,
                                                    full_y_groups, 1);
                    m_device->compute_list_end();
                }
            }
        }
    }
}

void KuwaharaShader::apply_config(const KuwaharaPresetConfig &config)
{
    radius->set(config.radius);
    kernel_size->set(config.kernel_size);
    alpha->set(config.alpha);
    sectors->set(config.sectors);
    sharpness->set(config.sharpness);
}

void KuwaharaShader::set_preset(KuwaharaPreset p)
{
    m_preset = p;
    apply_config(m_preset_configs[static_cast<uint8_t>(p)]);
}

void KuwaharaShader::set_preset(const KuwaharaPresetConfig &config)
{
    apply_config(config);
}

void KuwaharaShader::set_preset_as_selected(int32_t index)
{
    apply_config(m_preset_configs[index]);
}

void KuwaharaShader::add_preset_config(const KuwaharaPresetConfig &config)
{
    m_preset_configs.push_back(config);
}