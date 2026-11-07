"""Télécharge les fichiers sources officiels européens dans data/europe/raw/ (traités ensuite par europe_build.py)."""
import os, urllib.request, json
H = {"User-Agent": "Mozilla/5.0 (myinvesta data; contact@myinvesta.fr)"}
R = "data/europe/raw"; os.makedirs(R, exist_ok=True)
F = {
 "uk_hpi_average_prices.csv": "http://publicdata.landregistry.gov.uk/market-trend-data/house-price-index-data/Average-prices-2026-08.csv",
 "uk_ons_prix_m2_2004_2016.xls": "https://www.ons.gov.uk/file?uri=/economy/inflationandpriceindices/datasets/housepricepersquaremetreandhousepriceperroomenglandandwales/current/priceperareadata.xls",
 "es_valor_tasado_municipios.xls": "https://apps.fomento.gob.es/BoletinOnline2/sedal/35103500.XLS",
 "be_statbel_vastgoed.zip": "https://statbel.fgov.be/sites/default/files/files/opendata/immo/vastgoed_2010_9999.zip",
 "ecb_gbp_eur_annuel.csv": "https://data-api.ecb.europa.eu/service/data/EXR/A.GBP.EUR.SP00.A?format=csvdata",
 "it_milano_ckan.json": "https://dati.comune.milano.it/api/3/action/package_search?q=quotazioni%20immobiliari%20omi%20compravendita&rows=200",
 "it_ondata_contents.json": "https://api.github.com/repos/ondata/quotazioni-immobiliari-agenzia-entrate/contents",
 "de_muenchen_gutachter.html": "https://stadt.muenchen.de/infos/gutachterausschuss-jahresbericht.html",
}
for k, u in F.items():
    try:
        b = urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=180).read()
        open(f"{R}/{k}", "wb").write(b); print("ok", k, len(b))
    except Exception as e:
        print("ERREUR", k, e)
