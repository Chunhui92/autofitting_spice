from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from error_metrics import summarize_point_errors
from global_refit import fit_global_parameter_plane
from local_tuning import bounded_local_box
from objectives import aggregate_metric_objectives
from parameter_bounds import PARAMETER_NAMES, parameter_bounds
from parameterization import BilinearSurfaceModel, CornerParameterSet, ParameterSurfaceModel
from plotting import (
    plot_error_heatmap,
    plot_parameter_surface,
    plot_pareto_front,
    plot_target_vs_simulated,
)
from project_paths import CALIBRATION_OUTPUT_DIR, DEFAULT_TARGET_CSV
from pymoo_problem import CornerObjectiveProblem, CornerProblemLayout
from reporting import write_csv_rows, write_markdown_summary, write_pareto_candidates
from targets import MetricTarget

CORNER_OBJECTIVE_NAMES = (
    "vtlin_v",
    "vtsat_v",
    "idlin_a",
    "idsat_a",
    "idoff_a",
    "isoff_a",
)


def _validate_corner_targets(
    corner_targets: dict[str, MetricTarget],
    layout: CornerProblemLayout,
) -> None:
    expected = set(layout.corner_names)
    actual = set(corner_targets.keys())
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    messages: list[str] = []
    if missing:
        messages.append(f"missing corners: {missing}")
    if extra:
        messages.append(f"unexpected corners: {extra}")
    if messages:
        raise ValueError(", ".join(messages))


@dataclass(frozen=True)
class CornerCalibrationResult:
    optimized_params: dict[str, float]
    worst_relative_error: float
    point_errors: dict[str, float | str]


def _invoke_simulate_fn(simulate_fn, target_row: MetricTarget, model_params: dict[str, float]) -> dict[str, float]:
    if hasattr(target_row, "w_um") and hasattr(target_row, "l_um"):
        try:
            return simulate_fn(target_row.w_um, target_row.l_um, model_params)
        except TypeError:
            return simulate_fn(model_params)
    return simulate_fn(model_params)


def calibrate_corner_point(
    target_row: MetricTarget,
    initial_params: dict[str, float],
    simulate_fn,
) -> CornerCalibrationResult:
    simulated_metrics = _invoke_simulate_fn(simulate_fn, target_row, initial_params)
    point_errors = summarize_point_errors(simulated_metrics, target_row.as_metric_dict())
    return CornerCalibrationResult(
        optimized_params=dict(initial_params),
        worst_relative_error=float(point_errors["worst_relative_error"]),
        point_errors=point_errors,
    )


def evaluate_corner_candidate(
    target_row: MetricTarget,
    model_params: dict[str, float],
    simulate_fn,
) -> list[float]:
    metrics = _invoke_simulate_fn(simulate_fn, target_row, model_params)
    errors = summarize_point_errors(metrics, target_row.as_metric_dict())
    return [float(errors[metric_name]) for metric_name in CORNER_OBJECTIVE_NAMES]


def evaluate_corner_set_candidate(
    corner_targets: dict[str, MetricTarget],
    corner_params: dict[str, dict[str, float]],
    simulate_fn,
) -> dict[str, float]:
    point_error_rows = [
        {
            metric_name: objective_value
            for metric_name, objective_value in zip(
                CORNER_OBJECTIVE_NAMES,
                evaluate_corner_candidate(target, corner_params[corner_name], simulate_fn),
                strict=True,
            )
        }
        for corner_name, target in corner_targets.items()
    ]
    return aggregate_metric_objectives(point_error_rows)


def build_corner_problem(
    corner_targets: dict[str, MetricTarget],
    simulate_fn,
    layout: CornerProblemLayout | None = None,
) -> CornerObjectiveProblem:
    problem_layout = CornerProblemLayout() if layout is None else layout
    _validate_corner_targets(corner_targets, problem_layout)
    return CornerObjectiveProblem(
        layout=problem_layout,
        evaluate_fn=lambda decoded: [
            evaluate_corner_set_candidate(corner_targets, decoded, simulate_fn)[metric_name]
            for metric_name in CORNER_OBJECTIVE_NAMES
        ],
    )


