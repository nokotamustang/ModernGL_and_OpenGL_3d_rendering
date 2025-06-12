#define GLFW_INCLUDE_NONE  // This allows the gl.h import to happen afterwards
#include <GLFW/glfw3.h>
//
#define GLAD_GL_IMPLEMENTATION  // Define this once per project
#include <glad/gl.h>
//
#include "stb_image.h"
#define STB_IMAGE_IMPLEMENTATION  // Define this after the import, once per project
//
#include "app.hpp"
#include "opengl_glfw/ebo.h"
#include "opengl_glfw/shader.h"
#include "opengl_glfw/texture.h"
#include "opengl_glfw/vao.h"
#include "opengl_glfw/vbo.h"

using fmt::color;
using fmt::print;
using std::string;

using fmt::color;
using fmt::print;
using glm::mat4x4;
using std::array;
using std::make_unique;
using std::runtime_error;
using std::string;
using std::unique_ptr;
using std::vector;

static void error_callback(int error, const char* description) {
    print(stderr, fg(color::red), "{}\n", description);
}

static void key_callback(GLFWwindow* window, int key, int scancode, int action, int mods) {
    if (key == GLFW_KEY_ESCAPE && action == GLFW_PRESS) {
        glfwSetWindowShouldClose(window, 1);
    }
}

// Vertices: coordinates/color/texture coordinates
GLfloat vertices[] =
    {
        -0.5f, 0.0f, 0.5f, 0.83f, 0.70f, 0.44f, 0.0f, 0.0f,
        -0.5f, 0.0f, -0.5f, 0.83f, 0.70f, 0.44f, 5.0f, 0.0f,
        0.5f, 0.0f, -0.5f, 0.83f, 0.70f, 0.44f, 0.0f, 0.0f,
        0.5f, 0.0f, 0.5f, 0.83f, 0.70f, 0.44f, 5.0f, 0.0f,
        0.0f, 0.8f, 0.0f, 0.92f, 0.86f, 0.76f, 2.5f, 5.0f};

// Indices for vertices order
GLuint indices[] =
    {
        0, 1, 2,
        0, 2, 3,
        0, 1, 4,
        1, 2, 4,
        2, 3, 4,
        3, 0, 4};

App::App() {
}

App::~App() {
}

