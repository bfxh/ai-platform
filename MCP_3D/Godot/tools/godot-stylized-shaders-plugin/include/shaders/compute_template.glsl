#[compute]
#version 450

layout(local_size_x = 16, local_size_y = 16, local_size_z = 1) in;

layout(rgba16f, set = 0, binding = 0) uniform image2D color_image;

layout(push_constant, std430) uniform Params
{
	vec2 raster_size;
	vec2 reserved;
} params;

void main()
{
	ivec2 pixel = ivec2(gl_GlobalInvocationID.xy);
	ivec2 size = ivec2(params.raster_size);

	if (pixel.x >= size.x || pixel.y >= size.y) return;

	vec4 color = imageLoad(color_image, pixel);

	color.rgb = 1.0 - color.rgb;

	imageStore(color_image, pixel, color);
}