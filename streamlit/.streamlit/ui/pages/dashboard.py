import streamlit as st, pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np

def kpi(title, value, subtitle="", status="ok"):
    st.markdown(
        f"""
        <div class="kpi">
          <div class="title">{title}</div>
          <div class="value">{value}</div>
          <span class="badge {status}">{subtitle}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

def render():
    st.markdown("## Dashboard")

    c1,c2,c3,c4 = st.columns(4)
    with c1: kpi("Turbidez", "0,18 NTU", "Dentro do limite", "ok")
    with c2: kpi("pH", "7,2", "Alvo 6,5–8,5", "ok")
    with c3: kpi("Vazão", "122 m³/h", "Estável", "ok")
    with c4: kpi("Cloro Residual", "2,1 mg/L", "Atenção", "warn")

    # SÉRIE MOCK (substitua pelo seu fetch real)
    base = datetime.now().replace(minute=0, second=0, microsecond=0) - timedelta(hours=12)
    ts = [base + timedelta(minutes=15*i) for i in range(49)]
    y  = 0.12 + 0.05*np.sin(np.linspace(0, 3.5, len(ts))) + np.random.default_rng(7).normal(0,0.005,len(ts))
    df = pd.DataFrame({"Hora": ts, "Turbidez (NTU)": y.round(3)})

    fig = px.line(df, x="Hora", y="Turbidez (NTU)")
    fig.update_traces(line=dict(width=3))
    fig.update_layout(
        height=320, margin=dict(l=10,r=10,t=10,b=10),
        plot_bgcolor="#0c2731", paper_bgcolor="#0c2731",
        font=dict(color="#e9f1f7"),
        xaxis=dict(gridcolor="#174554", title=None),
        yaxis=dict(gridcolor="#174554")
    )
    st.markdown('<div class="card" style="margin-top:8px">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    r1, r2 = st.columns(2)
    with r1:
        st.markdown('<div class="card"><b>Captação</b><br><span class="badge ok">Operando</span></div>', unsafe_allow_html=True)
    with r2:
        st.markdown('<div class="card"><b>Filtração</b><br><span class="badge warn">Manutenção</span></div>', unsafe_allow_html=True)
