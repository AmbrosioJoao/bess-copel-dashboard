from __future__ import annotations

import numpy as np
import streamlit as st

from bess import charts, styles
from bess.model import (
    BUS_NAMES,
    CHEMISTRY,
    MODES,
    N_BUS,
    V_MAX,
    V_MIN,
    SimulationResult,
    energy_summary,
    financials,
    simulate_scenario,
)

st.set_page_config(
    page_title="BESS Lab · COPEL",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)
styles.inject_css()


@st.cache_data(show_spinner=False, max_entries=40)
def cached_sim(
    load_scale: float,
    pv_mw: float,
    cloud_event: bool,
    bess_power: float,
    bess_energy: float,
    bess_bus: int,
    mode: str,
    peak_threshold: float,
    chemistry: str,
) -> SimulationResult:
    return simulate_scenario(
        load_scale=load_scale,
        pv_mw=pv_mw,
        cloud_event=cloud_event,
        bess_power=bess_power,
        bess_energy=bess_energy,
        bess_bus=bess_bus,
        mode=mode,
        peak_threshold=peak_threshold,
        voltage_target=0.99,
        weights=(4.0, 2.0, 1.0, 2.0),
        chemistry=chemistry,
        protect_battery=True,
        cycle_limit=1.2,
    )


def fmt_brl(value: float, decimals: int = 0) -> str:
    if not np.isfinite(value):
        return "—"
    return f"R$ {value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_mi(value: float, decimals: int = 2) -> str:
    if not np.isfinite(value):
        return "—"
    return f"R$ {value / 1e6:.{decimals}f} mi".replace(".", ",")


def fmt_pct(value: float, decimals: int = 1) -> str:
    if not np.isfinite(value):
        return "—"
    return f"{value:.{decimals}f}%".replace(".", ",")


def fmt_pu(value: float) -> str:
    return f"{value:.4f} pu".replace(".", ",")


def fmt_mw(value: float, decimals: int = 2) -> str:
    return f"{value:.{decimals}f} MW".replace(".", ",")


def fmt_mwh(value: float, decimals: int = 1) -> str:
    return f"{value:,.{decimals}f} MWh".replace(",", "X").replace(".", ",").replace("X", ".")


def default_fin_inputs(chemistry: str) -> dict:
    chem = CHEMISTRY[chemistry]
    return {
        "tariff_peak": 1.05,
        "tariff_offpeak": 0.55,
        "demand_tariff": 60.0,
        "dec_fec_avoided": 450000.0,
        "deferred_capex": 400000.0,
        "capex_kwh": float(chem["capex_kwh"]),
        "capex_kw": 600.0,
        "opex_pct": 0.015,
        "horizon": 15,
        "discount": 0.12,
        "availability": 0.97,
        "degradation_pct": 0.02,
    }


def source_note(text: str) -> None:
    st.markdown(f'<div class="small-note">{text}</div>', unsafe_allow_html=True)


styles.brand_sidebar()
st.sidebar.markdown(
    '<div class="small-note" style="margin:4px 0 14px;">'
    "Uma página para ver o dia, os consumos e o SEP real de Curitiba."
    "</div>",
    unsafe_allow_html=True,
)

with st.sidebar.expander("Cenário do alimentador", expanded=True):
    load_scale_pct = st.slider(
        "Carga do alimentador (%)", 60, 130, 100, 5,
        help="Escala o pico de carga de todos os barramentos.",
    )
    pv_mw = st.slider(
        "Capacidade FV instalada (MWp)", 0.0, 8.0, 5.5, 0.5,
        help="Geração distribuída ao longo do alimentador.",
    )
    cloud_event = st.toggle(
        "Evento de nuvem às 14h45", value=True,
        help="Queda abrupta de geração FV para testar a suavização de rampas.",
    )

with st.sidebar.expander("Sistema de armazenamento", expanded=True):
    bess_power = st.slider("Potência do BESS (MW)", 0.5, 4.0, 2.0, 0.25)
    bess_energy = st.slider("Energia do BESS (MWh)", 2.0, 16.0, 8.0, 0.5)
    bess_bus = st.selectbox(
        "Barramento de conexão",
        list(range(1, N_BUS)),
        index=4,
        format_func=lambda i: f"B{i} · {BUS_NAMES[i]}",
    )
    chemistry = st.selectbox(
        "Química da bateria",
        list(CHEMISTRY.keys()),
        index=0,
        format_func=lambda k: CHEMISTRY[k]["label"],
    )

