# Contributing

Danke für dein Interesse an diesem Projekt! Diese Datei beschreibt, wie du zum Repository beitragen kannst.

## Lokale Entwicklung

1. Repository klonen:
   ```bash
git clone https://github.com/Trinsic82/paperless-manager.git
cd paperless-manager
```
2. Python-Umgebung einrichten:
   ```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
3. App lokal starten:
   ```bash
streamlit run app.py
```

## Code-Qualität

- Nutze Python 3.11.
- Halte die Modularisierung von `app.py`, `api.py`, `checks.py` und `views/` ein.
- Verwende `use_container_width=True` für Streamlit-Tabellen und `st.cache_data` für API-Abfragen.
- Füge neue Funktionen in `views/` als eigene Render-Funktionen hinzu.

## Tests

Aktuell gibt es keine automatisierten Tests, aber du kannst die Python-Syntax prüfen mit:
```bash
python -m py_compile app.py api.py checks.py views/home.py views/config.py views/analysis.py views/list.py views/checks.py
```

## Pull Requests

- Erstelle für neue Features oder Fixes immer einen separaten Branch.
- Schreibe aussagekräftige Commit-Nachrichten.
- Beschreibe in der PR, was sich geändert hat und warum.
- Vermeide das Einchecken von sensiblen Daten wie API-Token.

## Docker

Die App kann auch als Docker-Container gestartet werden:
```bash
docker build -t paperless-metadata-manager .
docker run -p 8501:8501 \
  -e PAPERLESS_URL="http://deine-ip:8000" \
  -e PAPERLESS_TOKEN="dein_token" \
  paperless-metadata-manager
```

## Hinweise

- Der Code speichert keine Zugangsdaten im Repository.
- Konfiguriere API-URL und Token über Umgebungsvariablen oder die Konfigurationsseite der App.
