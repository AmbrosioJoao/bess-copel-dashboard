from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .model import (
    AMPACITY_A,
    BRANCH_KM,
    BUS_NAMES,
    CHEMISTRY,
    N_BUS,
    V_MAX,
    V_MIN,
)

TEAL = "#2E6B5E"
AMBER = "#B7791F"
BLUE = "#2F5D7C"
RED = "#A84B4B"
PURPLE = "#5F5A7A"
MUTED = "#7A858C"
TEXT = "#263238"
GRID = "rgba(31,41,51,0.10)"

VOLT_SCALE = [
    [0.00, "#A84B4B"],
    [0.30, "#B7791F"],
    [0.48, "#F4F1E8"],
    [0.62, "#7FAF93"],
    [1.00, "#2E6B5E"],
]

HOUR_TICKS = dict(
    tickmode="array",
    tickvals=list(range(0, 25, 3)),
    ticktext=[f"{h:02d}h" for h in range(0, 25, 3)],
)


def _layout(
    fig: go.Figure,
    height: int = 380,
    title: str | None = None,
    hovermode: str | None = "x unified",
    showlegend: bool = True,
) -> go.Figure:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=TEXT, size=12),
        margin=dict(l=10, r=10, t=54 if title else 22, b=10),
        height=height,
        hovermode=hovermode,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11),
        ),
        showlegend=showlegend,
        xaxis=dict(
            gridcolor=GRID,
            zerolinecolor="rgba(31,41,51,0.10)",
            linecolor="rgba(31,41,51,0.08)",
            tickfont=dict(color="#5F6B72"),
        ),
        yaxis=dict(
            gridcolor=GRID,
            zerolinecolor="rgba(31,41,51,0.10)",
            linecolor="rgba(31,41,51,0.08)",
            tickfont=dict(color="#5F6B72"),
        ),
    )
    if title:
        fig.update_layout(
            title=dict(
                text=title,
                x=0.01,
                y=0.97,
                font=dict(family="Space Grotesk, sans-serif", size=16, color="#1F2933"),
            )
        )
    return fig


def _hour_axis(fig: go.Figure) -> go.Figure:
    fig.update_xaxes(range=[0, 24], **HOUR_TICKS, title_text="Hora do dia")
    return fig


def operation_chart(df: pd.DataFrame, base: pd.DataFrame, cloud_event: bool = True) -> go.Figure:
    fig = go.Figure()
    fig.add_vrect(
        x0=17.5,
        x1=21.0,
        fillcolor="rgba(183,121,31,0.075)",
        line_width=0,
        layer="below",
        annotation_text="PONTA",
        annotation_position="top left",
        annotation_font=dict(size=10, color=AMBER),
    )
    fig.add_vrect(
        x0=0,
        x1=6.0,
        fillcolor="rgba(47,93,124,0.055)",
        line_width=0,
        layer="below",
        annotation_text="FORA PONTA",
        annotation_position="top left",
        annotation_font=dict(size=10, color=BLUE),
    )

    if not base.empty:
        fig.add_trace(
            go.Scatter(
                x=base["time_h"],
                y=base["grid_mw"],
                name="Sem BESS",
                line=dict(color=MUTED, width=1.6, dash="dot"),
                hovertemplate="%{y:.2f} MW",
            )
        )

    fig.add_trace(
        go.Scatter(
            x=df["time_h"],
            y=df["load_mw"],
            name="Carga",
            line=dict(color=BLUE, width=2.0),
            hovertemplate="%{y:.2f} MW",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["time_h"],
            y=df["pv_mw"],
            name="Geração FV",
            line=dict(color=TEAL, width=1.2),
            fill="tozeroy",
            fillcolor="rgba(46,107,94,0.11)",
            hovertemplate="%{y:.2f} MW",
        )
    )

    bar_colors = np.where(
        df["bess_p_mw"].to_numpy() >= 0,
        "rgba(183,121,31,0.78)",
        "rgba(47,93,124,0.60)",
    )
    fig.add_trace(
        go.Bar(
            x=df["time_h"],
            y=df["bess_p_mw"],
            name="BESS · descarga (+) / carga (−)",
            marker=dict(color=bar_colors, line_width=0),
            opacity=0.9,
            hovertemplate="%{y:.2f} MW",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["time_h"],
            y=df["grid_mw"],
            name="Rede com BESS",
            line=dict(color=AMBER, width=2.7),
            fill="tozeroy",
            fillcolor="rgba(183,121,31,0.055)",
            hovertemplate="%{y:.2f} MW",
        )
    )

    fig.add_hline(y=0, line_color="rgba(31,41,51,0.20)", line_width=1)
    if cloud_event:
        fig.add_vrect(
            x0=14.25,
            x1=15.35,
            fillcolor="rgba(168,75,75,0.07)",
            line_width=0,
            layer="below",
        )
        fig.add_annotation(
            x=14.8,
            y=0.98,
            yref="paper",
            text="evento de nuvem",
            showarrow=False,
            font=dict(size=10, color=RED),
            bgcolor="rgba(255,255,255,0.7)",
            bordercolor="rgba(168,75,75,0.35)",
            borderpad=4,
        )

    _hour_axis(fig)
    fig.update_yaxes(title_text="Potência (MW)")
    return _layout(fig, height=410, title="Balanço de potência ao longo do dia")


