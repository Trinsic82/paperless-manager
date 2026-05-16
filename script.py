import os

app_py = """import streamlit as st
import requests
import pandas as pd
from collections import defaultdict

st.set_page_config(page_title="Paperless Metadata Manager", layout="wide")

# --- Konfiguration ---
st.sidebar.header("API Konfiguration")
URL = st.sidebar.text_input("Paperless URL", value=os.environ.get("PAPERLESS_URL", "http://192.168.x.x:8000"))
TOKEN = st.sidebar.text_input("API Token", value=os.environ.get("PAPERLESS_TOKEN", ""), type="password")

headers = {
    "Authorization": f"Token {TOKEN}",
    "Accept": "application/json"
}

@st.cache_data(ttl=60, show_spinner=False)
def fetch_all(endpoint):
    if not TOKEN: return []
    results = []
    next_url = f"{URL.rstrip('/')}/api/{endpoint}/"
    while next_url:
        try:
            resp = requests.get(next_url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            results.extend(data.get('results', []))
            next_url = data.get('next')
        except Exception as e:
            st.error(f"Fehler bei API {endpoint}: {e}")
            break
    return results

def update_document(doc_id, payload):
    update_url = f"{URL.rstrip('/')}/api/documents/{doc_id}/"
    resp = requests.patch(update_url, headers=headers, json=payload)
    return resp.status_code == 200

if not TOKEN:
    st.info("Bitte gib in der Seitenleiste deine Paperless URL und den API Token ein.")
    st.stop()

# --- Daten laden ---
with st.spinner("Lade Metadaten von Paperless-ngx..."):
    docs = fetch_all('documents')
    doc_types = {dt['id']: dt['name'] for dt in fetch_all('document_types')}
    corresp = {c['id']: c['name'] for c in fetch_all('correspondents')}
    st_paths = {sp['id']: sp['path'] for sp in fetch_all('storage_paths')}
    tags = {t['id']: t['name'] for t in fetch_all('tags')}

if not docs:
    st.warning("Keine Dokumente gefunden oder Verbindungsfehler.")
    st.stop()

# --- Tabs ---
tab1, tab2 = st.tabs(["🔍 Anomalien finden", "✏️ Massenbearbeitung (Bulk Edit)"])

with tab1:
    st.header("Metadaten-Anomalien")
    st.write("Findet Dokumente, die vom üblichen Speicherpfad ihres Dokumenttyps abweichen.")
    
    type_to_paths = defaultdict(list)
    for doc in docs:
        dt_id = doc.get('document_type')
        dt_name = doc_types.get(dt_id, "Ohne Typ")
        sp_id = doc.get('storage_path')
        sp_name = st_paths.get(sp_id, "Kein Pfad")
        type_to_paths[dt_name].append({
            'ID': doc['id'], 'Titel': doc['title'], 'Speicherpfad': sp_name, 'Korrespondent': corresp.get(doc.get('correspondent'), "")
        })
        
    anomalies = []
    for dt_name, items in type_to_paths.items():
        if dt_name == "Ohne Typ": continue
        
        path_counts = defaultdict(int)
        for item in items: path_counts[item['Speicherpfad']] += 1
        if not path_counts: continue
            
        main_path = max(path_counts, key=path_counts.get)
        outliers = [item for item in items if item['Speicherpfad'] != main_path]
        
        for out in outliers:
            anomalies.append({
                "ID": out['ID'], "Titel": out['Titel'], "Dokumenttyp": dt_name,
                "Falscher Pfad": out['Speicherpfad'], "Sollte sein": main_path, "Korrespondent": out['Korrespondent']
            })
            
    if anomalies:
        df_anomalies = pd.DataFrame(anomalies)
        st.dataframe(df_anomalies, use_container_width=True)
    else:
        st.success("Keine Abweichungen gefunden! Alles konsistent.")

with tab2:
    st.header("Massenbearbeitung")
    
    # Filter
    col1, col2 = st.columns(2)
    filter_type = col1.selectbox("Nach Dokumenttyp filtern", ["Alle"] + list(doc_types.values()))
    filter_corr = col2.selectbox("Nach Korrespondent filtern", ["Alle", "Ohne Korrespondent"] + list(corresp.values()))
    
    # Daten filtern
    filtered_docs = []
    for d in docs:
        d_type = doc_types.get(d.get('document_type'), "")
        d_corr = corresp.get(d.get('correspondent'), "")
        
        if filter_type != "Alle" and d_type != filter_type: continue
        if filter_corr == "Ohne Korrespondent" and d_corr != "": continue
        if filter_corr != "Alle" and filter_corr != "Ohne Korrespondent" and d_corr != filter_corr: continue
            
        filtered_docs.append({
            "Auswählen": False,
            "ID": d['id'],
            "Titel": d['title'],
            "Korrespondent": d_corr,
            "Dokumenttyp": d_type,
            "Speicherpfad": st_paths.get(d.get('storage_path'), "")
        })
        
    if filtered_docs:
        df = pd.DataFrame(filtered_docs)
        edited_df = st.data_editor(
            df,
            hide_index=True,
            use_container_width=True,
            column_config={"Auswählen": st.column_config.CheckboxColumn(required=True)},
            disabled=["ID", "Titel", "Korrespondent", "Dokumenttyp", "Speicherpfad"]
        )
        
        selected_ids = edited_df[edited_df["Auswählen"]]["ID"].tolist()
        
        if selected_ids:
            st.subheader(f"{len(selected_ids)} Dokument(e) ausgewählt. Neue Werte setzen:")
            c1, c2, c3 = st.columns(3)
            
            # Reverse lookups for IDs
            rev_doc_types = {v: k for k, v in doc_types.items()}
            rev_corresp = {v: k for k, v in corresp.items()}
            rev_st_paths = {v: k for k, v in st_paths.items()}
            
            new_type = c1.selectbox("Neuer Dokumenttyp", ["Unverändert"] + list(doc_types.values()))
            new_corr = c2.selectbox("Neuer Korrespondent", ["Unverändert"] + list(corresp.values()))
            new_path = c3.selectbox("Neuer Speicherpfad", ["Unverändert"] + list(st_paths.values()))
            
            if st.button("Änderungen anwenden"):
                payload = {}
                if new_type != "Unverändert": payload['document_type'] = rev_doc_types[new_type]
                if new_corr != "Unverändert": payload['correspondent'] = rev_corresp[new_corr]
                if new_path != "Unverändert": payload['storage_path'] = rev_st_paths[new_path]
                
                if not payload:
                    st.warning("Keine Änderungen ausgewählt.")
                else:
                    success_count = 0
                    progress_text = "Aktualisiere Dokumente..."
                    my_bar = st.progress(0, text=progress_text)
                    
                    for i, doc_id in enumerate(selected_ids):
                        if update_document(doc_id, payload):
                            success_count += 1
                        my_bar.progress((i + 1) / len(selected_ids), text=progress_text)
                        
                    st.success(f"{success_count}/{len(selected_ids)} Dokumente erfolgreich aktualisiert!")
                    st.cache_data.clear() # Cache leeren
                    st.rerun()
"""