def export_corner_pareto_candidates(
    path: Path,
    candidate_vectors: list[list[float]],
    objective_rows: list[list[float]],
    layout: CornerProblemLayout | None = None,
) -> None:
    problem_layout = CornerProblemLayout() if layout is None else layout
    fieldnames = ["candidate_id", *CORNER_OBJECTIVE_NAMES]
    for corner_name in problem_layout.corner_names:
        for parameter_name in problem_layout.parameter_names:
            fieldnames.append(f"{corner_name}__{parameter_name}")

    rows: list[dict[str, float | str]] = []
    for candidate_id, (vector, objective_values) in enumerate(
        zip(candidate_vectors, objective_rows, strict=True),
        start=1,
    ):
        decoded = problem_layout.decode(vector)
        row: dict[str, float | str] = {"candidate_id": candidate_id}
        for metric_name, objective_value in zip(CORNER_OBJECTIVE_NAMES, objective_values, strict=True):
            row[metric_name] = float(objective_value)
        for corner_name in problem_layout.corner_names:
            for parameter_name in problem_layout.parameter_names:
                row[f"{corner_name}__{parameter_name}"] = decoded[corner_name][parameter_name]
        rows.append(row)

    write_pareto_candidates(path, rows, fieldnames=fieldnames)


def _parameter_steps() -> dict[str, float]:
    bounds = parameter_bounds()
    return {
        name: max((upper - lower) * 0.01, abs(lower) * 1e-3, 1e-12)
        for name, (lower, upper) in bounds.items()
    }


def _corner_sizes() -> list[tuple[float, float, str]]:
    from dataset_generator import LENGTHS_UM, WIDTHS_UM

    w_min = float(min(WIDTHS_UM))
    w_max = float(max(WIDTHS_UM))
    l_min = float(min(LENGTHS_UM))
    l_max = float(max(LENGTHS_UM))
    return [
        (w_min, l_min, "w_min_l_min"),
        (w_min, l_max, "w_min_l_max"),
        (w_max, l_min, "w_max_l_min"),
        (w_max, l_max, "w_max_l_max"),
    ]


def _build_corner_targets(target_rows: list[MetricTarget]) -> dict[str, MetricTarget]:
    target_lookup = {(row.w_um, row.l_um): row for row in target_rows}
    return {
        corner_name: target_lookup[(w_um, l_um)]
        for w_um, l_um, corner_name in _corner_sizes()
    }


def _clip_model_params(model_params: dict[str, float]) -> dict[str, float]:
    bounds = parameter_bounds()
    return {
        name: min(max(float(model_params[name]), bounds[name][0]), bounds[name][1])
        for name in PARAMETER_NAMES
    }


def _current_model_params(w_um: float, l_um: float) -> dict[str, float]:
    from dataset_generator import build_model_params

    built_params = build_model_params(w_um, l_um)
    return {name: built_params[name] for name in PARAMETER_NAMES}


def _initial_corner_vector(layout: CornerProblemLayout) -> list[float]:
    baseline: list[float] = []
    corner_coords = {corner_name: (w_um, l_um) for w_um, l_um, corner_name in _corner_sizes()}
    for corner_name in layout.corner_names:
        w_um, l_um = corner_coords[corner_name]
        params = _current_model_params(w_um, l_um)
        for parameter_name in layout.parameter_names:
            baseline.append(params[parameter_name])
    return baseline


def _safe_corner_simulate(w_um: float, l_um: float, model_params: dict[str, float]) -> dict[str, float]:
    from simulator import simulate_metrics_for_point

    try:
        return simulate_metrics_for_point(w_um, l_um, _clip_model_params(model_params))
    except Exception:
        return {
            "vtlin_v": 10.0,
            "vtsat_v": 10.0,
            "idlin_a": 1.0,
            "idsat_a": 1.0,
            "idoff_a": 1.0,
            "isoff_a": 1.0,
        }


