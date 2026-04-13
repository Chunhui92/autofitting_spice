from __future__ import annotations

PARAMETER_NAMES = [
    "toxe",
    "vth0",
    "u0",
    "vsat",
    "rdsw",
    "nfactor",
    "eta0",
    "cit",
    "voff",
    "k2",
    "ub",
    "uc",
    "a0",
    "keta",
]


def parameter_bounds() -> dict[str, tuple[float, float]]:
    return {
        "toxe": (0.8e-9, 1.4e-9),
        "vth0": (0.15, 0.8),
        "u0": (150.0, 900.0),
        "vsat": (5.0e4, 1.8e5),
        "rdsw": (50.0, 400.0),
        "nfactor": (0.8, 2.0),
        "eta0": (0.0, 0.15),
        "cit": (1.0e-5, 3.0e-4),
        "voff": (-0.35, 0.05),
        "k2": (-0.1, 0.15),
        "ub": (1.0e-19, 1.0e-17),
        "uc": (-0.08, 0.02),
        "a0": (0.2, 2.0),
        "keta": (-0.1, 0.05),
    }


def default_parameter_guess() -> dict[str, float]:
    bounds = parameter_bounds()
    return {name: (lower + upper) / 2.0 for name, (lower, upper) in bounds.items()}
