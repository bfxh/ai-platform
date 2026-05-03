#[compute]
#version 450

layout(local_size_x = 16, local_size_y = 16, local_size_z = 1) in;

layout(rgba16f, binding = 0, set = 0) uniform image2D color_image;

layout(push_constant, std430) uniform Params 
{
	vec2 raster_size;
    float target_width;
    float target_height;
} params;

void main()
{
    ivec2 pixel = ivec2(gl_GlobalInvocationID.xy);
    vec2 size = params.raster_size;

    if(pixel.x >= size.x || pixel.y >= size.y) return;

    vec2 uv = pixel / size;
    vec2 target_resolution = vec2(params.target_width, params.target_height);
    vec2 pixelized_uv = floor(uv * target_resolution) / target_resolution;

    vec4 screen_tex = imageLoad(color_image, ivec2(pixelized_uv * params.raster_size));
    imageStore(color_image, pixel, screen_tex);
}