def _run_corner_nsga(corner_targets: dict[str, MetricTarget]) -> tuple[list[list[float]], list[list[float]]]:
    import numpy as np
    from pymoo.algorithms.moo.nsga2 import NSGA2
    from pymoo.optimize import minimize

    layout = CornerProblemLayout()
    baseline_vector = np.asarray(_initial_corner_vector(layout), dtype=float)
    problem = build_corner_problem(corner_targets, _safe_corner_simulate, layout=layout)

    lower = np.asarray(problem.xl, dtype=float)
    upper = np.asarray(problem.xu, dtype=float)
    rng = np.random.default_rng(7)
    pop_size = 12
    sampling = np.tile(baseline_vector, (pop_size, 1))
    if pop_size > 1:
        span = upper - lower
        noise = rng.normal(loc=0.0, scale=0.05, size=(pop_size - 1, baseline_vector.size))
        sampling[1:] = np.clip(baseline_vector + noise * span, lower, upper)

    result = minimize(
        problem,
        NSGA2(pop_size=pop_size, sampling=sampling, eliminate_duplicates=True),
        ("n_gen", 4),
        seed=7,
        verbose=False,
    )

    if result.X is None or result.F is None:
        baseline_objectives = problem.evaluate([baseline_vector], return_values_of=["F"])
        return [baseline_vector.tolist()], baseline_objectives.tolist()

    candidate_matrix = np.atleast_2d(result.X)
    objective_matrix = np.atleast_2d(result.F)
    return candidate_matrix.tolist(), objective_matrix.tolist()


def _select_reference_corner_vector(
    candidate_vectors: list[list[float]],
    objective_rows: list[list[float]],
) -> list[float]:
    if not candidate_vectors:
        return _initial_corner_vector(CornerProblemLayout())
    best_index = min(
        range(len(candidate_vectors)),
        key=lambda index: max(objective_rows[index]) if objective_rows else float("inf"),
    )
    return candidate_vectors[best_index]


def _build_surface_models_from_corner_vector(vector: list[float]) -> dict[str, ParameterSurfaceModel]:
    from dataset_generator import LENGTHS_UM, WIDTHS_UM

    layout = CornerProblemLayout()
    decoded = layout.decode(vector)
    corners = CornerParameterSet(
        w_min_l_min=decoded["w_min_l_min"],
        w_min_l_max=decoded["w_min_l_max"],
        w_max_l_min=decoded["w_max_l_min"],
        w_max_l_max=decoded["w_max_l_max"],
    )
    w_bounds = (float(min(WIDTHS_UM)), float(max(WIDTHS_UM)))
    l_bounds = (float(min(LENGTHS_UM)), float(max(LENGTHS_UM)))
    return {
        parameter_name: BilinearSurfaceModel.from_corners(parameter_name, corners, w_bounds, l_bounds)
        for parameter_name in PARAMETER_NAMES
    }


def _params_from_surface_models(
    w_um: float,
    l_um: float,
    surface_models: dict[str, ParameterSurfaceModel],
) -> dict[str, float]:
    return _clip_model_params(
        {
            parameter_name: surface_models[parameter_name](w_um, l_um)
            for parameter_name in PARAMETER_NAMES
        }
    )


def _point_summary(
    target_row: MetricTarget,
    model_params: dict[str, float],
) -> tuple[dict[str, float], dict[str, float | str]]:
    from simulator import simulate_metrics_for_point

    simulated = simulate_metrics_for_point(target_row.w_um, target_row.l_um, model_params)
    point_errors = summarize_point_errors(simulated, target_row.as_metric_dict())
    return simulated, point_errors


def _score_point_errors(point_errors: dict[str, float | str]) -> float:
    objective_values = [float(point_errors[metric_name]) for metric_name in CORNER_OBJECTIVE_NAMES]
    return max(objective_values) + 0.1 * sum(objective_values) / len(objective_values)


def _focus_metric_names(point_errors: dict[str, float | str]) -> list[str]:
    worst_error = float(point_errors["worst_relative_error"])
    threshold = max(worst_error * 0.8, 0.02)
    metric_names = [
        metric_name
        for metric_name in CORNER_OBJECTIVE_NAMES
        if float(point_errors[metric_name]) >= threshold
    ]
    return metric_names or list(CORNER_OBJECTIVE_NAMES)


def _candidate_starting_params(
    target: MetricTarget,
    surface_models: dict[str, ParameterSurfaceModel],
) -> list[dict[str, float]]:
    baseline_params = _current_model_params(target.w_um, target.l_um)
    surface_params = _params_from_surface_models(target.w_um, target.l_um, surface_models)
    blended_params = _clip_model_params(
        {
            parameter_name: 0.75 * baseline_params[parameter_name] + 0.25 * surface_params[parameter_name]
            for parameter_name in PARAMETER_NAMES
        }
    )
    return [baseline_params, surface_params, blended_params]