def soc_chart(df: pd.DataFrame, soc_min: float = 0.10, soc_max: float = 0.90) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["time_h"],
            y=df["soc"] * 100.0,
            name="SOC",
            line=dict(color=TEAL, width=2.5),
            fill="tozeroy",
            fillcolor="rgba(46,107,94,0.10)",
            hovertemplate="%{y:.1f}%",
        )
    )
    fig.add_hline(
        y=soc_max * 100.0,
        line_dash="dash",
        line_color="rgba(183,121,31,0.55)",
        annotation_text="SOC máximo",
        annotation_font_size=10,
    )
    fig.add_hline(
        y=soc_min * 100.0,
        line_dash="dash",
        line_color="rgba(168,75,75,0.55)",
        annotation_text="SOC mínimo",
        annotation_font_size=10,
    )
    _hour_axis(fig)
    fig.update_yaxes(title_text="Estado de carga (%)", range=[0, 100])
    return _layout(fig, height=300, title="Reserva de energia")


def voltage_envelope(df: pd.DataFrame, base: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["time_h"],
            y=df["vmax"],
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["time_h"],
            y=df["vmin"],
            name="Faixa com BESS",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(46,107,94,0.15)",
            hovertemplate="%{y:.4f} pu",
        )
    )
    if not base.empty:
        fig.add_trace(
            go.Scatter(
                x=base["time_h"],
                y=base["vmin"],
                name="Mínima sem BESS",
                line=dict(color=MUTED, width=1.4, dash="dot"),
                hovertemplate="%{y:.4f} pu",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=base["time_h"],
                y=base["vmax"],
                name="Máxima sem BESS",
                line=dict(color="rgba(122,133,140,0.45)", width=1.0, dash="dot"),
                hovertemplate="%{y:.4f} pu",
            )
        )
    fig.add_hline(
        y=V_MAX,
        line_dash="dash",
        line_color="rgba(183,121,31,0.7)",
        annotation_text="1,05 pu",
        annotation_font_size=10,
    )
    fig.add_hline(
        y=V_MIN,
        line_dash="dash",
        line_color="rgba(168,75,75,0.7)",
        annotation_text="0,93 pu",
        annotation_font_size=10,
    )
    _hour_axis(fig)
    fig.update_yaxes(title_text="Tensão (pu)")
    return _layout(fig, height=300, title="Envelope de tensão no alimentador")


def voltage_heatmap(result) -> go.Figure:
    fig = go.Figure(
        go.Heatmap(
            x=result.bess["time_h"],
            y=list(result.bus_names),
            z=result.v_bess.T,
            colorscale=VOLT_SCALE,
            zmin=0.915,
            zmax=1.055,
            colorbar=dict(
                title=dict(text="pu", side="right"),
                thickness=10,
                len=0.75,
                tickfont=dict(size=10),
                outlinewidth=0,
            ),
            hovertemplate="%{y}<br>%{x:.2f}h<br>%{z:.4f} pu<extra></extra>",
        )
    )
    fig.update_xaxes(range=[0, 24], **HOUR_TICKS, title_text="Hora do dia")
    fig.update_yaxes(autorange="reversed", title_text="")
    return _layout(fig, height=360, title="Mapa de calor da tensão por barramento", hovermode="closest")


