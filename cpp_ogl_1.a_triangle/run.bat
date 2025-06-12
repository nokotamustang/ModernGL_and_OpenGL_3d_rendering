@echo off

set current_path=%cd%

set build_compiler="MinGW Makefiles"
set build_sub=make

REM Param 2 and 3 is optional 
IF "%~2"=="ninja" (
    set build_compiler="Ninja"
    set build_sub=ninja
)
IF "%~3"=="ninja" (
    set build_compiler="Ninja"
    set build_sub=ninja
)

REM I've made param 1 required, so use either Debug or Release
set build_type=none
IF "%~1"=="debug" (
    set build_type=Debug
    set build_main=debug
)
IF "%~1"=="development" (
    set build_type=Development
    set build_main=development
)
IF "%~1"=="release" (
    set build_type=Release
    set build_main=release
)
REM if build_type is none then exit
IF "%build_type%"=="none" (
    echo no build type specified:
    echo build debug; build release; build development
    exit /b 1
)

echo Calling "%build_main%/%build_sub%":

cd "build/%build_main%/%build_sub%"
call "app.exe"
cd %current_path%