import os
import streamlit as st

# --- Modul-Importe ---
from api import fetch_all
from views.home import render_home
from views.config import render_config
from views.analysis import render_analysis
from views.checks import (
    render_path_check,
    render_doctype_check,
    render_date_check,
    render_custom_field_check,
)
from views.list import render_list

# --- Seiten-Konfiguration ---
st.set_page_config(page_title="Paperless Metadata Manager", page_icon="📄", layout="wide")

# --- Session State Initialisierung ---
if "PAPERLESS_URL" not in st.session_state:
    st.session_state["PAPERLESS_URL"] = os.environ.get("PAPERLESS_URL", "")
if "PAPERLESS_TOKEN" not in st.session_state:
    st.session_state["PAPERLESS_TOKEN"] = os.environ.get("PAPERLESS_TOKEN", "")
if "IS_CONNECTED" not in st.session_state:
    st.session_state["IS_CONNECTED"] = False

if "DOC_TYPE_COUNT_THRESHOLD" not in st.session_state:
    st.session_state["DOC_TYPE_COUNT_THRESHOLD"] = 5
if "DATE_FUTURE_THRESHOLD" not in st.session_state:
    st.session_state["DATE_FUTURE_THRESHOLD"] = 0
if "DATE_MIN_YEAR_OFFSET" not in st.session_state:
    st.session_state["DATE_MIN_YEAR_OFFSET"] = 5
if "DATE_ISOLATION_GAP_YEARS" not in st.session_state:
    st.session_state["DATE_ISOLATION_GAP_YEARS"] = 5
if "CUSTOM_FIELD_WARNING_THRESHOLD" not in st.session_state:
    st.session_state["CUSTOM_FIELD_WARNING_THRESHOLD"] = 75

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
        [
            "Speicherpfad-Dokumenttyp-Check",
            "Dokumenttypen-Check",
            "Datums-Check",
            "Custom Fields-Check",
        ]
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
base_url = None
if page not in ["Startseite", "Konfiguration"]:
    if not st.session_state["IS_CONNECTED"]:
        st.warning("Bitte stelle zuerst unter Konfiguration eine Verbindung her.")
        st.stop()
    
    base_url = st.session_state['PAPERLESS_URL'].strip().rstrip('/')
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
    render_analysis(docs, doc_types, corresp, st_paths, tags, base_url)

elif page == "Speicherpfad-Dokumenttyp-Check":
    render_path_check(docs, doc_types, st_paths, base_url)

elif page == "Dokumenttypen-Check":
    render_doctype_check(
        docs,
        doc_types,
        base_url,
        st.session_state["DOC_TYPE_COUNT_THRESHOLD"],
    )

elif page == "Datums-Check":
    render_date_check(
        docs,
        doc_types,
        base_url,
        future_years=st.session_state["DATE_FUTURE_THRESHOLD"],
        min_year_offset=st.session_state["DATE_MIN_YEAR_OFFSET"],
        isolation_gap_years=st.session_state["DATE_ISOLATION_GAP_YEARS"],
    )

elif page == "Custom Fields-Check":
    render_custom_field_check(
        docs,
        doc_types,
        base_url,
        warning_threshold=st.session_state["CUSTOM_FIELD_WARNING_THRESHOLD"],
    )

elif page == "Gesamtliste":
    render_list(docs, doc_types, corresp, st_paths, base_url)

# Status Update
if st.session_state["IS_CONNECTED"]: 
    status_placeholder.success("🟢 API: Verbunden")
else: 
    status_placeholder.error("🔴 API: Nicht verbunden")
