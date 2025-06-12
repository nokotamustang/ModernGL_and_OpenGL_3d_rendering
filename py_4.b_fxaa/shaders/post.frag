#version 460 core

// Known as FXAA 3.11
// Rewritten from these implementations:
// https://github.com/mattdesl/glsl-fxaa/blob/master/fxaa.glsl
// https://github.com/McNopper/OpenGL/blob/master/Example42/shader/fxaa.frag.glsl

in vec2 v_texcoord;

out vec4 frag_color;

uniform sampler2D u_tex;
uniform vec2 u_resolution;

// Params
const float luma_threshold = 0.5;
const float mul_reduce = 1.0 / 8.0;
const float min_reduce = 1.0 / 128.0;
const float max_span = 8.0;

// Cheap estimation for gray value ~~ luminance 
const vec3 luminance = vec3(0.299, 0.587, 0.114);

void main(void) {
    const vec2 texel_step = 1.0 / u_resolution;
    const vec4 color = texture(u_tex, v_texcoord);

	// Get neighbor texels diag, using textureOffset allows pixel indexing
    const vec3 nw = textureOffset(u_tex, v_texcoord, ivec2(-1, 1)).rgb;
    const vec3 ne = textureOffset(u_tex, v_texcoord, ivec2(1, 1)).rgb;
    const vec3 sw = textureOffset(u_tex, v_texcoord, ivec2(-1, -1)).rgb;
    const vec3 se = textureOffset(u_tex, v_texcoord, ivec2(1, -1)).rgb;

    // Calculate luma
    const float luma_center = dot(color.rgb, luminance);
    const float luma_nw = dot(nw, luminance);
    const float luma_ne = dot(ne, luminance);
    const float luma_sw = dot(sw, luminance);
    const float luma_se = dot(se, luminance);

    // Find min and max luma
    const float luma_min = min(luma_center, min(min(luma_nw, luma_ne), min(luma_sw, luma_se)));
    const float luma_max = max(luma_center, max(max(luma_nw, luma_ne), max(luma_sw, luma_se)));

	// If contrast is lower than a maximum threshold jump out
    if (luma_max - luma_min <= luma_max * luma_threshold) {
        frag_color = color; // Unmodified
        return;
    }

	// Sampling is done along the gradient
    vec2 dir = vec2(-((luma_nw + luma_ne) - (luma_sw + luma_se)), ((luma_nw + luma_sw) - (luma_ne + luma_se)));

    // Sampling step distance depends on the luma: the brighter the sampled texels, the smaller the final sampling step direction.
    // This results, that brighter areas are less blurred/more sharper than dark areas.
    const float dir_reduce = max((luma_nw + luma_ne + luma_sw + luma_se) * 0.25 * mul_reduce, min_reduce);

	// Factor for normalizing the sampling direction plus adding the brightness influence. 
    const float min_factor = 1.0 / (min(abs(dir.x), abs(dir.y)) + dir_reduce);

    // Calculate final sampling direction vector by reducing, clamping to a range and finally adapting to the texture size. 
    dir = clamp(dir * min_factor, vec2(-max_span), vec2(max_span)) * texel_step;

	// Inner samples on the tab.
    const vec3 sample_neg = texture(u_tex, v_texcoord + dir * (1.0 / 3.0 - 0.5)).rgb;
    const vec3 sample_pos = texture(u_tex, v_texcoord + dir * (2.0 / 3.0 - 0.5)).rgb;
    const vec3 two_tab = (sample_pos + sample_neg) * 0.5;  

	// Outer samples on the tab.
    const vec3 sample_neg_outer = texture(u_tex, v_texcoord + dir * (0.0 / 3.0 - 0.5)).rgb;
    const vec3 sample_pos_outer = texture(u_tex, v_texcoord + dir * (3.0 / 3.0 - 0.5)).rgb;
    const vec3 four_tab = (sample_pos_outer + sample_neg_outer) * 0.25 + two_tab * 0.5;   

	// Calculate luma for checking against the minimum and maximum value.
    const float check_four_tab = dot(four_tab, luminance);

	// Check that outer samples of the tab beyond the edge
    if (check_four_tab < luma_min || check_four_tab > luma_max) {
        frag_color = vec4(two_tab, 1.0); // Two samples
        // frag_color = vec4(1.0, 0.0, 1.0, 1.0); // Debug edges magenta
    } else {
        frag_color = vec4(four_tab, 1.0); // Four samples
        // frag_color = vec4(1.0, 1.0, 0.0, 1.0); // Debug edges yellow
    }
}
