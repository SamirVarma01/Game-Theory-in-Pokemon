#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "nash_solver.h"

namespace py = pybind11;

PYBIND11_MODULE(nash_solver, m) {
    m.doc() = "Nash equilibrium solver for Pokemon battle AI";
    
    m.def("solve_zero_sum_game", &solve_zero_sum_game, 
          "Solve a two-player zero-sum game using fictitious play",
          py::arg("payoff_matrix"));
}