#pragma once

#include <fmt/color.h>   // fmt::fg, fmt::bg
#include <fmt/format.h>  // fmt::print

#include <array>
#include <cassert>
#include <filesystem>
#include <fstream>                        // std::ifstream
#include <glm/ext/matrix_clip_space.hpp>  // glm::perspective
#include <glm/ext/matrix_transform.hpp>   // glm::translate, glm::rotate, glm::scale
#include <glm/ext/scalar_constants.hpp>   // glm::pi
#include <glm/gtc/type_ptr.hpp>
#include <glm/mat4x4.hpp>  // glm::mat4
#include <glm/vec3.hpp>    // glm::vec3
#include <glm/vec4.hpp>    // glm::vec4
#include <memory>          // std::unique_ptr
#include <stdexcept>       // std::runtime_error
#include <string>          // std::string
#include <vector>          // std::vector

class App {
   public:
    static const int WIDTH = 1600;
    static const int HEIGHT = 900;
    App();
    ~App();
    void run();

   private:
};
