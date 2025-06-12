#version 460 core

layout (location = 0) in vec3 in_position;

out vec4 frag_pos;

uniform mat4 m_invProjView;

void main() {
    gl_Position = vec4(in_position, 1.0);
    frag_pos = m_invProjView * gl_Position;
}