req_txt = """streamlit>=1.30.0
requests>=2.31.0
pandas>=2.1.0
"""

dockerfile_txt = """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
"""

readme_txt = """# Paperless-ngx Metadata Manager
Eine leichtgewichtige Streamlit Web-App zum Aufspüren von Metadaten-Anomalien und für die Massenbearbeitung (Bulk-Edit) in Paperless-ngx.

## Features
- **Anomalien finden**: Erkennt Dokumente, die einen vom Standard abweichenden Speicherpfad haben.
- **Bulk Edit**: Wähle mehrere Dokumente aus und ändere Korrespondent, Dokumenttyp und Speicherpfad auf einmal.

## Start mit Docker
```bash
docker build -t paperless-metadata-manager .
docker run -p 8501:8501 -e PAPERLESS_URL="http://deine-ip:8000" -e PAPERLESS_TOKEN="dein_token" paperless-metadata-manager
```
"""

os.makedirs("github_repo", exist_ok=True)
with open("github_repo/app.py", "w") as f: f.write(app_py)
with open("github_repo/requirements.txt", "w") as f: f.write(req_txt)
with open("github_repo/Dockerfile", "w") as f: f.write(dockerfile_txt)
with open("github_repo/README.md", "w") as f: f.write(readme_txt)

print("Repository files created successfully.")