def feeder_map(result, time_index: int) -> go.Figure:
    row = result.bess.iloc[time_index]
    v = result.v_bess[time_index]
    loads = result.p_load_bus[time_index]
    pv = result.p_pv_bus[time_index]
    x = np.concatenate([[0.0], np.cumsum(np.array(BRANCH_KM))])
    y = np.array([0.0, 0.10, -0.12, 0.14, -0.10, 0.12, -0.13, 0.09])

    line_pct = result.line_pct_bess[time_index]
    fig = go.Figure()
    for i in range(N_BUS - 1):
        width = 2.0 + min(line_pct[i] / 100.0, 1.0) * 6.0
        color = (
            "rgba(168,75,75,0.85)"
            if line_pct[i] > 85
            else "rgba(46,107,94,0.55)"
            if line_pct[i] < 55
            else "rgba(183,121,31,0.75)"
        )
        fig.add_trace(
            go.Scatter(
                x=[x[i], x[i + 1]],
                y=[y[i], y[i + 1]],
                mode="lines",
                line=dict(color=color, width=width),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    pv_idx = np.where(pv > 0.02)[0]
    if len(pv_idx):
        fig.add_trace(
            go.Scatter(
                x=x[pv_idx],
                y=y[pv_idx] + 0.055,
                mode="markers",
                name="Geração FV",
                marker=dict(symbol="triangle-up", size=10, color=TEAL, line=dict(width=0)),
                text=[f"{BUS_NAMES[i]}: {pv[i]:.2f} MW" for i in pv_idx],
                hovertemplate="%{text}<extra></extra>",
            )
        )

    node_colors = v
    hover = [
        f"<b>{BUS_NAMES[i]}</b><br>Tensão: {v[i]:.4f} pu<br>"
        f"Carga: {loads[i]:.2f} MW<br>FV: {pv[i]:.2f} MW"
        for i in range(N_BUS)
    ]
    fig.add_trace(
        go.Scatter(
            x=x[1:],
            y=y[1:],
            mode="markers+text",
            name="Barramentos",
            marker=dict(
                size=[22 + min(loads[i] * 1.8, 18) for i in range(1, N_BUS)],
                color=node_colors[1:],
                colorscale=VOLT_SCALE,
                cmin=0.915,
                cmax=1.055,
                line=dict(color="rgba(31,41,51,0.35)", width=1.3),
                colorbar=dict(
                    title=dict(text="pu", side="right"),
                    thickness=10,
                    len=0.65,
                    tickfont=dict(size=10),
                    outlinewidth=0,
                ),
            ),
            text=[f"{BUS_NAMES[i]}" for i in range(1, N_BUS)],
            textposition="bottom center",
            textfont=dict(size=11, color="#1F2933"),
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hover[1:],
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[x[0]],
            y=[y[0]],
            mode="markers+text",
            name="Subestação",
            marker=dict(symbol="square", size=30, color=BLUE, line=dict(color="#DCE6EC", width=2)),
            text=["SE"],
            textposition="bottom center",
            textfont=dict(size=12, color="#DCE6EC"),
            hovertemplate=hover[0] + "<extra></extra>",
        )
    )

    bus = int(result.params["bess_bus"])
    fig.add_trace(
        go.Scatter(
            x=[x[bus]],
            y=[y[bus] - 0.085],
            mode="markers",
            name="BESS",
            marker=dict(symbol="diamond", size=22, color=AMBER, line=dict(color="#F2E3C8", width=2)),
            hovertemplate=(
                f"<b>BESS em {BUS_NAMES[bus]}</b><br>"
                f"P: {row['bess_p_mw']:.2f} MW<br>"
                f"Q: {row['bess_q_mvar']:.2f} MVAr<br>"
                f"SOC: {row['soc']*100:.0f}%<extra></extra>"
            ),
        )
    )
    fig.add_annotation(
        x=x[bus],
        y=y[bus] - 0.16,
        text=f"BESS {result.params['bess_power']:.1f} MW / {result.params['bess_energy']:.1f} MWh",
        showarrow=False,
        font=dict(size=10, color=AMBER),
        bgcolor="rgba(255,255,255,0.75)",
        bordercolor="rgba(183,121,31,0.35)",
        borderpad=4,
    )

    fig.update_xaxes(visible=False, range=[-1.2, x[-1] + 1.2])
    fig.update_yaxes(visible=False, range=[-0.35, 0.35])
    fig.update_layout(
        height=390,
        margin=dict(l=10, r=10, t=36, b=10),
        legend=dict(orientation="h", y=1.04, x=0),
    )
    return _layout(fig, height=390, title=f"Alimentador 13,8 kV · snapshot {row['time_h']:.1f}h", showlegend=True)


def voltage_profile(result, time_index: int) -> go.Figure:
    v = result.v_bess[time_index]
    base_v = result.v_base[time_index] if result.v_base.size else v
    bus = int(result.params["bess_bus"])
    fig = go.Figure()
    fig.add_hrect(
        y0=V_MIN,
        y1=V_MAX,
        fillcolor="rgba(46,107,94,0.045)",
        line_width=0,
        layer="below",
    )
    fig.add_trace(
        go.Scatter(
            x=list(result.bus_names),
            y=base_v,
            name="Sem BESS",
            mode="lines+markers",
            line=dict(color=MUTED, width=1.5, dash="dot"),
            marker=dict(size=5, color=MUTED),
            hovertemplate="%{y:.4f} pu",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=list(result.bus_names),
            y=v,
            name="Com BESS",
            mode="lines+markers",
            line=dict(color=TEAL, width=2.6),
            marker=dict(size=8, color=TEAL, line=dict(color="#FFFFFF", width=1)),
            hovertemplate="%{y:.4f} pu",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[result.bus_names[bus]],
            y=[v[bus]],
            name="BESS",
            mode="markers",
            marker=dict(symbol="diamond", size=15, color=AMBER, line=dict(color="#F2E3C8", width=1.5)),
            hovertemplate=f"BESS: {v[bus]:.4f} pu<extra></extra>",
        )
    )
    fig.add_hline(y=V_MAX, line_dash="dash", line_color="rgba(183,121,31,0.65)")
    fig.add_hline(y=V_MIN, line_dash="dash", line_color="rgba(168,75,75,0.65)")
    y_low = min(float(np.min(base_v)), float(np.min(v)), V_MIN) - 0.012
    y_high = max(float(np.max(base_v)), float(np.max(v)), V_MAX) + 0.012
    fig.update_yaxes(title_text="Tensão (pu)", range=[y_low, y_high])
    fig.update_xaxes(title_text="")
    return _layout(fig, height=360, title="Perfil de tensão no snapshot")


def allocation_scatter(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["loss_reduction_pct"],
            y=df["vmin_gain_pu"] * 1000.0,
            mode="markers+text",
            text=df["name"],
            textposition="top center",
            textfont=dict(size=11, color="#1F2933"),
            marker=dict(
                size=14 + df["peak_reduction_mw"] * 12,
                color=df["score"],
                colorscale=[[0, "#DDE5E8"], [0.6, "#5F8F80"], [1, "#2E6B5E"]],
                cmin=0,
                cmax=100,
                line=dict(color="rgba(31,41,51,0.35)", width=1.2),
                colorbar=dict(
                    title=dict(text="score", side="right"),
                    thickness=9,
                    len=0.65,
                    tickfont=dict(size=10),
                    outlinewidth=0,
                ),
            ),
            customdata=np.stack(
                [
                    df["peak_reduction_mw"],
                    df["compliance_gain_pp"],
                    df["degradation_cost_day"],
                ],
                axis=-1,
            ),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Redução de perdas: %{x:.1f}%<br>"
                "Ganho de tensão mínima: %{y:.1f} mpu<br>"
                "Redução de pico: %{customdata[0]:.2f} MW<br>"
                "Ganho de conformidade: %{customdata[1]:.1f} pp<br>"
                "Custo de ciclagem: R$ %{customdata[2]:,.0f}/dia"
                "<extra></extra>"
            ),
        )
    )
    fig.add_hline(y=0, line_color="rgba(31,41,51,0.15)", line_width=1)
    fig.update_xaxes(title_text="Redução de perdas (%)")
    fig.update_yaxes(title_text="Ganho de tensão mínima (milésimos de pu)")
    best = df.iloc[0]
    fig.add_annotation(
        x=best["loss_reduction_pct"],
        y=best["vmin_gain_pu"] * 1000.0,
        text=f"Recomendado: {best['name']}",
        showarrow=True,
        arrowhead=2,
        arrowcolor=TEAL,
        font=dict(size=11, color=TEAL),
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="rgba(46,107,94,0.4)",
        borderpad=5,
        ax=35,
        ay=-35,
    )
    return _layout(fig, height=390, title="Onde o BESS entrega mais valor?", hovermode="closest")


