#[compute]
#version 450

layout(local_size_x = 16, local_size_y = 16, local_size_z = 1) in;

layout(rgba16f, binding = 0, set = 0) uniform image2D color_image;

layout(push_constant, std430) uniform Params 
{
	vec2 raster_size;
    vec2 reserved;
	float curvature;
    float vignette_mul;
    float brightness;
} params;

void main()
{
    ivec2 pixel = ivec2(gl_GlobalInvocationID.xy);
	vec2 size = params.raster_size;

    if(pixel.x >= size.x || pixel.y >= size.y) return;

    vec2 uv = pixel / size;

    vec2 centered_uv = uv * 2. - 1.;
    vec2 uv_offset = centered_uv.yx / params.curvature;
    vec2 warped_uv = centered_uv + (centered_uv * uv_offset * uv_offset);
    
    vec3 cutoff = vec3(step(abs(warped_uv.x), 1.) * step(abs(warped_uv.y), 1.));
    vec3 scanlines = vec3(sin(2. * warped_uv.y * 180.) * .1 + params.brightness);
    vec3 vignette = vec3(length(pow(abs(centered_uv), vec2(4.0)) / 3.0));

    vec3 color = imageLoad(color_image, pixel).rgb * cutoff * scanlines;
    color -= vignette * params.vignette_mul;
    imageStore(color_image, pixel, vec4(color, 1.));
}