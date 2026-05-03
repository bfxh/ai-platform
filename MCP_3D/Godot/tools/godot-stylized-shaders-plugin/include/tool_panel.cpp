#include "tool_panel.hpp"
#include "bloom_shader.hpp"
#include "crt_shader.hpp"
#include "effect_array.hpp"
#include "ext/callable_lambda.hpp"
#include "godot_cpp/classes/check_button.hpp"
#include "godot_cpp/classes/directional_light3d.hpp"
#include "godot_cpp/classes/h_box_container.hpp"
#include "godot_cpp/classes/v_box_container.hpp"
#include "godot_cpp/core/error_macros.hpp"
#include "godot_cpp/variant/color.hpp"
#include "godot_cpp/variant/utility_functions.hpp"
#include "manual_array_inspector.hpp"
#include "outline_shader.hpp"
#include "pixel_shader.hpp"
#include "slider_container.hpp"
#include "util/encapsulated_data.hpp"
#include "util/node_builder.hpp"
#include "vhs_shader.hpp"

#include <godot_cpp/classes/check_box.hpp>
#include <godot_cpp/classes/color_picker_button.hpp>
#include <godot_cpp/classes/display_server.hpp>
#include <godot_cpp/classes/editor_interface.hpp>
#include <godot_cpp/classes/editor_selection.hpp>
#include <godot_cpp/classes/editor_undo_redo_manager.hpp>
#include <godot_cpp/classes/engine.hpp>
#include <godot_cpp/classes/environment.hpp>
#include <godot_cpp/classes/h_separator.hpp>
#include <godot_cpp/classes/h_slider.hpp>
#include <godot_cpp/classes/node3d.hpp>
#include <godot_cpp/classes/object.hpp>
#include <godot_cpp/classes/random_number_generator.hpp>
#include <godot_cpp/classes/scene_tree.hpp>
#include <godot_cpp/classes/spin_box.hpp>
#include <godot_cpp/variant/callable.hpp>

void ToolPanel::_bind_methods()
{
    ClassDB::bind_method(D_METHOD("_on_cel_toggled"),
                         &ToolPanel::_on_cel_toggled);
    ClassDB::bind_method(D_METHOD("_on_outline_toggled"),
                         &ToolPanel::_on_outline_toggled);
    ClassDB::bind_method(D_METHOD("_on_invert_toggled"),
                         &ToolPanel::_on_invert_toggled);
    ClassDB::bind_method(D_METHOD("_on_crt_toggled"),
                         &ToolPanel::_on_crt_toggled);
    ClassDB::bind_method(D_METHOD("_on_dither_toggled"),
                         &ToolPanel::_on_dither_toggled);
    ClassDB::bind_method(D_METHOD("_on_pixel_toggled"),
                         &ToolPanel::_on_pixel_toggled);
    ClassDB::bind_method(D_METHOD("_on_vhs_toggled"),
                         &ToolPanel::_on_vhs_toggled);
    ClassDB::bind_method(D_METHOD("_on_bloom_toggled"),
                         &ToolPanel::_on_bloom_toggled);
}

ToolPanel::ToolPanel()
    : m_posterize_container(NodeBuilder<SliderContainer>::create("Posterize")),
      m_dither_container(NodeBuilder<SliderContainer>::create("Dither")),
      m_outline_container(
          NodeBuilder<ScrollContainer>::create_scroll_container("Outline")),
      m_crt_container(
          NodeBuilder<ScrollContainer>::create_scroll_container("CRT")),
      m_pixel_container(NodeBuilder<HBoxContainer>::create("Pixelize")),
      m_vhs_container(
          NodeBuilder<ScrollContainer>::create_scroll_container("VHS")),
      m_bloom_container(
          NodeBuilder<ScrollContainer>::create_scroll_container("Bloom")),
      m_kuwahara_container(
          NodeBuilder<ScrollContainer>::create_scroll_container("Kuwahara"))
{
}

ToolPanel::~ToolPanel() {}

