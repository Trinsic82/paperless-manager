import streamlit as st
import pandas as pd
from collections import Counter
from checks import (
    check_document_types_count,
    check_path_consistency,
    check_date_anomalies,
    check_custom_field_missing,
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


def render_custom_field_check(docs, doc_types, base_url, warning_threshold=75):
    st.title("🧩 Custom Fields Check")
    st.write("Prüft, welche Dokumenttypen Custom Fields nicht gefüllt haben und zeigt fehlende Dokumente an.")
    st.write(f"Dokumenttyp-Kombinationen mit mindestens {warning_threshold}% Befüllung, aber nicht 100%, werden als potenzielle Anomalie markiert.")

    # Lade verfügbare Custom Fields
    custom_fields = fetch_custom_fields()
    
    if not custom_fields:
        st.warning("Keine Custom Fields in Paperless gefunden.")
        return
    
    # Zeige Custom Fields als Checkboxen
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
                key=f"cf_{cf['id']}"
            ):
                selected_fields.append({'path': cf['path'], 'name': cf['name']})
    
    if st.button("🔄 Check ausführen", key="custom_fields_refresh"):
        st.cache_data.clear()
        st.rerun()

    if not selected_fields:
        st.info("Wähle mindestens ein Custom Field, um den Check auszuführen.")
        return

    anomalies, summary = check_custom_field_missing(docs, doc_types, selected_fields, base_url)

    # Neue Sektion: Dokumenttypen mit hohem, aber nicht vollständigem Befüllungsgrad
    st.subheader(f"⚠️ Potenzielle Anomalien ({warning_threshold}%–99% befüllt)")
    st.write(
        f"Diese Dokumenttyp-CustomField-Kombinationen sind mindestens {warning_threshold}% befüllt, aber nicht 100%."
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
            df_issues.sort_values("Befüllung %", ascending=False)[["Dokumenttyp", "Custom Field", "Gesamt", "Gefüllt", "Fehlend", "Befüllung %"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Dokumenttyp": st.column_config.TextColumn(width=None),
                "Custom Field": st.column_config.TextColumn(width=None),
                "Gesamt": st.column_config.NumberColumn(width=None),
                "Gefüllt": st.column_config.NumberColumn(width=None),
                "Fehlend": st.column_config.NumberColumn(width=None),
                "Befüllung %": st.column_config.TextColumn(width=None),
            }
        )
    else:
        st.success("Keine Anomalien gefunden - alle CustomField-Kombinationen sind entweder <75% oder 100% befüllt.")

    if summary:
        st.subheader("Zusammenfassung nach Dokumenttyp - Custom Fields-Check")
        st.dataframe(
            pd.DataFrame(summary).sort_values(["Fehlend", "Gesamt"], ascending=[False, False]),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Dokumenttyp": st.column_config.TextColumn(width=None),
                "Custom Field": st.column_config.TextColumn(width=None),
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
                "Dokumenttyp": st.column_config.TextColumn(width=None),
                "Custom Field": st.column_config.TextColumn(width=None),
                "Wert": st.column_config.TextColumn(width=None),
            }
        )
    elif not summary:
        st.success("Alle Custom Fields sind für alle Dokumenttypen gefüllt.")


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
