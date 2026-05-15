import os
import pandas as pd
import streamlit as st
from collections import Counter

# --- Modul-Importe ---
from api import test_connection, fetch_all, update_document
from checks import check_path_consistency, check_date_anomalies

# --- Seiten-Konfiguration ---
st.set_page_config(page_title="Paperless Metadata Manager", page_icon="📄", layout="wide")

# --- Session State Initialisierung ---
if "PAPERLESS_URL" not in st.session_state:
    st.session_state["PAPERLESS_URL"] = os.environ.get("PAPERLESS_URL", "http://192.168.5.136:8000")
if "PAPERLESS_TOKEN" not in st.session_state:
    st.session_state["PAPERLESS_TOKEN"] = os.environ.get("PAPERLESS_TOKEN", "9f825c85ecf5f0ca2b197986d0115d7c061cc3b4")
if "IS_CONNECTED" not in st.session_state:
    st.session_state["IS_CONNECTED"] = False

# --- SEITENLEISTE ---
st.sidebar.title("📄 Navigation")
page = st.sidebar.radio(
    "Wähle einen Bereich:", 
    ["🏠 Startseite", "⚙️ Konfiguration", "📊 Analyse Metadaten", "⚖️ Speicherpfad-Dokumenttyp-Check", "📉 Dokumenttypen-Check", "📅 Datums-Check", "✏️ Massenbearbeitung"]
)

st.sidebar.divider()

if st.sidebar.button("🔄 Daten neu laden", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()
status_placeholder = st.sidebar.empty()

# --- DATEN LADEN ---
if page not in ["🏠 Startseite", "⚙️ Konfiguration"]:
    if not st.session_state["IS_CONNECTED"]:
        st.warning("Bitte stelle zuerst unter Konfiguration eine Verbindung her.")
        st.stop()
    
    with st.spinner("Lade Daten..."):
        docs = fetch_all('documents')
        doc_types = {dt['id']: dt['name'] for dt in fetch_all('document_types')}
        corresp = {c['id']: c['name'] for c in fetch_all('correspondents')}
        st_paths = {sp['id']: sp['name'] for sp in fetch_all('storage_paths')}
        tags = {t['id']: t['name'] for t in fetch_all('tags')}
    
    if not docs:
        st.error("Konnte keine Dokumente laden.")
        st.stop()

# --- PAGES ---
if page == "🏠 Startseite":
    st.title("Paperless-ngx Metadata Manager")
    st.write("Verwalte und bereinige deine Metadaten effizient.")
    col1, col2, col3 = st.columns(3)
    with col1: st.info("Nutze den **Speicherpfad-Dokumenttyp-Check**, um falsche Speicherpfade zu finden.")
    with col2: st.info("Prüfe mit dem **Datums-Check** auf fehlerhafte OCR-Erkennungen.")
    with col3: st.info("Nutze die **Massenbearbeitung**, um Dokumente schnell zu korrigieren.")

elif page == "⚙️ Konfiguration":
    st.title("Konfiguration")
    new_url = st.text_input("URL", value=st.session_state["PAPERLESS_URL"])
    new_token = st.text_input("Token", value=st.session_state["PAPERLESS_TOKEN"], type="password")
    if st.button("Verbindung testen & speichern", type="primary"):
        st.session_state["PAPERLESS_URL"], st.session_state["PAPERLESS_TOKEN"] = new_url, new_token
        success, msg = test_connection()
        if success: st.success(msg); st.cache_data.clear()
        else: st.error(msg)

elif page == "📊 Analyse Metadaten":
    st.title("📊 Metadaten Analyse")
    if st.button("🔄 Analyse aktualisieren"):
        st.cache_data.clear(); st.rerun()

    type_counts = Counter([d.get('document_type') for d in docs])
    corr_counts = Counter([d.get('correspondent') for d in docs])
    path_counts = Counter([d.get('storage_path') for d in docs])
    tag_counts = Counter([t for d in docs for t in d.get('tags', [])])

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.subheader("Dokumenttypen")
        st.dataframe(pd.DataFrame([{"Typ": doc_types.get(k, "Ohne"), "Anzahl": v} for k, v in type_counts.items()]).sort_values("Anzahl", ascending=False), hide_index=True, use_container_width=True)
    with c2:
        st.subheader("Korrespondenten")
        st.dataframe(pd.DataFrame([{"Name": corresp.get(k, "Ohne"), "Anzahl": v} for k, v in corr_counts.items()]).sort_values("Anzahl", ascending=False), hide_index=True, use_container_width=True)
    with c3:
        st.subheader("Speicherpfade")
        st.dataframe(pd.DataFrame([{"Pfad Name": st_paths.get(k, "Standard"), "Anzahl": v} for k, v in path_counts.items()]).sort_values("Anzahl", ascending=False), hide_index=True, use_container_width=True)
    with c4:
        st.subheader("Tags")
        st.dataframe(pd.DataFrame([{"Tag": tags.get(k, "Unbekannt"), "Anzahl": v} for k, v in tag_counts.items()]).sort_values("Anzahl", ascending=False), hide_index=True, use_container_width=True)

elif page == "⚖️ Speicherpfad-Dokumenttyp-Check":
    st.title("⚖️ Speicherpfad-Dokumenttyp-Check")
    if st.button("🔄 Check wiederholen"):
        st.cache_data.clear(); st.rerun()

    base_url = st.session_state['PAPERLESS_URL'].strip().rstrip('/')
    anomalies = check_path_consistency(docs, doc_types, st_paths, base_url)
    
    if anomalies:
        st.dataframe(pd.DataFrame(anomalies), use_container_width=True, hide_index=True, column_config={"ID": st.column_config.LinkColumn("ID", display_text=r".*/documents/(\d+)/details")})
    else: st.success("Alle Pfade sind konsistent!")

elif page == "📉 Dokumenttypen-Check":
    st.title("📉 Dokumenttypen-Check")
    st.write("Zeigt alle Dokumenttypen, die weniger als 5 Einträge haben.")
    if st.button("🔄 Check wiederholen", key="doctype_refresh"):
        st.cache_data.clear(); st.rerun()

    type_counts = Counter([d.get('document_type') for d in docs])
    few_docs = []
    for dt_id, count in type_counts.items():
        if count < 5:
            dt_name = doc_types.get(dt_id, "Ohne Typ")
            few_docs.append({"Dokumenttyp": dt_name, "Anzahl": count})
    
    if few_docs:
        st.dataframe(pd.DataFrame(few_docs).sort_values("Anzahl", ascending=True), hide_index=True, use_container_width=True)
    else:
        st.success("Keine Dokumenttypen mit weniger als 5 Einträgen gefunden!")

elif page == "📅 Datums-Check":
    st.title("📅 Datums-Check")
    st.write("Identifiziert Dokumente mit verdächtigen Jahreszahlen (Zukunft, globale Ausreißer oder > 5 Jahre Lücke im Typ).")
    if st.button("🔄 Check wiederholen", key="date_refresh"):
        st.cache_data.clear(); st.rerun()

    base_url = st.session_state['PAPERLESS_URL'].strip().rstrip('/')
    date_anomalies = check_date_anomalies(docs, doc_types, base_url)

    if date_anomalies:
        df_dates = pd.DataFrame(date_anomalies)
        st.dataframe(
            df_dates, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "ID": st.column_config.LinkColumn("ID", display_text=r".*/documents/(\d+)/details"),
                "Typ": st.column_config.LinkColumn("Typ", display_text=r"#(.*)$"),
                "Jahr": st.column_config.NumberColumn(format="%d")
            }
        )
    else: 
        st.success("Keine Datums-Anomalien gefunden!")

