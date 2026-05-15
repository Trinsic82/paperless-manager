import streamlit as st
from api import test_connection

def render_config():
    st.title("Konfiguration")
    new_url = st.text_input("URL", value=st.session_state["PAPERLESS_URL"])
    new_token = st.text_input("Token", value=st.session_state["PAPERLESS_TOKEN"], type="password")
    if st.button("Verbindung testen & speichern", type="primary"):
        st.session_state["PAPERLESS_URL"], st.session_state["PAPERLESS_TOKEN"] = new_url, new_token
        success, msg = test_connection()
        if success:
            st.success(msg)
            st.cache_data.clear()
        else:
            st.error(msg)
