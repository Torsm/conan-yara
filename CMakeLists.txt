#
#   yara's automake setup is weird so I looked at vcpkg's yara port and wrote this CMakeLists.txt instead
#   https://github.com/microsoft/vcpkg/blob/master/ports/yara/CMakeLists.txt
#

cmake_minimum_required(VERSION 3.8)
project(yara C)

include(conanbuildinfo.cmake)
conan_basic_setup(TARGETS)

set(YARA_SOURCE_SUBFOLDER "${CMAKE_CURRENT_SOURCE_DIR}/source_subfolder")

if (MSVC)
    add_compile_options(/W3 /wd4005 /wd4996 /wd4018 -D_CRT_SECURE_NO_WARNINGS)
endif ()

include_directories(
        ${YARA_SOURCE_SUBFOLDER}/libyara
        ${YARA_SOURCE_SUBFOLDER}/libyara/include
)

set(PROC_PLATFORM_SOURCE "${YARA_SOURCE_SUBFOLDER}/libyara/proc/none.c")
set(PROC_PLATFORM_INTERFACE "USE_NO_PROC")

if (APPLE AND CMAKE_SYSTEM_NAME MATCHES "Darwin")
    set(PROC_PLATFORM_SOURCE "${YARA_SOURCE_SUBFOLDER}/libyara/proc/mach.c")
    set(PROC_PLATFORM_INTERFACE "USE_MACH_PROC")
elseif (WIN32 OR MINGW OR CYGWIN)
    set(PROC_PLATFORM_SOURCE "${YARA_SOURCE_SUBFOLDER}/libyara/proc/windows.c")
    set(PROC_PLATFORM_INTERFACE "USE_WINDOWS_PROC")
elseif (UNIX AND CMAKE_SYSTEM_NAME MATCHES "Linux")
    set(THREADS_PREFER_PTHREAD_FLAG TRUE)
    set(PROC_PLATFORM_SOURCE "${YARA_SOURCE_SUBFOLDER}/libyara/proc/linux.c")
    set(PROC_PLATFORM_INTERFACE "USE_LINUX_PROC")
endif ()

set(libyara_definitions
        HAVE_LIBCRYPTO
        ${PROC_PLATFORM_INTERFACE}
)

file(GLOB libyara_sources
        ${YARA_SOURCE_SUBFOLDER}/libyara/*.c
        ${YARA_SOURCE_SUBFOLDER}/libyara/modules/tests/*.c
        ${YARA_SOURCE_SUBFOLDER}/libyara/modules/pe/*.c
        ${YARA_SOURCE_SUBFOLDER}/libyara/modules/elf/*.c
        ${YARA_SOURCE_SUBFOLDER}/libyara/modules/math/*.c
        ${YARA_SOURCE_SUBFOLDER}/libyara/modules/time/*.c
        ${PROC_PLATFORM_SOURCE})

function(optional_module module_name)
    if (${module_name})
        string(TOUPPER ${module_name} module_name_upper)
        string(REPLACE "_module" "" module_dir ${module_name})
        file(GLOB module_sources ${YARA_SOURCE_SUBFOLDER}/libyara/modules/${module_dir}/*.c)
        list(APPEND libyara_definitions ${module_name_upper})
        list(APPEND libyara_sources ${module_sources})
        set(libyara_definitions ${libyara_definitions} PARENT_SCOPE)
        set(libyara_sources ${libyara_sources} PARENT_SCOPE)
    endif ()
endfunction()

optional_module(dotnet_module)
optional_module(cuckoo_module)
optional_module(magic_module)
optional_module(hash_module)
optional_module(macho_module)
optional_module(dex_module)
optional_module(pb_tests_module)

find_package(Threads REQUIRED)

set(libyara_dependencies
        Threads::Threads
        CONAN_PKG::openssl)

if (cuckoo_module)
    list(APPEND libyara_dependencies CONAN_PKG::jansson)
endif ()

IF (CMAKE_SYSTEM_NAME MATCHES "Windows")
    list(APPEND libyara_dependencies Crypt32.lib Ws2_32.lib)
endif ()
if ("${CMAKE_C_COMPILER_ID}" STREQUAL "GNU")
    list(APPEND libyara_dependencies m)
endif ()

set(build_type STATIC)
if (BUILD_SHARED)
    set(build_type SHARED)
endif ()

add_library(libyara ${build_type} ${libyara_sources})
target_link_libraries(libyara PRIVATE ${libyara_dependencies})
target_compile_definitions(libyara PRIVATE ${libyara_definitions})

install(
        TARGETS libyara
        RUNTIME DESTINATION bin
        LIBRARY DESTINATION lib
        ARCHIVE DESTINATION lib
)

install(DIRECTORY ${YARA_SOURCE_SUBFOLDER}/libyara/include/ DESTINATION include)