def allocation_bars(df: pd.DataFrame) -> go.Figure:
    data = df.sort_values("score", ascending=True)
    colors = [TEAL if i == len(data) - 1 else "rgba(46,107,94,0.32)" for i in range(len(data))]
    fig = go.Figure(
        go.Bar(
            x=data["score"],
            y=data["name"],
            orientation="h",
            marker=dict(color=colors, line_width=0),
            text=[f"{s:.0f}" for s in data["score"]],
            textposition="outside",
            hovertemplate="%{y}: score %{x:.0f}<extra></extra>",
        )
    )
    fig.update_xaxes(title_text="Score composto (0–100)", range=[0, 110])
    fig.update_yaxes(title_text="")
    return _layout(fig, height=330, title="Ranking de alocação", hovermode="closest", showlegend=False)


def service_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["time_h"],
            y=df["p_peak_req"],
            name="Corte de pico",
            line=dict(color=AMBER, width=1.7),
            hovertemplate="%{y:.2f} MW",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["time_h"],
            y=df["p_pv_req"],
            name="Suavização FV",
            line=dict(color=TEAL, width=1.7),
            hovertemplate="%{y:.2f} MW",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["time_h"],
            y=df["p_arb_req"],
            name="Arbitragem",
            line=dict(color=BLUE, width=1.7),
            hovertemplate="%{y:.2f} MW",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["time_h"],
            y=df["bess_p_mw"],
            name="Despacho final",
            line=dict(color="#FFFFFF", width=2.6, dash="dot"),
            hovertemplate="%{y:.2f} MW",
        )
    )
    fig.add_hline(y=0, line_color="rgba(31,41,51,0.20)", line_width=1)
    _hour_axis(fig)
    fig.update_yaxes(title_text="Potência solicitada (MW)")
    return _layout(fig, height=340, title="Como o EMS combina os serviços")


