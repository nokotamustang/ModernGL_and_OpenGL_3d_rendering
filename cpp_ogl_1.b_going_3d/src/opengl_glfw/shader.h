#pragma once

#include <glad/gl.h>

class Shader {
   public:
    GLuint ID;
    Shader(const char* vertexFile, const char* fragmentFile);
    void Activate();
    void Delete();

   private:
    void compileErrors(unsigned int shader, const char* type);
};