void ToolPanel::_ready()
{
    /// Initialize effects
    m_effect_arr.instantiate();
    m_invert.instantiate();
    m_outline.instantiate();
    m_cel.instantiate();
    m_crt.instantiate();
    m_dither.instantiate();
    m_pixel.instantiate();
    m_vhs.instantiate();
    m_bloom.instantiate();
    m_kuwahara.instantiate();

    /// Get UI nodes
    // ApplyToContainer
    m_apply_option_btn =
        get_node<OptionButton>("ApplyToContainer/OptionButton");
    // ToggleContainer
    m_cel_toggle = get_node<CheckButton>("ToggleContainer/CelToggle");
    m_outline_toggle = get_node<CheckButton>("ToggleContainer/OutlineToggle");
    m_invert_toggle = get_node<CheckButton>("ToggleContainer/InvertToggle");
    m_crt_toggle = get_node<CheckButton>("ToggleContainer/CRTToggle");
    m_dither_toggle = get_node<CheckButton>("ToggleContainer/DitherToggle");
    m_pixel_toggle = get_node<CheckButton>("ToggleContainer/PixelToggle");
    m_vhs_toggle = get_node<CheckButton>("ToggleContainer/VHSToggle");
    m_bloom_toggle = get_node<CheckButton>("ToggleContainer/BloomToggle");
    m_kuwahara_toggle = get_node<CheckButton>("ToggleContainer/KuwaharaToggle");

    // root
    m_array_inspector = get_node<ManualArrayInspector>("ArrayOrder");
    m_tab_container = get_node<TabContainer>("TabContainer");

    /// Check if "gotten" UI nodes even exist
    ERR_FAIL_COND_MSG(!m_apply_option_btn,
                      "ERROR: Could not find OptionButton node!");
    ERR_FAIL_COND_MSG(!m_cel_toggle, "ERROR: Could not find CelToggle node!");
    ERR_FAIL_COND_MSG(!m_outline_toggle,
                      "ERROR: Could not find OutlineToggle node!");
    ERR_FAIL_COND_MSG(!m_invert_toggle,
                      "ERROR: Could not find InvertToggle node!");
    ERR_FAIL_COND_MSG(!m_crt_toggle, "ERROR: Could not find CRTToggle node!");
    ERR_FAIL_COND_MSG(!m_dither_toggle,
                      "ERROR: Could not find DitherToggle node!");
    ERR_FAIL_COND_MSG(!m_pixel_toggle,
                      "ERROR: Could not find PixelToggle node!");
    ERR_FAIL_COND_MSG(!m_vhs_toggle, "ERROR: Could not find VHSToggle node!");
    ERR_FAIL_COND_MSG(!m_bloom_toggle,
                      "ERROR: Could not find BloomToggle node!");
    ERR_FAIL_COND_MSG(!m_kuwahara_toggle,
                      "ERROR: Could not find KuwaharaToggle node!");
    ERR_FAIL_COND_MSG(!m_bloom_toggle,
                      "ERROR: Could not find BloomToggle node!");
    ERR_FAIL_COND_MSG(!m_array_inspector,
                      "ERROR: Could not find ManualArrayInspector node!");
    ERR_FAIL_COND_MSG(!m_tab_container,
                      "ERROR: Could not find TabContainer node!");

    /// NodeBuilder object initialization, per effect
    setup_cel();
    setup_outline();
    setup_crt();
    setup_dither();
    setup_pixel();
    setup_vhs();
    setup_bloom();
    setup_kuwahara();

    m_array_inspector->set_effects(m_effect_arr->get_effects());

    /// Connect to signals
    m_cel_toggle->connect("toggled", Callable(this, "_on_cel_toggled"));
    m_outline_toggle->connect("toggled", Callable(this, "_on_outline_toggled"));
    m_invert_toggle->connect("toggled", Callable(this, "_on_invert_toggled"));
    m_crt_toggle->connect("toggled", Callable(this, "_on_crt_toggled"));
    m_dither_toggle->connect("toggled", Callable(this, "_on_dither_toggled"));
    m_pixel_toggle->connect("toggled", Callable(this, "_on_pixel_toggled"));
    m_vhs_toggle->connect("toggled", Callable(this, "_on_vhs_toggled"));
    m_bloom_toggle->connect("toggled", Callable(this, "_on_bloom_toggled"));
    m_kuwahara_toggle->connect(
        "toggled", callable_mp(this, &ToolPanel::_on_kuwahara_toggled));
    m_apply_option_btn->connect(
        "item_selected",
        callable_mp(this, &ToolPanel::_on_apply_option_selected));
    m_array_inspector->connect(
        "order_changed", create_custom_callable_lambda(
                             this,
                             [this](const TypedArray<BaseShader> &effects)
                             {
                                 m_effect_arr->set_effects(effects);
                                 reapply_compositor_effects("Reorder Effects");
                             }));
}

