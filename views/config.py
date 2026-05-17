import streamlit as st
from api import test_connection
from translations import translate


def render_config():
    language = st.session_state.get("LANGUAGE", "de")
    st.title(translate(language, "config.title"))
    new_url = st.text_input(translate(language, "config.url_label"), value=st.session_state["PAPERLESS_URL"])
    new_token = st.text_input(translate(language, "config.token_label"), value=st.session_state["PAPERLESS_TOKEN"], type="password")

    language_options = translate(language, "config.language_options")
    current_label = "Deutsch" if language == "de" else "English"
    new_language_label = st.selectbox(translate(language, "config.language_label"), list(language_options.keys()), index=list(language_options.keys()).index(current_label))
    new_language = language_options[new_language_label]

    st.markdown(translate(language, "config.check_thresholds"))
    new_doc_type_threshold = st.number_input(
        translate(language, "config.doc_type_threshold"),
        min_value=1,
        step=1,
        value=st.session_state["DOC_TYPE_COUNT_THRESHOLD"],
    )
    new_date_future_threshold = st.number_input(
        translate(language, "config.date_future_threshold"),
        min_value=0,
        step=1,
        value=st.session_state["DATE_FUTURE_THRESHOLD"],
    )
    new_date_min_year_offset = st.number_input(
        translate(language, "config.date_min_year_offset"),
        min_value=0,
        step=1,
        value=st.session_state["DATE_MIN_YEAR_OFFSET"],
    )
    new_date_isolation_gap = st.number_input(
        translate(language, "config.date_isolation_gap"),
        min_value=1,
        step=1,
        value=st.session_state["DATE_ISOLATION_GAP_YEARS"],
    )
    new_custom_field_warning = st.number_input(
        translate(language, "config.custom_field_warning"),
        min_value=0,
        max_value=100,
        step=1,
        value=st.session_state["CUSTOM_FIELD_WARNING_THRESHOLD"],
    )

    if st.button(translate(language, "config.save_button"), type="primary"):
        st.session_state["PAPERLESS_URL"] = new_url
        st.session_state["PAPERLESS_TOKEN"] = new_token
        st.session_state["DOC_TYPE_COUNT_THRESHOLD"] = new_doc_type_threshold
        st.session_state["DATE_FUTURE_THRESHOLD"] = new_date_future_threshold
        st.session_state["DATE_MIN_YEAR_OFFSET"] = new_date_min_year_offset
        st.session_state["DATE_ISOLATION_GAP_YEARS"] = new_date_isolation_gap
        st.session_state["CUSTOM_FIELD_WARNING_THRESHOLD"] = new_custom_field_warning
        st.session_state["LANGUAGE"] = new_language
        success, msg = test_connection()
        if success:
            st.success(msg)
            st.cache_data.clear()
        else:
            st.error(msg)
