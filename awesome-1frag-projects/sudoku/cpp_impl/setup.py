import pybind11
from setuptools import Extension, find_packages, setup

sudoku_c_ext = Extension(
    'c_sudoku',
    ['awesome-1frag-projects/sudoku/sudoku.cpp'],
    include_dirs=[pybind11.get_include()],
    language='c++',
    extra_compile_args=['-std=c++17', '-O3', '-Wall', '-shared', '-fPIC'],
)

setup(
    name='awesome-sudoku',
    version='0.0.1',
    ext_modules=[sudoku_c_ext],
    packages=find_packages(),
    requires=['pybind11'],
)
