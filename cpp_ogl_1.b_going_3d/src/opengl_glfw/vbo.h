#pragma once

#include <glad/gl.h>

class VBO {
   public:
    GLuint ID;
    VBO(GLfloat* vertices, GLsizeiptr size);
    void Bind();
    void Unbind();
    void Delete();
};
