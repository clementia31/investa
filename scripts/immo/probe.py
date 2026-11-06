"""Sonde de sources (listes de répertoires, premiers octets) -> data/immo/_probe.txt"""
import urllib.request
U = ["https://files.data.gouv.fr/geo-dvf/", "https://files.data.gouv.fr/geo-dvf/latest/csv/",
     "https://data.cquest.org/dgfip_dvf/", "https://data.cquest.org/geo_dvf/",
     "https://opendata.caissedesdepots.fr/api/explore/v2.1/catalog/datasets/donnees-valeurs-foncieres-a-la-commune/records?limit=3",
     "https://opendata.caissedesdepots.fr/api/explore/v2.1/catalog/datasets?where=search(%22valeurs%20foncieres%22)&limit=10&select=dataset_id",
     "https://www.data.gouv.fr/api/1/datasets/demandes-de-valeurs-foncieres/",
     "https://www.data.gouv.fr/api/1/datasets/?q=dvf%202014&page_size=10"]
out = []
for u in U:
    try:
        b = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "investa-immo-data/1.0"}), timeout=60).read()
        out.append(f"### {u}\n{b[:6000].decode('utf-8', 'ignore')}\n")
    except Exception as e:
        out.append(f"### {u}\nERREUR {e}\n")
open("data/immo/_probe.txt", "w").write("\n".join(out))
