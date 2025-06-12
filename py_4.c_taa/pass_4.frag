#version 460 core

out vec4 frag_color;

in vec2 uv_0;

uniform sampler2D taaResult; // Output from temporal accumulation
uniform vec2 resolution;

void main() {
    vec2 uv = uv_0;
    vec4 color = texture(taaResult, uv);

    // Simple sharpening filter (e.g., unsharp mask)
    vec2 invRes = 1.0 / resolution;
    vec4 blur = 0.25 * (texture(taaResult, uv + vec2(-invRes.x, 0.0)) +
        texture(taaResult, uv + vec2(invRes.x, 0.0)) +
        texture(taaResult, uv + vec2(0.0, -invRes.y)) +
        texture(taaResult, uv + vec2(0.0, invRes.y)));
    vec4 sharpened = color + (color - blur) * 0.5; // Adjust sharpening strength

    frag_color = clamp(sharpened, 0.0, 1.0);
}