#[compute]
#version 450

layout(local_size_x = 16, local_size_y = 16, local_size_z = 1) in;

layout(binding = 0, set = 0) uniform sampler2D input_image;
layout(rgba16f, binding = 1, set = 0) uniform image2D output_image;

layout(push_constant, std430) uniform Params 
{
    vec2 raster_size;
} params;

float luminance(vec3 c)
{
    return dot(c, vec3(0.2126, 0.7152, 0.0722));
}

void main()
{
    ivec2 pixel = ivec2(gl_GlobalInvocationID.xy);
    vec2 size = params.raster_size;

    if(pixel.x >= size.x || pixel.y >= size.y) return;

    vec2 uv = pixel / size;
    vec2 texel = 1. / vec2(size);

    // -1 -1, c00 
    // 0 -1, c10
    // 1 -1, c20
    // -1 0, c01
    // 0 0, c11
    // 1 0, c21
    // -1 1, c02
    // 0 1, c12
    // 1 1, c22
    vec2 uv00 = clamp(uv + vec2(-1.0, -1.0) * texel, vec2(0.0), vec2(1.0));
    vec2 uv10 = clamp(uv + vec2( 0.0, -1.0) * texel, vec2(0.0), vec2(1.0));
    vec2 uv20 = clamp(uv + vec2( 1.0, -1.0) * texel, vec2(0.0), vec2(1.0));
    vec2 uv01 = clamp(uv + vec2(-1.0,  0.0) * texel, vec2(0.0), vec2(1.0));
    vec2 uv11 = clamp(uv + vec2( 0.0,  0.0) * texel, vec2(0.0), vec2(1.0));
    vec2 uv21 = clamp(uv + vec2( 1.0,  0.0) * texel, vec2(0.0), vec2(1.0));
    vec2 uv02 = clamp(uv + vec2(-1.0,  1.0) * texel, vec2(0.0), vec2(1.0));
    vec2 uv12 = clamp(uv + vec2( 0.0,  1.0) * texel, vec2(0.0), vec2(1.0));
    vec2 uv22 = clamp(uv + vec2( 1.0,  1.0) * texel, vec2(0.0), vec2(1.0));

    vec3 c00 = texture(input_image, uv00).rgb;
    vec3 c10 = texture(input_image, uv10).rgb;
    vec3 c20 = texture(input_image, uv20).rgb;
    vec3 c01 = texture(input_image, uv01).rgb;
    vec3 c11 = texture(input_image, uv11).rgb;
    vec3 c21 = texture(input_image, uv21).rgb;
    vec3 c02 = texture(input_image, uv02).rgb;
    vec3 c12 = texture(input_image, uv12).rgb;
    vec3 c22 = texture(input_image, uv22).rgb;

    float l00 = luminance(c00);
    float l10 = luminance(c10);
    float l20 = luminance(c20);
    float l01 = luminance(c01);
    float l11 = luminance(c11);
    float l21 = luminance(c21);
    float l02 = luminance(c02);
    float l12 = luminance(c12);
    float l22 = luminance(c22);

    float sobel_x = (
        -1.0 * l00 + 0.0 * l10 + 1.0 * l20 +
        -2.0 * l01 + 0.0 * l11 + 2.0 * l21 +
        -1.0 * l02 + 0.0 * l12 + 1.0 * l22
    ) * 0.25;

    float sobel_y = (
        -1.0 * l00 + -2.0 * l10 + -1.0 * l20 +
        0.0 * l01 +  0.0 * l11 +  0.0 * l21 +
        1.0 * l02 +  2.0 * l12 +  1.0 * l22
    ) * 0.25;

    float sxx = sobel_x * sobel_x;
    float syy = sobel_y * sobel_y;
    float sxy = sobel_x * sobel_y;

    imageStore(output_image, pixel, vec4(sxx, syy, sxy, 1.0));
}