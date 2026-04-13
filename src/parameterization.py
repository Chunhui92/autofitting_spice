from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Protocol


@dataclass(frozen=True)
class CornerParameterSet:
    w_min_l_min: dict[str, float]
    w_min_l_max: dict[str, float]
    w_max_l_min: dict[str, float]
    w_max_l_max: dict[str, float]


class ParameterSurfaceModel(Protocol):
    def evaluate(self, w_um: float, l_um: float) -> float: ...

    def __call__(self, w_um: float, l_um: float) -> float: ...


class BilinearSurfaceModel:
    def __init__(
        self,
        parameter_name: str,
        corner_values: dict[str, float],
        w_bounds: tuple[float, float],
        l_bounds: tuple[float, float],
    ) -> None:
        self.parameter_name = parameter_name
        self.corner_values = corner_values
        self.w_bounds = w_bounds
        self.l_bounds = l_bounds

    @classmethod
    def from_corners(
        cls,
        parameter_name: str,
        corners: CornerParameterSet,
        w_bounds: tuple[float, float],
        l_bounds: tuple[float, float],
    ) -> "BilinearSurfaceModel":
        return cls(
            parameter_name=parameter_name,
            corner_values={
                "w_min_l_min": corners.w_min_l_min[parameter_name],
                "w_min_l_max": corners.w_min_l_max[parameter_name],
                "w_max_l_min": corners.w_max_l_min[parameter_name],
                "w_max_l_max": corners.w_max_l_max[parameter_name],
            },
            w_bounds=w_bounds,
            l_bounds=l_bounds,
        )

    def _normalize_log_scale(self, value: float, bounds: tuple[float, float]) -> float:
        lower, upper = bounds
        clamped_value = min(max(value, lower), upper)
        return (math.log10(clamped_value) - math.log10(lower)) / (math.log10(upper) - math.log10(lower))

    def evaluate(self, w_um: float, l_um: float) -> float:
        width_norm = self._normalize_log_scale(w_um, self.w_bounds)
        length_norm = self._normalize_log_scale(l_um, self.l_bounds)

        q11 = self.corner_values["w_min_l_min"]
        q12 = self.corner_values["w_min_l_max"]
        q21 = self.corner_values["w_max_l_min"]
        q22 = self.corner_values["w_max_l_max"]

        return (
            (1.0 - width_norm) * (1.0 - length_norm) * q11
            + (1.0 - width_norm) * length_norm * q12
            + width_norm * (1.0 - length_norm) * q21
            + width_norm * length_norm * q22
        )

    def __call__(self, w_um: float, l_um: float) -> float:
        return self.evaluate(w_um, l_um)
