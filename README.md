# Paperless-ngx Metadata Manager
Eine leichtgewichtige Streamlit Web-App zum Aufspüren von Metadaten-Anomalien und für die Massenbearbeitung (Bulk-Edit) in Paperless-ngx.

## Features
- **Anomalien finden**: Erkennt Dokumente, die einen vom Standard abweichenden Speicherpfad haben.
- **Bulk Edit**: Wähle mehrere Dokumente aus und ändere Korrespondent, Dokumenttyp und Speicherpfad auf einmal.

## Start mit Docker
```bash
docker build -t paperless-metadata-manager .
docker run -p 8501:8501 -e PAPERLESS_URL="http://deine-ip:8000" -e PAPERLESS_TOKEN="dein_token" paperless-metadata-manager
```
