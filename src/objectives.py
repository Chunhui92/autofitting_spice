from __future__ import annotations

from error_metrics import METRIC_NAMES


def aggregate_metric_objectives(point_error_rows: list[dict[str, float]]) -> dict[str, float]:
    return {
        metric_name: max(row[metric_name] for row in point_error_rows)
        for metric_name in METRIC_NAMES
    }
