import streamlit as st, pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np

def render():
    st.markdown("## Histórico")
    c1,c2,c3 = st.columns([1,1,1])
    dt_ini = c1.date_input("Data Inicial", datetime.now().date()-timedelta(days=30))
    dt_fim = c2.date_input("Data Final", datetime.now().date())
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    c3.button("Exportar Excel")

    df = pd.DataFrame({
        "Data":["06/10/2023","08/08/2023","08/08/2023","08/07/2023","08/06/2023"],
        "Turbidez (NTU)":[0.20,0.26,0.25,0.19,0.21],
        "pH":[7.3,7.4,7.1,7.2,7.3],
        "Vazão (m³/h)":[118,121,116,119,115]
    })
    st.markdown('<div class="card" style="margin-top:10px">', unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # série (mock) para o gráfico
    base = datetime.now()-timedelta(days=30)
    ts = [base + timedelta(days=i) for i in range(31)]
    dfp = pd.DataFrame({
        "ts": ts,
        "Turbidez (NTU)": 0.16 + 0.04*np.sin(np.linspace(0, 5.5, len(ts))),
        "pH": 7.2 + 0.15*np.cos(np.linspace(0, 3.5, len(ts))),
        "Vazão (m³/h)": 112 + 6*np.sin(np.linspace(0, 8, len(ts)))
    })
    fig = px.line(dfp, x="ts", y=["Turbidez (NTU)","pH","Vazão (m³/h)"])
    fig.update_layout(
        height=320, margin=dict(l=10,r=10,t=10,b=10), legend=dict(orientation="h"),
        plot_bgcolor="#0c2731", paper_bgcolor="#0c2731",
        font=dict(color="#e9f1f7"),
        xaxis=dict(gridcolor="#174554", title=None),
        yaxis=dict(gridcolor="#174554")
    )
    st.markdown('<div class="card" style="margin-top:14px">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
