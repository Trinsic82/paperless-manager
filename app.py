import os
import streamlit as st

# --- Modul-Importe ---
from api import fetch_all
from views.home import render_home, render_admin_overview
from views.config import render_config
from views.analysis import render_analysis, render_correspondent_usage
from views.checks import (
    render_path_check,
    render_doctype_check,
    render_date_check,
    render_custom_field_check,
    render_custom_field_correspondent_check,
    render_id_duplicate_check,
)
from views.list import render_list
from translations import translate

# --- Seiten-Konfiguration ---
st.set_page_config(page_title="Paperless Metadata Manager", page_icon="📄", layout="wide")

# --- Session State Initialisierung ---
if "PAPERLESS_URL" not in st.session_state:
    st.session_state["PAPERLESS_URL"] = os.environ.get("PAPERLESS_URL", "")
if "PAPERLESS_TOKEN" not in st.session_state:
    st.session_state["PAPERLESS_TOKEN"] = os.environ.get("PAPERLESS_TOKEN", "")
if "IS_CONNECTED" not in st.session_state:
    st.session_state["IS_CONNECTED"] = False
if "LANGUAGE" not in st.session_state:
    st.session_state["LANGUAGE"] = os.environ.get("LANGUAGE", "de") if os.environ.get("LANGUAGE") in ["de", "en"] else "de"
if "PAGE" not in st.session_state:
    st.session_state["PAGE"] = "dashboard"

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

language = st.session_state["LANGUAGE"]
page = st.session_state["PAGE"]

NAV_SECTIONS = [
    (None, ["dashboard", "configuration"]),
    ("basics", ["administration", "all_documents", "id_duplicates", "document_type_usage"]),
    ("doc_types", ["storage_path_anomalies", "custom_field_anomalies"]),
    ("correspondents", ["correspondent_usage"]),
    ("date", ["date_anomalies"]),
]

# --- SEITENLEISTE ---
for heading, page_ids in NAV_SECTIONS:
    if heading is not None:
        st.sidebar.markdown(f"### {translate(language, f'nav.headings.{heading}')}")

    for page_id in page_ids:
        label = translate(language, f'nav.pages.{page_id}')
        if st.sidebar.button(label, key=f"nav_{page_id}"):
            st.session_state["PAGE"] = page_id
            page = page_id

st.sidebar.divider()

if st.sidebar.button(translate(language, "app.reload_data"), use_container_width=True):
    st.cache_data.clear()

st.sidebar.divider()
status_placeholder = st.sidebar.empty()

# --- DATEN LADEN ---
base_url = None
needs_data = page not in ["dashboard", "configuration", "administration"]
if needs_data:
    if not st.session_state["IS_CONNECTED"]:
        st.warning(translate(language, "app.connection_warning"))
        st.stop()

    base_url = st.session_state['PAPERLESS_URL'].strip().rstrip('/')
    with st.spinner(translate(language, "app.loading_data")):
        docs = fetch_all('documents')
        doc_types = {dt['id']: dt['name'] for dt in fetch_all('document_types')}
        corresp = {c['id']: c['name'] for c in fetch_all('correspondents')}
        st_paths = {sp['id']: sp['name'] for sp in fetch_all('storage_paths')}
        tags = {t['id']: t['name'] for t in fetch_all('tags')}

    if not docs:
        st.error(translate(language, "app.load_error"))
        st.stop()

# --- PAGES ---
if page == "dashboard":
    render_home(language)

elif page == "configuration":
    render_config()

elif page == "administration":
    render_admin_overview(language)

elif page == "all_documents":
    render_list(docs, doc_types, corresp, st_paths, tags, base_url)

elif page == "id_duplicates":
    render_id_duplicate_check(docs, base_url)

elif page == "document_type_usage":
    render_analysis(docs, doc_types, corresp, st_paths, tags, base_url, st.session_state["LANGUAGE"])

elif page == "storage_path_anomalies":
    render_path_check(docs, doc_types, st_paths, base_url)

elif page == "custom_field_anomalies":
    render_custom_field_check(
        docs,
        doc_types,
        base_url,
        warning_threshold=st.session_state["CUSTOM_FIELD_WARNING_THRESHOLD"],
    )

elif page == "correspondent_usage":
    render_correspondent_usage(docs, corresp, st_paths, base_url, st.session_state["LANGUAGE"])

elif page == "date_anomalies":
    render_date_check(
        docs,
        doc_types,
        base_url,
        future_years=st.session_state["DATE_FUTURE_THRESHOLD"],
        min_year_offset=st.session_state["DATE_MIN_YEAR_OFFSET"],
        isolation_gap_years=st.session_state["DATE_ISOLATION_GAP_YEARS"],
    )

# Status Update
if st.session_state["IS_CONNECTED"]:
    status_placeholder.success(translate(language, "app.api_connected"))
else:
    status_placeholder.error(translate(language, "app.api_disconnected"))
