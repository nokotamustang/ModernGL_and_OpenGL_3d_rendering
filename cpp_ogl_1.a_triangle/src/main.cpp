#define GLFW_INCLUDE_NONE  // This allows the gl.h import to happen afterwards
#include <GLFW/glfw3.h>
//
#define GLAD_GL_IMPLEMENTATION  // Define this once per project
#include <glad/gl.h>
//
#include <fmt/color.h>   // fmt::fg, fmt::bg
#include <fmt/format.h>  // fmt::print

#include <glm/ext/matrix_clip_space.hpp>  // glm::perspective
#include <glm/ext/matrix_transform.hpp>   // glm::translate, glm::rotate, glm::scale
#include <glm/ext/scalar_constants.hpp>   // glm::pi
#include <glm/mat4x4.hpp>                 // glm::mat4
#include <glm/vec3.hpp>                   // glm::vec3
#include <glm/vec4.hpp>                   // glm::vec4
#include <string>                         // std::string
#include <vector>                         // std::vector

#include "linmath.h"

using fmt::color;
using fmt::print;
using std::string;
using std::vector;

typedef struct Vertex {
    vec2 pos;
    vec3 col;
} Vertex;

glm::mat4 camera(float Translate, glm::vec2 const& Rotate) {
    glm::mat4 Projection = glm::perspective(glm::pi<float>() * 0.25f, 4.0f / 3.0f, 0.1f, 100.0f);
    glm::mat4 View = glm::translate(glm::mat4(1.0f), glm::vec3(0.0f, 0.0f, -Translate));
    View = glm::rotate(View, Rotate.y, glm::vec3(-1.0f, 0.0f, 0.0f));
    View = glm::rotate(View, Rotate.x, glm::vec3(0.0f, 1.0f, 0.0f));
    glm::mat4 Model = glm::scale(glm::mat4(1.0f), glm::vec3(0.5f));
    return Projection * View * Model;
}

static const Vertex vertices[3] =
    {{{-0.6f, -0.4f}, {1.0f, 0.0f, 0.0f}},
     {{0.6f, -0.4f}, {0.0f, 1.0f, 0.0f}},
     {{0.f, 0.6f}, {0.0f, 0.0f, 1.0f}}};

static const char* vertex_shader_text =
    "#version 460\n"
    "uniform mat4 MVP;\n"
    "in vec3 vCol;\n"
    "in vec2 vPos;\n"
    "out vec3 color;\n"
    "void main()\n"
    "{\n"
    "    gl_Position = MVP * vec4(vPos, 0.0, 1.0);\n"
    "    color = vCol;\n"
    "}\n";

static const char* fragment_shader_text =
    "#version 460\n"
    "in vec3 color;\n"
    "out vec4 fragment;\n"
    "void main()\n"
    "{\n"
    "    fragment = vec4(color, 1.0);\n"
    "}\n";

static void error_callback(int error, const char* description) {
    print(stderr, fg(color::red), "{}\n", description);
}

static void key_callback(GLFWwindow* window, int key, int scancode, int action, int mods) {
    if (key == GLFW_KEY_ESCAPE && action == GLFW_PRESS) {
        glfwSetWindowShouldClose(window, 1);
    }
}

// Since we are running the application from the build directory that I set to
// 'build/release/ninja' for an example, we need to adjust the root path accordingly
// since I'm not moving the assets yet. In a release situation, this should adjust
// back to "./" and the asset directory copied to the release directory with the 'exe'.
// Alternatively, we could create a symbolic link to the asset directory in the build
// output and then adjust the root path accordingly to "./".
const string root_path = "../../../../";

const int window_w = 1600;
const int window_h = 900;

