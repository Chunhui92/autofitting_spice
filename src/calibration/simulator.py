from __future__ import annotations

from calibration.dataset_generator import VDD, VLIN, configure_pyspice_runtime, simulate_transfer_measures


def build_simulation_model_params(model_params: dict[str, float]) -> dict[str, float]:
    return {
        "level": 54,
        "version": 4.8,
        **model_params,
    }


def simulate_metrics_for_point(w_um: float, l_um: float, model_params: dict[str, float]) -> dict[str, float]:
    configure_pyspice_runtime()
    sim_params = build_simulation_model_params(model_params)
    threshold_target = 1e-8 * (w_um / l_um)
    lin_measures = simulate_transfer_measures(w_um, l_um, VLIN, sim_params, threshold_target)
    sat_measures = simulate_transfer_measures(w_um, l_um, VDD, sim_params, threshold_target)
    return {
        "idoff_a": float(sat_measures["idoff"]),
        "isoff_a": float(sat_measures["isoff"]),
        "vtlin_v": float(lin_measures["vtx"]),
        "vtsat_v": float(sat_measures["vtx"]),
        "idlin_a": float(lin_measures["idon"]),
        "idsat_a": float(sat_measures["idon"]),
    }
