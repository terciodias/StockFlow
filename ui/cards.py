"""Cartões de KPI em HTML/CSS. Nunca usar st.metric para indicadores de monitoramento."""

import streamlit as st

from config import CORES

_COR_STATUS = {"verde": CORES["ok"], "amarelo": CORES["atencao"], "vermelho": CORES["critico"]}


def card_kpi(rotulo, valor, meta, status, fmt="{:.0f}", sufixo="", maior_melhor=False, subtitulo_meta="Média histórica"):
    cor_borda = _COR_STATUS[status]
    delta = valor - meta
    delta_ok = (delta >= 0) if maior_melhor else (delta <= 0)
    cor_delta = CORES["ok"] if delta_ok else CORES["critico"]
    seta = "▲" if delta >= 0 else "▼"

    html = f"""
    <div style="background:{CORES['fundo_card']};border:1px solid {CORES['borda_card']};
                border-left:6px solid {cor_borda};border-radius:12px;padding:16px 18px;
                box-shadow:0 2px 8px rgba(0,0,0,.06);height:118px;display:flex;flex-direction:column;justify-content:space-between;">
      <div style="font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:#8A8A8A;font-weight:600;">{rotulo}</div>
      <div style="font-size:28px;font-weight:700;color:{CORES['texto']};line-height:1.1;">{fmt.format(valor)}{sufixo}</div>
      <div style="font-size:12.5px;color:#6B6B6B;">
        {subtitulo_meta} {fmt.format(meta)}{sufixo} ·
        <span style="color:{cor_delta};font-weight:600;">{seta} {fmt.format(abs(delta))}{sufixo}</span>
      </div>
    </div>"""
    st.markdown(html, unsafe_allow_html=True)