void ToolPanel::_process(double delta)
{
    if (Engine::get_singleton()->is_editor_hint())
    {
        EditorInterface *editor = EditorInterface::get_singleton();
        if (editor)
        {
            Node *current_scene = editor->get_edited_scene_root();

            if (current_scene != m_last_edited_scene_root)
            {
                m_last_edited_scene_root = current_scene;
                m_edited_scene_root = current_scene;
                m_scene_changed = true;
            }
        }

        if (m_scene_changed && m_edited_scene_root)
        {
            if (m_apply_option_btn)
            {
                m_apply_option_btn->clear();
            }

            m_camera3d = nullptr;
            m_world_environment = nullptr;
            m_camera3d_option_index = -1;
            m_world_environment_option_index = -1;

            find_nodes_recursive(m_edited_scene_root);

            if (m_apply_option_btn)
            {
                if (m_camera3d)
                {
                    Ref<Compositor> c3d_cmp = m_camera3d->get_compositor();
                    Ref<Compositor> wenv_cmp =
                        m_world_environment->get_compositor();
                    if (!c3d_cmp.is_valid())
                    {
                        c3d_cmp.instantiate();
                        m_camera3d->set_compositor(c3d_cmp);
                    }
                    if (!wenv_cmp.is_valid())
                    {
                        wenv_cmp.instantiate();
                        m_world_environment->set_compositor(wenv_cmp);
                    }

                    m_camera3d_compositor = c3d_cmp.ptr();
                    m_world_environment_compositor = wenv_cmp.ptr();

                    ERR_FAIL_COND_MSG(!m_camera3d_compositor,
                                      "ERROR: Camera3D compositor invalid!");
                    ERR_FAIL_COND_MSG(
                        !m_world_environment_compositor,
                        "ERROR: WorldEnvironment compositor invalid!");

                    m_camera3d_option_index =
                        m_apply_option_btn->get_item_count();
                    UtilityFunctions::print(
                        "Camera3D Option Index: " +
                        String::num(m_camera3d_option_index));
                    m_apply_option_btn->add_item("Camera3D",
                                                 m_camera3d_option_index);
                }
                if (m_world_environment)
                {
                    m_world_environment_option_index =
                        m_apply_option_btn->get_item_count();
                    UtilityFunctions::print(
                        "WEnv Option Index: " +
                        String::num(m_world_environment_option_index));
                    m_apply_option_btn->add_item(
                        "WorldEnvironment", m_world_environment_option_index);
                }
            }

            m_scene_changed = false;
        }
    }

    if (m_outline.is_valid())
        m_outline->m_dt->set(delta);
    if (m_vhs.is_valid())
        m_vhs->m_dt->set(m_vhs->m_dt->get() + delta);
}

void ToolPanel::_on_cel_toggled(bool toggled_on)
{
    effect_toggle<CelShader, SliderContainer>(
        "Posterize", m_cel, m_posterize_container, toggled_on);
}

void ToolPanel::_on_outline_toggled(bool toggled_on)
{
    effect_toggle<OutlineShader, VBoxContainer>(
        "Outline", m_outline, m_outline_container, toggled_on);
}

void ToolPanel::_on_invert_toggled(bool toggled_on)
{
    m_invert->set_enabled(toggled_on);
    if (toggled_on)
    {
        ADD_EFFECT(m_invert);
        UtilityFunctions::print("Invert toggled on");
    }
    else
    {
        REMOVE_EFFECT(m_invert);
        UtilityFunctions::print("Invert toggled off");
    }
    reapply_compositor_effects("Invert");
}

void ToolPanel::_on_crt_toggled(bool toggled_on)
{
    effect_toggle<CRTShader, VBoxContainer>("CRT", m_crt, m_crt_container,
                                            toggled_on);
}

void ToolPanel::_on_dither_toggled(bool toggled_on)
{
    effect_toggle<DitherShader, SliderContainer>(
        "Dither", m_dither, m_dither_container, toggled_on);
}

void ToolPanel::_on_pixel_toggled(bool toggled_on)
{
    effect_toggle<PixelShader, HBoxContainer>("Pixelize", m_pixel,
                                              m_pixel_container, toggled_on);
}

void ToolPanel::_on_vhs_toggled(bool toggled_on)
{
    effect_toggle<VHSShader, VBoxContainer>("VHS", m_vhs, m_vhs_container,
                                            toggled_on);
}