def _select_starting_params(
    target: MetricTarget,
    surface_models: dict[str, ParameterSurfaceModel],
) -> tuple[dict[str, float], float]:
    best_params: dict[str, float] | None = None
    best_score = float("inf")
    best_worst_error = float("inf")

    for candidate_params in _candidate_starting_params(target, surface_models):
        try:
            _simulated, point_errors = _point_summary(target, candidate_params)
        except Exception:
            continue

        score = _score_point_errors(point_errors)
        worst_error = float(point_errors["worst_relative_error"])
        if (score, worst_error) < (best_score, best_worst_error):
            best_params = candidate_params
            best_score = score
            best_worst_error = worst_error

    if best_params is None:
        fallback = _params_from_surface_models(target.w_um, target.l_um, surface_models)
        return fallback, float("inf")
    return best_params, best_score


def _select_focus_parameters(
    target: MetricTarget,
    base_params: dict[str, float],
    point_errors: dict[str, float | str],
    top_k: int = 6,
) -> list[str]:
    import math

    from sensitivity import finite_difference_sensitivity
    from simulator import simulate_metrics_for_point

    base_metrics = simulate_metrics_for_point(target.w_um, target.l_um, base_params)
    focus_metrics = _focus_metric_names(point_errors)
    sensitivities = finite_difference_sensitivity(
        base_params=base_params,
        parameter_steps=_parameter_steps(),
        evaluator=lambda params: simulate_metrics_for_point(target.w_um, target.l_um, _clip_model_params(params)),
    )

    target_metrics = target.as_metric_dict()
    parameter_scores: dict[str, float] = {}
    for parameter_name in PARAMETER_NAMES:
        score = 0.0
        for metric_name in focus_metrics:
            sensitivity_value = sensitivities[parameter_name][metric_name]
            if math.isnan(sensitivity_value):
                continue
            metric_scale = max(abs(base_metrics[metric_name]), abs(target_metrics[metric_name]), 1.0e-20)
            parameter_scale = max(abs(base_params[parameter_name]), 1.0e-20)
            relative_sensitivity = abs(sensitivity_value) * parameter_scale / metric_scale
            score = max(score, relative_sensitivity)
        parameter_scores[parameter_name] = score

    ranked_names = sorted(
        PARAMETER_NAMES,
        key=lambda name: (parameter_scores[name], abs(base_params[name])),
        reverse=True,
    )
    return ranked_names[:top_k]


def _refine_point_with_de(
    target: MetricTarget,
    base_params: dict[str, float],
    base_score: float,
) -> tuple[dict[str, float], float]:
    from scipy.optimize import differential_evolution

    try:
        _simulated, base_errors = _point_summary(target, base_params)
    except Exception:
        return base_params, base_score

    if float(base_errors["worst_relative_error"]) <= 0.04:
        return base_params, base_score

    focus_parameters = _select_focus_parameters(target, base_params, base_errors, top_k=6)
    local_bounds = bounded_local_box(base_params, parameter_bounds(), relative_radius=0.15)
    search_bounds = [local_bounds[name] for name in focus_parameters]

    def objective(vector) -> float:
        params = dict(base_params)
        for parameter_name, value in zip(focus_parameters, vector, strict=True):
            params[parameter_name] = float(value)
        params = _clip_model_params(params)
        try:
            _simulated, point_errors = _point_summary(target, params)
            return _score_point_errors(point_errors)
        except Exception:
            return 1.0e6

    result = differential_evolution(
        objective,
        bounds=search_bounds,
        seed=7,
        maxiter=12,
        popsize=6,
        polish=False,
        workers=1,
    )
    candidate_params = dict(base_params)
    for parameter_name, value in zip(focus_parameters, result.x, strict=True):
        candidate_params[parameter_name] = float(value)
    candidate_params = _clip_model_params(candidate_params)
    candidate_score = objective(result.x)
    if candidate_score < base_score:
        return candidate_params, candidate_score
    return base_params, base_score


