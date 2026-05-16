import os
import streamlit as st

# --- Modul-Importe ---
from api import fetch_all
from views.home import render_home
from views.config import render_config
from views.analysis import render_analysis
from views.checks import render_path_check, render_doctype_check, render_date_check
from views.list import render_list

# --- Seiten-Konfiguration ---
st.set_page_config(page_title="Paperless Metadata Manager", page_icon="📄", layout="wide")

# --- Session State Initialisierung ---
if "PAPERLESS_URL" not in st.session_state:
    st.session_state["PAPERLESS_URL"] = os.environ.get("PAPERLESS_URL", "http://192.168.5.136:8000")
if "PAPERLESS_TOKEN" not in st.session_state:
    st.session_state["PAPERLESS_TOKEN"] = os.environ.get("PAPERLESS_TOKEN", "9f825c85ecf5f0ca2b197986d0115d7c061cc3b4")
if "IS_CONNECTED" not in st.session_state:
    st.session_state["IS_CONNECTED"] = False

# --- SEITENLEISTE ---
st.sidebar.title("Navigation")
category = st.sidebar.radio(
    "Bereich", 
    ["Startseite", "Konfiguration", "Metadaten Analyse", "Checks", "Gesamtliste"],
    label_visibility="collapsed"
)

page = None
if category == "Startseite":
    page = "Startseite"
elif category == "Konfiguration":
    page = "Konfiguration"
elif category == "Metadaten Analyse":
    page = "Metadaten Analyse"
elif category == "Checks":
    page = st.sidebar.radio(
        "Verfügbare Checks:",
        ["Speicherpfad-Dokumenttyp-Check", "Dokumenttypen-Check", "Datums-Check"]
    )
elif category == "Gesamtliste":
    page = "Gesamtliste"

st.sidebar.divider()

if st.sidebar.button("Daten neu laden", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()
status_placeholder = st.sidebar.empty()

# --- DATEN LADEN ---
if page not in ["Startseite", "Konfiguration"]:
    if not st.session_state["IS_CONNECTED"]:
        st.warning("Bitte stelle zuerst unter Konfiguration eine Verbindung her.")
        st.stop()
    
    with st.spinner("Lade Daten..."):
        docs = fetch_all('documents')
        doc_types = {dt['id']: dt['name'] for dt in fetch_all('document_types')}
        corresp = {c['id']: c['name'] for c in fetch_all('correspondents')}
        st_paths = {sp['id']: sp['name'] for sp in fetch_all('storage_paths')}
        tags = {t['id']: t['name'] for t in fetch_all('tags')}
    
    if not docs:
        st.error("Konnte keine Dokumente laden.")
        st.stop()

# --- PAGES ---
if page == "Startseite":
    render_home()

elif page == "Konfiguration":
    render_config()

elif page == "Metadaten Analyse":
    base_url = st.session_state['PAPERLESS_URL'].strip().rstrip('/')
    render_analysis(docs, doc_types, corresp, st_paths, tags, base_url)

elif page == "Speicherpfad-Dokumenttyp-Check":
    base_url = st.session_state['PAPERLESS_URL'].strip().rstrip('/')
    render_path_check(docs, doc_types, st_paths, base_url)

elif page == "Dokumenttypen-Check":
    base_url = st.session_state['PAPERLESS_URL'].strip().rstrip('/')
    render_doctype_check(docs, doc_types, base_url)

elif page == "Datums-Check":
    base_url = st.session_state['PAPERLESS_URL'].strip().rstrip('/')
    render_date_check(docs, doc_types, base_url)

elif page == "Gesamtliste":
    base_url = st.session_state['PAPERLESS_URL'].strip().rstrip('/')
    render_list(docs, doc_types, corresp, st_paths, base_url)

# Status Update
if st.session_state["IS_CONNECTED"]: 
    status_placeholder.success("🟢 API: Verbunden")
else: 
    status_placeholder.error("🔴 API: Nicht verbunden")