void ToolPanel::_on_bloom_toggled(bool toggled_on)
{
    effect_toggle<BloomShader, VBoxContainer>("Bloom", m_bloom,
                                              m_bloom_container, toggled_on);
}

void ToolPanel::_on_kuwahara_toggled(bool toggled_on)
{
    effect_toggle<KuwaharaShader, VBoxContainer>(
        "Kuwahara", m_kuwahara, m_kuwahara_container, toggled_on);
}

void ToolPanel::setup_cel()
{
    m_posterize_container.slider_container_init(
        "Levels", 1.0, 2.0, 32.0, m_cel->m_levels,
        encapsulated_callable(float, m_cel, m_levels));
    notify_with_check();
}

void ToolPanel::setup_outline()
{
    auto width_container =
        m_outline_container.add_child<SliderContainer>().slider_container_init(
            "Outline Width", 0.001, 0.0, 0.01, m_outline->m_outline_width,
            encapsulated_callable(float, m_outline, m_outline_width));

    auto mul_container =
        m_outline_container.add_child<SliderContainer>().slider_container_init(
            "Outline Width Step", 0.01, 0.01, 1.0, m_outline->m_outline_mul,
            encapsulated_callable(float, m_outline, m_outline_mul));

    m_outline_container.add_child<CheckBox>()
        .call(&CheckBox::set_text, "Jitter")
        .call(&CheckBox::connect, "toggled",
              encapsulated_callable(bool, m_outline, m_jitter_toggle), 0u);

    auto amp_container =
        m_outline_container.add_child<SliderContainer>().slider_container_init(
            "Jitter Amplitude", 0.01, 0.01, 0.1, m_outline->m_jitter_amp,
            encapsulated_callable(float, m_outline, m_jitter_amp));
    auto freq_container =
        m_outline_container.add_child<SliderContainer>().slider_container_init(
            "Jitter Frequency", 0.01, 0.01, 0.1, m_outline->m_jitter_freq,
            encapsulated_callable(float, m_outline, m_jitter_freq));
    auto color_container = m_outline_container.add_child<HBoxContainer>();

    color_container.add_child<Label>().call(&Label::set_text,
                                            "Open Color Picker");
    color_container.add_child<ColorPickerButton>()
        .call(&ColorPickerButton::set_text, "Color Picker Button")
        .call(&ColorPickerButton::connect, "color_changed",
              callable_mp(m_outline.ptr(), &OutlineShader::set_outline_color),
              0u);
    notify_with_check();
}

void ToolPanel::setup_crt()
{
    m_crt_container.call(&VBoxContainer::set_name, "CRT");
    auto curvature_container =
        m_crt_container.add_child<SliderContainer>().slider_container_init(
            "Curvature", 1.0, 0.0, 10.0, m_crt->m_curvature,
            encapsulated_callable(float, m_crt, m_curvature));
    auto vignette_mul_container =
        m_crt_container.add_child<SliderContainer>().slider_container_init(
            "Vignette Multiplier", 1.0, 0.0, 10.0, m_crt->m_vignette_mul,
            encapsulated_callable(float, m_crt, m_vignette_mul));
    auto brightness_container =
        m_crt_container.add_child<SliderContainer>().slider_container_init(
            "Brightness", 0.1, 0.0, 10.0, m_crt->m_brightness,
            encapsulated_callable(float, m_crt, m_brightness));
    notify_with_check();
}

void ToolPanel::setup_dither()
{
    m_dither_container.slider_container_init(
        "Gamma Correction Amount", 0.1, 0.0, 10.0, m_dither->m_gamma_correction,
        encapsulated_callable(float, m_dither, m_gamma_correction));
    notify_with_check();
}

void ToolPanel::setup_pixel()
{
    auto label = m_pixel_container.add_child<Label>().call(
        &Label::set_text, "Target Width and Height");

    auto width_spin_box =
        m_pixel_container.add_child<SpinBox>()
            .call(&SpinBox::set_step, 1.0)
            .call(&SpinBox::set_min, 1.0)
            .call(&SpinBox::set_max,
                  static_cast<double>(
                      DisplayServer::get_singleton()->screen_get_size().x))
            .call(&SpinBox::set_value,
                  static_cast<double>(m_pixel->target_width->get()))
            .call(&SpinBox::connect, "value_changed",
                  encapsulated_callable(int, m_pixel, target_width), 0u);

    auto height_spin_box =
        m_pixel_container.add_child<SpinBox>()
            .call(&SpinBox::set_step, 1.0)
            .call(&SpinBox::set_min, 1.0)
            .call(&SpinBox::set_max,
                  static_cast<double>(
                      DisplayServer::get_singleton()->screen_get_size().y))
            .call(&SpinBox::set_value,
                  static_cast<double>(m_pixel->target_height->get()))
            .call(&SpinBox::connect, "value_changed",
                  encapsulated_callable(int, m_pixel, target_height), 0u);
    notify_with_check();
}

