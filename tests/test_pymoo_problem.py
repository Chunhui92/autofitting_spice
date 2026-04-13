import unittest

from parameter_bounds import PARAMETER_NAMES
from parameter_bounds import parameter_bounds
from pymoo_problem import CornerObjectiveProblem, CornerProblemLayout


class PymooProblemTests(unittest.TestCase):
    def test_corner_problem_layout_has_expected_variable_count(self) -> None:
        layout = CornerProblemLayout()

        self.assertEqual(layout.n_var, 4 * len(PARAMETER_NAMES))

    def test_decode_corner_vector_returns_four_named_corners(self) -> None:
        layout = CornerProblemLayout()
        vector = [0.0] * layout.n_var

        decoded = layout.decode(vector)

        self.assertEqual(
            sorted(decoded.keys()),
            ["w_max_l_max", "w_max_l_min", "w_min_l_max", "w_min_l_min"],
        )

    def test_corner_problem_layout_repeats_parameter_bounds_for_each_corner(self) -> None:
        layout = CornerProblemLayout()

        lower, upper = layout.bounds()

        self.assertEqual(len(lower), layout.n_var)
        self.assertEqual(len(upper), layout.n_var)
        first_parameter = PARAMETER_NAMES[0]
        bounds = parameter_bounds()[first_parameter]
        self.assertEqual(lower[0], bounds[0])
        self.assertEqual(upper[0], bounds[1])
        self.assertEqual(lower[len(PARAMETER_NAMES)], bounds[0])
        self.assertEqual(upper[len(PARAMETER_NAMES)], bounds[1])

    def test_corner_objective_problem_evaluates_vector_into_objective_matrix(self) -> None:
        captured = {}
        layout = CornerProblemLayout()

        def evaluate_fn(decoded):
            captured.update(decoded)
            return [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]

        problem = CornerObjectiveProblem(evaluate_fn=evaluate_fn, layout=layout)
        result = problem.evaluate([[0.0] * layout.n_var], return_values_of=["F"])

        self.assertEqual(problem.n_var, layout.n_var)
        self.assertEqual(problem.n_obj, 6)
        self.assertEqual(len(problem.xl), layout.n_var)
        self.assertEqual(len(problem.xu), layout.n_var)
        self.assertEqual(problem.xl[0], parameter_bounds()[PARAMETER_NAMES[0]][0])
        self.assertEqual(problem.xu[0], parameter_bounds()[PARAMETER_NAMES[0]][1])
        self.assertEqual(result.shape, (1, 6))
        self.assertEqual(result.tolist(), [[1.0, 2.0, 3.0, 4.0, 5.0, 6.0]])
        self.assertEqual(list(captured.keys()), list(layout.corner_names))
