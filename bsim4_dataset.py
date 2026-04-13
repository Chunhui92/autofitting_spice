import csv
import hashlib
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PySpice.Spice.NgSpice.SimulationType import SIMULATION_TYPE
from PySpice.Spice.NgSpice.Shared import NgSpiceShared
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

from calibration.parameter_bounds import PARAMETER_NAMES


VDD = 1.8
VLIN = 0.05
VG_STEP = 0.01
TEMPERATURE_C = 25

WIDTHS_UM = np.asarray([0.14, 0.28, 0.56, 1.5, 2.7, 5.4], dtype=float)
LENGTHS_UM = np.asarray([0.028, 0.056, 0.14, 0.28, 0.56, 1.5, 2.7], dtype=float)

OUTPUT_DIR = Path("bsim4_dataset_output")
PARAM_CSV_PATH = OUTPUT_DIR / "virtual_mosfet_params.csv"
METRIC_CSV_PATH = OUTPUT_DIR / "virtual_mosfet_metrics.csv"
PLOT_W_PATH = OUTPUT_DIR / "metrics_vs_w.png"
PLOT_L_PATH = OUTPUT_DIR / "metrics_vs_l.png"


@dataclass
class DeviceRecord:
    w_um: float
    l_um: float
    noise_model: float
    toxe: float
    vth0: float
    u0: float
    vsat: float
    rdsw: float
    nfactor: float
    eta0: float
    cit: float
    voff: float
    k2: float
    ub: float
    uc: float
    a0: float
    keta: float
    idoff_a: float
    isoff_a: float
    vtlin_v: float
    vtsat_v: float
    idlin_a: float
    idsat_a: float


def configure_pyspice_runtime() -> None:
    os.environ.setdefault("SPICE_LIB_DIR", "/opt/homebrew/share/ngspice")
    if Path("/opt/homebrew/lib/libngspice.dylib").exists():
        NgSpiceShared.LIBRARY_PATH = "/opt/homebrew/lib/libngspice{}.dylib"
    SIMULATION_TYPE.setdefault(46, SIMULATION_TYPE["last"])


def normalize_log_scale(value: float, values: np.ndarray) -> float:
    log_values = np.log10(values)
    return float((np.log10(value) - log_values.min()) / (log_values.max() - log_values.min()))


def deterministic_noise(tag: str, w_um: float, l_um: float, amplitude: float) -> float:
    key = f"{tag}:{w_um:.6f}:{l_um:.6f}".encode("utf-8")
    digest = hashlib.sha256(key).hexdigest()
    unit = int(digest[:12], 16) / float(16**12 - 1)
    return amplitude * (2.0 * unit - 1.0)


def build_model_params(w_um: float, l_um: float) -> dict[str, float]:
    width_norm = normalize_log_scale(w_um, WIDTHS_UM)
    length_norm = normalize_log_scale(l_um, LENGTHS_UM)

    narrow = 1.0 - width_norm
    short = 1.0 - length_norm
    model_noise = deterministic_noise("model", w_um, l_um, 0.035)

    # 用平滑函数而不是离散跳变来构造“虚拟工艺”，确保电学特性会随 W/L 连续变化。
    return {
        "level": 54,
        "version": 4.8,
        "toxe": (1.0e-9 + 0.15e-9 * length_norm) * (1.0 + 0.25 * model_noise),
        "vth0": 0.26 + 0.08 * length_norm + 0.035 * narrow + 0.012 * model_noise,
        "u0": (420.0 + 220.0 * width_norm + 80.0 * length_norm) * (1.0 + 0.16 * model_noise),
        "vsat": (9.5e4 + 2.0e4 * width_norm + 1.0e4 * short) * (1.0 + 0.14 * model_noise),
        "rdsw": (120.0 + 60.0 * length_norm + 40.0 * narrow) * (1.0 + 0.18 * model_noise),
        "nfactor": 1.04 + 0.06 * length_norm + 0.04 * narrow + 0.02 * model_noise,
        "eta0": 0.02 + 0.03 * short + 0.01 * narrow + 0.006 * model_noise,
        "cit": (8.0e-5 + 5.0e-5 * short + 2.5e-5 * narrow) * (1.0 + 0.18 * model_noise),
        "voff": -0.11 - 0.025 * short + 0.018 * length_norm + 0.008 * model_noise,
        "k2": 0.008 + 0.045 * length_norm - 0.016 * width_norm + 0.006 * model_noise,
        "ub": (1.5e-18 + 1.8e-18 * short + 0.8e-18 * narrow) * (1.0 + 0.15 * model_noise),
        "uc": -0.035 - 0.012 * short + 0.01 * length_norm + 0.003 * model_noise,
        "a0": 0.82 + 0.38 * width_norm + 0.16 * short + 0.03 * model_noise,
        "keta": -0.028 - 0.02 * short + 0.011 * length_norm + 0.004 * model_noise,
    }


