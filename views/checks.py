import streamlit as st
import pandas as pd
from collections import Counter
from translations import translate
from checks import (
    check_document_types_count,
    check_path_consistency,
    check_date_anomalies,
    check_custom_field_missing,
    check_custom_field_missing_by_correspondent,
    check_id_duplicates,
)
from api import fetch_custom_fields

def render_path_check(docs, doc_types, st_paths, base_url):
    language = st.session_state.get("LANGUAGE", "de")
    st.title(translate(language, "checks.path_check_title"))
    if st.button(translate(language, "checks.check_refresh")):
        st.cache_data.clear()

    anomalies = check_path_consistency(docs, doc_types, st_paths, base_url)
    
    if anomalies:
        df_anomalies = pd.DataFrame(anomalies)
        df_anomalies = df_anomalies.rename(columns={
            "ID": translate(language, "checks.id"),
            "Titel": translate(language, "checks.title"),
            "Dokumenttyp": translate(language, "checks.document_type_label"),
            "Aktueller Pfad": translate(language, "checks.current_path"),
            "Erwarteter Pfad": translate(language, "checks.expected_path"),
        })
        st.dataframe(
            df_anomalies, 
            use_container_width=True, 
            hide_index=True, 
            column_config={
                translate(language, "checks.id"): st.column_config.LinkColumn(translate(language, "checks.id"), display_text=r".*/documents/(\d+)/details", width=None)
            }
        )
    else:
        st.success(translate(language, "checks.path_consistent"))

def render_doctype_check(docs, doc_types, base_url, threshold=5):
    language = st.session_state.get("LANGUAGE", "de")
    st.title(translate(language, "checks.doctype_check_title"))
    st.write(translate(language, "checks.doctype_check_description", threshold=threshold))
    if st.button(translate(language, "checks.check_refresh"), key="doctype_refresh"):
        st.cache_data.clear()

    few_docs = check_document_types_count(docs, doc_types, base_url, threshold=threshold)
    if few_docs:
        df_few = pd.DataFrame(few_docs)
        df_few = df_few.rename(columns={
            "Dokumenttyp": translate(language, "checks.document_type_label"),
            "Anzahl": translate(language, "analysis.count"),
        })
        st.dataframe(
            df_few.sort_values(translate(language, "analysis.count"), ascending=True),
            hide_index=True,
            use_container_width=True,
            column_config={
                translate(language, "checks.document_type_label"): st.column_config.LinkColumn(translate(language, "checks.document_type_label"), display_text=r"#(.*)$", width=None)
            }
        )
    else:
        st.success(translate(language, "checks.doctype_no_results", threshold=threshold))

def render_date_check(
    docs,
    doc_types,
    base_url,
    future_years=0,
    min_year_offset=5,
    isolation_gap_years=5,
):
    language = st.session_state.get("LANGUAGE", "de")
    st.title(translate(language, "checks.date_check_title"))
    st.write(
        translate(
            language,
            "checks.date_check_description",
            future_years=future_years,
            min_year_offset=min_year_offset,
            isolation_gap_years=isolation_gap_years,
        )
    )
    if st.button(translate(language, "checks.check_refresh"), key="date_refresh"):
        st.cache_data.clear()

    date_anomalies = check_date_anomalies(
        docs,
        doc_types,
        base_url,
        future_years=future_years,
        min_year_offset=min_year_offset,
        isolation_gap_years=isolation_gap_years,
    )

    if date_anomalies:
        df_dates = pd.DataFrame(date_anomalies)
        df_dates = df_dates.rename(columns={
            "ID": translate(language, "checks.id"),
            "Titel": translate(language, "checks.title"),
            "Typ": translate(language, "checks.type"),
            "Jahr": translate(language, "checks.year"),
            "Grund": translate(language, "checks.reason"),
        })
        st.dataframe(
            df_dates, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                translate(language, "checks.id"): st.column_config.LinkColumn(translate(language, "checks.id"), display_text=r".*/documents/(\d+)/details", width=None),
                translate(language, "checks.type"): st.column_config.LinkColumn(translate(language, "checks.type"), display_text=r"#(.*)$", width=None),
                translate(language, "checks.year"): st.column_config.NumberColumn(format="%d", width=None)
            }
        )
    else: 
        st.success(translate(language, "checks.date_no_anomalies"))


def _build_paperless_filter_link(base_url, filter_field, group_id, display):
    if group_id is None:
        return f"{base_url}/documents/?{filter_field}__isnull=true#{display}"
    return f"{base_url}/documents/?{filter_field}__id={group_id}#{display}"


