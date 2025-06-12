#version 460 core

layout (location = 0) out vec4 frag_color;
layout (location = 1) out vec4 outDepth;
layout (location = 2) out vec4 outMotion;

in vec2 uv_0;
in vec3 vPrevWorldPos; // World position from previous frame

uniform vec2 u_resolution;
uniform sampler2D texAlbedo;

void main() {
    frag_color = texture(texAlbedo, uv_0);

    // Output depth (linearized if needed)
    outDepth = vec4(gl_FragCoord.z, 0.0, 0.0, 1.0);

    // Output motion vectors (current - previous position in screen space)
    vec2 currPos = gl_FragCoord.xy / u_resolution; // Normalize to [0,1]
    vec2 prevPos = (vPrevWorldPos.xy / vPrevWorldPos.z) * 0.5 + 0.5; // Project previous position
    outMotion = vec4(currPos - prevPos, 0.0, 1.0);
}