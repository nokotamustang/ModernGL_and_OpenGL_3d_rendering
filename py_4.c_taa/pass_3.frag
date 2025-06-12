#version 460 core

out vec4 frag_color;

in vec2 uv_0;

uniform sampler2D currentColor; // Current frame’s color
uniform sampler2D historyColor; // Previous frame’s accumulated color
uniform sampler2D motionVectors; // Motion vectors from G-buffer
uniform sampler2D depthBuffer;   // Depth buffer for validation

void main() {
    vec2 uv = uv_0;
    vec4 currColor = texture(currentColor, uv);
    vec2 motion = texture(motionVectors, uv).xy;

    // Re-project to previous frame’s UV coordinates
    vec2 prevUV = uv - motion;

    // Check if re-projected UV is valid
    if (prevUV.x < 0.0 || prevUV.x > 1.0 || prevUV.y < 0.0 || prevUV.y > 1.0) {
        frag_color = currColor; // No history data, use current color
        return;
    }

    // Sample history color
    vec4 historyColor = texture(historyColor, prevUV);

    // Depth test to avoid blending across occlusions
    float currDepth = texture(depthBuffer, uv).r;
    float prevDepth = texture(depthBuffer, prevUV).r;
    if (abs(currDepth - prevDepth) > 0.01) {
        frag_color = currColor; // Occlusion detected, use current color
        return;
    }

    // Variance clipping to reduce ghosting
    vec3 currRGB = currColor.rgb;
    vec3 historyRGB = historyColor.rgb;
    vec3 minColor = currRGB - 0.1; // Simple bounding box
    vec3 maxColor = currRGB + 0.1;
    historyRGB = clamp(historyRGB, minColor, maxColor);

    // Blend current and history (e.g., exponential moving average)
    float blendFactor = 0.1; // Adjust for temporal stability (0.05–0.2 typical)
    vec3 finalColor = mix(historyRGB, currRGB, blendFactor);

    frag_color = vec4(finalColor, 1.0);
}