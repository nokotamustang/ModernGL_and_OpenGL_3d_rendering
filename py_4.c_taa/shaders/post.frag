#version 460 core

in vec2 v_texcoord;

out vec4 fragColor;

uniform sampler2D u_tex;
uniform sampler2D u_history;
uniform float blend_factor;

// Very simple TAA resolve

void main() {
    const vec4 current = texture(u_tex, v_texcoord);
    const vec4 history = texture(u_history, v_texcoord);
    fragColor = mix(current, history, blend_factor);
}