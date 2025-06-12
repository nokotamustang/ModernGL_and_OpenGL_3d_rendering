#version 460 core

layout (points) in;
layout (triangle_strip, max_vertices = 36) out;

out GS_OUT {
	vec2 uv_0;
	float color_variation;
	vec3 normal;
	vec3 frag_pos;
	vec4 shadow_coord;
} gs_out;

uniform mat4 m_proj;
uniform mat4 m_view;
// uniform mat4 m_model;
uniform vec3 cam_pos;
uniform sampler2D u_wind;
uniform float u_time;
uniform mat4 m_view_global_light;

const mat4 model_wind = mat4(1);
const vec2 windDirection = vec2(1.0, 1.0);
const float windStrength = 0.15;
const float grass_scale = 2.0;
const float grass_min = 0.5;

const float LOD1 = 50.0;
const float LOD2 = 100.0;
const float LOD3 = 400.0;

const float PI = 3.141592653589793;

// Bias offset to remove shadow acne
const float tiny = -0.0005;

// Bias matrix to convert the coordinates from [-1, 1] to [0, 1] from clip space to texture space
const mat4 m_shadow_bias = mat4(0.5, 0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.5, 0.5, 0.5, 1.0);

// Constants
const vec4 v_pos_1 = vec4(-0.25, 0.0, 0.0, 0.0);
const vec4 v_pos_2 = vec4(0.25, 0.0, 0.0, 0.0);
const vec4 v_pos_3 = vec4(-0.25, 0.5, 0.0, 0.0);
const vec4 v_pos_4 = vec4(0.25, 0.5, 0.0, 0.0);
const vec2 t_coord_1 = vec2(0.0, 0.0); // Down left
const vec2 t_coord_2 = vec2(1.0, 0.0); // Down right
const vec2 t_coord_3 = vec2(0.0, 1.0); // Up left
const vec2 t_coord_4 = vec2(1.0, 1.0); // Up right
const mat4 model_0 = mat4(1.0);
const float rot_45 = radians(45);
const mat4 model_45 = mat4(cos(rot_45), 0, sin(rot_45), 0, 0, 1.0, 0, 0, -sin(rot_45), 0, cos(rot_45), 0, 0, 0, 0, 1);
const mat4 model_neg_45 = mat4(cos(-rot_45), 0, sin(-rot_45), 0, 0, 1.0, 0, 0, -sin(-rot_45), 0, cos(-rot_45), 0, 0, 0, 0, 1);

// Functions
mat4 rotationX(in float angle);
mat4 rotationY(in float angle);
mat4 rotationZ(in float angle);
float random(vec2 st);
float noise(in vec2 st);
float fbm(in vec2 _st);

// Variables set by main in this shader
float grass_size;
float lod2_dist = 1.0;
float lod3_dist = 1.0;

void createQuad(vec3 in_pos, mat4 x_model) {
	const vec4 in_gl_pos = gl_in[0].gl_Position;
	const mat4 base = m_proj * m_view;
	const mat4 shadow_mvp = m_proj * m_view_global_light; 

	// Diminish the wind based on LOD levels
	const float wind_scale = 0.6 + (lod2_dist * 0.25) + (lod3_dist * 0.15);

	// Wind calculation using the flow map texture and time
	const float wind_pos_scale = 0.1; // Pulled this out because it's interesting to modify it
	vec2 uv = in_pos.xz * wind_pos_scale + windDirection * windStrength * u_time * wind_scale;
	uv.x = mod(uv.x, 1.0);
	uv.y = mod(uv.y, 1.0);
	const vec4 wind = texture(u_wind, uv);
	const mat4 wind_mat = rotationX(wind.x * PI * 0.75 - PI * 0.25) * rotationZ(wind.y * PI * 0.75 - PI * 0.25);

	// The back of the quad will be invisible to the camera, so we rotate the quad with a random amount to create a complete scene.
	const mat4 rand_y = rotationY(random(in_pos.zx) * PI);
	const vec3 normal = vec3(model_wind * rand_y * x_model * vec4(0.0, 1.0, 0.0, 0.0));

	// Quad vertex positions
	const vec4 vert_1 = in_gl_pos + model_wind * rand_y * x_model * v_pos_1 * grass_size; // Down left
	const vec4 vert_2 = in_gl_pos + model_wind * rand_y * x_model * v_pos_2 * grass_size; // Down right
	const vec4 vert_3 = in_gl_pos + wind_mat * rand_y * x_model * v_pos_3 * grass_size; // Up left
	const vec4 vert_4 = in_gl_pos + wind_mat * rand_y * x_model * v_pos_4 * grass_size; // Up right

	// Billboard creation with 4 vertices
	gl_Position = base * vert_1;
	gs_out.uv_0 = t_coord_1;
	gs_out.frag_pos = vec3(vert_1);
	gs_out.normal = normalize(normal);
	gs_out.color_variation = fbm(in_gl_pos.xz);
	gs_out.shadow_coord = m_shadow_bias * shadow_mvp * vert_1;
	gs_out.shadow_coord.z += tiny;
	EmitVertex();

	gl_Position = base * vert_2;
	gs_out.uv_0 = t_coord_2;
	gs_out.frag_pos = vec3(vert_2);
	gs_out.normal = normal;
	gs_out.color_variation = fbm(in_gl_pos.xz);
	gs_out.shadow_coord = m_shadow_bias * shadow_mvp * vert_2;
	gs_out.shadow_coord.z += tiny;
	EmitVertex();

	gl_Position = base * vert_3;
	gs_out.uv_0 = t_coord_3;
	gs_out.frag_pos = vec3(vert_3);
	gs_out.normal = normal;
	gs_out.color_variation = fbm(in_gl_pos.xz);
	gs_out.shadow_coord = m_shadow_bias * shadow_mvp * vert_3;
	gs_out.shadow_coord.z += tiny;
	EmitVertex();

	gl_Position = base * vert_4;
	gs_out.uv_0 = t_coord_4;
	gs_out.frag_pos = vec3(vert_4);
	gs_out.normal = normal;
	gs_out.color_variation = fbm(in_gl_pos.xz);
	gs_out.shadow_coord = m_shadow_bias * shadow_mvp * vert_4;
	gs_out.shadow_coord.z += tiny;
	EmitVertex();

	EndPrimitive();
}