def reactive_chart(df: pd.DataFrame, voltage_target: float) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    colors = np.where(
        df["bess_q_mvar"].to_numpy() >= 0,
        "rgba(46,107,94,0.70)",
        "rgba(168,75,75,0.70)",
    )
    fig.add_trace(
        go.Bar(
            x=df["time_h"],
            y=df["bess_q_mvar"],
            name="Q do BESS",
            marker=dict(color=colors, line_width=0),
            hovertemplate="%{y:.2f} MVAr",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df["time_h"],
            y=df["v_bess"],
            name="Tensão no ponto do BESS",
            line=dict(color=AMBER, width=2.2),
            hovertemplate="%{y:.4f} pu",
        ),
        secondary_y=True,
    )
    fig.add_trace(
        go.Scatter(
            x=df["time_h"],
            y=np.full(len(df), voltage_target),
            name="Alvo",
            line=dict(color="rgba(31,41,51,0.25)", width=1.2, dash="dash"),
            hovertemplate="alvo %{y:.3f} pu<extra></extra>",
        ),
        secondary_y=True,
    )
    _hour_axis(fig)
    fig.update_yaxes(title_text="Potência reativa (MVAr)", secondary_y=False)
    fig.update_yaxes(title_text="Tensão (pu)", secondary_y=True, gridcolor="rgba(0,0,0,0)")
    return _layout(fig, height=330, title="Suporte de reativos e controle de tensão")


def soc_gauge(soc_final: float) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=soc_final * 100.0,
            number=dict(suffix="%", font=dict(size=30, color=TEXT)),
            title=dict(text="SOC final", font=dict(size=13, color="#5F6B72")),
            gauge=dict(
                axis=dict(range=[0, 100], tickwidth=0, tickfont=dict(size=9, color="#5F6B72")),
                bar=dict(color=TEAL, thickness=0.55),
                bgcolor="rgba(31,41,51,0.04)",
                borderwidth=0,
                steps=[
                    dict(range=[0, 10], color="rgba(168,75,75,0.20)"),
                    dict(range=[90, 100], color="rgba(183,121,31,0.20)"),
                ],
            ),
        )
    )
    fig.update_layout(
        height=220,
        margin=dict(l=20, r=20, t=42, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT),
    )
    return fig


def cycle_gauge(cycles: float, limit: float) -> go.Figure:
    top = max(limit * 1.35, cycles * 1.15, 0.5)
    color = TEAL if cycles < limit else RED
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=cycles,
            number=dict(suffix=" ciclos", font=dict(size=25, color=TEXT)),
            title=dict(text="Ciclos equivalentes hoje", font=dict(size=13, color="#5F6B72")),
            gauge=dict(
                axis=dict(range=[0, top], tickwidth=0, tickfont=dict(size=9, color="#5F6B72")),
                bar=dict(color=color, thickness=0.55),
                bgcolor="rgba(31,41,51,0.04)",
                borderwidth=0,
                steps=[
                    dict(range=[0, limit], color="rgba(46,107,94,0.13)"),
                    dict(range=[limit, top], color="rgba(168,75,75,0.16)"),
                ],
                threshold=dict(
                    line=dict(color=RED, width=3),
                    thickness=0.8,
                    value=limit,
                ),
            ),
        )
    )
    fig.update_layout(
        height=220,
        margin=dict(l=20, r=20, t=42, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT),
    )
    return fig


