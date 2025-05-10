#include "nash_solver.h"
#include <algorithm>
#include <numeric>
#include <cmath>

std::vector<double> solve_zero_sum_game(const std::vector<std::vector<double>>& payoff_matrix) {
    int n_rows = payoff_matrix.size();

    if (n_rows == 0) {
        return {};
    }

    int n_cols = payoff_matrix[0].size();
    
    if (n_cols == 0) {
        return {};
    }

    std::vector<double> row_strategy(n_rows, 1.0 / n_rows);
    std::vector<double> col_strategy(n_cols, 1.0 / n_cols);

    const int max_iterations = 1000;
    const double convergence_threshold = 1e-6;

    for (int iter = 0; iter < max_iterations; ++iter) {
        // Best response for column player
        std::vector<double> col_payoffs(n_cols, 0.0);
        for (int j = 0; j < n_cols; ++j) {
            for (int i = 0; i < n_rows; ++i) {
                col_payoffs[j] += row_strategy[i] * (-payoff_matrix[i][j]);
            }
        }

        int best_col = std::min_element(col_payoffs.begin(), col_payoffs.end()) - col_payoffs.begin();

        std::vector<double> new_col_strategy(n_cols, 0.0);
        new_col_strategy[best_col] = 1.0;

        std::vector<double> row_payoffs(n_rows, 0.0);
        for (int i = 0; i < n_rows; ++i) {
            for (int j = 0; j < n_cols; ++j) {
                row_payoffs[i] += col_strategy[j] * payoff_matrix[i][j];
            }
        }
        
        int best_row = std::max_element(row_payoffs.begin(), row_payoffs.end()) - row_payoffs.begin();
        
        std::vector<double> new_row_strategy(n_rows, 0.0);
        new_row_strategy[best_row] = 1.0;

        double learning_rate = 2.0 / (iter + 2.0);
        
        for (int i = 0; i < n_rows; ++i) {
            row_strategy[i] = (1 - learning_rate) * row_strategy[i] + learning_rate * new_row_strategy[i];
        }
        
        for (int j = 0; j < n_cols; ++j) {
            col_strategy[j] = (1 - learning_rate) * col_strategy[j] + learning_rate * new_col_strategy[j];
        }
        
        // Check for convergence
        if (iter > 10 && learning_rate < convergence_threshold) {
            break;
        }
    }

    double sum = std::accumulate(row_strategy.begin(), row_strategy.end(), 0.0);
    if (sum > 0) {
        for (int i = 0; i < n_rows; ++i) {
            row_strategy[i] /= sum;
        }
    } else {
        for (int i = 0; i < n_rows; ++i) {
            row_strategy[i] = 1.0 / n_rows;
        }
    }

    return row_strategy;
}