with st.sidebar.expander("Estratégia do EMS", expanded=False):
    mode = st.selectbox("Modo de operação", list(MODES), index=0)
    peak_threshold = st.slider(
        "Limiar de corte de pico (MW)", 2.5, 6.5, 5.5, 0.1,
        help="A rede acima deste valor aciona descarga do BESS.",
    )

st.sidebar.markdown("---")
st.sidebar.markdown(
    '<div class="small-note">Modelo ilustrativo. '
    "Perfis, rede e tarifas são premissas ajustáveis; não substituem um estudo elétrico formal.</div>",
    unsafe_allow_html=True,
)

load_scale = load_scale_pct / 100.0
sim = cached_sim(
    load_scale,
    pv_mw,
    cloud_event,
    bess_power,
    bess_energy,
    bess_bus,
    mode,
    peak_threshold,
    chemistry,
)
m = sim.metrics
energy = energy_summary(sim)
fin = financials(sim, **default_fin_inputs(chemistry))

styles.hero()

styles.section(
    "Resumo",
    "Indicadores do cenário atual",
    "Motivação: mostrar em quatro números o efeito do BESS no pico e na tensão.",
)
k = st.columns(4, gap="medium")
with k[0]:
    styles.metric_card(
        "Pico na rede",
        fmt_mw(m["peak_bess_mw"]),
        f"{fmt_mw(m['peak_base_mw'])} sem BESS",
        "teal",
        "good",
    )
with k[1]:
    styles.metric_card(
        "Redução de pico",
        fmt_pct(m["peak_reduction_pct"]),
        f"{fmt_mw(m['peak_reduction_mw'])} a menos",
        "amber",
        "good",
    )
with k[2]:
    vmin_gain = f"{m['vmin_gain_pu'] * 1000:+.1f}".replace(".", ",")
    styles.metric_card(
        "Tensão mínima",
        fmt_pu(m["vmin_bess"]),
        f"{vmin_gain} mpu vs. sem BESS",
        "blue",
        "good" if m["vmin_gain_pu"] > 0 else "",
    )
with k[3]:
    styles.metric_card(
        "Conformidade de tensão",
        fmt_pct(m["compliance_pct"]),
        f"{fmt_pct(m['compliance_gain_pp'])} pp vs. sem BESS",
        "purple",
        "good" if m["compliance_gain_pp"] >= 0 else "",
    )

st.divider()

styles.section(
    "Operação 24h",
    "Potência, SOC e tensão ao longo do dia",
    "Motivação: comparar o mesmo dia com e sem BESS em intervalos de 15 minutos.",
)
st.plotly_chart(
    charts.operation_chart(sim.bess, sim.base, cloud_event),
    width="stretch",
    config={"displayModeBar": False},
)
source_note(
    "Fonte: simulação própria. Carga, FV e rede são curvas sintéticas; "
    "a integração é feita em 96 passos de 15 min por dia."
)

left, right = st.columns([1.0, 1.0], gap="medium")
with left:
    st.plotly_chart(
        charts.soc_chart(sim.bess, sim.params["soc_min"], sim.params["soc_max"]),
        width="stretch",
        config={"displayModeBar": False},
    )
with right:
    st.plotly_chart(
        charts.voltage_envelope(sim.bess, sim.base),
        width="stretch",
        config={"displayModeBar": False},
    )

violation_hours = int(((sim.v_bess < V_MIN) | (sim.v_bess > V_MAX)).any(axis=1).sum())
if violation_hours:
    styles.callout(
        "Resultado do cenário: atenção",
        f"{violation_hours} passo(s) de 15 min ficaram fora de 0,93–1,05 pu. "
        "Ajuste o ponto de conexão, a potência ou o modo do EMS.",
        "warn",
    )
else:
    styles.callout(
        "Resultado do cenário",
        f"Pico reduzido em {fmt_mw(m['peak_reduction_mw'])}; tensão adequada em "
        f"{fmt_pct(m['compliance_pct'])} dos barramentos-tempo. "
        f"SOC e C-rate dentro dos limites adotados.",
    )

st.divider()

