#[compute]
#version 450

// from https://learnopengl.com/Guest-Articles/2022/Phys.-Based-Bloom

layout(local_size_x = 16, local_size_y = 16, local_size_z = 1) in;

layout(binding = 0, set = 0) uniform sampler2D input_image;
layout(rgba16f, binding = 1, set = 0) uniform image2D output_image;

layout(push_constant, std430) uniform Params 
{ 
    vec2 raster_size;
    float threshold;
} params;

const vec3 LUMA = vec3(0.03125, 0.0625, 0.125);

// from: https://catlikecoding.com/unity/tutorials/advanced-rendering/bloom/
vec3 prefilter(vec3 c, float threshold)
{
    float brightness = max(c.r, max(c.g, c.b));
    float contribution = max(0, brightness - threshold);
    contribution /= max(brightness, 0.00001);
    return c * contribution;
}

void main()
{
    ivec2 pixel = ivec2(gl_GlobalInvocationID.xy);
    vec2 size = params.raster_size;

    if (pixel.x >= size.x || pixel.y >= size.y)
        return;

    vec2 uv = vec2(pixel / size);
    vec2 texel = 1. / vec2(size);
    float x = texel.x;
    float y = texel.y;

    // Take 13 samples around current texel:
    // a - b - c
    // - j - k -
    // d - e - f
    // - l - m -
    // g - h - i
    // === ('e' is the current texel) ===
    vec3 a = texture(input_image, vec2(uv.x - 2 * x, uv.y + 2 * y)).rgb;
    vec3 b = texture(input_image, vec2(uv.x, uv.y + 2 * y)).rgb;
    vec3 c = texture(input_image, vec2(uv.x + 2 * x, uv.y + 2 * y)).rgb;
    vec3 d = texture(input_image, vec2(uv.x - 2 * x, uv.y)).rgb;
    vec3 e = texture(input_image, vec2(uv.x, uv.y)).rgb;
    vec3 f = texture(input_image, vec2(uv.x + 2 * x, uv.y)).rgb;
    vec3 g = texture(input_image, vec2(uv.x - 2 * x, uv.y - 2 * y)).rgb;
    vec3 h = texture(input_image, vec2(uv.x, uv.y - 2 * y)).rgb;
    vec3 i = texture(input_image, vec2(uv.x + 2 * x, uv.y - 2 * y)).rgb;
    vec3 j = texture(input_image, vec2(uv.x - x, uv.y + y)).rgb;
    vec3 k = texture(input_image, vec2(uv.x + x, uv.y + y)).rgb;
    vec3 l = texture(input_image, vec2(uv.x - x, uv.y - y)).rgb;
    vec3 m = texture(input_image, vec2(uv.x + x, uv.y - y)).rgb;

    // Apply weighted distribution:
    // 0.5 + 0.125 + 0.125 + 0.125 + 0.125 = 1
    // a,b,d,e * 0.125
    // b,c,e,f * 0.125
    // d,e,g,h * 0.125
    // e,f,h,i * 0.125
    // j,k,l,m * 0.5
    // This shows 5 square areas that are being sampled. But some of them
    // overlap, so to have an energy preserving downsample we need to make some
    // adjustments. The weights are the distributed, so that the sum of j,k,l,m
    // (e.g.) contribute 0.5 to the final color output. The code below is
    // written to effectively yield this sum. We get: 0.125*5 + 0.03125*4 +
    // 0.0625*4 = 1
    vec3 downsampled_color = e * LUMA.b;
    downsampled_color += (a + c + g + i) * LUMA.r;
    downsampled_color += (b + d + f + h) * LUMA.g;
    downsampled_color += (j + k + l + m) * LUMA.b;
    downsampled_color = max(downsampled_color, vec3(0.00001));
    downsampled_color = prefilter(downsampled_color, params.threshold);

    imageStore(output_image, pixel, vec4(downsampled_color, 1.));
}