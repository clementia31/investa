"""Sonde des sources officielles européennes -> data/europe/_probe.txt (début de chaque réponse)."""
import urllib.request, zlib, io, zipfile
H = {"User-Agent": "Mozilla/5.0 (myinvesta data; contact@myinvesta.fr)"}
U = [
 # Royaume-Uni : UK HPI (HM Land Registry / ONS) + prix au m² ONS 2004-2016
 "http://publicdata.landregistry.gov.uk/market-trend-data/house-price-index-data/Average-prices-2026-08.csv",
 "http://publicdata.landregistry.gov.uk/market-trend-data/house-price-index-data/Average-prices-2026-07.csv",
 "https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/housepricepersquaremetreandhousepriceperroomenglandandwales",
 # Espagne : valeur expertisée €/m² par commune (ministère)
 "https://apps.fomento.gob.es/BoletinOnline2/sedal/35103500.XLS",
 "https://datos.gob.es/apidata/catalog/dataset/a13002908-valor-tasado-de-la-vivienda-libre-por-municipios-de-mas-de-25-00-habitantes-total-base-20054.json",
 # Autriche
 "https://www.data.gv.at/katalog/api/3/action/package_search?q=Immobiliendurchschnittspreise",
 "https://www.data.gv.at/katalog/api/3/action/package_search?q=Wohnimmobilienpreisindex",
 # Belgique
 "https://statbel.fgov.be/fr/open-data?category=All&search=immobili",
 "https://statbel.fgov.be/sites/default/files/files/opendata/immo/vastgoed_2010_9999.zip",
 # Italie
 "https://dati.comune.milano.it/api/3/action/package_search?q=quotazioni%20immobiliari%20omi%20compravendita&rows=50",
 "https://api.github.com/repos/ondata/quotazioni-immobiliari-agenzia-entrate/contents",
 "https://dati.comune.roma.it/catalog/api/3/action/package_search?q=quotazioni%20omi",
 # Allemagne
 "https://daten.berlin.de/api/3/action/package_search?q=Immobilienpreise",
 "https://www.berlin.de/gutachterausschuss/marktinformationen/grundstuecksmarktberichte/",
 "https://stadt.muenchen.de/infos/gutachterausschuss-jahresbericht.html",
 # BCE taux de change
 "https://data-api.ecb.europa.eu/service/data/EXR/A.GBP.EUR.SP00.A?format=csvdata",
]
out = []
for u in U:
    try:
        b = urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=90).read()
        if u.endswith(".zip"):
            z = zipfile.ZipFile(io.BytesIO(b)); n = z.namelist()[0]
            t = f"ZIP {n}\n" + z.read(n)[:3000].decode("utf-8", "ignore")
        elif u.upper().endswith(".XLS"):
            import pandas as pd
            x = pd.read_excel(io.BytesIO(b), sheet_name=None, header=None)
            t = "\n".join(f"[feuille {k} {v.shape}]\n{v.head(12).to_string()[:2500]}" for k, v in list(x.items())[:3])
        else:
            t = b[:8000].decode("utf-8", "ignore")
        out.append(f"### {u}\nOK {len(b)} octets\n{t}\n")
    except Exception as e:
        out.append(f"### {u}\nERREUR {e}\n")
import os; os.makedirs("data/europe", exist_ok=True)
open("data/europe/_probe.txt", "w").write("\n".join(out)); print("ok")
