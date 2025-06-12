@echo off
setlocal enabledelayedexpansion

set current_path=%cd%

set build_compiler="MinGW Makefiles"
set build_sub=make
set releaseFile=%current_path%/release.txt

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
IF "%~2"=="clean" (
    call rm -rf "build/%build_main%/%build_sub%"
)
IF "%~3"=="clean" (
    call rm -rf "build/%build_main%/%build_sub%"
)
IF "%build_type%"=="Release" (
    if exist "%releaseFile%" (
        echo copy release assets:
        for /f "tokens=1,2 delims==" %%a in (%releaseFile%) do (
            set "part1=%%a"
            set "part2=%%b"
            call Xcopy /E /I /Y "%current_path%/!part1!" "%current_path%/build/%build_main%/%build_sub%/!part2!"
        )
    ) else (
        echo no release.txt to copy assets with
    )
)

echo current path: "%current_path%"
echo building "build/%build_main%/%build_sub%":

call cmake ^
-DCMAKE_BUILD_TYPE:STRING="%build_type%" ^
-DCMAKE_C_COMPILER:FILEPATH="gcc.exe" ^
-DCMAKE_CXX_COMPILER:FILEPATH="g++.exe" ^
-DCMAKE_EXPORT_COMPILE_COMMANDS=1 ^
-S "%current_path%" ^
-B "%current_path%/build/%build_main%/%build_sub%" ^
-G %build_compiler%