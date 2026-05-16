# Paperless-ngx Metadata Manager
Eine leichtgewichtige Streamlit Web-App zum Aufspüren von Metadaten-Anomalien und zur Massenbearbeitung von Dokumenten in Paperless-ngx.

## Übersicht
Dieses Projekt bietet eine Web-Oberfläche für:
- Analyse von Dokumentenmetadaten
- Identifikation von Speicherpfad- und Datumsanomalien
- Filterbaren Link-Export zu Paperless-ngx
- Massenbearbeitung von Dokumenttyp, Korrespondent und Speicherpfad

## Projektstruktur
- `app.py` – Haupt-Streamlit-App
- `api.py` – Paperless-ngx API-Zugriff und Caching
- `checks.py` – Prüflogik für Dokumenttypen, Speicherpfade und Datumswerte
- `views/` – Seiten-Renderfunktionen für die App
  - `views/home.py`
  - `views/config.py`
  - `views/analysis.py`
  - `views/checks.py`
  - `views/list.py`

## Voraussetzungen
- Python 3.11
- `pip`

## Lokale Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## App starten
```bash
streamlit run app.py
```

## Konfiguration
Setze die Umgebungsvariablen oder gib die Werte in der App ein:
- `PAPERLESS_URL` – Basis-URL deiner Paperless-ngx-Instanz
- `PAPERLESS_TOKEN` – API-Token für Paperless-ngx

## Docker
```bash
docker build -t paperless-metadata-manager .
docker run -p 8501:8501 \
  -e PAPERLESS_URL="http://deine-ip:8000" \
  -e PAPERLESS_TOKEN="dein_token" \
  paperless-metadata-manager
```

## Hinweise
- Die App speichert keine sensiblen Daten im Repository.
- Standardwerte für URL/Token sind nicht mehr fest im Code hinterlegt.