def chemistry_radar(selected: str) -> go.Figure:
    axes = ["Ciclo de vida", "Segurança", "Densidade", "Custo-benefício", "Potência"]
    fig = go.Figure()
    for key, chem in CHEMISTRY.items():
        cycle_score = min(5.0, 5.0 * (chem["cycle_life"] / 6000.0) ** 0.5)
        values = [cycle_score, chem["safety"], chem["density"], chem["cost"], chem["power"]]
        is_selected = key == selected
        fig.add_trace(
            go.Scatterpolar(
                r=values + [values[0]],
                theta=axes + [axes[0]],
                name=chem["short"],
                line=dict(
                    color=chem["color"],
                    width=3.0 if is_selected else 1.2,
                ),
                fill="toself" if is_selected else "none",
                fillcolor=(
                    "rgba(46,107,94,0.10)" if key == "LFP" else "rgba(183,121,31,0.08)"
                    if key == "NMC" else "rgba(47,93,124,0.08)"
                    if key == "Na-ion" else "rgba(95,90,122,0.08)"
                )
                if is_selected
                else None,
                opacity=1.0 if is_selected else 0.45,
            )
        )
    fig.update_layout(
        height=390,
        margin=dict(l=35, r=35, t=55, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=TEXT, size=11),
        polar=dict(
            bgcolor="rgba(255,255,255,0.015)",
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                gridcolor="rgba(31,41,51,0.08)",
                tickfont=dict(size=9, color="#7A858C"),
            ),
            angularaxis=dict(
                gridcolor="rgba(31,41,51,0.08)",
                tickfont=dict(size=10, color="#5F6B72"),
            ),
        ),
        legend=dict(orientation="h", y=1.10, x=0, bgcolor="rgba(0,0,0,0)"),
        title=dict(
            text="Trade-offs por química",
            x=0.01,
            y=0.98,
            font=dict(family="Space Grotesk, sans-serif", size=16),
        ),
    )
    return fig


def cashflow_chart(fin: dict, horizon: int) -> go.Figure:
    years = np.arange(0, horizon + 1)
    annual = np.array(fin["cashflows"][1:]) / 1e6
    cumulative = np.array(fin["cumulative"]) / 1e6
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=years[1:],
            y=annual,
            name="Fluxo anual",
            marker=dict(
                color=np.where(annual >= 0, "rgba(46,107,94,0.65)", "rgba(168,75,75,0.65)"),
                line_width=0,
            ),
            hovertemplate="Ano %{x}: R$ %{y:.2f} mi",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=years,
            y=cumulative,
            name="Acumulado",
            line=dict(color=AMBER, width=2.8),
            hovertemplate="Ano %{x}: R$ %{y:.2f} mi",
        ),
        secondary_y=True,
    )
    fig.add_hline(y=0, line_color="rgba(31,41,51,0.20)", line_width=1)
    if 0 < fin["payback"] <= horizon:
        fig.add_vline(
            x=fin["payback"],
            line_dash="dash",
            line_color="rgba(46,107,94,0.75)",
            annotation_text=f"payback {fin['payback']:.1f} anos",
            annotation_font_size=10,
            annotation_font_color=TEAL,
        )
    fig.update_xaxes(title_text="Ano")
    fig.update_yaxes(title_text="Fluxo anual (R$ mi)", secondary_y=False)
    fig.update_yaxes(title_text="Acumulado (R$ mi)", secondary_y=True, gridcolor="rgba(0,0,0,0)")
    return _layout(fig, height=390, title="Fluxo de caixa do investimento")


def revenue_waterfall(fin: dict) -> go.Figure:
    labels = [
        "Arbitragem",
        "Demanda",
        "DEC/FEC",
        "Obra adiada",
        "OPEX",
        "Ciclagem",
        "Resultado",
    ]
    values = [
        fin["arbitrage"] / 1e6,
        fin["demand_savings"] / 1e6,
        fin["dec_fec"] / 1e6,
        fin["deferred"] / 1e6,
        -fin["opex"] / 1e6,
        -fin["degradation_cost"] / 1e6,
        0.0,
    ]
    fig = go.Figure(
        go.Waterfall(
            x=labels,
            y=values,
            measure=["relative", "relative", "relative", "relative", "relative", "relative", "total"],
            connector=dict(line=dict(color="rgba(255,255,255,0.14)", width=1)),
            increasing=dict(marker=dict(color="rgba(46,107,94,0.72)")),
            decreasing=dict(marker=dict(color="rgba(168,75,75,0.72)")),
            totals=dict(marker=dict(color="rgba(183,121,31,0.85)")),
            text=[f"{v:+.2f}" for v in values[:-1]] + [f"{sum(values):+.2f}"],
            textposition="outside",
            hovertemplate="%{x}: R$ %{y:.2f} mi<extra></extra>",
        )
    )
    fig.update_yaxes(title_text="R$ milhões / ano")
    fig.update_xaxes(tickangle=-20)
    return _layout(fig, height=390, title="Stack de valor anual", hovermode="closest", showlegend=False)


def sensitivity_chart(sens: pd.DataFrame) -> go.Figure:
    data = sens.sort_values("range", ascending=True)
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=data["low_delta"] / 1e6,
            y=data["variable"],
            orientation="h",
            name="Cenário baixo",
            marker=dict(color="rgba(168,75,75,0.70)", line_width=0),
            hovertemplate="%{y}: R$ %{x:+.2f} mi<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            x=data["high_delta"] / 1e6,
            y=data["variable"],
            orientation="h",
            name="Cenário alto",
            marker=dict(color="rgba(46,107,94,0.70)", line_width=0),
            hovertemplate="%{y}: R$ %{x:+.2f} mi<extra></extra>",
        )
    )
    fig.add_vline(x=0, line_color="rgba(255,255,255,0.25)", line_width=1)
    fig.update_xaxes(title_text="Variação do VPL vs. caso base (R$ mi)")
    fig.update_yaxes(title_text="")
    return _layout(fig, height=350, title="Sensibilidade do VPL", hovermode="y unified")


