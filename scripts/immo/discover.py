"""Repérage des sources immobilières françaises gratuites (data.gouv.fr + INSEE BDM).
Écrit data/immo/_discovery.json : jeux de données, fichiers, tailles, et flux INSEE utiles."""
import json, os, re, urllib.request, urllib.parse

UA = {"User-Agent": "investa-immo-data/1.0"}
def get(url, raw=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        b = r.read()
    return b if raw else json.loads(b)

QUERIES = ["statistiques dvf", "demandes de valeurs foncieres geolocalisees", "carte des loyers",
           "indicateurs de loyers", "taux taxe fonciere communes", "fiscalite locale des particuliers",
           "logements vacants", "code officiel geographique", "populations legales communes",
           "base permanente des equipements", "observatoire des loyers", "prix immobilier notaires",
           "zonage abc", "zone tendue", "dpe logements", "communes de france base de donnees"]
out = {"datagouv": {}, "insee_dataflows": []}
for q in QUERIES:
    try:
        d = get("https://www.data.gouv.fr/api/1/datasets/?" + urllib.parse.urlencode({"q": q, "page_size": 8}))
        out["datagouv"][q] = [{
            "title": x["title"], "slug": x["slug"], "org": (x.get("organization") or {}).get("name"),
            "updated": x.get("last_update"),
            "resources": [{"title": r["title"], "url": r["url"], "format": r.get("format"), "size": r.get("filesize")}
                          for r in x.get("resources", [])][:25]} for x in d["data"]]
    except Exception as e:
        out["datagouv"][q] = f"ERREUR {e}"
try:
    xml = get("https://bdm.insee.fr/series/sdmx/dataflow", raw=True).decode("utf-8", "ignore")
    for m in re.finditer(r'<str:Dataflow[^>]*id="([^"]+)".*?<com:Name xml:lang="fr">([^<]+)</com:Name>', xml, re.S):
        out["insee_dataflows"].append([m.group(1), m.group(2)])
except Exception as e:
    out["insee_dataflows"] = f"ERREUR {e}"
os.makedirs("data/immo", exist_ok=True)
json.dump(out, open("data/immo/_discovery.json", "w"), ensure_ascii=False, indent=1)
print("ok", len(out["insee_dataflows"]))
