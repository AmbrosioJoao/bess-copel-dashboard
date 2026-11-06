from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import numpy as np
import pandas as pd

BASE_MVA = 10.0
BASE_KV = 13.8
Z_BASE = BASE_KV**2 / BASE_MVA
I_BASE = BASE_MVA * 1e3 / (np.sqrt(3) * BASE_KV)
V_MIN = 0.93
V_MAX = 1.05
N_BUS = 8
N_STEPS = 96
DT_H = 0.25

BUS_NAMES = ("SE 13,8 kV", "B1", "B2", "B3", "B4", "B5", "B6", "B7")
BRANCH_KM = (0.70, 0.98, 1.12, 0.84, 1.26, 0.98, 1.12)
R_KM = 0.22
X_KM = 0.30
PEAK_LOADS_KW = (0.0, 900.0, 1100.0, 1300.0, 800.0, 1400.0, 1000.0, 900.0)
LOAD_KINDS = ("none", "res", "com", "res", "com", "res", "ind", "res")
PV_SHARE = (0.0, 0.08, 0.10, 0.18, 0.10, 0.16, 0.22, 0.16)
PF_LOAD = 0.92
AMPACITY_A = 400.0
TRAFO_MVA = 10.0
S_RATING_FACTOR = 1.10
SOC_MIN_DEFAULT = 0.10
SOC_MAX_DEFAULT = 0.90

Z_PU = (R_KM + 1j * X_KM) * np.array(BRANCH_KM) / Z_BASE
R_PU = (R_KM * np.array(BRANCH_KM)) / Z_BASE

MODE_PEAK = "Corte de pico"
MODE_PV = "Suavização FV"
MODE_ARB = "Arbitragem tarifária"
MODE_VOLT = "Suporte de tensão"
MODE_MULTI = "EMS multi-serviço"
MODES = (MODE_MULTI, MODE_PEAK, MODE_PV, MODE_ARB, MODE_VOLT)

CHEMISTRY = {
    "LFP": {
        "label": "LFP · lítio-ferro-fosfato",
        "short": "LFP",
        "cycle_life": 6000,
        "safety": 5.0,
        "density": 3.0,
        "cost": 4.0,
        "power": 4.0,
        "capex_kwh": 1400.0,
        "color": "#00E5A8",
        "note": "Melhor equilíbrio entre segurança, vida útil e custo para ciclagem diária.",
    },
    "NMC": {
        "label": "NMC · níquel-manganês-cobalto",
        "short": "NMC",
        "cycle_life": 3500,
        "safety": 3.0,
        "density": 5.0,
        "cost": 3.0,
        "power": 5.0,
        "capex_kwh": 1700.0,
        "color": "#FFB020",
        "note": "Maior densidade energética; exige atenção redobrada a segurança e degradação.",
    },
    "Na-ion": {
        "label": "Na-ion · sódio-íon",
        "short": "Na-ion",
        "cycle_life": 4000,
        "safety": 4.4,
        "density": 2.5,
        "cost": 5.0,
        "power": 3.2,
        "capex_kwh": 1200.0,
        "color": "#39A0FF",
        "note": "Alternativa emergente, boa segurança e custo; densidade ainda é o gargalo.",
    },
    "VRFB": {
        "label": "VRFB · fluxo vanádio",
        "short": "VRFB",
        "cycle_life": 12000,
        "safety": 5.0,
        "density": 1.0,
        "cost": 2.2,
        "power": 2.0,
        "capex_kwh": 2000.0,
        "color": "#B388FF",
        "note": "Longa duração e vida útil elevada; menor densidade e maior área de implantação.",
    },
}


@dataclass
class SimulationResult:
    bess: pd.DataFrame
    base: pd.DataFrame
    v_bess: np.ndarray
    v_base: np.ndarray
    line_pct_bess: np.ndarray
    p_load_bus: np.ndarray
    p_pv_bus: np.ndarray
    bus_names: tuple[str, ...]
    metrics: dict
    params: dict


def _normalize(values: np.ndarray) -> np.ndarray:
    peak = float(np.max(values))
    return values / peak if peak > 0 else values


