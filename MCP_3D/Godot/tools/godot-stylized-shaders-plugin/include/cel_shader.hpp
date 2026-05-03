#pragma once

#include "base_shader.hpp"
#include <godot_cpp/core/class_db.hpp>

using namespace godot;

class CelShader : public BaseShader
{
    GDCLASS(CelShader, BaseShader);

  private:
    void init_compute(const String &shader_filename) override;

  protected:
    static void _bind_methods();

    // void _get_property_list(List<PropertyInfo> *p_list) const;
    // bool _get(const StringName &p_name, Variant &r_ret) const;
    // bool _set(const StringName &p_name, const Variant &p_value);
  public:
    CelShader();
    ~CelShader();
    EncapsuledData<float> *m_levels = memnew(EncapsuledData<float>(16.f));

    void _notification(int what) override;
    void _render_callback(int32_t, RenderData *) override;
};