from __future__ import annotations

import base64
import html
from pathlib import Path

import streamlit as st

CSS = """
<style>
:root {
  --bg: #f5f6f7;
  --panel: #ffffff;
  --panel-soft: #fafbfb;
  --line: #e1e5e8;
  --line-soft: #eef0f1;
  --text: #1f2933;
  --muted: #66727c;
  --accent: #2f5d7c;
  --green: #2e6b5e;
  --amber: #b7791f;
  --red: #a84b4b;
  --purple: #5f5a7a;
}

html, body, [class*="css"] {
  font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.stApp {
  background: var(--bg);
  color: var(--text);
}

.block-container {
  padding-top: 1.1rem;
  padding-bottom: 3rem;
  max-width: 1400px;
}

#MainMenu, footer {
  visibility: hidden;
}

[data-testid="stSidebar"] {
  background: #ffffff;
  border-right: 1px solid var(--line);
}

[data-testid="stSidebar"] .block-container {
  padding-top: 1rem;
}

h1, h2, h3, h4 {
  color: var(--text);
  letter-spacing: -0.02em;
}

p, li, label, span {
  color: var(--text);
}

a {
  color: var(--accent);
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

[data-testid="stMetric"] {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 12px 14px;
}

[data-testid="stMetricLabel"] p {
  color: var(--muted) !important;
  font-size: 0.72rem !important;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

[data-testid="stMetricValue"] {
  color: var(--text) !important;
}

[data-testid="stDataFrame"] {
  border: 1px solid var(--line);
  border-radius: 12px;
  overflow: hidden;
}

.page-head {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 22px 26px 24px;
  margin-bottom: 22px;
}

.brand-row {
  display: flex;
  align-items: center;
  gap: 22px;
  flex-wrap: wrap;
  margin-bottom: 18px;
}

.brand-row img {
  display: block;
  width: auto;
}

.brand-row img.copel {
  height: 34px;
}

.brand-row img.utfpr {
  height: 40px;
}

.brand-divider {
  width: 1px;
  height: 30px;
  background: var(--line);
}

.page-kicker {
  color: var(--muted);
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.page-head h1 {
  margin: 0;
  max-width: 900px;
  font-size: clamp(1.8rem, 3.1vw, 2.6rem);
  line-height: 1.1;
  font-weight: 700;
}

.page-head p {
  max-width: 860px;
  color: var(--muted);
  font-size: 0.95rem;
  line-height: 1.55;
  margin: 10px 0 0;
}

.section-head {
  margin: 30px 0 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--line);
}

.section-kicker {
  color: var(--muted);
  font-size: 0.66rem;
  font-weight: 700;
  letter-spacing: 0.13em;
  text-transform: uppercase;
  margin-bottom: 5px;
}

.section-title {
  color: var(--text);
  font-size: 1.35rem;
  font-weight: 650;
  letter-spacing: -0.02em;
}

.section-sub {
  color: var(--muted);
  font-size: 0.84rem;
  margin-top: 4px;
  max-width: 920px;
  line-height: 1.5;
}

.metric-card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-top: 3px solid var(--accent);
  border-radius: 12px;
  padding: 13px 15px;
  min-height: 92px;
}

.metric-card.teal { border-top-color: var(--green); }
.metric-card.blue { border-top-color: var(--accent); }
.metric-card.amber { border-top-color: var(--amber); }
.metric-card.red { border-top-color: var(--red); }
.metric-card.purple { border-top-color: var(--purple); }

.metric-label {
  color: var(--muted);
  font-size: 0.66rem;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
}

.metric-value {
  color: var(--text);
  font-size: 1.35rem;
  font-weight: 650;
  margin-top: 5px;
  font-variant-numeric: tabular-nums;
}

.metric-delta {
  color: var(--muted);
  font-size: 0.74rem;
  margin-top: 4px;
}

.metric-delta.good { color: var(--green); }
.metric-delta.warn { color: var(--amber); }
.metric-delta.bad { color: var(--red); }

.callout {
  background: var(--panel);
  border: 1px solid var(--line);
  border-left: 4px solid var(--accent);
  border-radius: 10px;
  padding: 13px 15px;
  margin: 14px 0 4px;
}

.callout.warn {
  border-left-color: var(--amber);
  background: #fffbf3;
}

.callout-title {
  color: var(--text);
  font-size: 0.86rem;
  font-weight: 650;
}

.callout-text {
  color: var(--muted);
  font-size: 0.82rem;
  line-height: 1.5;
  margin-top: 3px;
}

.small-note {
  color: var(--muted);
  font-size: 0.72rem;
  line-height: 1.45;
  margin: 5px 0 10px;
}

.sidebar-brand {
  border-bottom: 1px solid var(--line);
  padding: 2px 0 12px;
  margin-bottom: 10px;
}

.brand-text {
  color: var(--text);
  font-size: 1rem;
  font-weight: 700;
}

.brand-sub {
  color: var(--muted);
  font-size: 0.68rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-top: 2px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 10px;
  overflow: hidden;
  font-size: 0.79rem;
  margin: 6px 0 4px;
}

.data-table th {
  background: #f0f2f4;
  color: var(--muted);
  font-size: 0.66rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  text-align: left;
  padding: 9px 11px;
  border-bottom: 1px solid var(--line);
}

.data-table td {
  color: var(--text);
  padding: 9px 11px;
  border-bottom: 1px solid var(--line-soft);
  vertical-align: top;
}

.data-table tr:last-child td {
  border-bottom: 0;
}

.data-table tr:hover td {
  background: #f8f9fa;
}

.data-table td.num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
</style>
"""