def _load_shape(kind: str, t: np.ndarray) -> np.ndarray:
    if kind == "res":
        shape = (
            0.50
            + 0.20 * np.exp(-0.5 * ((t - 8.0) / 1.8) ** 2)
            + 0.62 * np.exp(-0.5 * ((t - 19.2) / 2.2) ** 2)
        )
    elif kind == "com":
        shape = 0.52 + 0.50 * np.exp(-0.5 * ((t - 14.0) / 3.9) ** 2)
    elif kind == "ind":
        shape = 0.86 + 0.12 * np.exp(-0.5 * ((t - 13.0) / 5.0) ** 2)
    else:
        return np.zeros_like(t)
    return _normalize(shape)


def build_profiles(
    load_scale: float = 1.0,
    pv_mw: float = 5.5,
    cloud_event: bool = True,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    t = np.arange(N_STEPS) * DT_H
    p_load_bus = np.zeros((N_STEPS, N_BUS))
    for i in range(1, N_BUS):
        base = PEAK_LOADS_KW[i] / 1000.0 * load_scale
        shape = _load_shape(LOAD_KINDS[i], t)
        ripple = 1.0 + 0.012 * np.sin(2 * np.pi * t * 3 / 24 + i * 1.7)
        p_load_bus[:, i] = base * shape * ripple

    pv_shape = np.zeros_like(t)
    daylight = (t >= 6.0) & (t <= 18.0)
    pv_shape[daylight] = np.sin(np.pi * (t[daylight] - 6.0) / 12.0) ** 1.65
    if cloud_event:
        pv_shape *= 1.0 - 0.46 * np.exp(-0.5 * ((t - 14.75) / 0.30) ** 2)

    p_pv_bus = np.zeros((N_STEPS, N_BUS))
    for i in range(1, N_BUS):
        p_pv_bus[:, i] = pv_mw * PV_SHARE[i] * pv_shape

    p_load_bus[:, 0] = 0.0
    p_pv_bus[:, 0] = 0.0
    return p_load_bus, p_pv_bus, t


def run_power_flow(
    p_load_bus: np.ndarray,
    p_pv_bus: np.ndarray,
    p_bess_bus: np.ndarray,
    q_bess_bus: np.ndarray,
) -> dict:
    q_load_bus = p_load_bus * np.tan(np.arccos(PF_LOAD))
    s_inj = (
        (p_load_bus - p_pv_bus - p_bess_bus)
        + 1j * (q_load_bus - q_bess_bus)
    ) / BASE_MVA

    v = np.ones(N_BUS, dtype=complex)
    i_branch = np.zeros(N_BUS - 1, dtype=complex)
    for _ in range(40):
        i_bus = np.conj(s_inj / v)
        acc = 0j
        for k in range(N_BUS - 1, 0, -1):
            acc += i_bus[k]
            i_branch[k - 1] = acc

        v_new = np.ones(N_BUS, dtype=complex)
        for k in range(1, N_BUS):
            v_new[k] = v_new[k - 1] - Z_PU[k - 1] * i_branch[k - 1]

        if np.max(np.abs(v_new - v)) < 1e-8:
            v = v_new
            break
        v = v_new

    s_source = v[0] * np.conj(i_branch[0]) * BASE_MVA
    losses_mw = float(np.sum(np.abs(i_branch) ** 2 * R_PU) * BASE_MVA)
    line_pct = np.abs(i_branch) * I_BASE / AMPACITY_A * 100.0
    return {
        "v": np.abs(v),
        "i_branch": np.abs(i_branch),
        "source_mw": float(s_source.real),
        "source_mvar": float(s_source.imag),
        "loss_mw": losses_mw,
        "line_pct": line_pct,
        "line_max_pct": float(np.max(line_pct)),
        "trafo_pct": float(abs(s_source) / TRAFO_MVA * 100.0),
    }


def _p_requests(
    t_idx: int,
    t_hours: np.ndarray,
    net_mw: np.ndarray,
    pv_total_mw: np.ndarray,
    soc: float,
    power_mw: float,
    soc_min: float,
    soc_max: float,
    peak_threshold: float,
    mode: str,
    weights: tuple[float, float, float, float],
) -> tuple[float, float, float, float, float]:
    hour = float(t_hours[t_idx])
    p_peak = 0.0
    if net_mw[t_idx] > peak_threshold:
        p_peak = min(net_mw[t_idx] - peak_threshold, power_mw)
    elif net_mw[t_idx] < peak_threshold * 0.58 and soc < soc_max - 0.02:
        p_peak = -min((peak_threshold * 0.58 - net_mw[t_idx]) * 0.55, power_mw)
        if 8.0 <= hour < 15.0 and soc > 0.72 and net_mw[t_idx] >= 0:
            p_peak = 0.0

    p_pv = 0.0
    if t_idx > 0:
        delta = pv_total_mw[t_idx - 1] - pv_total_mw[t_idx]
        ramp = 0.015
        if delta > ramp:
            p_pv = min(delta * 1.15, power_mw)
        elif delta < -ramp:
            p_pv = max(delta * 1.15, -power_mw)

    p_arb = 0.0
    if 0.0 <= hour < 6.0 and soc < soc_max - 0.03:
        p_arb = -power_mw * 0.55
    elif 17.5 <= hour < 21.0 and soc > soc_min + 0.03:
        p_arb = power_mw * 0.55

    w = np.asarray(weights, dtype=float)
    w = w / w.max() if w.max() > 0 else np.zeros(4)
    w_peak, w_pv, w_arb, w_volt = (float(x) for x in w)

    if mode == MODE_PEAK:
        p_req = p_peak
    elif mode == MODE_PV:
        p_req = p_pv
    elif mode == MODE_ARB:
        p_req = p_arb
    elif mode == MODE_VOLT:
        p_req = 0.0
    else:
        p_req = w_peak * p_peak + w_pv * p_pv + w_arb * p_arb

    return p_req, p_peak, p_pv, p_arb, w_volt


def simulate_scenario(
    load_scale: float = 1.0,
    pv_mw: float = 5.5,
    cloud_event: bool = True,
    bess_power: float = 2.0,
    bess_energy: float = 8.0,
    bess_bus: int = 5,
    mode: str = MODE_MULTI,
    peak_threshold: float = 5.5,
    voltage_target: float = 0.99,
    weights: tuple[float, float, float, float] = (4.0, 2.0, 1.0, 2.0),
    chemistry: str = "LFP",
    protect_battery: bool = True,
    cycle_limit: float = 1.2,
    soc_min: float = SOC_MIN_DEFAULT,
    soc_max: float = SOC_MAX_DEFAULT,
    include_baseline: bool = True,
) -> SimulationResult:
    p_load_bus, p_pv_bus, t_hours = build_profiles(load_scale, pv_mw, cloud_event)
    p_load_total = p_load_bus.sum(axis=1)
    p_pv_total = p_pv_bus.sum(axis=1)
    net_mw = p_load_total - p_pv_total

    eta = 0.94
    power_mw = max(bess_power, 0.0)
    energy_mwh = max(bess_energy, 0.01)
    bess_bus = int(np.clip(bess_bus, 1, N_BUS - 1))
    s_rating = S_RATING_FACTOR * power_mw
    soc = 0.55

    rows = []
    v_bess = np.zeros((N_STEPS, N_BUS))
    line_pct_bess = np.zeros((N_STEPS, N_BUS - 1))
    throughput = 0.0

    for k in range(N_STEPS):
        p_req, p_peak, p_pv, p_arb, w_volt = _p_requests(
            k,
            t_hours,
            net_mw,
            p_pv_total,
            soc,
            power_mw,
            soc_min,
            soc_max,
            peak_threshold,
            mode,
            weights,
        )

        if power_mw <= 0:
            p_req = 0.0

        cycles_used = throughput / (2.0 * energy_mwh) if energy_mwh > 0 else 0.0
        if protect_battery and cycles_used >= cycle_limit:
            p_req = 0.0

        if p_req > 0:
            max_discharge = max((soc - soc_min) * energy_mwh * eta / DT_H, 0.0)
            p_req = min(p_req, max_discharge)
        elif p_req < 0:
            max_charge = max((soc_max - soc) * energy_mwh / (eta * DT_H), 0.0)
            p_req = max(p_req, -max_charge)

        p_bess = float(np.clip(p_req, -power_mw, power_mw))
        p_bess_bus = np.zeros(N_BUS)
        p_bess_bus[bess_bus] = p_bess
        q_bess_bus = np.zeros(N_BUS)

        pf0 = run_power_flow(p_load_bus[k], p_pv_bus[k], p_bess_bus, q_bess_bus)
        q_bess = 0.0
        if s_rating > 0 and w_volt > 0:
            q_max = float(np.sqrt(max(s_rating**2 - p_bess**2, 0.0)))
            error = voltage_target - pf0["v"][bess_bus]
            if abs(error) > 0.003:
                q_bess = float(np.clip(error / 0.040, -1.0, 1.0) * q_max * w_volt)
        q_bess_bus[bess_bus] = q_bess

        pf = run_power_flow(p_load_bus[k], p_pv_bus[k], p_bess_bus, q_bess_bus)
        v_bess[k] = pf["v"]
        line_pct_bess[k] = pf["line_pct"]

        if p_bess >= 0:
            soc -= p_bess * DT_H / (energy_mwh * eta)
        else:
            soc -= p_bess * DT_H * eta / energy_mwh
        soc = float(np.clip(soc, 0.0, 1.0))
        throughput += abs(p_bess) * DT_H

        rows.append(
            {
                "time_h": float(t_hours[k]),
                "load_mw": float(p_load_total[k]),
                "pv_mw": float(p_pv_total[k]),
                "net_mw": float(net_mw[k]),
                "bess_p_mw": p_bess,
                "bess_q_mvar": q_bess,
                "soc": soc,
                "grid_mw": pf["source_mw"],
                "grid_mvar": pf["source_mvar"],
                "loss_mw": pf["loss_mw"],
                "vmin": float(pf["v"].min()),
                "vmax": float(pf["v"].max()),
                "v_bess": float(pf["v"][bess_bus]),
                "trafo_pct": pf["trafo_pct"],
                "line_max_pct": pf["line_max_pct"],
                "p_peak_req": p_peak,
                "p_pv_req": p_pv,
                "p_arb_req": p_arb,
                "q_volt": q_bess,
                "c_rate": abs(p_bess) / energy_mwh,
            }
        )

    bess_df = pd.DataFrame(rows)

    if include_baseline:
        base_rows = []
        v_base = np.zeros((N_STEPS, N_BUS))
        zero = np.zeros(N_BUS)
        for k in range(N_STEPS):
            pf = run_power_flow(p_load_bus[k], p_pv_bus[k], zero, zero)
            v_base[k] = pf["v"]
            base_rows.append(
                {
                    "time_h": float(t_hours[k]),
                    "load_mw": float(p_load_total[k]),
                    "pv_mw": float(p_pv_total[k]),
                    "net_mw": float(net_mw[k]),
                    "grid_mw": pf["source_mw"],
                    "grid_mvar": pf["source_mvar"],
                    "loss_mw": pf["loss_mw"],
                    "vmin": float(pf["v"].min()),
                    "vmax": float(pf["v"].max()),
                    "trafo_pct": pf["trafo_pct"],
                    "line_max_pct": pf["line_max_pct"],
                }
            )
        base_df = pd.DataFrame(base_rows)
    else:
        base_df = pd.DataFrame()
        v_base = np.zeros((0, N_BUS))

    metrics = _metrics(bess_df, base_df, v_bess, v_base, energy_mwh, chemistry)
    params = {
        "load_scale": load_scale,
        "pv_mw": pv_mw,
        "cloud_event": cloud_event,
        "bess_power": power_mw,
        "bess_energy": energy_mwh,
        "bess_bus": bess_bus,
        "mode": mode,
        "peak_threshold": peak_threshold,
        "voltage_target": voltage_target,
        "weights": tuple(weights),
        "chemistry": chemistry,
        "protect_battery": protect_battery,
        "cycle_limit": cycle_limit,
        "soc_min": soc_min,
        "soc_max": soc_max,
    }
    return SimulationResult(
        bess=bess_df,
        base=base_df,
        v_bess=v_bess,
        v_base=v_base,
        line_pct_bess=line_pct_bess,
        p_load_bus=p_load_bus,
        p_pv_bus=p_pv_bus,
        bus_names=BUS_NAMES,
        metrics=metrics,
        params=params,
    )


def _metrics(
    df: pd.DataFrame,
    base: pd.DataFrame,
    v_bess: np.ndarray,
    v_base: np.ndarray,
    energy_mwh: float,
    chemistry: str,
) -> dict:
    peak_bess = float(df["grid_mw"].max())
    peak_base = float(base["grid_mw"].max()) if not base.empty else peak_bess
    peak_reduction = max(peak_base - peak_bess, 0.0)
    peak_reduction_pct = peak_reduction / peak_base * 100.0 if peak_base > 0 else 0.0

    losses_bess = float(df["loss_mw"].sum() * DT_H)
    losses_base = float(base["loss_mw"].sum() * DT_H) if not base.empty else losses_bess
    loss_reduction_pct = (
        (losses_base - losses_bess) / losses_base * 100.0 if losses_base > 0 else 0.0
    )

    compliance = float(((v_bess >= V_MIN) & (v_bess <= V_MAX)).mean() * 100.0)
    base_compliance = (
        float(((v_base >= V_MIN) & (v_base <= V_MAX)).mean() * 100.0)
        if v_base.size
        else compliance
    )

    discharged = float(df["bess_p_mw"].clip(lower=0).sum() * DT_H)
    charged = float((-df["bess_p_mw"].clip(upper=0)).sum() * DT_H)
    cycles = discharged / energy_mwh if energy_mwh > 0 else 0.0
    reverse_hours = float((df["grid_mw"] < 0).sum() * DT_H)
    reverse_energy = float((-df["grid_mw"].clip(upper=0)).sum() * DT_H)
    q_hours = float((df["bess_q_mvar"].abs() > 0.01).sum() * DT_H)

    chem = CHEMISTRY.get(chemistry, CHEMISTRY["LFP"])
    cost_per_mwh_throughput = (
        chem["capex_kwh"] * 1000.0 / (2.0 * chem["cycle_life"])
    )
    degradation_cost_day = (charged + discharged) * cost_per_mwh_throughput

    return {
        "peak_bess_mw": peak_bess,
        "peak_base_mw": peak_base,
        "peak_reduction_mw": peak_reduction,
        "peak_reduction_pct": peak_reduction_pct,
        "losses_bess_mwh": losses_bess,
        "losses_base_mwh": losses_base,
        "loss_reduction_pct": loss_reduction_pct,
        "vmin_bess": float(v_bess.min()),
        "vmax_bess": float(v_bess.max()),
        "vmin_base": float(v_base.min()) if v_base.size else float(v_bess.min()),
        "vmax_base": float(v_base.max()) if v_base.size else float(v_bess.max()),
        "vmin_gain_pu": float(v_bess.min() - v_base.min()) if v_base.size else 0.0,
        "compliance_pct": compliance,
        "base_compliance_pct": base_compliance,
        "compliance_gain_pp": compliance - base_compliance,
        "discharged_mwh": discharged,
        "charged_mwh": charged,
        "cycles": cycles,
        "throughput_mwh": charged + discharged,
        "reverse_hours": reverse_hours,
        "reverse_energy_mwh": reverse_energy,
        "q_support_hours": q_hours,
        "max_c_rate": float(df["c_rate"].max()),
        "degradation_cost_day": degradation_cost_day,
        "degradation_cost_mwh": cost_per_mwh_throughput,
        "trafo_peak_pct": float(df["trafo_pct"].max()),
        "line_peak_pct": float(df["line_max_pct"].max()),
        "grid_min_mw": float(df["grid_mw"].min()),
    }


def sweep_locations(
    load_scale: float = 1.0,
    pv_mw: float = 5.5,
    cloud_event: bool = True,
    bess_power: float = 2.0,
    bess_energy: float = 8.0,
    mode: str = MODE_MULTI,
    peak_threshold: float = 5.5,
    voltage_target: float = 0.99,
    weights: tuple[float, float, float, float] = (4.0, 2.0, 1.0, 2.0),
    chemistry: str = "LFP",
    protect_battery: bool = True,
    cycle_limit: float = 1.2,
) -> pd.DataFrame:
    rows = []
    for bus in range(1, N_BUS):
        result = simulate_scenario(
            load_scale=load_scale,
            pv_mw=pv_mw,
            cloud_event=cloud_event,
            bess_power=bess_power,
            bess_energy=bess_energy,
            bess_bus=bus,
            mode=mode,
            peak_threshold=peak_threshold,
            voltage_target=voltage_target,
            weights=weights,
            chemistry=chemistry,
            protect_battery=protect_battery,
            cycle_limit=cycle_limit,
            include_baseline=True,
        )
        m = result.metrics
        rows.append(
            {
                "bus": bus,
                "name": BUS_NAMES[bus],
                "vmin_gain_pu": m["vmin_gain_pu"],
                "compliance_gain_pp": m["compliance_gain_pp"],
                "loss_reduction_pct": m["loss_reduction_pct"],
                "peak_reduction_mw": m["peak_reduction_mw"],
                "reverse_hours": m["reverse_hours"],
                "degradation_cost_day": m["degradation_cost_day"],
            }
        )
    df = pd.DataFrame(rows)
    for col in [
        "vmin_gain_pu",
        "compliance_gain_pp",
        "loss_reduction_pct",
        "peak_reduction_mw",
    ]:
        values = df[col].to_numpy(dtype=float)
        vmin, vmax = float(values.min()), float(values.max())
        df[f"{col}_norm"] = (
            (values - vmin) / (vmax - vmin) if vmax > vmin else np.zeros_like(values)
        )
    df["score"] = (
        0.40 * df["vmin_gain_pu_norm"]
        + 0.25 * df["loss_reduction_pct_norm"]
        + 0.20 * df["peak_reduction_mw_norm"]
        + 0.15 * df["compliance_gain_pp_norm"]
    ) * 100.0
    df = df.sort_values("score", ascending=False).reset_index(drop=True)
    df["rank"] = np.arange(1, len(df) + 1)
    return df


def energy_summary(result: SimulationResult) -> dict:
    """Balanço de energia diário e consumo por classe/barramento.

    Todos os valores são integrações de potência (MW) em passos de 15 min:
    energia [MWh] = soma(P [MW]) * 0,25 h.
    """
    dt = DT_H
    load_by_bus = result.p_load_bus.sum(axis=0) * dt
    pv_by_bus = result.p_pv_bus.sum(axis=0) * dt
    by_bus = pd.DataFrame(
        {
            "bus": np.arange(N_BUS),
            "name": list(BUS_NAMES),
            "class": list(LOAD_KINDS),
            "load_mwh": load_by_bus,
            "pv_mwh": pv_by_bus,
        }
    )
    class_labels = {"res": "Residencial", "com": "Comercial", "ind": "Industrial"}
    by_class = (
        by_bus[by_bus["class"] != "none"]
        .assign(classe=lambda d: d["class"].map(class_labels))
        .groupby("classe", as_index=False)["load_mwh"]
        .sum()
    )

    load_mwh = float(load_by_bus.sum())
    pv_mwh = float(pv_by_bus.sum())
    grid_import = float(result.bess["grid_mw"].clip(lower=0).sum() * dt)
    grid_export = float((-result.bess["grid_mw"].clip(upper=0)).sum() * dt)
    bess_discharge = float(result.bess["bess_p_mw"].clip(lower=0).sum() * dt)
    bess_charge = float((-result.bess["bess_p_mw"].clip(upper=0)).sum() * dt)
    losses = float(result.bess["loss_mw"].sum() * dt)

    return {
        "load_mwh": load_mwh,
        "load_annual_mwh": load_mwh * 365.0,
        "pv_mwh": pv_mwh,
        "pv_annual_mwh": pv_mwh * 365.0,
        "grid_import_mwh": grid_import,
        "grid_import_annual_mwh": grid_import * 365.0,
        "grid_export_mwh": grid_export,
        "grid_export_annual_mwh": grid_export * 365.0,
        "bess_discharge_mwh": bess_discharge,
        "bess_charge_mwh": bess_charge,
        "losses_mwh": losses,
        "losses_annual_mwh": losses * 365.0,
        "pv_share_load_pct": pv_mwh / load_mwh * 100.0 if load_mwh > 0 else 0.0,
        "grid_share_load_pct": grid_import / load_mwh * 100.0 if load_mwh > 0 else 0.0,
        "by_bus": by_bus,
        "by_class": by_class,
    }


def financials(
    result: SimulationResult,
    tariff_peak: float,
    tariff_offpeak: float,
    demand_tariff: float,
    dec_fec_avoided: float,
    deferred_capex: float,
    capex_kwh: float,
    capex_kw: float,
    opex_pct: float,
    horizon: int,
    discount: float,
    availability: float = 0.97,
    degradation_pct: float = 0.02,
) -> dict:
    p = result.params
    m = result.metrics
    capex = p["bess_power"] * 1000.0 * capex_kw + p["bess_energy"] * 1000.0 * capex_kwh
    opex = capex * opex_pct

    annual_discharge = m["discharged_mwh"] * 365.0 * availability
    spread = max(tariff_peak - tariff_offpeak, 0.0)
    arbitrage = annual_discharge * 1000.0 * spread
    demand_savings = m["peak_reduction_mw"] * 1000.0 * demand_tariff * 12.0
    degradation_cost = m["degradation_cost_day"] * 365.0 * availability

    gross_savings = arbitrage + demand_savings + dec_fec_avoided + deferred_capex
    net_savings = max(gross_savings - opex - degradation_cost, 0.0)

    cashflows = [-capex]
    for year in range(1, horizon + 1):
        cashflows.append(net_savings * (1.0 - degradation_pct) ** (year - 1))

    npv = sum(cf / (1.0 + discount) ** t for t, cf in enumerate(cashflows))
    simple_payback = capex / net_savings if net_savings > 0 else float("inf")
    irr = _irr(cashflows)

    discounted_energy = sum(
        annual_discharge * (1.0 - degradation_pct) ** (year - 1)
        / (1.0 + discount) ** year
        for year in range(1, horizon + 1)
    )
    discounted_cost = capex + sum(
        opex / (1.0 + discount) ** year for year in range(1, horizon + 1)
    )
    lcoe = discounted_cost / discounted_energy if discounted_energy > 0 else float("inf")

    cumulative = []
    running = 0.0
    for cf in cashflows:
        running += cf
        cumulative.append(running)

    return {
        "capex": capex,
        "opex": opex,
        "degradation_cost": degradation_cost,
        "arbitrage": arbitrage,
        "demand_savings": demand_savings,
        "dec_fec": dec_fec_avoided,
        "deferred": deferred_capex,
        "gross_savings": gross_savings,
        "net_savings": net_savings,
        "cashflows": cashflows,
        "cumulative": cumulative,
        "npv": npv,
        "irr": irr,
        "payback": simple_payback,
        "lcoe": lcoe,
        "annual_discharge_mwh": annual_discharge,
    }


def _irr(cashflows: Iterable[float]) -> float:
    cfs = np.asarray(list(cashflows), dtype=float)

    def npv(rate: float) -> float:
        return float(np.sum(cfs / (1.0 + rate) ** np.arange(len(cfs))))

    low, high = -0.90, 1.50
    if npv(low) * npv(high) > 0:
        return float("nan")
    for _ in range(100):
        mid = (low + high) / 2.0
        if npv(low) * npv(mid) <= 0:
            high = mid
        else:
            low = mid
    return (low + high) / 2.0


def sensitivity(
    result: SimulationResult,
    base_inputs: dict,
    horizon: int = 15,
) -> pd.DataFrame:
    base = financials(result, horizon=horizon, **base_inputs)
    base_npv = base["npv"]
    variations = {
        "CAPEX": ("capex_kwh", -0.30, 0.30, "capex_kw"),
        "Spread tarifário": ("tariff_peak", -0.30, 0.30, None),
        "Tarifa de demanda": ("demand_tariff", -0.30, 0.30, None),
        "DEC/FEC evitados": ("dec_fec_avoided", -0.50, 0.50, None),
        "Taxa de desconto": ("discount", -0.03, 0.03, None),
    }
    rows = []
    for label, (key, low_mult, high_mult, secondary) in variations.items():
        low_inputs = dict(base_inputs)
        high_inputs = dict(base_inputs)
        if key == "capex_kwh":
            low_inputs["capex_kwh"] *= 1.0 + low_mult
            high_inputs["capex_kwh"] *= 1.0 + high_mult
            low_inputs["capex_kw"] *= 1.0 + low_mult
            high_inputs["capex_kw"] *= 1.0 + high_mult
        elif key == "discount":
            low_inputs[key] = max(low_inputs[key] + low_mult, 0.01)
            high_inputs[key] = high_inputs[key] + high_mult
        else:
            low_inputs[key] = max(low_inputs[key] * (1.0 + low_mult), 0.0)
            high_inputs[key] = high_inputs[key] * (1.0 + high_mult)
        low_npv = financials(result, horizon=horizon, **low_inputs)["npv"]
        high_npv = financials(result, horizon=horizon, **high_inputs)["npv"]
        rows.append(
            {
                "variable": label,
                "low_delta": low_npv - base_npv,
                "high_delta": high_npv - base_npv,
                "range": abs(high_npv - low_npv),
            }
        )
    return pd.DataFrame(rows).sort_values("range", ascending=True)