styles.section(
    "Consumo e balanço de energia",
    "Consumo, geração e perdas do dia",
    "Motivação: mostrar de onde vem a energia e quanto cada classe e barramento consome.",
)
balance_rows = [
    [
        "Consumo total de carga",
        fmt_mwh(energy["load_mwh"]),
        fmt_mwh(energy["load_annual_mwh"], 0),
        "Σ carga × 0,25 h",
    ],
    [
        "Geração FV",
        fmt_mwh(energy["pv_mwh"]),
        fmt_mwh(energy["pv_annual_mwh"], 0),
        f"{fmt_pct(energy['pv_share_load_pct'])} da carga",
    ],
    [
        "Importação da rede",
        fmt_mwh(energy["grid_import_mwh"]),
        fmt_mwh(energy["grid_import_annual_mwh"], 0),
        "Σ max(P_rede, 0) × 0,25 h",
    ],
    [
        "Injeção na rede",
        fmt_mwh(energy["grid_export_mwh"]),
        fmt_mwh(energy["grid_export_annual_mwh"], 0),
        "Σ max(−P_rede, 0) × 0,25 h",
    ],
    [
        "BESS descarregado",
        fmt_mwh(energy["bess_discharge_mwh"]),
        "—",
        f"{fmt_mwh(energy['bess_charge_mwh'])} carregados",
    ],
    [
        "Perdas elétricas",
        fmt_mwh(energy["losses_mwh"]),
        fmt_mwh(energy["losses_annual_mwh"], 0),
        "Σ P_perdas × 0,25 h",
    ],
]
styles.data_table(
    ["Componente", "MWh/dia", "MWh/ano", "Cálculo"],
    balance_rows,
    numeric_cols={1, 2},
)
source_note(
    "Anualização simples: valor diário × 365. Os perfis de carga e FV são sintéticos e "
    "não representam medições da COPEL."
)

col_a, col_b = st.columns([0.85, 1.15], gap="medium")
with col_a:
    st.plotly_chart(
        charts.energy_class_donut(energy["by_class"]),
        width="stretch",
        config={"displayModeBar": False},
    )
with col_b:
    st.plotly_chart(
        charts.energy_bus_bar(energy["by_bus"]),
        width="stretch",
        config={"displayModeBar": False},
    )

class_labels = {"res": "Residencial", "com": "Comercial", "ind": "Industrial", "none": "—"}
bus_rows = []
for _, row in energy["by_bus"].iterrows():
    share = row["load_mwh"] / energy["load_mwh"] * 100.0 if energy["load_mwh"] > 0 else 0.0
    bus_rows.append(
        [
            f"B{int(row['bus'])} · {row['name']}",
            class_labels.get(row["class"], row["class"]),
            fmt_mwh(row["load_mwh"]),
            fmt_mwh(row["load_mwh"] * 365.0, 0),
            fmt_mwh(row["pv_mwh"]),
            fmt_pct(share),
        ]
    )
styles.data_table(
    ["Barramento", "Classe", "Consumo MWh/dia", "Consumo MWh/ano", "FV MWh/dia", "Participação"],
    bus_rows,
    numeric_cols={2, 3, 4, 5},
)
source_note(
    "Os números de consumo e geração vêm das mesmas curvas usadas nos gráficos. "
    "A tabela por barramento permite comparar classes e participação de cada carga."
)

st.divider()

styles.section(
    "SEP de referência em Curitiba",
    "SE Capanema → Alimentador Prado → UFPR",
    "Motivação: conectar a simulação a uma rede real de 13,8 kV em Curitiba.",
)
st.plotly_chart(
    charts.curitiba_sep_schematic(),
    width="stretch",
    config={"displayModeBar": False},
)
source_note(
    "Fonte: Oliveira et al. (2019/2020), microrrede UFPR; O Setor Elétrico (2021). "
    "O diagrama é uma referência topológica; o alimentador simulado é didático."
)
styles.callout(
    "Leitura do diagrama",
    "O BESS proposto pode ser conectado no POI da UFPR ou ao longo do Alimentador Prado. "
    "O esquemático serve para localizar o debate; não é o modelo elétrico usado nos cálculos.",
)

st.divider()

styles.section(
    "Viabilidade",
    "Indicadores com premissas padrão",
    "Motivação: traduzir a operação do dia em custo e retorno.",
)
f = st.columns(4, gap="medium")
with f[0]:
    styles.metric_card("CAPEX estimado", fmt_mi(fin["capex"]), f"{fmt_brl(fin['capex'])}", "amber")
