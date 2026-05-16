import requests
import streamlit as st

def get_headers():
    return {
        "Authorization": f"Token {st.session_state['PAPERLESS_TOKEN']}",
        "Accept": "application/json; version=2, application/json, */*;q=0.8"
    }

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
    if not st.session_state.get("IS_CONNECTED"): return []
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

@st.cache_data(ttl=60, show_spinner=False)
def fetch_custom_fields():
    """Ruft alle verfügbaren Custom Fields aus Paperless ab."""
    custom_fields = fetch_all("custom_fields")
    # Extrahiere Name, ID und bereite den Pfad für Dokumentdaten vor
    result = []
    for cf in custom_fields:
        cf_id = cf.get('id')
        name = cf.get('name') or str(cf_id)
        result.append({
            'id': cf_id,
            'name': name,
            'slug': cf.get('slug'),
            'data_type': cf.get('data_type'),
            'path': cf_id,  # Nutze die ID als Pfad für Lookups
        })
    return result

def update_document(doc_id, payload):
    base_url = st.session_state['PAPERLESS_URL'].strip().rstrip('/')
    update_url = f"{base_url}/api/documents/{doc_id}/"
    resp = requests.patch(update_url, headers=get_headers(), json=payload)
    return resp.status_code == 200
