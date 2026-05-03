#pragma once

#include "base_shader.hpp"
#include "util/encapsulated_data.hpp"
#include <godot_cpp/core/class_db.hpp>

using namespace godot;

class BloomShader : public BaseShader
{
    GDCLASS(BloomShader, BaseShader);

  private:
    RID m_downsample_shader;
    RID m_upsample_shader;
    RID m_add_shader;
    RID m_downsample_pipeline;
    RID m_upsample_pipeline;
    RID m_add_pipeline;
    RID m_bilinear_sampler;

    int32_t m_num_sampled_mips = 0;
    bool m_mip_finished = false;
    std::vector<Vector2i> m_mip_resolutions;

    void init_compute();

  protected:
    static void _bind_methods();

  public:
    BloomShader();
    ~BloomShader();
    EncapsuledData<float> *m_threshold = memnew(EncapsuledData<float>(1.0f));
    EncapsuledData<float> *m_radius = memnew(EncapsuledData<float>(2.5f));
    EncapsuledData<float> *m_strength = memnew(EncapsuledData<float>(0.5f));

    void _notification(int what) override;
    void _render_callback(int32_t, RenderData *) override;
};