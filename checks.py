from collections import defaultdict, Counter
from datetime import datetime

def check_document_types_count(docs, doc_types, base_url):
    """
    Findet Dokumenttypen, die weniger als 5 Einträge haben.
    """
    type_counts = Counter([d.get('document_type') for d in docs])
    few_docs = []
    for dt_id, count in type_counts.items():
        if count < 5:
            dt_name = doc_types.get(dt_id, "Ohne Typ")
            if dt_id is not None:
                link = f"{base_url}/documents/?document_type__id={dt_id}#{dt_name}"
            else:
                link = f"{base_url}/documents/?document_type__isnull=true#{dt_name}"
            few_docs.append({"Dokumenttyp": link, "Anzahl": count})
    return few_docs

def check_path_consistency(docs, doc_types, st_paths, base_url):
    """
    Prüft Dokumente auf Konsistenz der Speicherpfade innerhalb desselben Dokumenttyps.
    """
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
    return anomalies

def check_date_anomalies(docs, doc_types, base_url):
    """
    Prüft Dokumente auf Datumsanomalien.
    """
    current_year = datetime.now().year
    
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
                type_filter_url = f"{base_url}/documents/?document_type__id={dt_id}#{dt_name}"
                
                date_anomalies.append({
                    "ID": f"{base_url}/documents/{d['id']}/details",
                    "Titel": d['title'],
                    "Typ": type_filter_url,
                    "Jahr": doc_year,
                    "Grund": reason
                })
    return date_anomalies


def _resolve_field_value(document, field_path):
    """
    Versucht, einen verschachtelten Feldwert aus einem Dokument zu extrahieren.
    Unterstützt: "field", "parent.child", "custom_fields.slug"
    """
    parts = field_path.split('.')
    if len(parts) != 2 or parts[0] != 'custom_fields':
        # Fallback für nicht-custom-fields Pfade
        value = document
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        return value
    
    # Spezialfall: custom_fields.slug
    slug = parts[1]
    custom_fields = document.get('custom_fields')
    
    if custom_fields is None:
        return None
    
    # Fall 1: custom_fields ist ein Dict mit Slug als Key
    if isinstance(custom_fields, dict):
        if slug in custom_fields:
            cf_value = custom_fields[slug]
            # Wenn es ein Dict ist, hole 'value' Key
            if isinstance(cf_value, dict):
                return cf_value.get('value')
            return cf_value
        return None
    
    # Fall 2: custom_fields ist ein Array von Objekten
    if isinstance(custom_fields, list):
        for item in custom_fields:
            if not isinstance(item, dict):
                continue
            # Prüfe ob slug oder id passt
            if item.get('slug') == slug or item.get('id') == slug:
                return item.get('value')
        return None
    
    return None


def _is_field_filled(value):
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) > 0
    return True


def check_custom_field_missing(docs, doc_types, field_names, base_url):
    """
    Findet Dokumente, bei denen die benannten Custom Fields fehlen oder leer sind.
    field_names kann ein String, eine Liste von Strings oder eine Liste von Dictionaries sein.
    """
    normalized_fields = []
    if isinstance(field_names, (str, dict)):
        field_names = [field_names]

    for field in field_names:
        if isinstance(field, dict):
            normalized_fields.append({
                'path': field.get('path'),
                'display': field.get('name') or field.get('path'),
            })
        else:
            normalized_fields.append({
                'path': field,
                'display': field,
            })

    all_anomalies = []
    all_summary = []
    
    # Prüfe jeden Field einzeln
    for field_info in normalized_fields:
        field_path = field_info['path']
        field_display = field_info['display']
        anomalies = []
        type_summary = {}

        for d in docs:
            dt_id = d.get('document_type')
            dt_name = doc_types.get(dt_id, 'Ohne Typ')
            if dt_id is None:
                continue

            value = _resolve_field_value(d, field_path)
            filled = _is_field_filled(value)

            if dt_name not in type_summary:
                type_summary[dt_name] = {'filled': 0, 'missing': 0}

            if filled:
                type_summary[dt_name]['filled'] += 1
            else:
                type_summary[dt_name]['missing'] += 1
                anomalies.append({
                    'ID': f"{base_url}/documents/{d['id']}/details",
                    'Titel': d.get('title', ''),
                    'Dokumenttyp': dt_name,
                    'Custom Field': field_display,
                    'Wert': value if value is not None else '',
                })

        summary = []
        for dt_name, counts in type_summary.items():
            if counts['filled'] == 0 and counts['missing'] == 0:
                continue  # Dokumenttyp ohne Dokumente
                
            if counts['missing'] == 0:
                status = 'Vollständig gefüllt'
            elif counts['filled'] == 0:
                status = 'Feld in allen Dokumenten fehlend'
            else:
                status = f"{counts['missing']} von {counts['missing'] + counts['filled']} fehlend"
                
            summary.append({
                'Dokumenttyp': dt_name,
                'Custom Field': field_display,
                'Gesamt': counts['missing'] + counts['filled'],
                'Gefüllt': counts['filled'],
                'Fehlend': counts['missing'],
                'Status': status,
            })
        
        all_anomalies.extend(anomalies)
        all_summary.extend(summary)

    return all_anomalies, all_summary


# Hier können in Zukunft weitere Prüfungen hinzugefügt werden.
