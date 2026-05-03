#[compute]
#version 450

layout(local_size_x = 16, local_size_y = 16, local_size_z = 1) in;

layout(binding = 0, set = 0) uniform sampler2D input_image;
layout(rgba16f, binding = 1, set = 0) uniform image2D output_image;

layout(push_constant, std430) uniform Params
{
    vec2 raster_size;
    float radius;
} params;

float gaussian(float x, float sigma)
{
    return exp(-(x*x)/(2. * sigma * sigma));
}

void main()
{
    ivec2 pixel = ivec2(gl_GlobalInvocationID.xy);
    vec2 size = params.raster_size;

    if(pixel.x >= size.x || pixel.y >= size.y) return;

    vec2 uv = pixel / size;
    vec2 texel = 1. / vec2(size);

    float sigma = 2.;
    vec4 sum = vec4(0.);
    float ksum = 0.;
    int radius = int(params.radius);
    for(int dx = -radius; dx <= radius; ++dx)
    {
        vec2 sample_uv = clamp(uv + vec2(float(dx), 0.) * texel, vec2(0.), vec2(1.));
        vec4 v = texture(input_image, sample_uv);
        float w = gaussian(float(dx), sigma);
        sum += v * w;
        ksum += w;
    }

    imageStore(output_image, pixel, sum / ksum);
}