// TODO: refactor this function and get rid of the static raw pointers, 200
// lines just for this currently lol
void ToolPanel::setup_vhs()
{
    m_vhs_container.call(&VBoxContainer::set_name, "VHS");

    auto scanline_checkbox =
        m_vhs_container.add_child<CheckBox>()
            .call(&CheckBox::set_text, "Enable Scanlines")
            .call(&CheckBox::connect, "toggled",
                  create_custom_callable_lambda(
                      this,
                      [this](bool toggled_on)
                      {
                          m_vhs->m_scanline_enabled->set(toggled_on);

                          if (toggled_on)
                          {
                              auto scanline_blend_container =
                                  m_vhs_container.add_child<SliderContainer>()
                                      .slider_container_init(
                                          "Scanline Blend Factor", 0.01, 0.0,
                                          1.0, m_vhs->m_scanline_blend_factor,
                                          encapsulated_callable(
                                              float, m_vhs,
                                              m_scanline_blend_factor));

                              m_scanline_blend = scanline_blend_container.get();

                              auto scanline_height_container =
                                  m_vhs_container.add_child<SliderContainer>()
                                      .slider_container_init(
                                          "Scanline Height", 1.0, 1.0, 20.0,
                                          m_vhs->m_scanline_height,
                                          encapsulated_callable(
                                              float, m_vhs, m_scanline_height));

                              m_scanline_height =
                                  scanline_height_container.get();

                              auto scanline_intensity_container =
                                  m_vhs_container.add_child<SliderContainer>()
                                      .slider_container_init(
                                          "Scanline Intensity", 0.01, 0.0, 1.0,
                                          m_vhs->m_scanline_intensity,
                                          encapsulated_callable(
                                              float, m_vhs,
                                              m_scanline_intensity));

                              m_scanline_intensity =
                                  scanline_intensity_container.get();

                              auto scanline_scroll_container =
                                  m_vhs_container.add_child<SliderContainer>()
                                      .slider_container_init(
                                          "Scanline Scroll Speed", 1.0, 0.0,
                                          100.0, m_vhs->m_scanline_scroll_speed,
                                          encapsulated_callable(
                                              float, m_vhs,
                                              m_scanline_scroll_speed));

                              m_scanline_scroll =
                                  scanline_scroll_container.get();
                          }
                          else
                          {
                              if (m_scanline_blend)
                              {
                                  m_scanline_blend->queue_free();
                                  m_scanline_blend = nullptr;
                              }
                              if (m_scanline_height)
                              {
                                  m_scanline_height->queue_free();
                                  m_scanline_height = nullptr;
                              }
                              if (m_scanline_intensity)
                              {
                                  m_scanline_intensity->queue_free();
                                  m_scanline_intensity = nullptr;
                              }
                              if (m_scanline_scroll)
                              {
                                  m_scanline_scroll->queue_free();
                                  m_scanline_scroll = nullptr;
                              }
                          }
                          notify_with_check();
                      }),
                  0u);

    auto grain_checkbox =
        m_vhs_container.add_child<CheckBox>()
            .call(&CheckBox::set_text, "Enable Grain")
            .call(&CheckBox::connect, "toggled",
                  create_custom_callable_lambda(
                      this,
                      [this](bool toggled_on)
                      {
                          m_vhs->m_grain_enabled->set(toggled_on);

                          if (toggled_on)
                          {
                              auto grain_intensity_container =
                                  m_vhs_container.add_child<SliderContainer>()
                                      .slider_container_init(
                                          "Grain Intensity", 0.1, 0.0, 10.0,
                                          m_vhs->m_grain_intensity,
                                          encapsulated_callable(
                                              float, m_vhs, m_grain_intensity));
                              m_grain_intensity =
                                  grain_intensity_container.get();
                          }
                          else
                          {
                              if (m_grain_intensity)
                              {
                                  m_grain_intensity->queue_free();
                                  m_grain_intensity = nullptr;
                              }
                          }
                          notify_with_check();
                      }),
                  0u);

    auto vertical_band_checkbox =
        m_vhs_container.add_child<CheckBox>()
            .call(&CheckBox::set_text, "Enable Vertical Bands")
            .call(
                &CheckBox::connect, "toggled",
                create_custom_callable_lambda(
                    this,
                    [this](bool toggled_on)
                    {
                        m_vhs->m_vertical_band_enabled->set(toggled_on);

                        if (toggled_on)
                        {
                            auto vertical_band_speed_container =
                                m_vhs_container.add_child<SliderContainer>()
                                    .slider_container_init(
                                        "Vertical Band Speed", 0.01, 0.0, 5.0,
                                        m_vhs->m_vertical_band_speed,
                                        encapsulated_callable(
                                            float, m_vhs,
                                            m_vertical_band_speed));

                            m_vband_speed = vertical_band_speed_container.get();

                            auto vertical_band_height_container =
                                m_vhs_container.add_child<SliderContainer>()
                                    .slider_container_init(
                                        "Vertical Band Height", 0.001, 0.001,
                                        0.1, m_vhs->m_vertical_band_height,
                                        encapsulated_callable(
                                            float, m_vhs,
                                            m_vertical_band_height));

                            m_vband_height =
                                vertical_band_height_container.get();

                            auto vertical_band_intensity_container =
                                m_vhs_container.add_child<SliderContainer>()
                                    .slider_container_init(
                                        "Vertical Band Intensity", 0.01, 0.0,
                                        1.0, m_vhs->m_vertical_band_intensity,
                                        encapsulated_callable(
                                            float, m_vhs,
                                            m_vertical_band_intensity));

                            m_vband_intensity =
                                vertical_band_intensity_container.get();

                            auto vertical_band_choppiness_container =
                                m_vhs_container.add_child<SliderContainer>()
                                    .slider_container_init(
                                        "Vertical Band Choppiness", 0.01, 0.0,
                                        1.0, m_vhs->m_vertical_band_choppiness,
                                        encapsulated_callable(
                                            float, m_vhs,
                                            m_vertical_band_choppiness));

                            m_vband_choppiness =
                                vertical_band_choppiness_container.get();

                            auto vertical_band_static_container =
                                m_vhs_container.add_child<SliderContainer>()
                                    .slider_container_init(
                                        "Vertical Band Static Amount", 0.001,
                                        0.0, 0.1,
                                        m_vhs->m_vertical_band_static_amount,
                                        encapsulated_callable(
                                            float, m_vhs,
                                            m_vertical_band_static_amount));

                            m_vband_static =
                                vertical_band_static_container.get();

                            auto vertical_band_warp_container =
                                m_vhs_container.add_child<SliderContainer>()
                                    .slider_container_init(
                                        "Vertical Band Warp Factor", 0.001, 0.0,
                                        0.1, m_vhs->m_vertical_band_warp_factor,
                                        encapsulated_callable(
                                            float, m_vhs,
                                            m_vertical_band_warp_factor));

                            m_vband_warp = vertical_band_warp_container.get();
                        }
                        else
                        {
                            if (m_vband_speed)
                            {
                                m_vband_speed->queue_free();
                                m_vband_speed = nullptr;
                            }
                            if (m_vband_height)
                            {
                                m_vband_height->queue_free();
                                m_vband_height = nullptr;
                            }
                            if (m_vband_intensity)
                            {
                                m_vband_intensity->queue_free();
                                m_vband_intensity = nullptr;
                            }
                            if (m_vband_choppiness)
                            {
                                m_vband_choppiness->queue_free();
                                m_vband_choppiness = nullptr;
                            }
                            if (m_vband_static)
                            {
                                m_vband_static->queue_free();
                                m_vband_static = nullptr;
                            }
                            if (m_vband_warp)
                            {
                                m_vband_warp->queue_free();
                                m_vband_warp = nullptr;
                            }
                        }
                        notify_with_check();
                    }),
                0u);
    notify_with_check();
}

