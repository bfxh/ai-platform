#[compute]
#version 450

layout(local_size_x = 16, local_size_y = 16, local_size_z = 1) in;

layout(binding = 0, set = 0) uniform sampler2D input_image;
layout(binding = 1, set = 0) uniform sampler2D downsample_image;
layout(rgba16f, binding = 2, set = 0) uniform image2D output_image;

layout(push_constant, std430) uniform Params
{
    vec2 raster_size;
    float radius;
} params;

void main()
{
    ivec2 pixel = ivec2(gl_GlobalInvocationID.xy);
    vec2 size = params.raster_size;

    if (pixel.x >= size.x || pixel.y >= size.y)
        return;

    vec2 texCoord = pixel / size;
    vec2 texel = 1. / size;
    float x = texel.x * params.radius;
    float y = texel.y * params.radius;

    // Take 9 samples around current texel:
    // a - b - c
    // d - e - f
    // g - h - i
    // === ('e' is the current texel) ===
    vec3 a = texture(input_image, vec2(texCoord.x - 2 * x, texCoord.y + 2 * y), 0).rgb;
    vec3 b = texture(input_image, vec2(texCoord.x, texCoord.y + 2 * y), 0).rgb;
    vec3 c = texture(input_image, vec2(texCoord.x + 2 * x, texCoord.y + 2 * y), 0).rgb;
    vec3 d = texture(input_image, vec2(texCoord.x - 2 * x, texCoord.y), 0).rgb;
    vec3 e = texture(input_image, vec2(texCoord.x, texCoord.y), 0).rgb;
    vec3 f = texture(input_image, vec2(texCoord.x + 2 * x, texCoord.y), 0).rgb;
    vec3 g = texture(input_image, vec2(texCoord.x - 2 * x, texCoord.y - 2 * y), 0).rgb;
    vec3 h = texture(input_image, vec2(texCoord.x, texCoord.y - 2 * y), 0).rgb;
    vec3 i = texture(input_image, vec2(texCoord.x + 2 * x, texCoord.y - 2 * y), 0).rgb;
    vec3 j = texture(input_image, vec2(texCoord.x - x, texCoord.y + y), 0).rgb;
    vec3 k = texture(input_image, vec2(texCoord.x + x, texCoord.y + y), 0).rgb;
    vec3 l = texture(input_image, vec2(texCoord.x - x, texCoord.y - y), 0).rgb;
    vec3 m = texture(input_image, vec2(texCoord.x + x, texCoord.y - y), 0).rgb;

    // Apply weighted distribution, by using a 3x3 tent filter:
    //  1   | 1 2 1 |
    // -- * | 2 4 2 |
    // 16   | 1 2 1 |
    vec3 upsample = e * 0.125;
    upsample += (a + c + g + i) * 0.03125;
    upsample += (b + d + f + h) * 0.0625;
    upsample += (j + k + l + m) * 0.125;
    vec3 downsample = texture(downsample_image, texCoord).rgb;
    imageStore(output_image, pixel, vec4(downsample + upsample, 1.0));
}