#[compute]
#version 450

layout(local_size_x = 16, local_size_y = 16, local_size_z = 1) in;

layout(binding = 0, set = 0) uniform sampler2D input_image;
layout(rgba16f, binding = 1, set = 0) uniform image2D output_image;

layout(push_constant, std430) uniform Params
{
    vec2 input_size;
    vec2 output_size;
} params;

void main()
{
    ivec2 pixel = ivec2(gl_GlobalInvocationID.xy);
    vec2 out_size = params.output_size;

    if(pixel.x >= out_size.x || pixel.y >= out_size.y) return;

    vec2 uv = (vec2(pixel) + .5) / out_size;
    vec2 texel = 1. / params.input_size;

    // 2x2 box filter downsample
    vec3 sum = vec3(0.);
    sum += texture(input_image, uv + vec2(-0.25, -0.25) * texel).rgb;
    sum += texture(input_image, uv + vec2( 0.25, -0.25) * texel).rgb;
    sum += texture(input_image, uv + vec2(-0.25,  0.25) * texel).rgb;
    sum += texture(input_image, uv + vec2( 0.25,  0.25) * texel).rgb;

    imageStore(output_image, pixel, vec4(sum * 0.25, 1.));
}