void ToolPanel::setup_bloom()
{
    m_bloom_container.call(&VBoxContainer::set_name, "Bloom");

    m_bloom_container.add_child<SliderContainer>().slider_container_init(
        "Threshold", 0.1, 0.0, 2.0, m_bloom->m_threshold,
        encapsulated_callable(float, m_bloom, m_threshold));
    m_bloom_container.add_child<SliderContainer>().slider_container_init(
        "Radius", 0.1, 0.1, 8.0, m_bloom->m_radius,
        encapsulated_callable(float, m_bloom, m_radius));
    m_bloom_container.add_child<SliderContainer>().slider_container_init(
        "Strength", 0.05, 0.0, 2.0, m_bloom->m_strength,
        encapsulated_callable(float, m_bloom, m_strength));
    notify_with_check();
}

void ToolPanel::setup_kuwahara()
{
    auto preset_box = m_kuwahara_container.add_child<HBoxContainer>();
    preset_box.add_child<Label>().call(&Label::set_text, "Preset");
    auto option_button = preset_box.add_child<OptionButton>();

    for (size_t i = 0; i < m_kuwahara->get_preset_configs().size(); ++i)
    {
        const auto &preset = m_kuwahara->get_preset_configs()[i];

        option_button.call(&OptionButton::add_item, preset.label_text, i);
    }

    option_button.call(
        &OptionButton::connect, "item_selected",
        callable_mp(m_kuwahara.ptr(), &KuwaharaShader::set_preset_as_selected),
        0U);

    m_kuwahara_container.add_child<HSeparator>();

    auto downsample_box = m_kuwahara_container.add_child<HBoxContainer>();
    downsample_box.add_child<Label>().call(&Label::set_text,
                                           "Downsample Factor");
    downsample_box.add_child<SpinBox>()
        .call(&SpinBox::set_step, 1.0)
        .call(&SpinBox::set_min, 1.0)
        .call(&SpinBox::set_max, 12.0)
        .call(&SpinBox::set_value,
              static_cast<double>(m_kuwahara->downsample_factor->get()))
        .call(&SpinBox::connect, "value_changed",
              encapsulated_callable(int, m_kuwahara, downsample_factor), 0u);

    m_kuwahara_container.add_child<SliderContainer>().slider_container_init(
        "Radius", 1.0, 3.0, 7.0, m_kuwahara->radius,
        encapsulated_callable(float, m_kuwahara, radius));

    m_kuwahara_container.add_child<SliderContainer>().slider_container_init(
        "Kernel Size", 1.0, 7.0, 15.0, m_kuwahara->kernel_size,
        encapsulated_callable(float, m_kuwahara, kernel_size));

    m_kuwahara_container.add_child<SliderContainer>().slider_container_init(
        "Alpha", 0.1, 0.1, 1.0, m_kuwahara->alpha,
        encapsulated_callable(float, m_kuwahara, alpha));

    m_kuwahara_container.add_child<SliderContainer>().slider_container_init(
        "Sectors", 1.0, 4.0, 8.0, m_kuwahara->sectors,
        encapsulated_callable(float, m_kuwahara, sectors));

    m_kuwahara_container.add_child<SliderContainer>().slider_container_init(
        "Sharpness", 1.0, 6.0, 12.0, m_kuwahara->sharpness,
        encapsulated_callable(float, m_kuwahara, sharpness));

    notify_with_check();
}

