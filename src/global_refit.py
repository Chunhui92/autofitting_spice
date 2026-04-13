from __future__ import annotations

from dataclasses import dataclass
import math

from parameterization import ParameterSurfaceModel


@dataclass(frozen=True)
class InverseDistanceSurfaceModel:
    parameter_name: str
    points: tuple[tuple[float, float, float], ...]
    power: float = 2.0

    def evaluate(self, w_um: float, l_um: float) -> float:
        x = math.log10(w_um)
        y = math.log10(l_um)
        weighted_sum = 0.0
        total_weight = 0.0

        for point_x, point_y, point_value in self.points:
            distance = math.hypot(point_x - x, point_y - y)
            if distance == 0.0:
                return point_value
            weight = 1.0 / (distance**self.power)
            weighted_sum += weight * point_value
            total_weight += weight

        return weighted_sum / total_weight

    def __call__(self, w_um: float, l_um: float) -> float:
        return self.evaluate(w_um, l_um)


def fit_global_parameter_plane(parameter_name: str, samples: list[dict[str, float]]) -> ParameterSurfaceModel:
    if not samples:
        raise ValueError("fit_global_parameter_plane requires at least one sample")

    points = tuple(
        (math.log10(sample["w_um"]), math.log10(sample["l_um"]), sample[parameter_name])
        for sample in samples
    )
    return InverseDistanceSurfaceModel(parameter_name=parameter_name, points=points)
