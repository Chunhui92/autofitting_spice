from __future__ import annotations


def bounded_local_box(
    base_params: dict[str, float],
    global_bounds: dict[str, tuple[float, float]],
    relative_radius: float,
) -> dict[str, tuple[float, float]]:
    result: dict[str, tuple[float, float]] = {}
    for name, value in base_params.items():
        scaled_a = value * (1.0 - relative_radius)
        scaled_b = value * (1.0 + relative_radius)
        lower = min(scaled_a, scaled_b)
        upper = max(scaled_a, scaled_b)
        global_lower, global_upper = global_bounds[name]
        result[name] = (max(lower, global_lower), min(upper, global_upper))
    return result
