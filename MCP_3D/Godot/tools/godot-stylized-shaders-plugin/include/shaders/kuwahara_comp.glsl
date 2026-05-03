#[compute]
#version 450

layout(local_size_x = 16, local_size_y = 16, local_size_z = 1) in;

layout(binding = 0, set = 0) uniform sampler2D base_image;
layout(binding = 1, set = 0) uniform sampler2D prev_pass;
layout(rgba16f, binding = 2, set = 0) uniform image2D output_image;

layout(push_constant, std430) uniform Params 
{
    vec2 raster_size;
    float kernel_size;
    float alpha;
    float zero_crossing;
    float sectors;
    float sharpness;
} params;

// from acerolafx
void main()
{
    ivec2 pixel = ivec2(gl_GlobalInvocationID.xy);
    vec2 size = params.raster_size;

    if(pixel.x >= size.x || pixel.y >= size.y)
        return;
    
    vec2 uv = pixel / size;
    if (params.kernel_size < 3.0) 
    {
        vec3 center = texture(base_image, uv).rgb;
        imageStore(output_image, pixel, vec4(center, 1.0));
        return;
    }
    
    vec2 texel = 1. / size;

    vec4 t = texture(prev_pass, uv);
    float sin_phi = sin(t.z); 
    float cos_phi = cos(t.z);

    int radius = int(params.kernel_size) / 2;
    float alpha_safe = max(1e-6, params.alpha);
    float a = float(radius) * clamp((alpha_safe + t.w) / alpha_safe, 0.1, 2.0);
    float b = float(radius) * clamp(alpha_safe / (alpha_safe + t.w), 0.1, 2.0);

    mat2 R = mat2(cos_phi, -sin_phi, sin_phi, cos_phi);
    mat2 S = mat2(.5 / a, 0., 0., .5 / b);
    mat2 SR = S * R;

    int max_x = int(ceil(sqrt(a*a*cos_phi*cos_phi+b*b*sin_phi*sin_phi)));
    int max_y = int(ceil(sqrt(a*a*sin_phi*sin_phi+b*b*cos_phi*cos_phi)));
    const int HARD_MAX_RADIUS = 32;
    max_x = min(max_x, HARD_MAX_RADIUS);
    max_y = min(max_y, HARD_MAX_RADIUS);


    float zeta = 2. / (params.kernel_size / 2.);
    float zero_cross = params.zero_crossing;
    float sin_zero = sin(zero_cross);
    float eta = (zeta + cos(zero_cross)) / (sin_zero*sin_zero);

    const int MAX_SECTORS = 16;
    int N = min(int(params.sectors), MAX_SECTORS);
    vec4 m[MAX_SECTORS]; vec3 s[MAX_SECTORS];
    for(int k = 0; k < N; ++k)
    {
        m[k] = vec4(0.);
        s[k] = vec3(0.);
    }

    for (int yy = -max_y; yy <= max_y; ++yy)
    {
        for (int xx = -max_x; xx <= max_x; ++xx)
        {
            vec2 v = SR * vec2(float(xx), float(yy));
            if (dot(v, v) <= .25) 
            {
                vec2 sample_uv = (uv + vec2(xx, yy) * texel);
                sample_uv = clamp(sample_uv, texel * 0.5, vec2(1.0) - texel * 0.5);
                vec3 c = texture(base_image, sample_uv).rgb;
                float sum = 0.0;
                float w[8];

                float vxx = zeta - eta * v.x * v.x;
                float vyy = zeta - eta * v.y * v.y;
                float z = max(0., v.y + vxx);
                w[0] = z * z; sum += w[0];
                z = max(0., -v.x + vyy);
                w[2] = z * z; sum += w[2];
                z = max(0., -v.y + vxx);
                w[4] = z * z; sum += w[4];
                z = max(0., v.x + vyy);
                w[6] = z * z; sum += w[6];

                // rotated by 45 degrees
                vec2 v2 = .70710678 * vec2(v.x - v.y, v.x + v.y);
                vxx = zeta - eta * v2.x * v2.x;
                vyy = zeta - eta * v2.y * v2.y;
                z = max(0., v2.y + vxx);
                w[1] = z * z; sum += w[1];
                z = max(0., -v2.x + vyy);
                w[3] = z * z; sum += w[3];
                z = max(0., -v2.y + vxx);
                w[5] = z * z; sum += w[5];
                z = max(0., v2.x + vyy);
                w[7] = z * z; sum += w[7];

                float g = exp(-3.125 * dot(v, v)) / sum;
                for (int k = 0; k < N; ++k)
                {
                    float wk = w[k] * g;
                    m[k] += vec4(c * wk, wk);
                    s[k] += c * c * wk;
                }
            }
        }
    }

    vec4 out_color = vec4(0.);
    float wsum = 0.;
    for(int k = 0; k < N; ++k)
    {
        if(m[k].a <= 0.) continue;

        vec3 mk = m[k].rgb / m[k].a;
        vec3 sk = abs(s[k] / m[k].a - mk * mk);
        float sigma2 = sk.r + sk.g + sk.b;
        float w = 1. / (1. + pow(abs(1000. * sigma2), .5 * params.sharpness));
        out_color.rgb += mk * w;
        wsum += w;
    }
    if (wsum > 1e-6) {
        out_color.rgb /= wsum;
    } else {
        out_color.rgb = texture(base_image, uv).rgb;
    }
    out_color.a = 1.;
    out_color = clamp(out_color, 0.0, 1.0);
    imageStore(output_image, pixel, out_color);
}