cmake_minimum_required (VERSION 4.0)
project (app VERSION 1.0 LANGUAGES CXX C)
include(FetchContent)

# Enable C++
enable_language(CXX)
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -g")
else()
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O2 -Wno-pragmas -Wno-stringop-overflow")
endif()
# -g to enable debugging
# -O2 for optimization in speed, 01 for code size
# -Wextra and -Wall for extra warnings
# -Wno-pragmas to ignore pragmas warnings
# -Wno-stringop-overflow to ignore string overflow warnings

# Enable C
enable_language(C)
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -g")
else()
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -O2 -Wno-pragmas -Wno-stringop-overflow")
endif()

# Add the given directories to those the compiler uses to search for include files.
# Relative paths are interpreted as relative to the current source directory.
include_directories(external)

# OpenGL
cmake_policy(SET CMP0072 NEW)
find_package(OpenGL REQUIRED)

# Include the GLFW library
FetchContent_Declare(
    glfw
    GIT_REPOSITORY https://github.com/glfw/glfw.git
    # GIT_TAG 3.4
    GIT_TAG master
    GIT_SHALLOW 1
)
FetchContent_MakeAvailable(glfw)

# Include the FMT library
FetchContent_Declare(
    fmt
    GIT_REPOSITORY https://github.com/fmtlib/fmt.git
    # GIT_TAG 11.1.4
    GIT_TAG master
    GIT_SHALLOW 1
)
FetchContent_MakeAvailable(fmt)

# Linmath headers [no CMakeLists]
FetchContent_Declare(
    linmath
    GIT_REPOSITORY https://github.com/datenwolf/linmath.h.git
    GIT_TAG master
    GIT_SHALLOW 1
)
FetchContent_MakeAvailable(linmath)
# Method 1 - add as a library and interface it with the src files, then add to the exe below
# add_library(linmath INTERFACE)
# target_include_directories(linmath INTERFACE ${linmath_SOURCE_DIR})
# Method 2 - add the source files as is
include_directories(${linmath_SOURCE_DIR})

# stb_image library [this one has a CMakeLists build but it is at v3.9]
# cmake_minimum_required(VERSION 3.9)
# FetchContent_Declare(
#     stb_image
#     GIT_REPOSITORY https://github.com/M2-TE/stb_image.git
#     GIT_TAG master
#     GIT_SHALLOW 1
# )
# FetchContent_MakeAvailable(stb_image)
# add_library(stb_image INTERFACE)
# target_include_directories(stb_image INTERFACE ${stb_image_SOURCE_DIR})
# cmake_minimum_required(VERSION 4.0)

# stb_image headers [no CMakeLists]
FetchContent_Declare(
    stb_image
    GIT_REPOSITORY https://github.com/nothings/stb.git
    GIT_TAG master
    GIT_SHALLOW 1
)
FetchContent_MakeAvailable(stb_image)
include_directories(${stb_image_SOURCE_DIR})

# GLM library
FetchContent_Declare(
    glm
    GIT_REPOSITORY https://github.com/g-truc/glm.git
    GIT_TAG master
    GIT_SHALLOW 1
)
FetchContent_MakeAvailable(glm)

# Add an executable target called <name> to be built from the source files.
# This is the manual way of adding source files.
# add_executable(app
#     src/main.cpp
# )

# Add all source files in the src directory to the app executable.
file(GLOB_RECURSE CPP_SOURCES ${PROJECT_SOURCE_DIR}/src/*.cpp)
file(GLOB_RECURSE C_SOURCES ${PROJECT_SOURCE_DIR}/src/*.c)
add_executable(app ${CPP_SOURCES} ${C_SOURCES})

# Define a custom macro for build type
if(CMAKE_BUILD_TYPE STREQUAL Debug)
  target_compile_definitions(app PRIVATE COMPILE_DEBUG=1)
endif()
if(CMAKE_BUILD_TYPE STREQUAL Development)
  target_compile_definitions(app PRIVATE COMPILE_DEVELOPMENT=1)
endif()
if(CMAKE_BUILD_TYPE STREQUAL Release)
  target_compile_definitions(app PRIVATE COMPILE_RELEASE=1)
endif()

# Specifies external directories to use when compiling a given target.
# The <target> was created by a command such as add_executable() or add_library().
target_include_directories(app PRIVATE ../external)

# Specify libraries or flags to use when linking a given target and/or its dependents.
target_link_libraries(app PRIVATE 
    OpenGL::GL
    glfw
    # linmath # enable if using as a library see above
    fmt::fmt
    glm::glm
)
