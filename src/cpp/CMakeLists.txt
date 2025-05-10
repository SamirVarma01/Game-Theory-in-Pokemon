cmake_minimum_required(VERSION 3.5)
project(nash_solver)

add_subdirectory(pybind11)
pybind11_add_module(nash_solver binding.cpp nash_solver.cpp)