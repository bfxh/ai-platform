#[compute]
#version 450

layout(local_size_x = 16, local_size_y = 16, local_size_z = 1) in;

layout(rgba16f, binding = 0, set = 0) uniform image2D color_image;

layout(push_constant, std430) uniform Params
{
    vec2 raster_size;
    float levels;
} params;

const vec3 LUMINANCE = vec3(0.299, 0.587, 0.114);

void main()
{
    ivec2 pixel = ivec2(gl_GlobalInvocationID.xy);
    vec2 size = params.raster_size;
    
    if(pixel.x >= size.x || pixel.y >= size.y) return;

    // vec2 uv = pixel / size;

    vec3 screen_color = imageLoad(color_image, pixel).rgb;
    float lum = dot(screen_color, LUMINANCE);
    float step_size = 1. / params.levels;
    float band = floor(lum / step_size) * step_size;

    vec4 cel_color = vec4(normalize(screen_color) * band, 1.);
    imageStore(color_image, pixel, cel_color);
}