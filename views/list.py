import streamlit as st
import pandas as pd
from api import update_document, fetch_custom_fields


def render_list(docs, doc_types, corresp, st_paths, tags, base_url):
    st.title("Gesamtliste")
    if st.button("🔄 Liste aktualisieren"):
        st.cache_data.clear()
        st.rerun()

    col1, col2 = st.columns(2)
    f_type = col1.selectbox("Typ Filter", ["Alle"] + list(doc_types.values()))
    f_corr = col2.selectbox("Korrespondent Filter", ["Alle", "Ohne"] + list(corresp.values()))
    
    custom_fields = fetch_custom_fields()
    cf_names = {cf['id']: cf['name'] for cf in custom_fields}

    filtered = []
    for d in docs:
        dt, co = doc_types.get(d.get('document_type'), ""), corresp.get(d.get('correspondent'), "")
        if f_type != "Alle" and dt != f_type: continue
        if f_corr == "Ohne" and co != "": continue
        if f_corr != "Alle" and f_corr != "Ohne" and co != f_corr: continue

        filled_fields = []
        for cf in d.get('custom_fields', []) or []:
            if not isinstance(cf, dict):
                continue
            value = cf.get('value')
            if value is None or (isinstance(value, str) and value.strip() == ""):
                continue
            field_name = cf_names.get(cf.get('field'), f"#{cf.get('field')}")
            filled_fields.append(field_name)

        doc_tags = [tags.get(tag_id, f"#{tag_id}") for tag_id in d.get('tags', [])]

        filtered.append({
            "Wählen": False,
            "ID": f"{base_url}/documents/{d['id']}/details",
            "Titel": d['title'],
            "Typ": dt,
            "Korrespondent": co,
            "Pfad": st_paths.get(d.get('storage_path'), "Standard"),
            "Custom Fields": "; ".join(filled_fields) if filled_fields else "",
            "Tags": "; ".join(doc_tags) if doc_tags else ""
        })
    
    if filtered:
        edited = st.data_editor(
            pd.DataFrame(filtered), hide_index=True, use_container_width=True,
            column_config={
                "Wählen": st.column_config.CheckboxColumn(required=True, width=None),
                "ID": st.column_config.LinkColumn("ID", display_text=r".*/documents/(\d+)/details", width=None)
            },
            disabled=["ID", "Titel", "Typ", "Korrespondent", "Pfad", "Custom Fields", "Tags"]
        )
        selected_ids = [int(url.split('/')[-2]) for url in edited[edited["Wählen"]]["ID"].tolist()]
        
        if selected_ids:
            st.subheader(f"{len(selected_ids)} ausgewählt. Neue Werte:")
            c1, c2, c3 = st.columns(3)
            nt = c1.selectbox("Neuer Typ", ["-"] + list(doc_types.values()))
            nc = c2.selectbox("Neuer Korrespondent", ["-"] + list(corresp.values()))
            np = c3.selectbox("Neuer Pfad", ["-"] + list(st_paths.values()))
            
            if st.button("🚀 Änderungen anwenden", type="primary"):
                pay = {}
                if nt != "-": pay['document_type'] = {v:k for k,v in doc_types.items()}[nt]
                if nc != "-": pay['correspondent'] = {v:k for k,v in corresp.items()}[nc]
                if np != "-": pay['storage_path'] = {v:k for k,v in st_paths.items()}[np]
                for sid in selected_ids: update_document(sid, pay)
                st.success(f"{len(selected_ids)} erfolgreich aktualisiert!")
                st.cache_data.clear()
                st.rerun()
