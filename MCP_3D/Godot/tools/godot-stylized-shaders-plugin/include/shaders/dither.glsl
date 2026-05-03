#[compute]
#version 450

layout(local_size_x = 16, local_size_y = 16, local_size_z = 1) in;

layout(rgba16f, binding = 0, set = 0) uniform image2D color_image;

layout(push_constant, std430) uniform Params 
{
	vec2 raster_size;
    float gamma_correction;
} params;

const float bayer_matrix[4][4] = float[4][4](
    float[4](0.0,   8.0,   2.0,  10.0),
    float[4](12.0,  4.0,  14.0,   6.0),
    float[4](3.0,  11.0,   1.0,   9.0),
    float[4](15.0,  7.0,  13.0,   5.0)
);

void main()
{
    ivec2 pixel = ivec2(gl_GlobalInvocationID.xy);
    vec2 size = params.raster_size;

    if(pixel.x >= size.x || pixel.y >= size.y) return;

    float bayer_val = bayer_matrix[pixel.x%4][pixel.y%4] / 16.;
    vec3 screen_tex = imageLoad(color_image, pixel).rgb;
    screen_tex = vec3(pow(screen_tex.rgb, vec3(params.gamma_correction)) - 0.004);
    vec3 col = vec3(step(bayer_val, screen_tex.r), step(bayer_val, screen_tex.g), step(bayer_val, screen_tex.b));
    vec4 color = vec4(col, 1.);
    imageStore(color_image, pixel, color);
}