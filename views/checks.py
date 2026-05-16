import streamlit as st
import pandas as pd
from collections import Counter
from checks import check_document_types_count, check_path_consistency, check_date_anomalies

def render_path_check(docs, doc_types, st_paths, base_url):
    st.title("⚖️ Speicherpfad-Dokumenttyp-Check")
    if st.button("🔄 Check wiederholen"):
        st.cache_data.clear()
        st.rerun()

    anomalies = check_path_consistency(docs, doc_types, st_paths, base_url)
    
    if anomalies:
        st.dataframe(
            pd.DataFrame(anomalies), 
            use_container_width=True, 
            hide_index=True, 
            column_config={"ID": st.column_config.LinkColumn("ID", display_text=r".*/documents/(\d+)/details", width=None)}
        )
    else:
        st.success("Alle Pfade sind konsistent!")

def render_doctype_check(docs, doc_types, base_url):
    st.title("📉 Dokumenttypen-Check")
    st.write("Zeigt alle Dokumenttypen, die weniger als 5 Einträge haben.")
    if st.button("🔄 Check wiederholen", key="doctype_refresh"):
        st.cache_data.clear()
        st.rerun()

    few_docs = check_document_types_count(docs, doc_types, base_url)
    if few_docs:
        st.dataframe(
            pd.DataFrame(few_docs).sort_values("Anzahl", ascending=True),
            hide_index=True,
            use_container_width=True,
            column_config={
                "Dokumenttyp": st.column_config.LinkColumn("Dokumenttyp", display_text=r"#(.*)$", width=None)
            }
        )
    else:
        st.success("Keine Dokumenttypen mit weniger als 5 Einträgen gefunden!")

def render_date_check(docs, doc_types, base_url):
    st.title("📅 Datums-Check")
    st.write("Identifiziert Dokumente mit verdächtigen Jahreszahlen (Zukunft, globale Ausreißer oder > 5 Jahre Lücke im Typ).")
    if st.button("🔄 Check wiederholen", key="date_refresh"):
        st.cache_data.clear()
        st.rerun()

    date_anomalies = check_date_anomalies(docs, doc_types, base_url)

    if date_anomalies:
        df_dates = pd.DataFrame(date_anomalies)
        st.dataframe(
            df_dates, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "ID": st.column_config.LinkColumn("ID", display_text=r".*/documents/(\d+)/details", width=None),
                "Typ": st.column_config.LinkColumn("Typ", display_text=r"#(.*)$", width=None),
                "Jahr": st.column_config.NumberColumn(format="%d", width=None)
            }
        )
    else: 
        st.success("Keine Datums-Anomalien gefunden!")
