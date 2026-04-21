from __future__ import annotations

from pathlib import Path
import math

import matplotlib
import numpy as np

matplotlib.use("Agg")

import matplotlib.pyplot as plt


def build_metric_grid(
    rows: list[dict[str, float]],
    value_key: str,
    fill_value: float = np.nan,
) -> tuple[list[float], list[float], np.ndarray]:
    widths = sorted({float(row["w_um"]) for row in rows})
    lengths = sorted({float(row["l_um"]) for row in rows})
    grid = np.full((len(widths), len(lengths)), fill_value, dtype=float)
    width_index = {value: index for index, value in enumerate(widths)}
    length_index = {value: index for index, value in enumerate(lengths)}
    for row in rows:
        grid[width_index[float(row["w_um"])], length_index[float(row["l_um"])]] = float(row[value_key])
    return widths, lengths, grid


def _prepare_output_path(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def plot_error_heatmap(
    path: Path,
    rows: list[dict[str, float]],
    metric_name: str,
    value_key: str = "relative_error",
) -> None:
    widths, lengths, grid = build_metric_grid(rows, value_key=value_key)
    _prepare_output_path(path)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    image = ax.imshow(grid.T, origin="lower", aspect="auto", cmap="magma")
    ax.set_xticks(range(len(widths)), [f"{value:g}" for value in widths])
    ax.set_yticks(range(len(lengths)), [f"{value:g}" for value in lengths])
    ax.set_xlabel("W (um)")
    ax.set_ylabel("L (um)")
    ax.set_title(f"{metric_name} {value_key.replace('_', ' ')}")
    fig.colorbar(image, ax=ax, label=value_key.replace("_", " "))
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_pareto_front(
    path: Path,
    rows: list[dict[str, float | int]],
    x_metric: str,
    y_metric: str,
) -> None:
    _prepare_output_path(path)
    fig, ax = plt.subplots(figsize=(6.5, 5.0))
    x_values = [float(row[x_metric]) for row in rows]
    y_values = [float(row[y_metric]) for row in rows]
    ax.scatter(x_values, y_values, s=44, c=np.linspace(0.2, 0.8, len(rows)) if rows else [])
    for row, x_value, y_value in zip(rows, x_values, y_values, strict=True):
        candidate_id = row.get("candidate_id")
        if candidate_id is not None:
            ax.annotate(str(candidate_id), (x_value, y_value), textcoords="offset points", xytext=(4, 4), fontsize=8)
    ax.set_xlabel(x_metric)
    ax.set_ylabel(y_metric)
    ax.set_title("Corner Pareto Boundary")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_target_vs_simulated(
    path: Path,
    rows: list[dict[str, float | str]],
    metric_name: str,
) -> None:
    filtered_rows = [row for row in rows if row["metric_name"] == metric_name]
    _prepare_output_path(path)
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    target_values = [float(row["target_value"]) for row in filtered_rows]
    simulated_values = [float(row["simulated_value"]) for row in filtered_rows]
    ax.scatter(target_values, simulated_values, s=40, alpha=0.85)
    if target_values and simulated_values:
        lower = min(min(target_values), min(simulated_values))
        upper = max(max(target_values), max(simulated_values))
        ax.plot([lower, upper], [lower, upper], linestyle="--", linewidth=1.2, color="black")
    ax.set_xlabel(f"Target {metric_name}")
    ax.set_ylabel(f"Simulated {metric_name}")
    ax.set_title(f"Target vs Simulated: {metric_name}")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_parameter_surface(path: Path, rows: list[dict[str, float]], parameter_name: str) -> None:
    widths, lengths, grid = build_metric_grid(rows, value_key=parameter_name)
    _prepare_output_path(path)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    image = ax.imshow(grid.T, origin="lower", aspect="auto", cmap="viridis")
    ax.set_xticks(range(len(widths)), [f"{value:g}" for value in widths])
    ax.set_yticks(range(len(lengths)), [f"{value:g}" for value in lengths])
    ax.set_xlabel("W (um)")
    ax.set_ylabel("L (um)")
    ax.set_title(f"Parameter Surface: {parameter_name}")
    fig.colorbar(image, ax=ax, label=parameter_name)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_parameter_trend_grid(
    path: Path,
    rows: list[dict[str, float]],
    parameter_names: list[str],
    vary_by: str,
) -> None:
    if vary_by not in {"w", "l"}:
        raise ValueError("vary_by must be 'w' or 'l'")
    if not parameter_names:
        raise ValueError("parameter_names must not be empty")

    _prepare_output_path(path)
    ncols = 3
    nrows = math.ceil(len(parameter_names) / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(5.2 * ncols, 3.1 * nrows), squeeze=False)
    all_axes = axes.flatten()

    x_key = "w_um" if vary_by == "w" else "l_um"
    group_key = "l_um" if vary_by == "w" else "w_um"
    x_label = "W (um)" if vary_by == "w" else "L (um)"
    group_label = "L" if vary_by == "w" else "W"

    for ax, parameter_name in zip(all_axes, parameter_names, strict=False):
        group_values = sorted({float(row[group_key]) for row in rows})
        for group_value in group_values:
            series = sorted(
                (row for row in rows if float(row[group_key]) == group_value),
                key=lambda row: float(row[x_key]),
            )
            x_values = [float(row[x_key]) for row in series]
            y_values = [float(row[parameter_name]) for row in series]
            ax.plot(
                x_values,
                y_values,
                marker="o",
                linewidth=1.6,
                markersize=3.8,
                label=f"{group_label}={group_value:g} um",
            )

        ax.set_title(parameter_name)
        ax.set_xlabel(x_label)
        ax.set_ylabel(parameter_name)
        ax.grid(True, alpha=0.25)
        ax.ticklabel_format(axis="y", style="sci", scilimits=(-2, 2))
        if group_values:
            ax.legend(fontsize=7, loc="best")

    for ax in all_axes[len(parameter_names):]:
        ax.axis("off")

    title_axis = "W" if vary_by == "w" else "L"
    fig.suptitle(f"Calibrated Parameter Trends vs {title_axis}", fontsize=15, y=0.995)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.985))
    fig.savefig(path, dpi=160)
    plt.close(fig)