with f[1]:
    styles.metric_card(
        "VPL em 15 anos",
        fmt_mi(fin["npv"]),
        f"TIR {fmt_pct(fin['irr'] * 100.0)}",
        "teal",
        "good" if fin["npv"] > 0 else "bad",
    )
with f[2]:
    styles.metric_card(
        "Payback simples",
        f"{fin['payback']:.1f} anos".replace(".", ","),
        f"{fmt_mi(fin['net_savings'])}/ano de economia",
        "blue",
        "good" if np.isfinite(fin["payback"]) and fin["payback"] <= 8 else "warn",
    )
with f[3]:
    styles.metric_card("LCOE", f"R$ {fin['lcoe']:.0f}/MWh".replace(".", ","), "custos descontados", "purple")
source_note(
    "Premissas: ponta R$ 1,05/kWh; fora ponta R$ 0,55/kWh; demanda R$ 60/kW/mês; "
    "DEC/FEC evitados R$ 450 mil/ano; obra adiada R$ 400 mil/ano; CAPEX de potência R$ 600/kW; "
    "OPEX 1,5%/ano; horizonte 15 anos; desconto 12%; disponibilidade 97%; degradação 2%/ano."
)

st.divider()

styles.section(
    "Fontes e premissas",
    "Dados, premissas e simulação",
    "Motivação: deixar explícito o que é referência pública, premissa e resultado do modelo.",
)
source_rows = [
    [
        "Rede simulada",
        "Alimentador didático de 8 barras / 7 trechos em 13,8 kV; parâmetros típicos de R e X.",
        "Simulação",
    ],
    [
        "Perfis de carga",
        "Curvas sintéticas residencial, comercial e industrial; anualização = diário × 365.",
        "Sintético",
    ],
    [
        "Geração FV",
        "Curva clear-sky com evento de nuvem; capacidade padrão de 5,5 MWp.",
        "Sintético",
    ],
    [
        "BESS",
        "LFP 2 MW / 8 MWh; RTE 94%; SOC 10–90%; limite de 1,2 ciclos/dia; 6.000 ciclos.",
        "Premissa",
    ],
    [
        "Tarifas",
        '<a href="https://www.aneel.gov.br/tarifas" target="_blank" rel="noopener">ANEEL</a> · '
        "ponta R$ 1,05/kWh; fora ponta R$ 0,55/kWh; demanda R$ 60/kW/mês.",
        "Premissa",
    ],
    [
        "Tensão",
        '<a href="https://www.gov.br/aneel/pt-br/centrais-de-conteudo/prodist" target="_blank" rel="noopener">'
        "PRODIST/ANEEL</a> · faixa adequada de 0,93–1,05 pu.",
        "Norma",
    ],
    [
        "SEP de distribuição",
        '<a href="https://www.osetoreletrico.com.br/wp-content/uploads/2021/10/Cap6-PD.pdf" '
        'target="_blank" rel="noopener">SE Capanema → Alimentador Prado → UFPR</a> · '
        "9 alimentadores internos e 16 trafos 13,8/0,22 kV.",
        "Referência pública",
    ],
    [
        "SEP de transmissão",
        '<a href="https://www.curitiba.pr.gov.br/noticias/com-nova-subestacao-curitiba-amplia-autonomia-energetica/52665" '
        'target="_blank" rel="noopener">SE Curitiba-Centro → SE Uberaba</a> · 230 kV e 8 km de linha subterrânea.',
        "Referência pública",
    ],
    [
        "Financeiro",
        "CAPEX, OPEX, DEC/FEC, obra adiada, horizonte e desconto conforme premissas acima.",
        "Premissa",
    ],
]
styles.data_table(["Bloco", "Fonte / premissa", "Status"], source_rows)

st.markdown(
    "**Links:** "
    "[COPEL](https://www.copel.com/) · "
    "[UTFPR](https://www.utfpr.edu.br/) · "
    "[ANEEL PRODIST](https://www.gov.br/aneel/pt-br/centrais-de-conteudo/prodist) · "
    "[O Setor Elétrico](https://www.osetoreletrico.com.br/wp-content/uploads/2021/10/Cap6-PD.pdf)"
)
source_note(
    "Os indicadores técnicos vêm do modelo radial em `bess/model.py`. "
    "Os indicadores financeiros usam as premissas padrão da página e servem para comparação de cenários."
)
