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
        dt_id = d.get('document_type')
        cf_display = "; ".join(filled_fields) if filled_fields else ""
        cf_link = f"{base_url}/documents/?document_type__id={dt_id}#{cf_display}" if cf_display and dt_id else ""

        filtered.append({
            "ID": f"{base_url}/documents/{d['id']}/details",
            "Titel": d['title'],
            "Typ": dt,
            "Korrespondent": co,
            "Pfad": st_paths.get(d.get('storage_path'), "Standard"),
            "Custom Fields": cf_link,
            "Tags": "; ".join(doc_tags) if doc_tags else ""
        })
    
    if filtered:
        st.dataframe(
            pd.DataFrame(filtered), hide_index=True, use_container_width=True,
            column_config={
                "ID": st.column_config.LinkColumn("ID", display_text=r".*/documents/(\d+)/details", width=None),
                "Custom Fields": st.column_config.LinkColumn("Custom Fields", display_text=r"#(.*)$", width=None)
            }
        )
    else:
        st.info("Keine Dokumente mit den gewählten Filtern gefunden.")