def _local_tune_target_rows(
    target_rows: list[MetricTarget],
    surface_models: dict[str, ParameterSurfaceModel],
) -> list[dict[str, float]]:
    import numpy as np
    from scipy.optimize import minimize

    tuned_rows: list[dict[str, float]] = []
    global_bounds = parameter_bounds()

    for target in target_rows:
        base_params, base_score = _select_starting_params(target, surface_models)
        local_box = bounded_local_box(base_params, global_bounds, relative_radius=0.10)
        x0 = np.asarray([base_params[name] for name in PARAMETER_NAMES], dtype=float)
        bounds = [local_box[name] for name in PARAMETER_NAMES]

        def objective(vector: np.ndarray) -> float:
            params = _clip_model_params(
                {name: float(value) for name, value in zip(PARAMETER_NAMES, vector, strict=True)}
            )
            try:
                _simulated, point_errors = _point_summary(target, params)
                return _score_point_errors(point_errors)
            except Exception:
                return 1.0e6

        result = minimize(
            objective,
            x0,
            method="Powell",
            bounds=bounds,
            options={"maxiter": 20, "maxfev": 150, "xtol": 1e-4, "ftol": 1e-4},
        )
        candidate_vector = np.asarray(result.x, dtype=float)
        candidate_score = objective(candidate_vector)
        best_vector = candidate_vector if candidate_score < base_score else x0
        tuned_params = _clip_model_params(
            {name: float(value) for name, value in zip(PARAMETER_NAMES, best_vector, strict=True)}
        )
        tuned_params, _best_score = _refine_point_with_de(
            target=target,
            base_params=tuned_params,
            base_score=min(base_score, candidate_score),
        )
        tuned_rows.append({"w_um": target.w_um, "l_um": target.l_um, **tuned_params})

    return tuned_rows


def _fit_surface_models_from_rows(rows: list[dict[str, float]]) -> dict[str, ParameterSurfaceModel]:
    return {
        parameter_name: fit_global_parameter_plane(parameter_name, rows)
        for parameter_name in PARAMETER_NAMES
    }


def _collect_rows_from_surface_models(
    target_rows: list[MetricTarget],
    surface_models: dict[str, ParameterSurfaceModel],
) -> tuple[list[dict[str, float]], list[dict[str, float]], list[dict[str, float | str]], float]:
    param_rows: list[dict[str, float]] = []
    metric_rows: list[dict[str, float]] = []
    error_rows: list[dict[str, float | str]] = []
    worst_relative_error = 0.0

    for target in target_rows:
        model_params = _params_from_surface_models(target.w_um, target.l_um, surface_models)
        simulated, point_errors = _point_summary(target, model_params)
        worst_relative_error = max(worst_relative_error, float(point_errors["worst_relative_error"]))

        param_rows.append({"w_um": target.w_um, "l_um": target.l_um, **model_params})
        metric_rows.append({"w_um": target.w_um, "l_um": target.l_um, **simulated})

        for metric_name, target_value in target.as_metric_dict().items():
            error_rows.append(
                {
                    "w_um": target.w_um,
                    "l_um": target.l_um,
                    "metric_name": metric_name,
                    "target_value": target_value,
                    "simulated_value": simulated[metric_name],
                    "relative_error": float(point_errors[metric_name]),
                }
            )

    return param_rows, metric_rows, error_rows, worst_relative_error


def _collect_sensitivity_rows() -> list[dict[str, float | str]]:
    from sensitivity import finite_difference_sensitivity
    from simulator import simulate_metrics_for_point

    rows: list[dict[str, float | str]] = []
    steps = _parameter_steps()
    for w_um, l_um, corner_name in _corner_sizes():
        base_params = _current_model_params(w_um, l_um)
        sensitivities = finite_difference_sensitivity(
            base_params=base_params,
            parameter_steps=steps,
            evaluator=lambda params, w=w_um, l=l_um: simulate_metrics_for_point(w, l, params),
        )
        for parameter_name, metric_map in sensitivities.items():
            for metric_name, sensitivity_value in metric_map.items():
                rows.append(
                    {
                        "corner_name": corner_name,
                        "w_um": w_um,
                        "l_um": l_um,
                        "parameter_name": parameter_name,
                        "metric_name": metric_name,
                        "sensitivity": sensitivity_value,
                    }
                )
    return rows


