#version 460 core

layout (location = 0) in vec3 in_texcoord_0;
layout (location = 1) in vec3 in_position;
layout (location = 2) in vec3 in_normal;

out vec2 uv_0;
out vec3 normal;
out vec3 frag_pos;
out float color_variation;
out vec4 shadow_coord;

uniform mat4 m_proj;
uniform mat4 m_view;
uniform mat4 m_model;
uniform mat4 m_view_global_light;

float random(vec2 st);
float noise(in vec2 st);
float fbm(in vec2 _st);

// Bias offset to remove shadow acne
const float tiny = -0.0005;

// Bias matrix to convert the coordinates from [-1, 1] to [0, 1] from clip space to texture space
const mat4 m_shadow_bias = mat4(0.5, 0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.5, 0.5, 0.5, 1.0);

void main() {
    uv_0 = in_texcoord_0.xy;
    normal = normalize(mat3(m_model) * in_normal);
    frag_pos = vec3(m_model * vec4(in_position, 1.0));
    color_variation = fbm(in_position.xz);
    gl_Position = m_proj * m_view * m_model * vec4(in_position, 1.0);

    const mat4 shadow_mvp = m_proj * m_view_global_light * m_model;
    shadow_coord = m_shadow_bias * shadow_mvp * vec4(in_position, 1.0);
    shadow_coord.z += tiny;
}

float random(vec2 st) {
    return fract(sin(dot(st.xy, vec2(12.9898, 78.233))) * 43758.5453123);
}

float noise(in vec2 st) {
    const vec2 i = floor(st);
    const vec2 f = fract(st);
	// Four corners in 2D of a tile
    const float a = random(i);
    const float b = random(i + vec2(1.0, 0.0));
    const float c = random(i + vec2(0.0, 1.0));
    const float d = random(i + vec2(1.0, 1.0));
	// Smooth Interpolation
    const vec2 u = smoothstep(0.0, 1.0, f);
	// Mix 4 percentages
    return mix(a, b, u.x) + (c - a) * u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
}

const vec2 fbm_shift = vec2(100.0);
const mat2 fbm_rot = mat2(cos(0.5), sin(0.5), -sin(0.5), cos(0.50));
const int num_octaves = 4;
float fbm(in vec2 _st) {
	// Craete variation with Fractal Brownian Motion (between 0 and 1)
    float v = 0.0;
    float a = 0.5;
    for (int i = 0; i < num_octaves; ++i) {
        v += a * noise(_st);
        _st = fbm_rot * _st * 2.0 + fbm_shift;
        a *= 0.5;
    }
    return v;
}