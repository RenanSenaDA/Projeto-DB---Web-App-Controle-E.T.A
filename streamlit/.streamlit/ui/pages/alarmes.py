import streamlit as st, pandas as pd
from datetime import datetime, timedelta

# pontos de integração com seu backend (substitua pelas suas funções reais)
def fetch_alarmes(dt_ini, dt_fim):
    data = [
        ("27/04/2024","08:07","Falha na bomba de recirculação","Floculação","Crítico",False, 101),
        ("27/04/2024","08:42","Nível alto no tanque de floculação","Floculação","Alto",False, 102),
        ("26/04/2024","18:22","Pressão elevada no filtro","Filtração","Médio",True, 103),
        ("26/04/2024","12:10","Queda de pressão na entrada","Captação","Médio",False, 104),
        ("25/04/2024","02:15","Baixo nível no reservatório","Captação","Alto",False, 105),
    ]
    df = pd.DataFrame(data, columns=["Data","Hora","Alarme","Subsistema","Severidade","Reconhecido","ID"])
    return df

def ack_backend(ids:list):
    # TODO: implemente sua chamada ao Postgres/API aqui
    return True

def render():
    st.markdown("## Alarmes")

    # filtros
    c1,c2,c3,c4 = st.columns([1,1,1,1])
    dt_ini = c1.date_input("Início", datetime.now().date()-timedelta(days=7))
    dt_fim = c2.date_input("Fim", datetime.now().date())
    subs   = c3.selectbox("Subsistema", ["Todos","Captação","Floculação","Filtração"])
    apenas_abertos = c4.toggle("Apenas não reconhecidos", value=False)

    qtexto = st.text_input("Buscar por texto/equipamento", "")

    # dados
    df = fetch_alarmes(dt_ini, dt_fim)

    if subs!="Todos":
        df = df[df["Subsistema"]==subs]
    if apenas_abertos:
        df = df[~df["Reconhecido"]]
    if qtexto.strip():
        s = qtexto.strip().lower()
        df = df[df["Alarme"].str.lower().str.contains(s)]

    # tabela HTML com Pills
    def sev_pill(s):
        s = s.strip().lower()
        if s.startswith("cr"):  return '<span class="pill crit">Crítico</span>'
        if s.startswith("al"):  return '<span class="pill alto">Alto</span>'
        return '<span class="pill medio">Médio</span>'

    st.markdown('<div class="card">', unsafe_allow_html=True)
    html = ['<table class="table">']
    html.append("<thead><tr><th>DATA</th><th>HORA</th><th>ALARME</th><th>SUBSISTEMA</th><th>SEVERIDADE</th><th style='text-align:right;padding-right:18px'>AÇÃO</th></tr></thead><tbody>")
    for _,row in df.iterrows():
        btn_name = f"ack_{row['ID']}"
        html.append(
            f"<tr><td>{row['Data']}</td><td>{row['Hora']}</td><td>{row['Alarme']}</td>"
            f"<td>{row['Subsistema']}</td><td>{sev_pill(row['Severidade'])}</td>"
            f"<td style='text-align:right'><form action='#'><button kind='secondary' name='{btn_name}'>Reconhecer</button></form></td></tr>"
        )
    html.append("</tbody></table>")
    st.markdown("".join(html), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # botão de linha (fallback usando data_editor seria mais “nativo”, mas mantive o visual)
    # atalho: botão global para reconhecer selecionados
    if st.button("✅ Reconhecer todos filtrados"):
        ok = ack_backend(df["ID"].tolist())
        if ok: st.success("Alarmes reconhecidos.")
