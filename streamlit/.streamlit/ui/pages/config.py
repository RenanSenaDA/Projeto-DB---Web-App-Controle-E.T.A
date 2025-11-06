import streamlit as st

def render():
    st.markdown("## Configurações")
    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.markdown("### Unidades")
    st.selectbox("Turbidez", ["NTU"], key="cfg_turb")
    st.selectbox("Vazão", ["m³/h","L/s"], key="cfg_vazao")

    st.markdown("### Alarmes")
    c1,c2 = st.columns(2)
    c1.number_input("pH mínimo", 0.0, 14.0, 6.0, 0.1, key="cfg_ph_min")
    c2.number_input("pH máximo", 0.0, 14.0, 8.0, 0.1, key="cfg_ph_max")

    st.markdown("### Conta")
    st.text_input("Nome de usuário", value="usuario_exemplo")
    st.text_input("Alterar senha", type="password")

    st.markdown("### Tema")
    st.toggle("Modo escuro", value=True, disabled=True)

    st.button("💾 Salvar")
    st.markdown('</div>', unsafe_allow_html=True)
