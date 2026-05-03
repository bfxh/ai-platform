#pragma once

#include "godot_cpp/classes/object.hpp"
#include "godot_cpp/classes/slider.hpp"
#include "slider_container.hpp"
#include <godot_cpp/variant/callable.hpp>
#include <godot_cpp/variant/callable_method_pointer.hpp>

using namespace godot;

#define encapsulated_callable(type, object, variable)                          \
    callable_mp(object->variable, &EncapsuledData<type>::set)

#define try_delete_encapsulated(encapsulated)                                  \
    if (encapsulated)                                                          \
    memdelete(encapsulated)

template <typename Type> class EncapsuledData : public Object
{
    GDCLASS(EncapsuledData, Object);

    Type data;
    SliderContainer *m_linked_slider = nullptr;

  protected:
    static void _bind_methods() {}

  public:
    EncapsuledData() = default;
    EncapsuledData(const Type &initial_value) : data(initial_value) {}

    float get() const { return data; }
    void set(const Type &value)
    {
        data = value;
        if (m_linked_slider)
            m_linked_slider->set_label_value(value);
    }

    void connect_slider(SliderContainer *slider) { m_linked_slider = slider; }

    EncapsuledData *ptr() { return this; }
};