def build_transfer_circuit(w_um: float, l_um: float, drain_voltage: float, model_params: dict[str, float]) -> Circuit:
    circuit = Circuit(f"Virtual BSIM4 NMOS W={w_um:.3f}um L={l_um:.3f}um")
    circuit.V("dd", "Vd", circuit.gnd, drain_voltage @ u_V)
    circuit.V("gg", "Vg", circuit.gnd, 0 @ u_V)
    circuit.V("ss", "Vs", circuit.gnd, 0 @ u_V)
    circuit.V("bb", "Vb", circuit.gnd, 0 @ u_V)
    circuit.model("NMOS_BSIM4", "nmos", **model_params)
    circuit.MOSFET(
        "1",
        drain="Vd",
        gate="Vg",
        source="Vs",
        bulk="Vb",
        model="NMOS_BSIM4",
        w=w_um @ u_um,
        l=l_um @ u_um,
    )
    return circuit


MEASURE_PATTERN = re.compile(r"^\s*([A-Za-z]\w*)\s*=\s*([+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)\s*$", re.MULTILINE)


def parse_measured_values(stdout: str) -> dict[str, float]:
    return {match.group(1).lower(): float(match.group(2)) for match in MEASURE_PATTERN.finditer(stdout)}


def simulate_transfer_measures(
    w_um: float,
    l_um: float,
    drain_voltage: float,
    model_params: dict[str, float],
    threshold_target: float,
) -> dict[str, float]:
    circuit = build_transfer_circuit(w_um, l_um, drain_voltage, model_params)
    simulator = circuit.simulator(temperature=TEMPERATURE_C, nominal_temperature=TEMPERATURE_C)
    simulator.measure("dc", "vtx", f"when par('-i(vdd)')={threshold_target:.12e} cross=1")
    simulator.measure("dc", "idon", f"find par('-i(vdd)') at={VDD:.6f}")
    simulator.measure("dc", "idoff", "find par('-i(vdd)') at=0")
    simulator.measure("dc", "isoff", "find par('abs(i(vss))') at=0")
    simulator.dc(Vgg=slice(0, VDD, VG_STEP))
    return parse_measured_values(simulator._ngspice_shared.stdout)


def extract_metrics(w_um: float, l_um: float) -> DeviceRecord:
    model_params = build_model_params(w_um, l_um)
    model_noise = deterministic_noise("model", w_um, l_um, 0.035)
    from calibration.simulator import simulate_metrics_for_point

    metrics = simulate_metrics_for_point(w_um, l_um, model_params)

    return DeviceRecord(
        w_um=w_um,
        l_um=l_um,
        noise_model=model_noise,
        toxe=model_params["toxe"],
        vth0=model_params["vth0"],
        u0=model_params["u0"],
        vsat=model_params["vsat"],
        rdsw=model_params["rdsw"],
        nfactor=model_params["nfactor"],
        eta0=model_params["eta0"],
        cit=model_params["cit"],
        voff=model_params["voff"],
        k2=model_params["k2"],
        ub=model_params["ub"],
        uc=model_params["uc"],
        a0=model_params["a0"],
        keta=model_params["keta"],
        idoff_a=metrics["idoff_a"],
        isoff_a=metrics["isoff_a"],
        vtlin_v=metrics["vtlin_v"],
        vtsat_v=metrics["vtsat_v"],
        idlin_a=metrics["idlin_a"],
        idsat_a=metrics["idsat_a"],
    )


def write_dataset_csvs(records: list[DeviceRecord], param_output_path: Path, metric_output_path: Path) -> None:
    param_output_path.parent.mkdir(parents=True, exist_ok=True)

    param_fields = ["w_um", "l_um", "noise_model", *PARAMETER_NAMES]
    metric_fields = [
        "w_um",
        "l_um",
        "idoff_a",
        "isoff_a",
        "vtlin_v",
        "vtsat_v",
        "idlin_a",
        "idsat_a",
    ]

    with param_output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=param_fields)
        writer.writeheader()
        for record in records:
            row = asdict(record)
            writer.writerow({field: row[field] for field in param_fields})

    with metric_output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=metric_fields)
        writer.writeheader()
        for record in records:
            row = asdict(record)
            writer.writerow({field: row[field] for field in metric_fields})


