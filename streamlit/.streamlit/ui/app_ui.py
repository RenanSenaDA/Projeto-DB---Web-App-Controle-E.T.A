import streamlit as st
from datetime import datetime
import os, sys

# --- Config da página ---
st.set_page_config(page_title="ETA Monitor", page_icon="💧", layout="wide", initial_sidebar_state="collapsed")

# --- Paths ---
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))          # .../.streamlit/ui
ROOT_DIR   = os.path.abspath(os.path.join(BASE_DIR, "..", "..")) # .../streamlit
ASSETS_DIR = os.path.join(ROOT_DIR, ".streamlit", "assets")
PAGES_DIR  = os.path.join(BASE_DIR, "pages")                     # .../.streamlit/ui/pages

# Torna possível: import dashboard/alarmes/historico/config
if PAGES_DIR not in sys.path:
    sys.path.append(PAGES_DIR)

# --- CSS global ---
css_path = os.path.join(ASSETS_DIR, "styles.css")
if os.path.exists(css_path):
    st.markdown(f"<style>{open(css_path, encoding='utf-8').read()}</style>", unsafe_allow_html=True)

# Esconde menu lateral padrão
st.markdown("<style>[data-testid='stSidebarNav']{display:none}</style>", unsafe_allow_html=True)

# --- Header / Brand ---
st.markdown(
    f"""
    <div class="navbar">
      <div class="brand">
        <span class="logo"></span>
        <span>ETA Monitor</span>
      </div>
      <div class="time">Atualizado: {datetime.now():%H:%M:%S}</div>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Abas (funcionais) ---
tab_labels = ["Dashboard", "Alarmes", "Histórico", "Configurações"]
tabs = st.tabs(tab_labels)

with tabs[0]:
    import dashboard as pg
    pg.render()

with tabs[1]:
    import alarmes as pg
    pg.render()

with tabs[2]:
    import historico as pg
    pg.render()

with tabs[3]:
    import config as pg
    pg.render()
