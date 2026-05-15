import streamlit as st
import pandas as pd
from collections import Counter

def render_analysis(docs, doc_types, corresp, st_paths, tags):
    st.title("📊 Metadaten Analyse")
    if st.button("🔄 Analyse aktualisieren"):
        st.cache_data.clear()
        st.rerun()

    type_counts = Counter([d.get('document_type') for d in docs])
    corr_counts = Counter([d.get('correspondent') for d in docs])
    path_counts = Counter([d.get('storage_path') for d in docs])
    tag_counts = Counter([t for d in docs for t in d.get('tags', [])])

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.subheader("Dokumenttypen")
        df_types = pd.DataFrame([{"Typ": doc_types.get(k, "Ohne"), "Anzahl": v} for k, v in type_counts.items()])
        st.dataframe(df_types.sort_values("Anzahl", ascending=False), hide_index=True, use_container_width=True)
    with c2:
        st.subheader("Korrespondenten")
        df_corr = pd.DataFrame([{"Name": corresp.get(k, "Ohne"), "Anzahl": v} for k, v in corr_counts.items()])
        st.dataframe(df_corr.sort_values("Anzahl", ascending=False), hide_index=True, use_container_width=True)
    with c3:
        st.subheader("Speicherpfade")
        df_paths = pd.DataFrame([{"Pfad Name": st_paths.get(k, "Standard"), "Anzahl": v} for k, v in path_counts.items()])
        st.dataframe(df_paths.sort_values("Anzahl", ascending=False), hide_index=True, use_container_width=True)
    with c4:
        st.subheader("Tags")
        df_tags = pd.DataFrame([{"Tag": tags.get(k, "Unbekannt"), "Anzahl": v} for k, v in tag_counts.items()])
        st.dataframe(df_tags.sort_values("Anzahl", ascending=False), hide_index=True, use_container_width=True)