def get_metric_value(record: DeviceRecord, metric_name: str) -> float:
    return float(getattr(record, metric_name))


def format_size_label(size_um: float) -> str:
    if size_um < 1.0:
        return f"{size_um * 1000:.0f}nm"
    return f"{size_um:.2f}um"


def plot_metrics_vs_w(records: list[DeviceRecord], output_path: Path) -> None:
    metrics = [
        ("idoff_a", "Idoff (A)", True),
        ("isoff_a", "Isoff (A)", True),
        ("vtlin_v", "Vtlin (V)", False),
        ("vtsat_v", "Vtsat (V)", False),
        ("idlin_a", "Idlin (A)", True),
        ("idsat_a", "Idsat (A)", True),
    ]

    fig, axes = plt.subplots(3, 2, figsize=(14, 12))
    axes = axes.flatten()

    for axis, (metric_name, ylabel, use_log_y) in zip(axes, metrics):
        for l_um in LENGTHS_UM:
            subset = [record for record in records if np.isclose(record.l_um, l_um)]
            x_values = [record.w_um for record in subset]
            y_values = [get_metric_value(record, metric_name) for record in subset]
            axis.plot(x_values, y_values, marker="o", linewidth=1.8, label=f"L={format_size_label(l_um)}")

        axis.set_xscale("log")
        if use_log_y:
            axis.set_yscale("log")
        axis.set_xlabel("W (um)")
        axis.set_ylabel(ylabel)
        axis.set_title(f"{ylabel} vs W")
        axis.grid(True, which="both", alpha=0.25)

    axes[0].legend(fontsize=8, loc="best")
    fig.suptitle("Virtual BSIM4 Metrics vs Width", fontsize=14)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def plot_metrics_vs_l(records: list[DeviceRecord], output_path: Path) -> None:
    metrics = [
        ("idoff_a", "Idoff (A)", True),
        ("isoff_a", "Isoff (A)", True),
        ("vtlin_v", "Vtlin (V)", False),
        ("vtsat_v", "Vtsat (V)", False),
        ("idlin_a", "Idlin (A)", True),
        ("idsat_a", "Idsat (A)", True),
    ]

    fig, axes = plt.subplots(3, 2, figsize=(14, 12))
    axes = axes.flatten()

    for axis, (metric_name, ylabel, use_log_y) in zip(axes, metrics):
        for w_um in WIDTHS_UM:
            subset = [record for record in records if np.isclose(record.w_um, w_um)]
            x_values = [record.l_um for record in subset]
            y_values = [get_metric_value(record, metric_name) for record in subset]
            axis.plot(x_values, y_values, marker="o", linewidth=1.8, label=f"W={format_size_label(w_um)}")

        axis.set_xscale("log")
        if use_log_y:
            axis.set_yscale("log")
        axis.set_xlabel("L (um)")
        axis.set_ylabel(ylabel)
        axis.set_title(f"{ylabel} vs L")
        axis.grid(True, which="both", alpha=0.25)

    axes[0].legend(fontsize=8, loc="best")
    fig.suptitle("Virtual BSIM4 Metrics vs Length", fontsize=14)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def main() -> None:
    records: list[DeviceRecord] = []
    for w_um in WIDTHS_UM:
        for l_um in LENGTHS_UM:
            records.append(extract_metrics(float(w_um), float(l_um)))

    write_dataset_csvs(records, PARAM_CSV_PATH, METRIC_CSV_PATH)
    plot_metrics_vs_w(records, PLOT_W_PATH)
    plot_metrics_vs_l(records, PLOT_L_PATH)

    print(f"Generated {len(records)} virtual devices")
    print(f"Params CSV: {PARAM_CSV_PATH}")
    print(f"Metrics CSV: {METRIC_CSV_PATH}")
    print(f"Plot vs W: {PLOT_W_PATH}")
    print(f"Plot vs L: {PLOT_L_PATH}")


if __name__ == "__main__":
    configure_pyspice_runtime()
    main()
