import streamlit as st
import pandas as pd
from collections import Counter
from translations import translate

def _build_link(label, url):
    return f"{url}#{label}"


def render_analysis(docs, doc_types, corresp, st_paths, tags, base_url, language="de"):
    st.title(translate(language, "analysis.document_type_usage_title"))
    refresh_label = translate(language, "analysis.analysis_refresh")
    if st.button(refresh_label):
        st.cache_data.clear()

    type_counts = Counter([d.get('document_type') for d in docs])
    corr_counts = Counter([d.get('correspondent') for d in docs])
    path_counts = Counter([d.get('storage_path') for d in docs])
    tag_counts = Counter([t for d in docs for t in d.get('tags', [])])

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.subheader(translate(language, "analysis.document_types"))
        df_types = pd.DataFrame([
            {
                translate(language, "analysis.document_types"): _build_link(
                    doc_types.get(k, translate(language, "analysis.unknown")),
                    f"{base_url}/documents/?document_type__id={k}" if k is not None else f"{base_url}/documents/?document_type__isnull=true"
                ),
                translate(language, "analysis.count"): v,
            }
            for k, v in type_counts.items()
        ])
        st.dataframe(
            df_types.sort_values(translate(language, "analysis.count"), ascending=False),
            hide_index=True,
            use_container_width=True,
            column_config={translate(language, "analysis.document_types"): st.column_config.LinkColumn(translate(language, "analysis.document_types"), display_text=r"#(.*)$", width=None)}
        )
    with c2:
        st.subheader(translate(language, "analysis.correspondents"))
        df_corr = pd.DataFrame([
            {
                translate(language, "analysis.correspondents"): _build_link(
                    corresp.get(k, translate(language, "analysis.unknown")),
                    f"{base_url}/documents/?correspondent__id={k}" if k is not None else f"{base_url}/documents/?correspondent__isnull=true"
                ),
                translate(language, "analysis.count"): v,
            }
            for k, v in corr_counts.items()
        ])
        st.dataframe(
            df_corr.sort_values(translate(language, "analysis.count"), ascending=False),
            hide_index=True,
            use_container_width=True,
            column_config={translate(language, "analysis.correspondents"): st.column_config.LinkColumn(translate(language, "analysis.correspondents"), display_text=r"#(.*)$", width=None)}
        )
    with c3:
        st.subheader(translate(language, "analysis.storage_paths"))
        df_paths = pd.DataFrame([
            {
                translate(language, "analysis.storage_paths"): _build_link(
                    st_paths.get(k, translate(language, "common.standard")),
                    f"{base_url}/documents/?storage_path__id={k}" if k is not None else f"{base_url}/documents/?storage_path__isnull=true"
                ),
                translate(language, "analysis.count"): v,
            }
            for k, v in path_counts.items()
        ])
        st.dataframe(
            df_paths.sort_values(translate(language, "analysis.count"), ascending=False),
            hide_index=True,
            use_container_width=True,
            column_config={translate(language, "analysis.storage_paths"): st.column_config.LinkColumn(translate(language, "analysis.storage_paths"), display_text=r"#(.*)$", width=None)}
        )
    with c4:
        st.subheader(translate(language, "analysis.tags"))
        df_tags = pd.DataFrame([
            {
                translate(language, "analysis.tags"): _build_link(
                    tags.get(k, translate(language, "analysis.unknown")),
                    f"{base_url}/documents/?tags__id={k}" if k is not None else f"{base_url}/documents/?tags__isnull=true"
                ),
                translate(language, "analysis.count"): v,
            }
            for k, v in tag_counts.items()
        ])
        st.dataframe(
            df_tags.sort_values(translate(language, "analysis.count"), ascending=False),
            hide_index=True,
            use_container_width=True,
            column_config={translate(language, "analysis.tags"): st.column_config.LinkColumn(translate(language, "analysis.tags"), display_text=r"#(.*)$", width=None)}
        )


def render_correspondent_usage(docs, corresp, st_paths, base_url, language="de"):
    st.title(translate(language, "correspondent_usage.title"))
    st.write(translate(language, "correspondent_usage.intro"))
    refresh_label = translate(language, "correspondent_usage.refresh")
    if st.button(refresh_label, key="correspondent_usage_refresh"):
        st.cache_data.clear()

    corr_counts = Counter([d.get('correspondent') for d in docs])
    usage_rows = []
    for corr_id, count in corr_counts.most_common():
        corr_name = corresp.get(corr_id, translate(language, "list.none"))
        if corr_id is not None:
            link = f"{base_url}/documents/?correspondent__id={corr_id}#{corr_name}"
        else:
            link = f"{base_url}/documents/?correspondent__isnull=true#{corr_name}"
        usage_rows.append({
            translate(language, "correspondent_usage.correspondent"): corr_name,
            translate(language, "correspondent_usage.count"): count,
            translate(language, "correspondent_usage.link"): link,
        })

    if usage_rows:
        st.subheader(translate(language, "correspondent_usage.correspondent"))
        st.dataframe(
            pd.DataFrame(usage_rows),
            use_container_width=True,
            hide_index=True,
            column_config={
                translate(language, "correspondent_usage.link"): st.column_config.LinkColumn(
                    translate(language, "correspondent_usage.link"), display_text=r".*", width=None
                )
            },
        )
    else:
        st.info(translate(language, "correspondent_usage.no_correspondent_documents"))

    combo_counts = Counter(
        (
            corresp.get(d.get('correspondent'), translate(language, "list.none")),
            st_paths.get(d.get('storage_path'), translate(language, "common.standard")),
        )
        for d in docs
    )

    combo_rows = []
    for (corr_name, path_name), count in combo_counts.most_common():
        corr_id = next((d.get('correspondent') for d in docs if corresp.get(d.get('correspondent'), translate(language, "list.none")) == corr_name), None)
        path_id = next((d.get('storage_path') for d in docs if st_paths.get(d.get('storage_path'), translate(language, "common.standard")) == path_name), None)
        corr_filter = f"correspondent__id={corr_id}" if corr_id is not None else "correspondent__isnull=true"
        path_filter = f"storage_path__id={path_id}" if path_id is not None else "storage_path__isnull=true"
        link = f"{base_url}/documents/?{corr_filter}&{path_filter}#{corr_name} / {path_name}"
        combo_rows.append({
            translate(language, "correspondent_usage.correspondent"): corr_name,
            translate(language, "correspondent_usage.storage_path"): path_name,
            translate(language, "correspondent_usage.count"): count,
            translate(language, "correspondent_usage.link"): link,
        })

    if combo_rows:
        st.subheader(translate(language, "correspondent_usage.combo_title"))
        st.write(translate(language, "correspondent_usage.combo_description"))
        st.dataframe(
            pd.DataFrame(combo_rows),
            use_container_width=True,
            hide_index=True,
            column_config={
                translate(language, "correspondent_usage.link"): st.column_config.LinkColumn(
                    translate(language, "correspondent_usage.link"), display_text=r".*", width=None
                )
            },
        )
    else:
        st.info(translate(language, "correspondent_usage.no_combinations"))
