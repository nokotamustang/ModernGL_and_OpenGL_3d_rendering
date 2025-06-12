#version 460 core

out vec4 frag_color;

in vec4 clipCoords;

uniform samplerCube u_cube_map;
uniform mat4 m_invProjView;

void main() {
    const vec4 frag_pos = m_invProjView * clipCoords;
    const vec3 texCubeCoord = normalize(frag_pos.xyz / frag_pos.w);
    frag_color = texture(u_cube_map, texCubeCoord);
}