int main(void) {
    string build_type = "Unknown";
#ifdef COMPILE_DEBUG
    build_type = "Debug";
#elif COMPILE_RELEASE
    build_type = "Release";
#elif COMPILE_DEVELOPMENT
    build_type = "Development";
#endif
    print("build type: {}\n", build_type);

    // Initialize GLFW
    glfwSetErrorCallback(error_callback);
    bool success = glfwInit();
    if (!success) {
        print(stderr, fg(fmt::color::red), "failed to initialize GLFW\n");
        exit(EXIT_FAILURE);
    }
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 6);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);

    // Set up GLFW window
    print("window size    : {}x{}\n", window_w, window_h);
    GLFWwindow* window = glfwCreateWindow(window_w, window_h, "OpenGL", NULL, NULL);
    if (!window) {
        print(stderr, "failed to create GLFW window\n");
        glfwTerminate();
        exit(EXIT_FAILURE);
    }

    // Get the resolution of the primary monitor and center the window
    const GLFWvidmode* mode = glfwGetVideoMode(glfwGetPrimaryMonitor());
    print("primary screen : {}x{}\n", mode->width, mode->height);
    if (mode) {
        const int xPos = (mode->width - window_w) * 0.5;
        const int yPos = (mode->height - window_h) * 0.5;
        glfwSetWindowPos(window, xPos, yPos);
    }

    // Set up GLFW callbacks and create the window
    glfwSetKeyCallback(window, key_callback);
    glfwMakeContextCurrent(window);
    gladLoadGL(glfwGetProcAddress);
    glfwSwapInterval(1);

    GLuint vertex_buffer;
    glGenBuffers(1, &vertex_buffer);
    glBindBuffer(GL_ARRAY_BUFFER, vertex_buffer);
    glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_STATIC_DRAW);

    const GLuint vertex_shader = glCreateShader(GL_VERTEX_SHADER);
    glShaderSource(vertex_shader, 1, &vertex_shader_text, NULL);
    glCompileShader(vertex_shader);
    const GLuint fragment_shader = glCreateShader(GL_FRAGMENT_SHADER);
    glShaderSource(fragment_shader, 1, &fragment_shader_text, NULL);
    glCompileShader(fragment_shader);
    const GLuint default_program = glCreateProgram();
    glAttachShader(default_program, vertex_shader);
    glAttachShader(default_program, fragment_shader);
    glLinkProgram(default_program);

    const GLint mvp_location = glGetUniformLocation(default_program, "MVP");
    const GLint vpos_location = glGetAttribLocation(default_program, "vPos");
    const GLint vcol_location = glGetAttribLocation(default_program, "vCol");

    GLuint vertex_array;
    glGenVertexArrays(1, &vertex_array);
    glBindVertexArray(vertex_array);
    glEnableVertexAttribArray(vpos_location);
    glVertexAttribPointer(vpos_location, 2, GL_FLOAT, GL_FALSE,
                          sizeof(Vertex), (void*)offsetof(Vertex, pos));
    glEnableVertexAttribArray(vcol_location);
    glVertexAttribPointer(vcol_location, 3, GL_FLOAT, GL_FALSE,
                          sizeof(Vertex), (void*)offsetof(Vertex, col));

    double last_time = glfwGetTime();
    const float rotation_speed = glm::radians(25.0);
    float rotation = 0;
    int buffer_w, buffer_h;
    glfwGetFramebufferSize(window, &buffer_w, &buffer_h);
    const float ratio = buffer_w / (float)buffer_h;
    mat4x4 model, view, projection;
    glViewport(0, 0, buffer_w, buffer_h);
    glClearColor(0.08, 0.16, 0.18, 1.0);
    // glEnable(GL_DEPTH_TEST);

    print("start main loop \n");
    while (!glfwWindowShouldClose(window)) {
        glClear(GL_COLOR_BUFFER_BIT);
        const double now_time = glfwGetTime();
        const float delta_time = (float)(now_time - last_time);
        last_time = now_time;
        rotation += rotation_speed * delta_time;

        mat4x4_identity(model);
        mat4x4_rotate_Z(model, model, rotation);
        mat4x4_ortho(view, -ratio, ratio, -1.f, 1.f, 1.f, -1.f);
        mat4x4_mul(projection, view, model);

        glUseProgram(default_program);
        glUniformMatrix4fv(mvp_location, 1, GL_FALSE, (const GLfloat*)&projection);
        glBindVertexArray(vertex_array);
        glDrawArrays(GL_TRIANGLES, 0, 3);

        // Swap the buffer and let GLFW run events
        glfwSwapBuffers(window);
        glfwPollEvents();
    }

    // Cleanup and terminate
    glfwDestroyWindow(window);
    glfwTerminate();
    exit(EXIT_SUCCESS);
}