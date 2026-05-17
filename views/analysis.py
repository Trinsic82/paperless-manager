import streamlit as st
import pandas as pd
from collections import Counter
from translations import translate

def _build_link(label, url):
    return f"{url}#{label}"


def render_analysis(docs, doc_types, corresp, st_paths, tags, base_url, language="de"):
    st.title(translate(language, "nav.pages.document_type_usage"))
    if st.button(translate(language, "analysis.document_type_usage_button"), key="document_type_usage_button"):
        st.cache_data.clear()

    st.subheader(translate(language, "analysis.document_type_usage_heading"))

    threshold = st.session_state.get("DOC_TYPE_COUNT_THRESHOLD", 5)
    type_counts = Counter([d.get('document_type') for d in docs])

    anomalies = []
    for dt_id, count in sorted(type_counts.items(), key=lambda item: item[1]):
        if count < threshold:
            dt_name = doc_types.get(dt_id, translate(language, "analysis.unknown"))
            if dt_id is not None:
                link = _build_link(dt_name, f"{base_url}/documents/?document_type__id={dt_id}")
            else:
                link = _build_link(dt_name, f"{base_url}/documents/?document_type__isnull=true")
            anomalies.append({
                translate(language, "analysis.document_types"): link,
                translate(language, "analysis.count"): count,
            })

    st.subheader(translate(language, "analysis.document_type_usage_anomaly_title", threshold=threshold))
    if anomalies:
        st.dataframe(
            pd.DataFrame(anomalies),
            hide_index=True,
            use_container_width=True,
            column_config={
                translate(language, "analysis.document_types"): st.column_config.LinkColumn(translate(language, "analysis.document_types"), display_text=r"#(.*)$", width=None),
            },
        )
    else:
        st.success(translate(language, "checks.doctype_no_results", threshold=threshold))

    st.subheader(translate(language, "analysis.document_type_usage_list_title"))
    df_types = pd.DataFrame([
        {
            translate(language, "analysis.document_types"): _build_link(
                doc_types.get(k, translate(language, "analysis.unknown")),
                f"{base_url}/documents/?document_type__id={k}" if k is not None else f"{base_url}/documents/?document_type__isnull=true"
            ),
            translate(language, "analysis.count"): v,
        }
        for k, v in sorted(type_counts.items(), key=lambda item: item[1], reverse=True)
    ])
    st.dataframe(
        df_types,
        hide_index=True,
        use_container_width=True,
        column_config={
            translate(language, "analysis.document_types"): st.column_config.LinkColumn(translate(language, "analysis.document_types"), display_text=r"#(.*)$", width=None),
        },
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
