from __future__ import annotations

import csv
from pathlib import Path

from calibration.plotting import (
    plot_error_heatmap,
    plot_parameter_surface,
    plot_pareto_front,
    plot_target_vs_simulated,
)


def write_csv_rows(
    path: Path,
    rows: list[dict[str, float | str]],
    fieldnames: list[str] | None = None,
) -> None:
    if not rows and fieldnames is None:
        return
    with path.open("w", encoding="utf-8", newline="") as fh:
        resolved_fieldnames = list(rows[0].keys()) if fieldnames is None else fieldnames
        writer = csv.DictWriter(fh, fieldnames=resolved_fieldnames)
        writer.writeheader()
        if rows:
            writer.writerows(rows)


def write_markdown_summary(
    path: Path,
    worst_relative_error: float,
    target_count: int,
    passed: bool,
    extra_lines: list[str] | None = None,
) -> None:
    lines = [
        "# Calibration Summary",
        "",
        f"- Target rows: {target_count}",
        f"- Worst-case relative error: {worst_relative_error:.6e}",
        f"- Passed <3% target: {'yes' if passed else 'no'}",
    ]
    if extra_lines:
        lines.extend(["", *extra_lines])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_pareto_candidates(
    path: Path,
    rows: list[dict[str, float | str]],
    fieldnames: list[str] | None = None,
) -> None:
    write_csv_rows(path, rows, fieldnames=fieldnames)


def write_calibration_plots(
    output_dir: Path,
    pareto_rows: list[dict[str, float | int | str]],
    error_rows: list[dict[str, float | str]],
    parameter_rows: list[dict[str, float]],
    parameter_names: list[str],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    if pareto_rows:
        plot_pareto_front(
            output_dir / "pareto_front_vtlin_v_vs_idsat_a.png",
            pareto_rows,
            x_metric="vtlin_v",
            y_metric="idsat_a",
        )

    metric_names = sorted({str(row["metric_name"]) for row in error_rows})
    for metric_name in metric_names:
        metric_rows = [row for row in error_rows if row["metric_name"] == metric_name]
        plot_error_heatmap(
            output_dir / f"error_heatmap_{metric_name}.png",
            metric_rows,
            metric_name=metric_name,
            value_key="relative_error",
        )
        plot_target_vs_simulated(
            output_dir / f"target_vs_simulated_{metric_name}.png",
            error_rows,
            metric_name=metric_name,
        )

    for parameter_name in parameter_names:
        if parameter_rows and parameter_name in parameter_rows[0]:
            plot_parameter_surface(
                output_dir / f"parameter_surface_{parameter_name}.png",
                parameter_rows,
                parameter_name=parameter_name,
            )
