import streamlit as st
from api import test_connection

def render_config():
    st.title("Konfiguration")
    new_url = st.text_input("URL", value=st.session_state["PAPERLESS_URL"])
    new_token = st.text_input("Token", value=st.session_state["PAPERLESS_TOKEN"], type="password")

    st.markdown("### Check-Grenzwerte")
    new_doc_type_threshold = st.number_input(
        "Dokumenttyp-Grenze für den Dokumenttypen-Check",
        min_value=1,
        step=1,
        value=st.session_state["DOC_TYPE_COUNT_THRESHOLD"],
    )
    new_date_future_threshold = st.number_input(
        "Maximale Jahre in der Zukunft für den Datums-Check",
        min_value=0,
        step=1,
        value=st.session_state["DATE_FUTURE_THRESHOLD"],
    )
    new_date_min_year_offset = st.number_input(
        "Jahre unterhalb des unteren 5%-Datums für den Datums-Check",
        min_value=0,
        step=1,
        value=st.session_state["DATE_MIN_YEAR_OFFSET"],
    )
    new_date_isolation_gap = st.number_input(
        "Isolierte Lücke in Jahren für den Datums-Check",
        min_value=1,
        step=1,
        value=st.session_state["DATE_ISOLATION_GAP_YEARS"],
    )
    new_custom_field_warning = st.number_input(
        "Custom Fields Warnschwelle (%)",
        min_value=0,
        max_value=100,
        step=1,
        value=st.session_state["CUSTOM_FIELD_WARNING_THRESHOLD"],
    )

    if st.button("Verbindung testen & speichern", type="primary"):
        st.session_state["PAPERLESS_URL"] = new_url
        st.session_state["PAPERLESS_TOKEN"] = new_token
        st.session_state["DOC_TYPE_COUNT_THRESHOLD"] = new_doc_type_threshold
        st.session_state["DATE_FUTURE_THRESHOLD"] = new_date_future_threshold
        st.session_state["DATE_MIN_YEAR_OFFSET"] = new_date_min_year_offset
        st.session_state["DATE_ISOLATION_GAP_YEARS"] = new_date_isolation_gap
        st.session_state["CUSTOM_FIELD_WARNING_THRESHOLD"] = new_custom_field_warning
        success, msg = test_connection()
        if success:
            st.success(msg)
            st.cache_data.clear()
        else:
            st.error(msg)