def _render_custom_field_group_check(
    docs,
    group_names,
    base_url,
    warning_threshold,
    title,
    group_label,
    filter_field,
    check_function,
):
    language = st.session_state.get("LANGUAGE", "de")
    st.title(title)
    st.write(translate(language, "checks.custom_fields_intro", group_label=group_label))
    st.write(translate(language, "checks.custom_fields_warning_intro", group_label=group_label, warning_threshold=warning_threshold))

    custom_fields = fetch_custom_fields()
    if not custom_fields:
        st.warning(translate(language, "checks.no_custom_fields"))
        return

    st.subheader(translate(language, "checks.custom_fields_select_title"))
    selected_fields = []
    cols = st.columns(2)
    for idx, cf in enumerate(custom_fields):
        col = cols[idx % 2]
        with col:
            label = cf['name']
            if cf.get('slug'):
                label += f" ({cf['slug']})"
            if st.checkbox(
                f"{label} — {cf['data_type']}",
                key=f"cf_{cf['id']}_{filter_field}",
            ):
                selected_fields.append({'path': cf['path'], 'name': cf['name']})

    if st.button(translate(language, "checks.custom_fields_submit"), key=f"custom_fields_refresh_{filter_field}"):
        st.cache_data.clear()

    if not selected_fields:
        st.info(translate(language, "checks.choose_custom_fields"))
        return

    anomalies, summary = check_function(docs, group_names, selected_fields, base_url)

    for row in summary:
        group_id = row.pop('GroupID')
        group_name = row.pop('Group')
        row[group_label] = _build_paperless_filter_link(base_url, filter_field, group_id, group_name)
        row[translate(language, "checks.custom_field_label")] = _build_paperless_filter_link(base_url, filter_field, group_id, row['Custom Field'])
        row.pop('Custom Field', None)

    for row in anomalies:
        group_id = row.pop('GroupID')
        group_name = row.pop('Group')
        row[group_label] = _build_paperless_filter_link(base_url, filter_field, group_id, group_name)
        row[translate(language, "checks.custom_field_label")] = _build_paperless_filter_link(base_url, filter_field, group_id, row['Custom Field'])
        row.pop('Custom Field', None)

    st.subheader(translate(language, "checks.custom_fields_warning", warning_threshold=warning_threshold))
    st.write(translate(language, "checks.custom_fields_warning_intro", group_label=group_label, warning_threshold=warning_threshold))

    potential_issues = [
        s for s in summary
        if s.get('Gesamt', 0) > 0
        and (s.get('Gefüllt', 0) / s.get('Gesamt', 1) * 100) >= warning_threshold
        and s.get('Gefüllt', 0) < s.get('Gesamt', 0)
    ]

    if potential_issues:
        df_issues = pd.DataFrame(potential_issues).copy()
        df_issues = df_issues.rename(columns={
            'Gesamt': translate(language, "checks.total"),
            'Gefüllt': translate(language, "checks.filled"),
            'Fehlend': translate(language, "checks.missing"),
        })
        df_issues[translate(language, "checks.fill_percent")] = (
            df_issues.get(translate(language, "checks.filled"))
            / df_issues.get(translate(language, "checks.total")) * 100
        ).round(1).astype(str) + '%'
        st.dataframe(
            df_issues.sort_values(translate(language, "checks.fill_percent"), ascending=False)[
                [group_label, translate(language, "checks.custom_field_label"), translate(language, "checks.total"), translate(language, "checks.filled"), translate(language, "checks.missing"), translate(language, "checks.fill_percent")]
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                group_label: st.column_config.LinkColumn(group_label, display_text=r"#(.*)$", width=None),
                translate(language, "checks.custom_field_label"): st.column_config.LinkColumn(translate(language, "checks.custom_field_label"), display_text=r"#(.*)$", width=None),
                translate(language, "checks.total"): st.column_config.NumberColumn(width=None),
                translate(language, "checks.filled"): st.column_config.NumberColumn(width=None),
                translate(language, "checks.missing"): st.column_config.NumberColumn(width=None),
                translate(language, "checks.fill_percent"): st.column_config.TextColumn(width=None),
            }
        )
    else:
        st.success(translate(language, "checks.custom_fields_no_anomalies", warning_threshold=warning_threshold))

    if summary:
        st.subheader(translate(language, "checks.custom_fields_summary_title", group_label=group_label))
        df_summary = pd.DataFrame(summary)
        df_summary = df_summary.rename(columns={
            'Gesamt': translate(language, "checks.total"),
            'Gefüllt': translate(language, "checks.filled"),
            'Fehlend': translate(language, "checks.missing"),
            'Status': translate(language, "checks.summary_status"),
        })
        st.dataframe(
            df_summary.sort_values([translate(language, "checks.missing"), translate(language, "checks.total")], ascending=[False, False]),
            use_container_width=True,
            hide_index=True,
            column_config={
                group_label: st.column_config.LinkColumn(group_label, display_text=r"#(.*)$", width=None),
                translate(language, "checks.custom_field_label"): st.column_config.LinkColumn(translate(language, "checks.custom_field_label"), display_text=r"#(.*)$", width=None),
                translate(language, "checks.total"): st.column_config.NumberColumn(width=None),
                translate(language, "checks.filled"): st.column_config.NumberColumn(width=None),
                translate(language, "checks.missing"): st.column_config.NumberColumn(width=None),
                translate(language, "checks.summary_status"): st.column_config.TextColumn(width=None),
            }
        )

    if anomalies:
        st.subheader(translate(language, "checks.custom_fields_missing_docs_title"))
        df_anomalies = pd.DataFrame(anomalies)
        df_anomalies = df_anomalies.rename(columns={
            'ID': translate(language, "checks.id"),
            'Titel': translate(language, "checks.title"),
            'Wert': translate(language, "checks.value"),
        })
        st.dataframe(
            df_anomalies,
            use_container_width=True,
            hide_index=True,
            column_config={
                translate(language, "checks.id"): st.column_config.LinkColumn(translate(language, "checks.id"), display_text=r".*/documents/(\d+)/details", width=None),
                group_label: st.column_config.LinkColumn(group_label, display_text=r"#(.*)$", width=None),
                translate(language, "checks.custom_field_label"): st.column_config.LinkColumn(translate(language, "checks.custom_field_label"), display_text=r"#(.*)$", width=None),
                translate(language, "checks.value"): st.column_config.TextColumn(width=None),
            }
        )
    elif not summary:
        st.success(translate(language, "checks.custom_fields_filled"))


