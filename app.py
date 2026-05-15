import os
import requests
import pandas as pd
import streamlit as st
from collections import defaultdict, Counter
from datetime import datetime

# --- Seiten-Konfiguration ---
st.set_page_config(page_title="Paperless Metadata Manager", page_icon="📄", layout="wide")

# --- Session State Initialisierung ---
if "PAPERLESS_URL" not in st.session_state:
    st.session_state["PAPERLESS_URL"] = os.environ.get("PAPERLESS_URL", "http://192.168.5.136:8000")
if "PAPERLESS_TOKEN" not in st.session_state:
    st.session_state["PAPERLESS_TOKEN"] = os.environ.get("PAPERLESS_TOKEN", "9f825c85ecf5f0ca2b197986d0115d7c061cc3b4")
if "IS_CONNECTED" not in st.session_state:
    st.session_state["IS_CONNECTED"] = False

def get_headers():
    return {
        "Authorization": f"Token {st.session_state['PAPERLESS_TOKEN']}",
        "Accept": "application/json; version=2, application/json, */*;q=0.8"
    }

# --- Hilfsfunktionen für API ---
def test_connection():
    if not st.session_state["PAPERLESS_TOKEN"]:
        return False, "Kein API-Token hinterlegt."
    try:
        base_url = st.session_state['PAPERLESS_URL'].strip().rstrip('/')
        url = f"{base_url}/api/"
        resp = requests.get(url, headers=get_headers(), timeout=5)
        if resp.status_code == 200:
            st.session_state["IS_CONNECTED"] = True
            return True, "Verbindung erfolgreich hergestellt!"
        else:
            st.session_state["IS_CONNECTED"] = False
            return False, f"Fehler: API antwortete mit Status {resp.status_code}"
    except Exception as e:
        st.session_state["IS_CONNECTED"] = False
        return False, f"Verbindungsfehler: {str(e)}"

@st.cache_data(ttl=60, show_spinner=False)
def fetch_all(endpoint):
    if not st.session_state["IS_CONNECTED"]: return []
    results = []
    base_url = st.session_state['PAPERLESS_URL'].strip().rstrip('/')
    next_url = f"{base_url}/api/{endpoint}/"
    while next_url:
        try:
            resp = requests.get(next_url, headers=get_headers(), timeout=10)
            resp.raise_for_status()
            data = resp.json()
            results.extend(data.get('results', []))
            next_url = data.get('next')
        except Exception: break
    return results

def update_document(doc_id, payload):
    base_url = st.session_state['PAPERLESS_URL'].strip().rstrip('/')
    update_url = f"{base_url}/api/documents/{doc_id}/"
    resp = requests.patch(update_url, headers=get_headers(), json=payload)
    return resp.status_code == 200

# --- SEITENLEISTE ---
st.sidebar.title("📄 Navigation")
page = st.sidebar.radio(
    "Wähle einen Bereich:", 
    ["🏠 Startseite", "⚙️ Konfiguration", "📊 Analyse Metadaten", "⚖️ Konsistenz-Check", "📅 Datums-Check", "✏️ Massenbearbeitung"]
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
    with col1: st.info("Nutze den **Konsistenz-Check**, um falsche Speicherpfade zu finden.")
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

elif page == "⚖️ Konsistenz-Check":
    st.title("⚖️ Konsistenz-Check")
    if st.button("🔄 Check wiederholen"):
        st.cache_data.clear(); st.rerun()

    base_url = st.session_state['PAPERLESS_URL'].strip().rstrip('/')
    type_map = defaultdict(list)
    for d in docs:
        type_map[doc_types.get(d.get('document_type'), "Ohne Typ")].append(d)
    
    anomalies = []
    for dt_name, d_list in type_map.items():
        if dt_name == "Ohne Typ": continue
        paths = [st_paths.get(d.get('storage_path'), "Standard") for d in d_list]
        if not paths: continue
        main_path = Counter(paths).most_common(1)[0][0]
        for d in d_list:
            current_p = st_paths.get(d.get('storage_path'), "Standard")
            if current_p != main_path:
                anomalies.append({
                    "ID": f"{base_url}/documents/{d['id']}/details", 
                    "Titel": d['title'], "Dokumenttyp": dt_name,
                    "Aktueller Pfad": current_p, "Erwarteter Pfad": main_path
                })
    
    if anomalies:
        st.dataframe(pd.DataFrame(anomalies), use_container_width=True, hide_index=True, column_config={"ID": st.column_config.LinkColumn("ID", display_text=r".*/documents/(\d+)/details")})
    else: st.success("Alle Pfade sind konsistent!")

elif page == "📅 Datums-Check":
    st.title("📅 Datums-Check")
    st.write("Identifiziert Dokumente mit verdächtigen Jahreszahlen (Zukunft, globale Ausreißer oder > 5 Jahre Lücke im Typ).")
    if st.button("🔄 Check wiederholen", key="date_refresh"):
        st.cache_data.clear(); st.rerun()

    current_year = datetime.now().year
    base_url = st.session_state['PAPERLESS_URL'].strip().rstrip('/')
    
    # Globalen Ausreißer-Schwellenwert berechnen
    valid_years = sorted([int(d.get('created')[:4]) for d in docs if d.get('created') and d.get('created')[:4].isdigit()])
    if valid_years:
        p05_year = valid_years[int(len(valid_years) * 0.05)]
        global_min_threshold = p05_year - 5
    else:
        global_min_threshold = 1900

    group_map = defaultdict(list)
    for d in docs:
        dt_name = doc_types.get(d.get('document_type'), "Ohne Typ")
        group_map[dt_name].append(d)

    date_anomalies = []
    
    for dt_name, d_list in group_map.items():
        # Einzigartige Jahre dieser Gruppe ermitteln
        group_years = sorted(list({int(d.get('created')[:4]) for d in d_list if d.get('created') and d.get('created')[:4].isdigit()}))
        
        for d in d_list:
            created_str = d.get('created', '')
            if not created_str or not created_str[:4].isdigit():
                continue
                
            doc_year = int(created_str[:4])
            reason = ""
            is_anomaly = False
            
            if doc_year > current_year:
                is_anomaly = True
                reason = f"Zukunft ({doc_year})"
            elif doc_year < global_min_threshold:
                is_anomaly = True
                reason = f"Sehr alt ({doc_year})"
            elif len(group_years) > 1:
                min_dist = min([abs(doc_year - y) for y in group_years if y != doc_year])
                if min_dist > 5:
                    is_anomaly = True
                    reason = f"Isoliert (> 5 J. Lücke)"

            if is_anomaly:
                dt_id = d.get('document_type')
                # Erstelle Filter-Link für Paperless-ngx
                type_filter_url = f"{base_url}/documents/?document_type__id={dt_id}#{dt_name}"
                
                date_anomalies.append({
                    "ID": f"{base_url}/documents/{d['id']}/details",
                    "Titel": d['title'],
                    "Typ": type_filter_url,
                    "Jahr": doc_year,
                    "Grund": reason
                })

    if date_anomalies:
        df_dates = pd.DataFrame(date_anomalies)
        st.dataframe(
            df_dates, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "ID": st.column_config.LinkColumn("ID", display_text=r".*/documents/(\d+)/details"),
                # Nutzt den URL-Fragment-Trick, um den Namen anzuzeigen, aber auf den Filter zu verlinken
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
