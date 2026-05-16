import streamlit as st
import pandas as pd
from collections import Counter

def _build_link(label, url):
    return f"{url}#{label}"


def render_analysis(docs, doc_types, corresp, st_paths, tags, base_url):
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
        df_types = pd.DataFrame([
            {
                "Typ": _build_link(
                    doc_types.get(k, "Ohne"),
                    f"{base_url}/documents/?document_type__id={k}" if k is not None else f"{base_url}/documents/?document_type__isnull=true"
                ),
                "Anzahl": v
            }
            for k, v in type_counts.items()
        ])
        st.dataframe(
            df_types.sort_values("Anzahl", ascending=False),
            hide_index=True,
            use_container_width=True,
            column_config={"Typ": st.column_config.LinkColumn("Typ", display_text=r"#(.*)$")}
        )
    with c2:
        st.subheader("Korrespondenten")
        df_corr = pd.DataFrame([
            {
                "Name": _build_link(
                    corresp.get(k, "Ohne"),
                    f"{base_url}/documents/?correspondent__id={k}" if k is not None else f"{base_url}/documents/?correspondent__isnull=true"
                ),
                "Anzahl": v
            }
            for k, v in corr_counts.items()
        ])
        st.dataframe(
            df_corr.sort_values("Anzahl", ascending=False),
            hide_index=True,
            use_container_width=True,
            column_config={"Name": st.column_config.LinkColumn("Name", display_text=r"#(.*)$")}
        )
    with c3:
        st.subheader("Speicherpfade")
        df_paths = pd.DataFrame([
            {
                "Pfad Name": _build_link(
                    st_paths.get(k, "Standard"),
                    f"{base_url}/documents/?storage_path__id={k}" if k is not None else f"{base_url}/documents/?storage_path__isnull=true"
                ),
                "Anzahl": v
            }
            for k, v in path_counts.items()
        ])
        st.dataframe(
            df_paths.sort_values("Anzahl", ascending=False),
            hide_index=True,
            use_container_width=True,
            column_config={"Pfad Name": st.column_config.LinkColumn("Pfad Name", display_text=r"#(.*)$")}
        )
    with c4:
        st.subheader("Tags")
        df_tags = pd.DataFrame([
            {
                "Tag": _build_link(
                    tags.get(k, "Unbekannt"),
                    f"{base_url}/documents/?tags__id={k}" if k is not None else f"{base_url}/documents/?tags__isnull=true"
                ),
                "Anzahl": v
            }
            for k, v in tag_counts.items()
        ])
        st.dataframe(
            df_tags.sort_values("Anzahl", ascending=False),
            hide_index=True,
            use_container_width=True,
            column_config={"Tag": st.column_config.LinkColumn("Tag", display_text=r"#(.*)$")}
        )
