from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .error_metrics import METRIC_NAMES


@dataclass(frozen=True)
class MetricTarget:
    w_um: float
    l_um: float
    idoff_a: float
    isoff_a: float
    vtlin_v: float
    vtsat_v: float
    idlin_a: float
    idsat_a: float

    def as_metric_dict(self) -> dict[str, float]:
        return {name: getattr(self, name) for name in METRIC_NAMES}


class MetricTargetSet:
    def __init__(self, rows: list[MetricTarget]) -> None:
        self.rows = rows
        self._by_size: dict[tuple[float, float], MetricTarget] = {}
        for row in rows:
            size = (row.w_um, row.l_um)
            if size in self._by_size:
                raise ValueError(f"duplicate metric target row for w_um={row.w_um}, l_um={row.l_um}")
            self._by_size[size] = row

    @classmethod
    def from_csv(cls, path: Path) -> "MetricTargetSet":
        with path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            rows = [
                MetricTarget(**{key: float(value) for key, value in row.items()})
                for row in reader
            ]
        return cls(rows)

    def get(self, w_um: float, l_um: float) -> MetricTarget:
        return self._by_size[(w_um, l_um)]