void main() {
	const vec3 in_pos = gl_in[0].gl_Position.xyz;

	// Distance of position to camera
	float dist_length = length(in_pos - cam_pos);
	grass_size = random(in_pos.xz) * grass_scale * (1.0 - grass_min) + grass_min;

	/* I created a custom LOD calculation here - Charlie */
	float t = 6.0;
	if (dist_length > LOD1) {
		t *= 1.5;
	}
	dist_length += (random(in_pos.xz) * t - t * 0.5);
	if (dist_length > LOD3) {
		return;
	}
	int detail_level = 3;
	if (dist_length > LOD1) {
		detail_level = 2;
		lod2_dist = 0.0;
	}
	if (dist_length > LOD2) {
		detail_level = 1;
		lod3_dist = 0.0;
	}
	if ((detail_level == 1) && ((int(in_pos.x * 10) % 1) == 0 || (int(in_pos.z * 10) % 1) == 0)) {
		createQuad(in_pos, model_0);
	} else if ((detail_level == 2) && ((int(in_pos.x * 5) % 1) == 0 || (int(in_pos.z * 5) % 1) == 0)) {
		createQuad(in_pos, model_45);
		createQuad(in_pos, model_neg_45);
	} else if (detail_level == 3) {
		createQuad(in_pos, model_0);
		createQuad(in_pos, model_45);
		createQuad(in_pos, model_neg_45);
	}

	/* Original LOD function */
	// float t = 6.0;
	// if (dist_length > LOD2)
	// 	t *= 1.5;
	// dist_length += (random(gl_in[0].gl_Position.xz) * t - t / 2.0);
	// int detail_level = 3;
	// if (dist_length > LOD1)
	// 	detail_level = 2;
	// if (dist_length > LOD2)
	// 	detail_level = 1;
	// if (dist_length > LOD3)
	// 	detail_level = 0;
	// if (detail_level != 1 || (detail_level == 1 && (int(gl_in[0].gl_Position.x * 10) % 1) == 0 || (int(gl_in[0].gl_Position.z * 10) % 1) == 0) || (detail_level == 2 && (int(gl_in[0].gl_Position.x * 5) % 1) == 0 || (int(gl_in[0].gl_Position.z * 5) % 1) == 0)) {
	// 	if (detail_level == 1) {
	// 		createQuad(in_pos, model_0);
	// 	} else if (detail_level == 2) {
	// 		createQuad(in_pos, model_45);
	// 		createQuad(in_pos, model_neg_45);
	// 	} else if (detail_level == 3) {
	// 		createQuad(in_pos, model_0);
	// 		createQuad(in_pos, model_45);
	// 		createQuad(in_pos, model_neg_45);
	// 	}
	// }
}

mat4 rotationX(in float angle) {
	return mat4(1.0, 0, 0, 0, 0, cos(angle), -sin(angle), 0, 0, sin(angle), cos(angle), 0, 0, 0, 0, 1);
}

mat4 rotationY(in float angle) {
	return mat4(cos(angle), 0, sin(angle), 0, 0, 1.0, 0, 0, -sin(angle), 0, cos(angle), 0, 0, 0, 0, 1);
}

mat4 rotationZ(in float angle) {
	return mat4(cos(angle), -sin(angle), 0, 0, sin(angle), cos(angle), 0, 0, 0, 0, 1, 0, 0, 0, 0, 1);
}

float random(vec2 st) {
	return fract(sin(dot(st.xy, vec2(12.9898, 78.233))) * 43758.5453123);
}

// 2D Noise based on Morgan McGuire @morgan3d https://www.shadertoy.com/view/4dS3Wd
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
const int num_octaves = 3; // 5 was the original suggested value here, more variation and more cost
float fbm(in vec2 _st) {
	// Create variation with Fractal Brownian Motion (between 0 and 1)
	float v = 0.0;
	float a = 0.5;
	for (int i = 0; i < num_octaves; ++i) {
		v += a * noise(_st);
		_st = fbm_rot * _st * 2.0 + fbm_shift;
		a *= 0.5;
	}
	return v;
}