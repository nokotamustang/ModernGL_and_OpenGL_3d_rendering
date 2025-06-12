#include <fmt/color.h>   // fmt::fg, fmt::bg
#include <fmt/format.h>  // fmt::print

#include "app.hpp"

using fmt::color;
using fmt::print;

int main() {
    App app;

    try {
        app.run();
    } catch (const std::exception& err) {
        print(stderr, fg(color::red), "{}\n", err.what());
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}