void App::run() {
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
    print("window size    : {}x{}\n", WIDTH, HEIGHT);
    GLFWwindow* window = glfwCreateWindow(WIDTH, HEIGHT, "OpenGL", NULL, NULL);
    if (!window) {
        print(stderr, "failed to create GLFW window\n");
        glfwTerminate();
        exit(EXIT_FAILURE);
    }

    // Get the resolution of the primary monitor and center the window
    const GLFWvidmode* mode = glfwGetVideoMode(glfwGetPrimaryMonitor());
    print("primary screen : {}x{}\n", mode->width, mode->height);
    if (mode) {
        const int xPos = (mode->width - WIDTH) * 0.5;
        const int yPos = (mode->height - HEIGHT) * 0.5;
        glfwSetWindowPos(window, xPos, yPos);
    }

    // Set up GLFW callbacks and create the window
    glfwSetKeyCallback(window, key_callback);
    glfwMakeContextCurrent(window);
    gladLoadGL(glfwGetProcAddress);
    glfwSwapInterval(1);

    // Generates Shader object using shaders default.vert and default.frag
    string root_path = "../../../";
#ifdef COMPILE_RELEASE
    root_path = "";
#endif
    string vert_shader = root_path + "shaders/default.vert";
    string frag_shader = root_path + "shaders/default.frag";
    print("shaders '{}' '{}'", vert_shader, frag_shader);
    Shader default_shader(vert_shader.c_str(), frag_shader.c_str());
    print("shaders loaded from '{}' '{}'", vert_shader, frag_shader);

    // Generates Vertex Array Object and binds it
    VAO VAO1;
    VAO1.Bind();
    // Generates Vertex Buffer Object and links it to vertices
    VBO VBO1(vertices, sizeof(vertices));
    // Generates Element Buffer Object and links it to indices
    EBO EBO1(indices, sizeof(indices));
    // Links VBO attributes such as coordinates and colors to VAO
    VAO1.LinkAttrib(VBO1, 0, 3, GL_FLOAT, 8 * sizeof(float), (void*)0);
    VAO1.LinkAttrib(VBO1, 1, 3, GL_FLOAT, 8 * sizeof(float), (void*)(3 * sizeof(float)));
    VAO1.LinkAttrib(VBO1, 2, 2, GL_FLOAT, 8 * sizeof(float), (void*)(6 * sizeof(float)));
    // Unbind all to prevent accidentally modifying them
    VAO1.Unbind();
    VBO1.Unbind();
    EBO1.Unbind();

    // Gets ID of uniform called "scale"
    GLuint uniID = glGetUniformLocation(default_shader.ID, "scale");
    string textures_path = "../../.../textures/";
#ifdef COMPILE_RELEASE
    textures_path = "textures/";
#endif

    // Texture
    string texture_file = textures_path + "brick_wall.png";
    Texture texture_0(texture_file.c_str(), GL_TEXTURE_2D, GL_TEXTURE0, GL_RGB, GL_UNSIGNED_BYTE);
    texture_0.texUnit(default_shader, "tex0", 0);
    print("texture loaded from '{}'", texture_file);

    double last_time = glfwGetTime();
    const float rotation_speed = glm::radians(25.0);
    float rotation = 0;
    int buffer_w, buffer_h;
    glfwGetFramebufferSize(window, &buffer_w, &buffer_h);
    const float ratio = buffer_w / (float)buffer_h;
    const mat4x4 identity = mat4x4(1.0f);
    mat4x4 model = identity;
    mat4x4 view = identity;
    mat4x4 projection = glm::perspective(glm::radians(45.0f), ratio, 0.1f, 100.0f);
    glViewport(0, 0, buffer_w, buffer_h);
    glClearColor(0.08, 0.16, 0.18, 1.0);
    glEnable(GL_DEPTH_TEST);

    print("start main loop \n");
    while (!glfwWindowShouldClose(window)) {
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
        const double now_time = glfwGetTime();
        const float delta_time = (float)now_time - (float)last_time;
        last_time = now_time;
        rotation += rotation_speed * delta_time;

        default_shader.Activate();  // Use the shader

        // Assigns different transformations to each matrix
        model = glm::rotate(identity, rotation, glm::vec3(0.0f, 1.0f, 0.0f));
        view = glm::translate(identity, glm::vec3(0.0f, -0.5f, -2.0f));

        // Outputs the matrices into the Vertex Shader
        int modelLoc = glGetUniformLocation(default_shader.ID, "model");
        glUniformMatrix4fv(modelLoc, 1, GL_FALSE, glm::value_ptr(model));
        int viewLoc = glGetUniformLocation(default_shader.ID, "view");
        glUniformMatrix4fv(viewLoc, 1, GL_FALSE, glm::value_ptr(view));
        int projLoc = glGetUniformLocation(default_shader.ID, "proj");
        glUniformMatrix4fv(projLoc, 1, GL_FALSE, glm::value_ptr(projection));
        glUniform1f(uniID, 0.5f);  // Assigns a value to the uniform; always do after activating a shader
        texture_0.Bind();          // Binds texture so that is appears in rendering
        VAO1.Bind();               // Bind the VAO so OpenGL knows to use it
        // Draw primitives, number of indices, datatype of indices, index of indices
        glDrawElements(GL_TRIANGLES, sizeof(indices) / sizeof(int), GL_UNSIGNED_INT, 0);

        // Swap the buffer and let GLFW run events
        glfwSwapBuffers(window);
        glfwPollEvents();
    }

    // Cleanup and terminate
    VAO1.Delete();
    VBO1.Delete();
    EBO1.Delete();
    texture_0.Delete();
    default_shader.Delete();
    glfwDestroyWindow(window);
    glfwTerminate();
}
