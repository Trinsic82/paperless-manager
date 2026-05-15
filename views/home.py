import streamlit as st

def render_home():
    st.title("Paperless-ngx Metadata Manager")
    st.write("Willkommen! Dieses Tool hilft dir dabei, deine Paperless-ngx Metadaten effizient zu verwalten und zu bereinigen.")
    
    st.subheader("Funktionen im Überblick:")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**Checks**\n\nFinde Inkonsistenzen bei Speicherpfaden, entdecke ungenutzte Dokumenttypen und identifiziere fehlerhafte Datumsangaben.")
    with col2:
        st.info("**Gesamtliste**\n\nNutze die Tabellenansicht zur komfortablen Massenbearbeitung von Dokumenttypen, Korrespondenten und Speicherpfaden.")
    with col3:
        st.info("**Konfiguration**\n\nVerbinde das Tool mit deiner Paperless-ngx Instanz über die API.")
