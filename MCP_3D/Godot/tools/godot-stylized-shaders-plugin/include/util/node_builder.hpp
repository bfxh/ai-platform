#pragma once

#include "encapsulated_data.hpp"
#include "godot_cpp/classes/v_box_container.hpp"
#include <godot_cpp/classes/node.hpp>
#include <godot_cpp/classes/scroll_container.hpp>
#include <type_traits>

using namespace godot;

class SliderContainer;

template <typename T> class NodeBuilder
{
    T *node = nullptr;

  public:
    NodeBuilder(T *n) : node(n) {}

    template <typename Func, typename... Args>
    NodeBuilder<T> &call(Func func, Args &&...args)
    {
        static_assert(std::is_member_function_pointer_v<Func>,
                      "call() can only be used with member function pointers");
        (node->*func)(std::forward<Args>(args)...);
        return *this;
    }

    template <class C> NodeBuilder<C> add_child()
    {
        static_assert(std::is_base_of_v<Node, C>,
                      "add_child() can only be used to add Node children");
        C *child = memnew(C);
        node->add_child(child);
        return NodeBuilder<C>(child);
    }

    NodeBuilder<SliderContainer> &
    slider_container_init(const String &label_text, double step, double min,
                          double max, EncapsuledData<float> *value,
                          const Callable &callable)
    {
        static_assert(std::is_same_v<T, SliderContainer>,
                      "slider_container_init() can only be used on "
                      "SliderContainer builders");
        node->set_label_text(label_text);
        node->set_slider_step(step);
        node->set_slider_min(min);
        node->set_slider_max(max);
        node->set_slider_value(value->get());
        value->connect_slider(get());
        node->connect_to_slider(callable);
        return *this;
    }

    static NodeBuilder<T> create(const String &name, Node *parent = nullptr)
    {
        static_assert(std::is_base_of_v<Node, T>,
                      "create() can only be used on Node builders");
        T *node = memnew(T);
        if (parent)
            parent->add_child(node);

        NodeBuilder<T> builder(node);

        return builder.call(&Node::set_name, name);
    }

    static NodeBuilder<VBoxContainer>
    create_scroll_container(const String &name)
    {
        static_assert(std::is_same_v<ScrollContainer, T>,
                      "create_scroll_container() can only be used on "
                      "ScrollContainer builders");

        T *node = memnew(T);
        // no parent here usually
        NodeBuilder<T> builder(node);

        builder.call(&Node::set_name, name);
        builder.call(&Control::set_custom_minimum_size, Vector2(300, 400));
        builder.call(&Control::set_v_size_flags, Control::SIZE_EXPAND_FILL);
        builder.call(&Control::set_h_size_flags, Control::SIZE_EXPAND_FILL);
        builder.call(&ScrollContainer::set_horizontal_scroll_mode,
                     ScrollContainer::SCROLL_MODE_DISABLED);

        return builder.add_child<VBoxContainer>();
    }

    template <typename C> NodeBuilder<T> &remove_child(NodeBuilder<C> &builder)
    {
        static_assert(std::is_base_of_v<Node, C>,
                      "remove_child() can only be used on Node builders");
        Node *child = builder.get();
        if (child && child->get_parent() == node)
        {
            child->queue_free();
        }
        return *this;
    }

    template <typename C> NodeBuilder<T> &try_remove_child(C *child)
    {
        static_assert(std::is_base_of_v<Node, C>,
                      "remove_child() can only be used on Node children");
        if (child)
        {
            if (child->get_parent() == node)
            {
                child->queue_free();
            }
        }
        return *this;
    }

    NodeBuilder<T> &clear_children()
    {
        TypedArray<Node> children = node->get_children();
        for (int i = 0; i < children.size(); i++)
        {
            Node *child = Object::cast_to<Node>(children[i]);
            if (child)
            {
                child->queue_free();
            }
        }
        return *this;
    }

    T *get() const { return node; }
    operator T *() const { return node; }
};