#version 460 core

out vec4 frag_color;

in vec2 uv_0;

uniform sampler2D texAlbedo;

// Simple fragment shading (could include lighting, etc.)

void main() {
    frag_color = texture(texAlbedo, uv_0);
}