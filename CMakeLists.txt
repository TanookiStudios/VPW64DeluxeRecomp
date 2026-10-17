cmake_minimum_required(VERSION 3.20)
# Build for Virtual Pro Wrestling 64 Deluxe: Recompiled.
# Adapted from jessetbh/VPW2Recomp (Windows) with the macOS/Linux pieces from Zelda64Recomp.
#   cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
#   cmake --build build --target VPW64Deluxe
if (APPLE)
    set(CMAKE_OSX_DEPLOYMENT_TARGET "13.0" CACHE STRING "Minimum macOS version")
endif()
project(VPW64DeluxeRecompiled LANGUAGES C CXX)
set(CMAKE_C_STANDARD 17)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

if (APPLE)
    enable_language(OBJC OBJCXX)
endif()
if (WIN32)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -D_DISABLE_CONSTEXPR_MUTEX_CONSTRUCTOR")
    add_compile_definitions(NOMINMAX)
endif()
if (CMAKE_VERSION VERSION_GREATER_EQUAL "3.24.0")
    cmake_policy(SET CMP0135 NEW)
endif()
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})

set(NMR ${CMAKE_SOURCE_DIR}/vendor/N64ModernRuntime)
set(RT64DIR ${CMAKE_SOURCE_DIR}/vendor/rt64)
set(FRONTEND ${CMAKE_SOURCE_DIR}/vendor/RecompFrontend)

# --- RT64 (renderer) ---
set(RT64_STATIC TRUE)
set(RT64_SDL_WINDOW_VULKAN TRUE)
add_compile_definitions(HLSL_CPU)
add_subdirectory(${RT64DIR} ${CMAKE_BINARY_DIR}/rt64)
target_include_directories(rt64 PRIVATE ${CMAKE_BINARY_DIR}/rt64/src)

# --- Runtime core (ultramodern + librecomp) ---
set(BUILD_SHARED_LIBS OFF)
add_subdirectory(${NMR} ${CMAKE_BINARY_DIR}/N64ModernRuntime)

set(RECOMP_INCLUDES
    ${CMAKE_SOURCE_DIR}/include
    ${NMR}/ultramodern/include
    ${NMR}/librecomp/include
    ${NMR}/N64Recomp/include
)

# --- RecompiledFuncs: the recompiled game (generated, never committed) ---
add_library(RecompiledFuncs STATIC)
target_compile_options(RecompiledFuncs PRIVATE -Wno-everything -g)   # line info for crash backtraces
option(VPW_TRACE_CALLERS "Log every computed jump with its caller (bring-up diagnostics)" OFF)
if (VPW_TRACE_CALLERS)
    target_compile_definitions(RecompiledFuncs PRIVATE VPW_TRACE_CALLERS)
