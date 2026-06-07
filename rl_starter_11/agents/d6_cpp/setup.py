from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext

ext_modules = [
    Pybind11Extension(
        "chess_engine_d6_han",
        ["engine.cpp"],
        include_dirs=["deps"],
        cxx_std=17,
        extra_compile_args=["-O3", "-flto", "-DNDEBUG"],
    ),
]

setup(
    name="chess_engine_d6_han",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext}
)