elif page == "✏️ Massenbearbeitung":
    st.title("✏️ Massenbearbeitung")
    if st.button("🔄 Liste aktualisieren"):
        st.cache_data.clear(); st.rerun()

    col1, col2 = st.columns(2)
    f_type = col1.selectbox("Typ Filter", ["Alle"] + list(doc_types.values()))
    f_corr = col2.selectbox("Korrespondent Filter", ["Alle", "Ohne"] + list(corresp.values()))
    
    base_url = st.session_state['PAPERLESS_URL'].strip().rstrip('/')
    filtered = []
    for d in docs:
        dt, co = doc_types.get(d.get('document_type'), ""), corresp.get(d.get('correspondent'), "")
        if f_type != "Alle" and dt != f_type: continue
        if f_corr == "Ohne" and co != "": continue
        if f_corr != "Alle" and f_corr != "Ohne" and co != f_corr: continue
        filtered.append({
            "Wählen": False, 
            "ID": f"{base_url}/documents/{d['id']}/details", 
            "Titel": d['title'], 
            "Typ": dt, "Korrespondent": co, "Pfad": st_paths.get(d.get('storage_path'), "Standard")
        })
    
    if filtered:
        edited = st.data_editor(
            pd.DataFrame(filtered), hide_index=True, use_container_width=True,
            column_config={
                "Wählen": st.column_config.CheckboxColumn(required=True),
                "ID": st.column_config.LinkColumn("ID", display_text=r".*/documents/(\d+)/details")
            },
            disabled=["ID", "Titel", "Typ", "Korrespondent", "Pfad"]
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
                st.success(f"{len(selected_ids)} erfolgreich aktualisiert!"); st.cache_data.clear(); st.rerun()

# Status Update
if st.session_state["IS_CONNECTED"]: status_placeholder.success("🟢 API: Verbunden")
else: status_placeholder.error("🔴 API: Nicht verbunden")
