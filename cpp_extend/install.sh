#!/bin/bash
c++ -O3 -Wall -shared -std=c++11 -fPIC `python3 -m pybind11 \
  --includes` sudoku.cpp -o sudoku`python3-config \
  --extension-suffix` -std=c++17
