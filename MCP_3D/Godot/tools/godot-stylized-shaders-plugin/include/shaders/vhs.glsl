#[compute]
#version 450

// credits: https://www.shadertoy.com/view/dtGyzR

struct ScanlineSettings
{
    float blend_factor;
    float height;
    float intensity;
    float scroll_speed;
    float enabled; // 20
};

struct GrainSettings
{
    float intensity;
    float enabled; // 10
};

struct VerticalBandSettings
{
    float speed;
    float height;
    float intensity;
    float choppiness;
    float static_amount;
    float warp_factor;
    float enabled; // 28 
};
// 56 total ^

layout(local_size_x = 16, local_size_y = 16, local_size_z = 1) in;

layout(rgba16f, binding = 0, set = 0) uniform image2D color_image;

layout(push_constant, std430) uniform Params 
{
	vec2 raster_size;
    ScanlineSettings scanline_settings;
    GrainSettings grain_settings;
    VerticalBandSettings vertical_band_settings;
    float delta_time; // 68
    // + one float for padding, added in cpp push_constant array already
} params;

const vec3 SCANLINE_COLOR = vec3(1., 1., 1.); // i don't want the user to change this, sorry!
const vec2 SEED = vec2(12.9898, 78.233);

void main()
{
    ivec2 pixel = ivec2(gl_GlobalInvocationID.xy); // fragCoord on shadertoy
    vec2 size = params.raster_size; // iResolution on shadertoy

    if(pixel.x >= size.x || pixel.y >= size.y) return;

    vec2 uv = pixel / size;

    vec2 grain_seed = SEED + params.delta_time * .1;

    float scanline = sin((uv.y * size.y - params.delta_time * params.scanline_settings.scroll_speed) * (1. / params.scanline_settings.height));
    vec3 vhs_color = vec3(1.0); 
    if(params.scanline_settings.enabled == 1.0) vhs_color = SCANLINE_COLOR * scanline * params.scanline_settings.intensity;

    if(params.grain_settings.enabled == 1.0)
    {
        float grain = fract(sin(dot(pixel * uv, grain_seed)) * 43758.5453);
        vhs_color.x += grain * params.grain_settings.intensity;
        vhs_color.y += grain * params.grain_settings.intensity;    
        vhs_color.z += grain * params.grain_settings.intensity;
    }

    float band_pos = fract(params.delta_time * params.vertical_band_settings.speed);
    float band_noise = fract(sin(dot(uv * size, SEED)) * 43758.5453);

    if((abs(uv.y - band_pos) < params.vertical_band_settings.height) && params.vertical_band_settings.enabled == 1.0)
    {
        float random_static = band_noise * params.vertical_band_settings.choppiness;
        
        vhs_color.x += random_static * params.vertical_band_settings.static_amount;
        vhs_color.y += random_static * params.vertical_band_settings.static_amount;
        vhs_color.z += random_static * params.vertical_band_settings.static_amount;

        uv.x += sin(uv.y * size.y * 10. + random_static) * params.vertical_band_settings.warp_factor;

        float adjusted_intensity = params.vertical_band_settings.intensity * (1. - random_static);
        vhs_color.x *= 1. + adjusted_intensity;
        vhs_color.y *= 1. + adjusted_intensity;    
        vhs_color.z *= 1. + adjusted_intensity;
    }

    vec3 color = imageLoad(color_image, ivec2(uv * size)).rgb;
    vec3 final_color = mix(color, vhs_color, params.scanline_settings.blend_factor);

    imageStore(color_image, pixel, vec4(final_color, 1.));
}