def render_custom_field_check(docs, doc_types, base_url, warning_threshold=75):
    language = st.session_state.get("LANGUAGE", "de")
    _render_custom_field_group_check(
        docs,
        doc_types,
        base_url,
        warning_threshold,
        translate(language, "checks.custom_fields_title"),
        translate(language, "checks.document_type_label"),
        "document_type",
        check_custom_field_missing,
    )


def render_custom_field_correspondent_check(docs, corresp, base_url, warning_threshold=75):
    language = st.session_state.get("LANGUAGE", "de")
    _render_custom_field_group_check(
        docs,
        corresp,
        base_url,
        warning_threshold,
        translate(language, "checks.custom_fields_correspondent_title"),
        translate(language, "checks.correspondent_label"),
        "correspondent",
        check_custom_field_missing_by_correspondent,
    )


def render_id_duplicate_check(docs, base_url):
    language = st.session_state.get("LANGUAGE", "de")
    st.title(translate(language, "checks.id_duplicate_title"))
    st.write(translate(language, "checks.id_duplicate_description"))
    if st.button(translate(language, "checks.check_refresh"), key="id_duplicate_refresh"):
        st.cache_data.clear()

    duplicates = check_id_duplicates(docs, base_url)

    if duplicates:
        df_duplicates = pd.DataFrame(duplicates)
        st.warning(translate(language, "checks.id_duplicate_warning", count=len(df_duplicates)))
        df_duplicates = df_duplicates.rename(columns={
            "ID": translate(language, "checks.id"),
            "Titel": translate(language, "checks.title"),
            "Dokumenttyp": translate(language, "checks.document_type_label"),
            "Erstellt": translate(language, "checks.created"),
            "Duplikate": translate(language, "checks.duplicates"),
        })
        st.dataframe(
            df_duplicates.sort_values(translate(language, "checks.duplicates"), ascending=False),
            use_container_width=True,
            hide_index=True,
            column_config={
                translate(language, "checks.id"): st.column_config.LinkColumn(translate(language, "checks.id"), display_text=r".*/documents/(\d+)/details", width=None),
                translate(language, "checks.title"): st.column_config.TextColumn(width=None),
                translate(language, "checks.document_type_label"): st.column_config.TextColumn(width=None),
                translate(language, "checks.created"): st.column_config.TextColumn(width=None),
                translate(language, "checks.duplicates"): st.column_config.NumberColumn(width=None),
            }
        )
    else:
        st.success(translate(language, "checks.id_duplicate_no_duplicates"))