def _pareto_rows_for_plot(objective_rows: list[list[float]]) -> list[dict[str, float | int]]:
    rows: list[dict[str, float | int]] = []
    for candidate_id, objective_values in enumerate(objective_rows, start=1):
        row: dict[str, float | int] = {"candidate_id": candidate_id}
        for metric_name, objective_value in zip(CORNER_OBJECTIVE_NAMES, objective_values, strict=True):
            row[metric_name] = float(objective_value)
        rows.append(row)
    return rows


def _generate_plots(
    output_dir: Path,
    pareto_rows: list[dict[str, float | int]],
    error_rows: list[dict[str, float | str]],
    calibrated_param_rows: list[dict[str, float]],
) -> None:
    if pareto_rows:
        plot_pareto_front(
            output_dir / "pareto_front.png",
            pareto_rows,
            x_metric="vtlin_v",
            y_metric="idsat_a",
        )

    for metric_name in CORNER_OBJECTIVE_NAMES:
        metric_error_rows = [row for row in error_rows if row["metric_name"] == metric_name]
        if metric_error_rows:
            plot_error_heatmap(
                output_dir / f"error_heatmap_{metric_name}.png",
                metric_error_rows,
                metric_name=metric_name,
            )
            plot_target_vs_simulated(
                output_dir / f"target_vs_simulated_{metric_name}.png",
                error_rows,
                metric_name=metric_name,
            )

    for parameter_name in PARAMETER_NAMES:
        plot_parameter_surface(
            output_dir / f"parameter_surface_{parameter_name}.png",
            calibrated_param_rows,
            parameter_name,
        )


def run_full_calibration(
    target_csv_path: str | Path = DEFAULT_TARGET_CSV,
    output_dir: str | Path = CALIBRATION_OUTPUT_DIR,
) -> int:
    from targets import MetricTargetSet

    target_csv_path = Path(target_csv_path)
    output_dir = Path(output_dir)
    targets = MetricTargetSet.from_csv(target_csv_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    corner_targets = _build_corner_targets(targets.rows)
    candidate_vectors, objective_rows = _run_corner_nsga(corner_targets)
    export_corner_pareto_candidates(output_dir / "pareto_candidates.csv", candidate_vectors, objective_rows)
    pareto_rows = _pareto_rows_for_plot(objective_rows)

    reference_corner_vector = _select_reference_corner_vector(candidate_vectors, objective_rows)
    initial_surface_models = _build_surface_models_from_corner_vector(reference_corner_vector)

    local_tuned_rows = _local_tune_target_rows(targets.rows, initial_surface_models)
    write_csv_rows(output_dir / "local_tuned_params.csv", local_tuned_rows)

    refitted_surface_models = _fit_surface_models_from_rows(local_tuned_rows)
    refitted_param_rows, _refitted_metric_rows, _refitted_error_rows, _refitted_worst_error = _collect_rows_from_surface_models(
        targets.rows,
        refitted_surface_models,
    )
    write_csv_rows(output_dir / "refitted_global_params.csv", refitted_param_rows)

    param_rows, metric_rows, error_rows, worst_relative_error = _collect_rows_from_surface_models(
        targets.rows,
        refitted_surface_models,
    )
    sensitivity_rows = _collect_sensitivity_rows()

    write_csv_rows(output_dir / "calibrated_params.csv", param_rows)
    write_csv_rows(output_dir / "calibrated_metrics.csv", metric_rows)
    write_csv_rows(output_dir / "calibration_error_report.csv", error_rows)
    write_csv_rows(output_dir / "sensitivity_report.csv", sensitivity_rows)
    _generate_plots(output_dir, pareto_rows, error_rows, param_rows)
    write_markdown_summary(
        output_dir / "calibration_summary.md",
        worst_relative_error=worst_relative_error,
        target_count=len(targets.rows),
        passed=worst_relative_error < 0.03,
    )

    print(f"Target rows: {len(targets.rows)}")
    print(f"Worst-case relative error: {worst_relative_error:.6e}")
    print(f"Passed <3% target: {'yes' if worst_relative_error < 0.03 else 'no'}")
    print(f"Output directory: {output_dir}")
    return 0 if worst_relative_error < 0.03 else 1
