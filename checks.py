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

# Hier können in Zukunft weitere Prüfungen hinzugefügt werden.
