import os
import sys
from setuptools import Extension, find_packages, setup

print(os.popen(f'{sys.executable} -m pip install pybind11').read())
import pybind11  # noqa: we need to install pybind to run setup.py

sudoku_c_ext = Extension(
    'c_sudoku',
    ['awesome-1frag-projects/sudoku/sudoku.cpp'],
    include_dirs=[pybind11.get_include()],
    language='c++',
    extra_compile_args=['-std=c++17', '-O3', '-Wall', '-shared', '-fPIC'],
)

setup(
    name='awesome-1frag-projects',
    version='0.4.0',
    ext_modules=[sudoku_c_ext],
    packages=find_packages(),
    requires=['pybind11'],
)