void ToolPanel::set_edited_scene_root(Node *edited_scene_root)
{
    m_edited_scene_root = edited_scene_root;
}

void ToolPanel::find_nodes_recursive(Node *node)
{
    if (!node)
        return;

    if (Camera3D *c3d = Object::cast_to<Camera3D>(node))
    {
        m_camera3d = c3d;
        UtilityFunctions::print("Found Camera3D node in edited scene!");
    }

    if (WorldEnvironment *w_env = Object::cast_to<WorldEnvironment>(node))
    {
        m_world_environment = w_env;
        UtilityFunctions::print("Found WorldEnvironment node in edited scene!");
    }

    for (int i = 0; i < node->get_child_count(); i++)
    {
        find_nodes_recursive(node->get_child(i));
    }
}

void ToolPanel::_on_apply_option_selected(int index)
{
    EditorInterface *editor = EditorInterface::get_singleton();
    if (!editor)
        return;

    EditorUndoRedoManager *undo_redo = editor->get_editor_undo_redo();
    if (!undo_redo)
        return;

    if (index == m_camera3d_option_index && m_camera3d_compositor)
    {
        TypedArray<CompositorEffect> effects = m_effect_arr->get_effects();

        undo_redo->create_action("Apply Compositor Effects to Camera3D");
        undo_redo->add_do_method(m_camera3d_compositor,
                                 "set_compositor_effects", effects);
        undo_redo->add_undo_method(
            m_camera3d_compositor, "set_compositor_effects",
            m_camera3d_compositor->get_compositor_effects());

        if (m_world_environment_compositor)
        {
            undo_redo->add_do_method(m_world_environment_compositor,
                                     "set_compositor_effects",
                                     TypedArray<CompositorEffect>());
        }

        undo_redo->commit_action();
    }
    else if (index == m_world_environment_option_index &&
             m_world_environment_compositor)
    {
        TypedArray<CompositorEffect> effects = m_effect_arr->get_effects();

        undo_redo->create_action(
            "Apply Compositor Effects to WorldEnvironment");
        undo_redo->add_do_method(m_world_environment_compositor,
                                 "set_compositor_effects", effects);
        undo_redo->add_undo_method(
            m_world_environment_compositor, "set_compositor_effects",
            m_world_environment_compositor->get_compositor_effects());

        if (m_camera3d_compositor)
        {
            undo_redo->add_do_method(m_camera3d_compositor,
                                     "set_compositor_effects",
                                     TypedArray<CompositorEffect>());
        }

        undo_redo->commit_action();
    }

    editor->mark_scene_as_unsaved();
}

