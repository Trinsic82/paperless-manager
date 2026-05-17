import streamlit as st
import pandas as pd
from collections import Counter
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

def render_doctype_check(docs, doc_types, base_url, threshold=5):
    st.title("📉 Dokumenttypen-Check")
    st.write(f"Zeigt alle Dokumenttypen, die weniger als {threshold} Einträge haben.")
    if st.button("🔄 Check wiederholen", key="doctype_refresh"):
        st.cache_data.clear()
        st.rerun()

    few_docs = check_document_types_count(docs, doc_types, base_url, threshold=threshold)
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
        st.success(f"Keine Dokumenttypen mit weniger als {threshold} Einträgen gefunden!")

def render_date_check(
    docs,
    doc_types,
    base_url,
    future_years=0,
    min_year_offset=5,
    isolation_gap_years=5,
):
    st.title("📅 Datums-Check")
    st.write(
        "Identifiziert Dokumente mit verdächtigen Jahreszahlen "
        f"(Zukunft +{future_years} Jahre, globale Ausreißer unter dem 5. Perzentil minus {min_year_offset} Jahre, "
        f"oder isolierte Lücken größer {isolation_gap_years} Jahre pro Typ)."
    )
    if st.button("🔄 Check wiederholen", key="date_refresh"):
        st.cache_data.clear()
        st.rerun()

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
    st.title(title)
    st.write(f"Prüft, welche {group_label.lower()}bezogenen Custom Fields nicht gefüllt haben und zeigt fehlende Dokumente an.")
    st.write(
        f"{group_label}-CustomField-Kombinationen mit mindestens {warning_threshold}% Befüllung, aber nicht 100%, werden als potenzielle Anomalie markiert."
    )

    custom_fields = fetch_custom_fields()
    if not custom_fields:
        st.warning("Keine Custom Fields in Paperless gefunden.")
        return

    st.subheader("Wähle Custom Fields zum Prüfen:")
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

    if st.button("🔄 Check ausführen", key=f"custom_fields_refresh_{filter_field}"):
        st.cache_data.clear()
        st.rerun()

    if not selected_fields:
        st.info("Wähle mindestens ein Custom Field, um den Check auszuführen.")
        return

    anomalies, summary = check_function(docs, group_names, selected_fields, base_url)

    for row in summary:
        group_id = row.pop('GroupID')
        group_name = row.pop('Group')
        row[group_label] = _build_paperless_filter_link(base_url, filter_field, group_id, group_name)
        row['Custom Field'] = _build_paperless_filter_link(base_url, filter_field, group_id, row['Custom Field'])

    for row in anomalies:
        group_id = row.pop('GroupID')
        group_name = row.pop('Group')
        row[group_label] = _build_paperless_filter_link(base_url, filter_field, group_id, group_name)
        row['Custom Field'] = _build_paperless_filter_link(base_url, filter_field, group_id, row['Custom Field'])

    st.subheader(f"⚠️ Potenzielle Anomalien ({warning_threshold}%–99% befüllt)")
    st.write(
        f"Diese {group_label}-CustomField-Kombinationen sind mindestens {warning_threshold}% befüllt, aber nicht 100%."
    )

    potential_issues = [
        s for s in summary
        if s['Gesamt'] > 0
        and (s['Gefüllt'] / s['Gesamt'] * 100) >= warning_threshold
        and s['Gefüllt'] < s['Gesamt']
    ]

    if potential_issues:
        df_issues = pd.DataFrame(potential_issues).copy()
        df_issues['Befüllung %'] = (df_issues['Gefüllt'] / df_issues['Gesamt'] * 100).round(1).astype(str) + '%'
        st.dataframe(
            df_issues.sort_values("Befüllung %", ascending=False)[[group_label, "Custom Field", "Gesamt", "Gefüllt", "Fehlend", "Befüllung %"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                group_label: st.column_config.LinkColumn(group_label, display_text=r"#(.*)$", width=None),
                "Custom Field": st.column_config.LinkColumn("Custom Field", display_text=r"#(.*)$", width=None),
                "Gesamt": st.column_config.NumberColumn(width=None),
                "Gefüllt": st.column_config.NumberColumn(width=None),
                "Fehlend": st.column_config.NumberColumn(width=None),
                "Befüllung %": st.column_config.TextColumn(width=None),
            }
        )
    else:
        st.success("Keine Anomalien gefunden - alle CustomField-Kombinationen sind entweder <75% oder 100% befüllt.")

    if summary:
        st.subheader(f"Zusammenfassung nach {group_label} - Custom Fields-Check")
        st.dataframe(
            pd.DataFrame(summary).sort_values(["Fehlend", "Gesamt"], ascending=[False, False]),
            use_container_width=True,
            hide_index=True,
            column_config={
                group_label: st.column_config.LinkColumn(group_label, display_text=r"#(.*)$", width=None),
                "Custom Field": st.column_config.LinkColumn("Custom Field", display_text=r"#(.*)$", width=None),
                "Gesamt": st.column_config.NumberColumn(width=None),
                "Gefüllt": st.column_config.NumberColumn(width=None),
                "Fehlend": st.column_config.NumberColumn(width=None),
                "Status": st.column_config.TextColumn(width=None),
            }
        )

    if anomalies:
        st.subheader("Dokumente mit fehlendem Custom Field")
        st.dataframe(
            pd.DataFrame(anomalies),
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID": st.column_config.LinkColumn("ID", display_text=r".*/documents/(\d+)/details", width=None),
                group_label: st.column_config.LinkColumn(group_label, display_text=r"#(.*)$", width=None),
                "Custom Field": st.column_config.LinkColumn("Custom Field", display_text=r"#(.*)$", width=None),
                "Wert": st.column_config.TextColumn(width=None),
            }
        )
    elif not summary:
        st.success("Alle Custom Fields sind für alle Dokumente gefüllt.")


def render_custom_field_check(docs, doc_types, base_url, warning_threshold=75):
    _render_custom_field_group_check(
        docs,
        doc_types,
        base_url,
        warning_threshold,
        "🧩 Custom Fields Check",
        "Dokumenttyp",
        "document_type",
        check_custom_field_missing,
    )


def render_custom_field_correspondent_check(docs, corresp, base_url, warning_threshold=75):
    _render_custom_field_group_check(
        docs,
        corresp,
        base_url,
        warning_threshold,
        "🧩 Custom Fields Check - Korrespondenten",
        "Korrespondent",
        "correspondent",
        check_custom_field_missing_by_correspondent,
    )


def render_id_duplicate_check(docs, base_url):
    st.title("🆔 ID-Duplikat-Check")
    st.write("Sucht nach Dokumenten mit doppelten IDs. Dies ist normalerweise ein Fehler.")
    if st.button("🔄 Check wiederholen", key="id_duplicate_refresh"):
        st.cache_data.clear()
        st.rerun()

    duplicates = check_id_duplicates(docs, base_url)

    if duplicates:
        df_duplicates = pd.DataFrame(duplicates)
        st.warning(f"⚠️ {len(df_duplicates)} Dokumente mit doppelten IDs gefunden!")
        st.dataframe(
            df_duplicates.sort_values("Duplikate", ascending=False),
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID": st.column_config.LinkColumn("ID", display_text=r".*/documents/(\d+)/details", width=None),
                "Dokumenttyp": st.column_config.TextColumn(width=None),
                "Titel": st.column_config.TextColumn(width=None),
                "Erstellt": st.column_config.TextColumn(width=None),
                "Duplikate": st.column_config.NumberColumn(width=None),
            }
        )
    else:
        st.success("Keine Duplikate gefunden! Alle IDs sind eindeutig.")
