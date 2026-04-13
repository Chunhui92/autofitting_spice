from __future__ import annotations


def finite_difference_sensitivity(
    base_params: dict[str, float],
    parameter_steps: dict[str, float],
    evaluator,
) -> dict[str, dict[str, float]]:
    baseline = evaluator(base_params)
    output: dict[str, dict[str, float]] = {}
    for name, step in parameter_steps.items():
        forward_params = dict(base_params)
        backward_params = dict(base_params)
        forward_params[name] = forward_params[name] + step
        backward_params[name] = backward_params[name] - step

        forward_result = None
        backward_result = None

        try:
            forward_result = evaluator(forward_params)
        except Exception:
            forward_result = None

        try:
            backward_result = evaluator(backward_params)
        except Exception:
            backward_result = None

        if forward_result is not None and backward_result is not None:
            output[name] = {
                metric: (forward_result[metric] - backward_result[metric]) / (2.0 * step)
                for metric in baseline
            }
            continue

        if forward_result is not None:
            output[name] = {
                metric: (forward_result[metric] - baseline[metric]) / step
                for metric in baseline
            }
            continue

        if backward_result is not None:
            output[name] = {
                metric: (baseline[metric] - backward_result[metric]) / step
                for metric in baseline
            }
            continue

        output[name] = {
            metric: float("nan")
            for metric in baseline
        }
    return output
