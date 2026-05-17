import streamlit as st
import pandas as pd
from api import update_document, fetch_custom_fields
from translations import translate


def render_list(docs, doc_types, corresp, st_paths, tags, base_url):
    language = st.session_state.get("LANGUAGE", "de")
    st.title(translate(language, "list.title"))
    if st.button(translate(language, "list.refresh")):
        st.cache_data.clear()
        st.rerun()

    col1, col2 = st.columns(2)
    f_type = col1.selectbox(translate(language, "list.type_filter"), [translate(language, "list.all")] + list(doc_types.values()))
    f_corr = col2.selectbox(
        translate(language, "list.correspondent_filter"),
        [translate(language, "list.all"), translate(language, "list.none")] + list(corresp.values()),
    )
    
    custom_fields = fetch_custom_fields()
    cf_names = {cf['id']: cf['name'] for cf in custom_fields}

    filtered = []
    for d in docs:
        dt, co = doc_types.get(d.get('document_type'), ""), corresp.get(d.get('correspondent'), "")
        if f_type != translate(language, "list.all") and dt != f_type:
            continue
        if f_corr == translate(language, "list.none") and co != "":
            continue
        if f_corr != translate(language, "list.all") and f_corr != translate(language, "list.none") and co != f_corr:
            continue

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
            translate(language, "list.id"): f"{base_url}/documents/{d['id']}/details",
            translate(language, "list.title_col"): d['title'],
            translate(language, "list.type_col"): dt,
            translate(language, "list.correspondent_col"): co,
            translate(language, "list.path_col"): st_paths.get(d.get('storage_path'), translate(language, "common.standard")),
            translate(language, "list.custom_fields"): cf_link,
            translate(language, "list.tags"): "; ".join(doc_tags) if doc_tags else ""
        })
    
    if filtered:
        st.dataframe(
            pd.DataFrame(filtered), hide_index=True, use_container_width=True,
            column_config={
                translate(language, "list.id"): st.column_config.LinkColumn(translate(language, "list.id"), display_text=r".*/documents/(\d+)/details", width=None),
                translate(language, "list.custom_fields"): st.column_config.LinkColumn(translate(language, "list.custom_fields"), display_text=r"#(.*)$", width=None)
            }
        )
    else:
        st.info(translate(language, "list.no_documents"))
