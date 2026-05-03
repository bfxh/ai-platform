#include "effect_array.hpp"
#include "godot_cpp/core/error_macros.hpp"

void EffectArray::_bind_methods()
{
    ClassDB::bind_method(D_METHOD("get_effects"), &EffectArray::get_effects);
    ClassDB::bind_method(D_METHOD("set_effects", "effects"),
                         &EffectArray::set_effects);

    ADD_PROPERTY(PropertyInfo(Variant::ARRAY, "effects",
                              PROPERTY_HINT_ARRAY_TYPE, "BaseShader"),
                 "set_effects", "get_effects");
}

void EffectArray::set_effects(const TypedArray<BaseShader> &effects)
{
    m_effects = effects;
}

TypedArray<BaseShader> EffectArray::get_effects() const { return m_effects; }

TypedArray<BaseShader> &EffectArray::get_effects_as_mutable()
{
    return m_effects;
}

void EffectArray::add_effect(const Ref<BaseShader> &effect)
{
    if (effect.is_null())
    {
        ERR_PRINT("Tried to add a null effect.");
        return;
    }
    m_effects.push_back(effect);
    ERR_FAIL_COND_MSG(m_effects.find(effect) == -1,
                      "Could not push back effect into array");
}
void EffectArray::remove_effect(const Ref<BaseShader> &effect)
{
    if (effect.is_null())
    {
        ERR_PRINT("Tried to remove a null effect.");
        return;
    }
    m_effects.erase(effect);
}

void EffectArray::remove_effect(int64_t index)
{
    ERR_FAIL_COND_MSG(!m_effects.pop_at(index),
                      "ERROR: Could not remove effect at index " +
                          String::num(index));
}