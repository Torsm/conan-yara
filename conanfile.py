import os

from conans import ConanFile, CMake, tools


def _optional_modules():
    return dict(
        dotnet_module=True,
        cuckoo_module=True,
        hash_module=True,
        macho_module=True,
        dex_module=True,
        magic_module=False,
        pb_tests_module=False
    )


class CapstoneConan(ConanFile):
    name = "yara"
    description = "The pattern matching swiss knife"
    version = "4.0.2"
    license = "BSD-3-Clause"
    url = "https://github.com/Torsm/conan-yara"
    homepage = "https://github.com/VirusTotal/yara"
    settings = "os", "compiler", "build_type", "arch"
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake"
    options = dict({"shared": [True, False], "fPIC": [True, False]},
                   **{module: [True, False] for module in _optional_modules()})
    default_options = dict({"shared": False, "fPIC": True},
                           **{module: value for module, value in _optional_modules().items()})

    _cmake = None

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def requirements(self):
        self.requires("openssl/1.1.1h")
        if self.options.cuckoo_module:
            self.requires("jansson/2.13.1")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        folder_name = "yara-{}".format(self.version)
        os.rename(folder_name, self._source_subfolder)

    def _configure_cmake(self):
        if self._cmake:
            return self._cmake
        self._cmake = CMake(self)
        self._cmake.definitions["BUILD_SHARED"] = self.options.shared
        for module in _optional_modules():
            self._cmake.definitions[module] = self.options.get_safe(module)
        self._cmake.configure(build_folder=self._build_subfolder)
        return self._cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy("COPYING", src=self._source_subfolder, dst="licenses")
        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["libyara"]
