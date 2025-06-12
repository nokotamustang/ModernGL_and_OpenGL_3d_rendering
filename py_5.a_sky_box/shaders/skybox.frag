#version 460 core

out vec4 frag_color;

in vec4 frag_pos;

uniform samplerCube u_cube_map;

void main() {
    const vec3 texCubeCoord = normalize(frag_pos.xyz / frag_pos.w);
    frag_color = texture(u_cube_map, texCubeCoord);
}