def mini_grid(green: float, blue: float, amber: float) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=np.arange(48),
            y=np.sin(np.arange(48) / 5.0) * green + green,
            mode="lines",
            line=dict(color=TEAL, width=2),
            fill="tozeroy",
            fillcolor="rgba(46,107,94,0.08)",
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=np.arange(48),
            y=np.cos(np.arange(48) / 7.0) * blue + blue,
            mode="lines",
            line=dict(color=BLUE, width=1.4),
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=np.arange(48),
            y=np.sin(np.arange(48) / 3.0) * amber * 0.4,
            mode="lines",
            line=dict(color=AMBER, width=1.2, dash="dot"),
            hoverinfo="skip",
        )
    )
    fig.update_layout(
        height=90,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig


def energy_class_donut(by_class: pd.DataFrame) -> go.Figure:
    labels = by_class["classe"].tolist()
    values = by_class["load_mwh"].tolist()
    palette = {"Residencial": BLUE, "Comercial": TEAL, "Industrial": AMBER}
    colors = [palette.get(label, MUTED) for label in labels]
    total = float(sum(values))
    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.64,
            sort=False,
            marker=dict(colors=colors, line=dict(color="rgba(255,255,255,0.9)", width=2)),
            textinfo="percent",
            textfont=dict(size=11, color="#FFFFFF"),
            hovertemplate="%{label}: %{value:.1f} MWh/dia<extra></extra>",
        )
    )
    fig.add_annotation(
        text=f"<b>{total:.1f}</b><br><span style='font-size:10px'>MWh/dia</span>",
        showarrow=False,
        font=dict(size=20, color="#1F2933"),
    )
    fig.update_layout(legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center"))
    return _layout(fig, height=330, title="Consumo por classe", hovermode="closest")


def energy_bus_bar(by_bus: pd.DataFrame) -> go.Figure:
    data = by_bus[by_bus["load_mwh"] > 0].sort_values("load_mwh", ascending=True)
    palette = {"res": BLUE, "com": TEAL, "ind": AMBER, "none": MUTED}
    colors = [palette.get(kind, MUTED) for kind in data["class"]]
    fig = go.Figure(
        go.Bar(
            x=data["load_mwh"],
            y=[f"B{int(b)} · {name}" for b, name in zip(data["bus"], data["name"])],
            orientation="h",
            marker=dict(color=colors, line_width=0),
            text=[f"{v:.1f} MWh" for v in data["load_mwh"]],
            textposition="outside",
            textfont=dict(size=10),
            hovertemplate="%{y}: %{x:.2f} MWh/dia<extra></extra>",
        )
    )
    fig.update_xaxes(title_text="Energia consumida no dia (MWh)")
    fig.update_yaxes(title_text="")
    return _layout(fig, height=330, title="Consumo por barramento", hovermode="closest", showlegend=False)


def curitiba_sep_schematic() -> go.Figure:
    """Esquemático de referência da microrrede UFPR / SE Capanema (Curitiba)."""
    fig = go.Figure()

    def wire(x0, y0, x1, y1, color=TEAL, width=3, dash="solid"):
        fig.add_shape(
            type="line", x0=x0, y0=y0, x1=x1, y1=y1,
            line=dict(color=color, width=width, dash=dash), layer="below",
        )

    def box(x0, y0, x1, y1, color, text, fill):
        fig.add_shape(
            type="rect", x0=x0, y0=y0, x1=x1, y1=y1,
            line=dict(color=color, width=1.4), fillcolor=fill, layer="below",
        )
        fig.add_annotation(
            x=(x0 + x1) / 2, y=(y0 + y1) / 2, text=text, showarrow=False,
            font=dict(size=10.5, color=TEXT), align="center",
        )

    fig.add_shape(
        type="rect", x0=0.12, y0=0.55, x1=2.35, y1=5.55,
        line=dict(color="rgba(47,93,124,0.22)", width=1),
        fillcolor="rgba(47,93,124,0.045)", layer="below",
    )
    fig.add_shape(
        type="rect", x0=2.35, y0=0.55, x1=8.9, y1=5.55,
        line=dict(color="rgba(46,107,94,0.22)", width=1),
        fillcolor="rgba(46,107,94,0.035)", layer="below",
    )
    fig.add_annotation(x=1.22, y=5.78, text="REDE COPEL · 69 kV", showarrow=False,
                       font=dict(size=10, color=BLUE))
    fig.add_annotation(x=5.65, y=5.78, text="CURITIBA · CENTRO POLITÉCNICO", showarrow=False,
                       font=dict(size=10, color=TEAL))

    wire(0.25, 4.05, 0.78, 4.05, BLUE)
    wire(0.78, 3.25, 0.78, 4.85, BLUE, 5)
    fig.add_annotation(x=0.78, y=5.0, text="SE Capanema<br>69 kV", showarrow=False,
                       font=dict(size=11, color="#1F2933"), align="center")

    wire(0.78, 4.05, 1.04, 4.05, BLUE, 2.4)
    fig.add_trace(go.Scatter(
        x=[1.15, 1.35], y=[4.05, 4.05], mode="markers",
        marker=dict(symbol="circle", size=26, color="rgba(255,255,255,0.9)",
                    line=dict(color=BLUE, width=2.5)),
        showlegend=False, hoverinfo="skip",
    ))
    wire(1.46, 4.05, 1.78, 4.05, BLUE, 2.4)
    fig.add_annotation(x=1.25, y=3.55, text="69/13,8 kV", showarrow=False,
                       font=dict(size=10, color=BLUE))

    wire(1.78, 1.25, 1.78, 5.05, TEAL, 5)
    fig.add_annotation(x=1.78, y=5.18, text="Barra 13,8 kV", showarrow=False,
                       font=dict(size=10, color=TEAL))

    wire(1.78, 4.05, 4.45, 4.05, TEAL, 3.2)
    fig.add_annotation(x=3.12, y=4.22, text="Alimentador Prado · ~5 km", showarrow=False,
                       font=dict(size=10.5, color=TEAL))
    fig.add_annotation(x=3.12, y=3.86, text="13,8 kV", showarrow=False,
                       font=dict(size=9.5, color=MUTED))

    wire(4.45, 1.25, 4.45, 5.05, TEAL, 5)
    fig.add_annotation(x=4.45, y=5.18, text="POI UFPR<br>Barra 5", showarrow=False,
                       font=dict(size=10.5, color="#1F2933"), align="center")

    feeder_ys = [4.75, 4.35, 3.95, 3.55, 3.15, 2.75, 2.35, 1.95, 1.55]
    for y in feeder_ys:
        wire(4.45, y, 5.28, y, TEAL, 1.4)
        fig.add_trace(go.Scatter(
            x=[5.33], y=[y], mode="markers",
            marker=dict(symbol="arrow-down", size=10, color=TEAL),
            showlegend=False, hoverinfo="skip",
        ))
    fig.add_annotation(x=5.45, y=4.78, text="9 alimentadores internos · 13,8 kV",
                       showarrow=False, font=dict(size=10, color=TEAL), align="left")
    fig.add_annotation(x=5.45, y=4.33, text="16 trafos 13,8/0,22 kV",
                       showarrow=False, font=dict(size=9.5, color=MUTED), align="left")

    wire(5.28, 3.55, 6.12, 3.55, AMBER, 2)
    box(6.12, 2.95, 7.65, 4.15, AMBER,
        "Cargas do campus<br>residencial · comercial<br>industrial · iluminação",
        "rgba(183,121,31,0.10)")

    wire(5.28, 4.75, 6.12, 5.05, TEAL, 1.8)
    box(6.12, 4.75, 7.65, 5.45, TEAL, "FV + gerador biodiesel", "rgba(46,107,94,0.10)")

    wire(5.28, 1.95, 6.12, 1.85, AMBER, 2, dash="dash")
    fig.add_trace(go.Scatter(
        x=[6.35], y=[1.85], mode="markers",
        marker=dict(symbol="diamond", size=22, color="rgba(255,255,255,0.9)",
                    line=dict(color=AMBER, width=2.5)),
        showlegend=False, hoverinfo="skip",
    ))
    fig.add_annotation(x=6.55, y=1.85, text="BESS proposto · 2 MW / 8 MWh",
                       showarrow=False, font=dict(size=10.5, color=AMBER), align="left")
    fig.add_annotation(x=6.55, y=1.45, text="conexão no POI ou ao longo do Prado",
                       showarrow=False, font=dict(size=9.2, color=MUTED), align="left")

    fig.add_annotation(
        x=0.18, y=0.20,
        text="Esquemático de referência — não é o alimentador didático simulado.",
        showarrow=False, font=dict(size=9, color=MUTED), align="left",
    )

    fig.update_xaxes(visible=False, range=[0, 9.0])
    fig.update_yaxes(visible=False, range=[0, 6.0])
    return _layout(
        fig, height=430,
        title="SEP real de referência em Curitiba: SE Capanema → Alimentador Prado → UFPR",
        hovermode="closest", showlegend=False,
    )
