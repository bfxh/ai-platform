#include <godot_cpp/variant/callable_custom.hpp>
#include <godot_cpp/variant/callable_method_pointer.hpp>
#include <utility>

// Credits:
// https://github.com/IvanInventor/godot-cppscript-template/blob/test/callable_lambda_via_custom_expandpack/src/callable_lambda.hpp

namespace impl {

using namespace godot;

// Func traits
template <typename T>
struct function_traits : public function_traits<decltype(&T::operator())>
{};

template <typename ClassType, typename ReturnType, typename... Args>
struct function_traits<ReturnType(ClassType::*)(Args...) const>
{
    using result_type = ReturnType;
    using arg_tuple = std::tuple<Args...>;
    static constexpr auto arity = sizeof...(Args);
};


template<class T>
struct ExpandPack;

template<class ...Args>
struct ExpandPack<std::tuple<Args...>> {
	template<class L, std::size_t ...Is>
	_FORCE_INLINE_ static void call(L&& l, const Variant **p_arguments, int p_argcount, Variant &r_return_value, GDExtensionCallError &r_call_error, IndexSequence<Is...>) {
#ifdef DEBUG_ENABLED
	if ((size_t)p_argcount > sizeof...(Args)) {
		r_call_error.error = GDEXTENSION_CALL_ERROR_TOO_MANY_ARGUMENTS;
		r_call_error.expected = (int32_t)sizeof...(Args);
		return;
	}

	if ((size_t)p_argcount < sizeof...(Args)) {
		r_call_error.error = GDEXTENSION_CALL_ERROR_TOO_FEW_ARGUMENTS;
		r_call_error.expected = (int32_t)sizeof...(Args);
		return;
	}
#endif

	r_call_error.error = GDEXTENSION_CALL_OK;

#ifdef DEBUG_METHODS_ENABLED
	l(VariantCasterAndValidate<Args>::cast(p_arguments, Is, r_call_error)...);
#else
	l(VariantCaster<Args>::cast(*p_arguments[Is])...);
#endif
		(void)(p_arguments); // Avoid warning.
	}

};

// CallableCustom
template<class Lambda>
class CallableCustomLambda : public CallableCustom {
	Lambda l;
	Object* instance;

public:
	CallableCustomLambda(Object* inst, Lambda&& new_l) : instance(inst), l(new_l) {};
	virtual ~CallableCustomLambda() = default;

	uint32_t hash() const override {
		return (intptr_t)this;
	}

	String get_as_text() const override {
		return "CallableCustomLambda";
	}

	virtual CompareEqualFunc get_compare_equal_func() const override {
		return [](const CallableCustom* a, const CallableCustom* b) {
			return a->hash() == b->hash();
		};
	}

	CompareLessFunc get_compare_less_func() const override {
		return [](const CallableCustom* a, const CallableCustom* b) {
			return a->hash() < b->hash();
		};
	}

	bool is_valid() const override {
		return instance != nullptr;
	}

	ObjectID get_object() const override {
		return ObjectID();
	}

	void call(const Variant **p_arguments, int p_argcount, Variant &r_return_value, GDExtensionCallError &r_call_error) const override {
		using traits = function_traits<Lambda>;
		using E = ExpandPack<typename traits::arg_tuple>;
		E::call(l, p_arguments, p_argcount, r_return_value, r_call_error, BuildIndexSequence<traits::arity>());
	}
};
}

// Binding
template <class Lambda>
godot::Callable create_custom_callable_lambda(godot::Object* p_instance, Lambda&& l) {
	auto* ccl = memnew(impl::CallableCustomLambda(p_instance, std::forward<Lambda>(l)));
	return godot::Callable(ccl);
}


