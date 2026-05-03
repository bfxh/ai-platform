#pragma once

#include "base_shader.hpp"
#include <godot_cpp/classes/resource.hpp>
#include <godot_cpp/core/class_db.hpp>

using namespace godot;

class EffectArray : public Resource
{
    GDCLASS(EffectArray, Resource);

  private:
    TypedArray<BaseShader> m_effects;

  protected:
    static void _bind_methods();

  public:
    void add_effect(const Ref<BaseShader> &effect);
    void remove_effect(const Ref<BaseShader> &effect);
    void remove_effect(int64_t index);
    void set_effects(const TypedArray<BaseShader> &effects);
    TypedArray<BaseShader> get_effects() const;
    TypedArray<BaseShader> &get_effects_as_mutable();
};