def _logo_data_uri(name: str) -> str:
    path = Path(__file__).resolve().parent.parent / "assets" / name
    try:
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    except OSError:
        return ""
    return f"data:image/svg+xml;base64,{encoded}"


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def hero() -> None:
    copel = _logo_data_uri("copel.svg")
    utfpr = _logo_data_uri("utfpr.svg")
    logos = []
    if copel:
        logos.append(
            '<a href="https://www.copel.com/" target="_blank" rel="noopener">'
            f'<img class="copel" src="{copel}" alt="COPEL"></a>'
        )
    if utfpr:
        logos.append(
            '<a href="https://www.utfpr.edu.br/" target="_blank" rel="noopener">'
            f'<img class="utfpr" src="{utfpr}" alt="UTFPR"></a>'
        )
    brand_html = (
        '<div class="brand-row">'
        + '<span class="brand-divider"></span>'.join(logos)
        + "</div>"
        if logos
        else ""
    )
    st.markdown(
        f"""
        <div class="page-head">
          {brand_html}
          <div class="page-kicker">Oficina de Integração 2 · Engenharia Elétrica</div>
          <h1>BESS em redes de distribuição</h1>
          <p>
            Simulador para comparar a operação de um alimentador de 13,8 kV com e sem
            um BESS de 2 MW / 8 MWh. Ajuste o cenário na barra lateral.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def brand_sidebar() -> None:
    st.markdown(
        """
        <div class="sidebar-brand">
          <div class="brand-text">BESS Lab</div>
          <div class="brand-sub">COPEL · UTFPR</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section(kicker: str, title: str, subtitle: str = "") -> None:
    sub = f'<div class="section-sub">{html.escape(subtitle)}</div>' if subtitle else ""
    st.markdown(
        f'<div class="section-head"><div class="section-kicker">{html.escape(kicker)}</div>'
        f'<div class="section-title">{html.escape(title)}</div>{sub}</div>',
        unsafe_allow_html=True,
    )


def metric_card(
    label: str,
    value: str,
    delta: str | None = None,
    tone: str = "teal",
    delta_tone: str = "",
) -> None:
    delta_html = (
        f'<div class="metric-delta {delta_tone}">{html.escape(delta)}</div>'
        if delta
        else ""
    )
    st.markdown(
        f'<div class="metric-card {tone}">'
        f'<div class="metric-label">{html.escape(label)}</div>'
        f'<div class="metric-value">{html.escape(value)}</div>'
        f'{delta_html}</div>',
        unsafe_allow_html=True,
    )


def callout(title: str, text: str, tone: str = "") -> None:
    cls = f"callout {tone}".strip()
    st.markdown(
        f'<div class="{cls}"><div class="callout-title">{html.escape(title)}</div>'
        f'<div class="callout-text">{html.escape(text)}</div></div>',
        unsafe_allow_html=True,
    )


def data_table(headers: list[str], rows: list[list[str]], numeric_cols: set[int] | None = None) -> None:
    numeric_cols = numeric_cols or set()
    head = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    body = []
    for row in rows:
        cells = []
        for i, cell in enumerate(row):
            cls = ' class="num"' if i in numeric_cols else ""
            cells.append(f"<td{cls}>{cell}</td>")
        body.append(f"<tr>{''.join(cells)}</tr>")
    st.markdown(
        f'<table class="data-table"><thead><tr>{head}</tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table>',
        unsafe_allow_html=True,
    )