endif()
target_include_directories(RecompiledFuncs PRIVATE ${RECOMP_INCLUDES})
file(GLOB FUNC_C_SOURCES ${CMAKE_SOURCE_DIR}/RecompiledFuncs/*.c)
target_sources(RecompiledFuncs PRIVATE ${FUNC_C_SOURCES})

# --- DXC setup for the frontend's shaders ---
# rt64 sets DXC/DXC_*_OPTS in its own directory scope; RecompFrontend (a sibling) needs them
# in ours, so mirror rt64's definitions here (same values as rt64/CMakeLists.txt).
set(DXC_COMMON_OPTS "-I${RT64DIR}/src")
set(DXC_DXIL_OPTS "-Wno-ignored-attributes")
set(DXC_SPV_OPTS "-spirv" "-fspv-target-env=vulkan1.0" "-fvk-use-dx-layout")
set(DXC_PS_OPTS "${DXC_COMMON_OPTS}" "-E" "PSMain" "-T ps_6_0" "-D DYNAMIC_RENDER_PARAMS")
set(DXC_VS_OPTS "${DXC_COMMON_OPTS}" "-E" "VSMain" "-T vs_6_0" "-D DYNAMIC_RENDER_PARAMS" "-fvk-invert-y")
set(DXC_CS_OPTS "${DXC_COMMON_OPTS}" "-E" "CSMain" "-T cs_6_0")
set(DXC_GS_OPTS "${DXC_COMMON_OPTS}" "-E" "GSMain" "-T gs_6_0")
set(DXC_RT_OPTS "${DXC_COMMON_OPTS}" "-D" "RT_SHADER" "-T" "lib_6_3" "-fspv-target-env=vulkan1.1spirv1.4" "-fspv-extension=SPV_KHR_ray_tracing" "-fspv-extension=SPV_EXT_descriptor_indexing")
if (WIN32)
    set(DXC "${RT64DIR}/src/contrib/dxc/bin/x64/dxc.exe")
elseif (APPLE)
    if (CMAKE_SYSTEM_PROCESSOR STREQUAL "x86_64")
        set(DXC "DYLD_LIBRARY_PATH=${RT64DIR}/src/contrib/dxc/lib/x64" "${RT64DIR}/src/contrib/dxc/bin/x64/dxc-macos")
        set(SPIRVCROSS "DYLD_LIBRARY_PATH=${RT64DIR}/src/contrib/spirv-cross/lib/x64" "${RT64DIR}/src/contrib/spirv-cross/bin/x64/spirv-cross")
    else()
        set(DXC "DYLD_LIBRARY_PATH=${RT64DIR}/src/contrib/dxc/lib/arm64" "${RT64DIR}/src/contrib/dxc/bin/arm64/dxc-macos")
        set(SPIRVCROSS "DYLD_LIBRARY_PATH=${RT64DIR}/src/contrib/spirv-cross/lib/arm64" "${RT64DIR}/src/contrib/spirv-cross/bin/arm64/spirv-cross")
    endif()
else()
    if (CMAKE_SYSTEM_PROCESSOR STREQUAL "x86_64")
        set(DXC "LD_LIBRARY_PATH=${RT64DIR}/src/contrib/dxc/lib/x64" "${RT64DIR}/src/contrib/dxc/bin/x64/dxc-linux")
    else()
        set(DXC "LD_LIBRARY_PATH=${RT64DIR}/src/contrib/dxc/lib/arm64" "${RT64DIR}/src/contrib/dxc/bin/arm64/dxc-linux")
    endif()
endif()

# --- SDL2 ---
if (WIN32)
    include(FetchContent)
    set(SDL2_VERSION "2.30.3")
    FetchContent_Declare(sdl2
        URL https://github.com/libsdl-org/SDL/releases/download/release-${SDL2_VERSION}/SDL2-devel-${SDL2_VERSION}-VC.zip)
    FetchContent_MakeAvailable(sdl2)
else()
    find_package(SDL2 REQUIRED)
endif()

# --- RecompFrontend (recompui + recompinput) ---
set(RECOMP_FRONTEND_N64MODERNRUNTIME_PATH ${NMR})
set(RECOMP_FRONTEND_RT64_PATH ${RT64DIR})
add_subdirectory(${FRONTEND} ${CMAKE_BINARY_DIR}/RecompFrontend)

# --- Main executable ---
add_executable(VPW64Deluxe)

add_custom_command(OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/icon_bytes.c ${CMAKE_CURRENT_BINARY_DIR}/icon_bytes.h
    COMMAND file_to_c ${CMAKE_SOURCE_DIR}/icons/app.png icon_bytes ${CMAKE_CURRENT_BINARY_DIR}/icon_bytes.c ${CMAKE_CURRENT_BINARY_DIR}/icon_bytes.h
    DEPENDS ${CMAKE_SOURCE_DIR}/icons/app.png file_to_c
)
add_custom_command(OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/logo_bytes.c ${CMAKE_CURRENT_BINARY_DIR}/logo_bytes.h
    COMMAND file_to_c ${CMAKE_SOURCE_DIR}/icons/logo.png logo_bytes ${CMAKE_CURRENT_BINARY_DIR}/logo_bytes.c ${CMAKE_CURRENT_BINARY_DIR}/logo_bytes.h
    DEPENDS ${CMAKE_SOURCE_DIR}/icons/logo.png file_to_c
)
target_sources(VPW64Deluxe PRIVATE ${CMAKE_CURRENT_BINARY_DIR}/icon_bytes.c ${CMAKE_CURRENT_BINARY_DIR}/logo_bytes.c)

set(SOURCES
    ${CMAKE_SOURCE_DIR}/src/main/main.cpp
    ${CMAKE_SOURCE_DIR}/src/main/register_overlays.cpp
    ${CMAKE_SOURCE_DIR}/src/game/recomp_api.cpp
    ${CMAKE_SOURCE_DIR}/src/game/raytracing.cpp
    ${CMAKE_SOURCE_DIR}/src/ra/ra_client.cpp
    ${CMAKE_SOURCE_DIR}/rsp/vpw2_audio.cpp
)

# RetroAchievements client (vendored rcheevos, env-gated at runtime).
file(GLOB RCHEEVOS_SOURCES
    ${CMAKE_SOURCE_DIR}/src/ra/rcheevos/src/*.c
    ${CMAKE_SOURCE_DIR}/src/ra/rcheevos/src/rcheevos/*.c
    ${CMAKE_SOURCE_DIR}/src/ra/rcheevos/src/rapi/*.c
    ${CMAKE_SOURCE_DIR}/src/ra/rcheevos/src/rhash/*.c
)
list(APPEND SOURCES ${RCHEEVOS_SOURCES})
target_include_directories(VPW64Deluxe PRIVATE
    ${CMAKE_SOURCE_DIR}/src/ra/rcheevos/include
    ${CMAKE_SOURCE_DIR}/src/ra/rcheevos/src
)
target_compile_definitions(VPW64Deluxe PRIVATE RC_DISABLE_LUA RC_CLIENT_SUPPORTS_HASH)

target_include_directories(VPW64Deluxe PRIVATE
    ${CMAKE_SOURCE_DIR}/include
    ${NMR}/N64Recomp/include
    ${NMR}/thirdparty/sse2neon
    ${RT64DIR}/src
    ${FRONTEND}/recompinput/include
    ${FRONTEND}/recompui/include
    ${CMAKE_CURRENT_BINARY_DIR}
)

if (WIN32)
    target_include_directories(VPW64Deluxe PRIVATE ${sdl2_SOURCE_DIR}/include)
    target_link_directories(VPW64Deluxe PRIVATE ${sdl2_SOURCE_DIR}/lib/x64)
    target_link_libraries(VPW64Deluxe PRIVATE SDL2 Winmm.lib winhttp.lib)
    set_target_properties(VPW64Deluxe PROPERTIES
        LINK_FLAGS_DEBUG "/SUBSYSTEM:CONSOLE"
        LINK_FLAGS_RELEASE "/SUBSYSTEM:WINDOWS /ENTRY:mainCRTStartup")
    target_link_options(VPW64Deluxe PRIVATE /STACK:16777216)
else()
    target_include_directories(VPW64Deluxe PRIVATE ${SDL2_INCLUDE_DIRS})
    set(THREADS_PREFER_PTHREAD_FLAG TRUE)
    find_package(Threads REQUIRED)
    target_link_libraries(VPW64Deluxe PRIVATE ${CMAKE_DL_LIBS} Threads::Threads SDL2::SDL2)
endif()

# Runtime UI assets and controller db next to the program.
add_custom_command(TARGET VPW64Deluxe POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
        "${CMAKE_SOURCE_DIR}/assets" "$<TARGET_FILE_DIR:VPW64Deluxe>/assets"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "${CMAKE_SOURCE_DIR}/recompcontrollerdb.txt" "$<TARGET_FILE_DIR:VPW64Deluxe>")

target_link_libraries(VPW64Deluxe PRIVATE
    RecompiledFuncs
    recompui
    recompinput
    librecomp
    ultramodern
    rt64
    nfd
)
target_sources(VPW64Deluxe PRIVATE ${SOURCES})

# librecomp's RSP vector-unit header (used by rsp/vpw2_audio.cpp) needs SSE4.1 on x86-64
# (sse2neon covers arm64).
if(CMAKE_SIZEOF_VOID_P EQUAL 8 AND CMAKE_SYSTEM_PROCESSOR MATCHES "x86_64|amd64|AMD64")
    target_compile_options(VPW64Deluxe PRIVATE -march=nehalem -fno-strict-aliasing -fms-extensions)
else()
    target_compile_options(VPW64Deluxe PRIVATE -fno-strict-aliasing -fms-extensions)
endif()
