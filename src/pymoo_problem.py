from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from parameter_bounds import PARAMETER_NAMES, parameter_bounds

try:
    from pymoo.core.problem import Problem as PymooProblem
except ImportError:
    class PymooProblem:  # type: ignore[no-redef]
        def __init__(self, n_var: int, n_obj: int, xl: list[float], xu: list[float]) -> None:
            self.n_var = n_var
            self.n_obj = n_obj
            self.xl = np.asarray(xl, dtype=float)
            self.xu = np.asarray(xu, dtype=float)

        def evaluate(self, x, return_values_of: list[str] | None = None):
            values = ["F"] if return_values_of is None else return_values_of
            out: dict[str, np.ndarray] = {}
            self._evaluate(np.asarray(x, dtype=float), out)
            if values == ["F"]:
                return out["F"]
            return tuple(out[name] for name in values)

CORNER_NAMES = [
    "w_min_l_min",
    "w_min_l_max",
    "w_max_l_min",
    "w_max_l_max",
]


@dataclass(frozen=True)
class CornerProblemLayout:
    corner_names: tuple[str, ...] = tuple(CORNER_NAMES)
    parameter_names: tuple[str, ...] = tuple(PARAMETER_NAMES)

    @property
    def n_var(self) -> int:
        return len(self.corner_names) * len(self.parameter_names)

    def decode(self, vector: list[float]) -> dict[str, dict[str, float]]:
        if len(vector) != self.n_var:
            raise ValueError(f"expected {self.n_var} variables, received {len(vector)}")

        decoded: dict[str, dict[str, float]] = {}
        index = 0
        for corner_name in self.corner_names:
            corner_params: dict[str, float] = {}
            for parameter_name in self.parameter_names:
                corner_params[parameter_name] = float(vector[index])
                index += 1
            decoded[corner_name] = corner_params
        return decoded

    def bounds(self) -> tuple[list[float], list[float]]:
        limits = parameter_bounds()
        lower: list[float] = []
        upper: list[float] = []
        for _corner_name in self.corner_names:
            for parameter_name in self.parameter_names:
                lo, hi = limits[parameter_name]
                lower.append(lo)
                upper.append(hi)
        return lower, upper


@dataclass
class CornerObjectiveProblem(PymooProblem):
    evaluate_fn: Callable[[dict[str, dict[str, float]]], list[float]]
    layout: CornerProblemLayout = field(default_factory=CornerProblemLayout)
    n_obj: int = field(init=False, default=6)

    def __post_init__(self) -> None:
        lower, upper = self.layout.bounds()
        super().__init__(
            n_var=self.layout.n_var,
            n_obj=self.n_obj,
            xl=lower,
            xu=upper,
        )

    def evaluate_one(self, vector: list[float] | np.ndarray) -> list[float]:
        return self.evaluate_fn(self.layout.decode(list(vector)))

    def _evaluate(self, x, out, *args, **kwargs) -> None:
        matrix = np.asarray(x, dtype=float)
        if matrix.ndim == 1:
            matrix = matrix.reshape(1, -1)
        out["F"] = np.asarray([self.evaluate_one(row) for row in matrix], dtype=float)
