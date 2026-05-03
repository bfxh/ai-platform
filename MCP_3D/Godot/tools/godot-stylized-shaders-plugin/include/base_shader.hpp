#pragma once
#include "godot_cpp/classes/render_scene_buffers_rd.hpp"
#include "godot_cpp/variant/packed_float32_array.hpp"
#include "util/encapsulated_data.hpp"
#include <godot_cpp/classes/compositor_effect.hpp>
#include <godot_cpp/classes/render_data.hpp>
#include <godot_cpp/classes/rendering_server.hpp>
#include <godot_cpp/core/class_db.hpp>

using namespace godot;

// CompositorEffect shader helper class
class BaseShader : public CompositorEffect
{
    GDCLASS(BaseShader, CompositorEffect);

  private:
    String m_addon_path = "res://addons/GodotStylizedShadersPlugin/shaders/";
    TypedArray<Callable> m_uniform_callables;

  protected:
    RID m_shader;
    RID m_pipeline;
    RenderingDevice *m_device = nullptr;

    void create_shader(const String &shader_path, RID &shader, RID &pipeline);
    void free_shader();
    void free_rid(RID &rid);
    Ref<RDUniform> get_sampler_uniform(const RID &image, const RID &sampler,
                                       int32_t binding);
    Ref<RDUniform> get_image_uniform(const RID &image, int32_t binding);
    Ref<RDUniform> get_buffer_uniform(const RID &buffer, int32_t binding);

    void construct();
    void queue_callable_on_render_thread(const Callable &c);
    void base_compute_update(int32_t p_effect_callback_type,
                             RenderData *p_render_data,
                             Ref<RenderSceneBuffersRD> &buffers,
                             const PackedFloat32Array &push_constant,
                             const Vector2i &size);

    static void _bind_methods();
    virtual void init_compute(const String &shader_filename);
    void push_back_callable(const Callable &c);
    Vector2i get_buffers_internal_size(RenderData *,
                                       Ref<RenderSceneBuffersRD> &) const;

  public:
    virtual void _notification(int what) = 0;
    String get_addon_path() const { return m_addon_path; }
};
