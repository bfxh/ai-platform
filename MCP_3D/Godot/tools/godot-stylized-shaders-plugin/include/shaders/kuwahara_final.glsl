#[compute]
#version 450

layout(local_size_x = 16, local_size_y = 16, local_size_z = 1) in;

layout(rgba16f, binding = 0, set = 0) uniform image2D base_image;
layout(binding = 1, set = 0) uniform sampler2D prev_image;

layout(push_constant, std430) uniform Params 
{
    vec2 raster_size;
} params;

void main()
{
    ivec2 pixel = ivec2(gl_GlobalInvocationID.xy);
    vec2 size = params.raster_size;

    if(pixel.x >= size.x || pixel.y >= size.y) return;

    vec2 uv = pixel / size;

    vec4 prev_color = texture(prev_image, uv);
    imageStore(base_image, pixel, prev_color);
}