// Function generated with ChatGPT due to time constraints
void ToolPanel::reapply_compositor_effects(const String &action_name)
{
    EditorInterface *editor = EditorInterface::get_singleton();
    if (!editor || !m_apply_option_btn)
        return;

    EditorUndoRedoManager *undo_redo = editor->get_editor_undo_redo();
    if (!undo_redo)
        return;

    int32_t selected_idx = m_apply_option_btn->get_selected();

    if (selected_idx == m_camera3d_option_index && m_camera3d_compositor)
    {
        TypedArray<CompositorEffect> old_effects =
            m_camera3d_compositor->get_compositor_effects();
        TypedArray<CompositorEffect> new_effects = m_effect_arr->get_effects();

        undo_redo->create_action(action_name);
        undo_redo->add_do_method(m_camera3d_compositor,
                                 "set_compositor_effects", new_effects);
        undo_redo->add_undo_method(m_camera3d_compositor,
                                   "set_compositor_effects", old_effects);

        // Keep references alive
        undo_redo->add_do_reference(m_camera3d_compositor);
        undo_redo->add_undo_reference(m_camera3d_compositor);

        if (m_world_environment_compositor)
        {
            undo_redo->add_do_method(m_world_environment_compositor,
                                     "set_compositor_effects",
                                     TypedArray<CompositorEffect>());
            undo_redo->add_do_reference(m_world_environment_compositor);
            undo_redo->add_undo_reference(m_world_environment_compositor);
        }

        undo_redo->commit_action();

        // Apply immediately
        m_camera3d_compositor->set_compositor_effects(new_effects);
        if (m_world_environment_compositor)
        {
            m_world_environment_compositor->set_compositor_effects(
                TypedArray<CompositorEffect>());
        }
    }
    else if (selected_idx == m_world_environment_option_index &&
             m_world_environment_compositor)
    {
        TypedArray<CompositorEffect> old_effects =
            m_world_environment_compositor->get_compositor_effects();
        TypedArray<CompositorEffect> new_effects = m_effect_arr->get_effects();

        undo_redo->create_action(action_name);
        undo_redo->add_do_method(m_world_environment_compositor,
                                 "set_compositor_effects", new_effects);
        undo_redo->add_undo_method(m_world_environment_compositor,
                                   "set_compositor_effects", old_effects);

        // Keep references alive
        undo_redo->add_do_reference(m_world_environment_compositor);
        undo_redo->add_undo_reference(m_world_environment_compositor);

        if (m_camera3d_compositor)
        {
            undo_redo->add_do_method(m_camera3d_compositor,
                                     "set_compositor_effects",
                                     TypedArray<CompositorEffect>());
            undo_redo->add_do_reference(m_camera3d_compositor);
            undo_redo->add_undo_reference(m_camera3d_compositor);
        }

        undo_redo->commit_action();

        // Apply immediately
        m_world_environment_compositor->set_compositor_effects(new_effects);
        if (m_camera3d_compositor)
        {
            m_camera3d_compositor->set_compositor_effects(
                TypedArray<CompositorEffect>());
        }
    }

    editor->mark_scene_as_unsaved();
}