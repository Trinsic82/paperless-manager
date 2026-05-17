import streamlit as st
from translations import translate

def render_home(language="de"):
    st.title(translate(language, "home.title"))
    st.write(translate(language, "home.welcome"))

    st.subheader(translate(language, "home.overview_header"))
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(translate(language, "home.checks_info"))
    with col2:
        st.info(translate(language, "home.all_documents_info"))
    with col3:
        st.info(translate(language, "home.configuration_info"))


def render_admin_overview(language="de"):
    st.title(translate(language, "nav.pages.administration"))
    st.write(translate(language, "home.administration_intro"))

    col1, col2 = st.columns(2)
    buttons = [
        (translate(language, "nav.pages.all_documents"), "all_documents"),
        (translate(language, "nav.pages.id_duplicates"), "id_duplicates"),
        (translate(language, "nav.pages.document_type_usage"), "document_type_usage"),
        (translate(language, "nav.pages.storage_path_anomalies"), "storage_path_anomalies"),
        (translate(language, "nav.pages.custom_field_anomalies"), "custom_field_anomalies"),
        (translate(language, "nav.pages.correspondent_usage"), "correspondent_usage"),
        (translate(language, "nav.pages.date_anomalies"), "date_anomalies"),
    ]

    for idx, (label, page_id) in enumerate(buttons):
        col = col1 if idx % 2 == 0 else col2
        with col:
            if st.button(label, key=f"admin_nav_{page_id}"):
                st.session_state["PAGE"] = page_id
