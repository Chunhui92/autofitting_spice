from __future__ import annotations

METRIC_NAMES = [
    "vtlin_v",
    "vtsat_v",
    "idlin_a",
    "idsat_a",
    "idoff_a",
    "isoff_a",
]


def relative_error(simulated: float, target: float) -> float:
    if target == 0.0:
        return 0.0 if simulated == 0.0 else float("inf")
    return abs(simulated - target) / abs(target)


def summarize_point_errors(simulated: dict[str, float], target: dict[str, float]) -> dict[str, float | str]:
    relative = {name: relative_error(simulated[name], target[name]) for name in target}
    worst_metric = max(relative, key=relative.get)
    return {
        "worst_metric": worst_metric,
        "worst_relative_error": relative[worst_metric],
        **relative,
    }
