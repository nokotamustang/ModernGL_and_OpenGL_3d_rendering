#version 460 core

layout (location = 0) out vec4 frag_color;

struct Light {
    vec3 color;
};

uniform Light light;

const vec3 gamma = vec3(2.2);
const vec3 i_gamma = vec3(1 / 2.2);

void main() {
    vec3 color = light.color;
    color = pow(color, gamma);

    color = pow(color, i_gamma);
    frag_color = vec4(color, 1.0);
}