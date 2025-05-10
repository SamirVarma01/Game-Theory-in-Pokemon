#!/bin/bash
# Script to build the C++ Nash equilibrium solver

# Create build directory
mkdir -p src/cpp/build
cd src/cpp/build

# Clone pybind11 if not present
if [ ! -d "pybind11" ]; then
    git clone https://github.com/pybind/pybind11.git
fi

# Configure with CMake
cmake ..

# Build
make

# Go back to the original directory
cd ../../..

echo "C++ solver built successfully!"