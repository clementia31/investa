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
 "it_milano_omi_riepilogo.csv": "https://dati.comune.milano.it/dataset/1ad8ecfd-5d4a-487d-b2e3-7d45fe9e1274/resource/90df91fa-9bc9-4100-9192-cb3a2f46fd44/download/ds1996_quotazioni_omi_compravendita_e_locazione_riepilogo.csv",
 "it_ondata_data.json": "https://api.github.com/repos/ondata/quotazioni-immobiliari-agenzia-entrate/contents/data",
 "it_ondata_rawdata.json": "https://api.github.com/repos/ondata/quotazioni-immobiliari-agenzia-entrate/contents/rawData",
 "it_ondata_readme.md": "https://raw.githubusercontent.com/ondata/quotazioni-immobiliari-agenzia-entrate/master/README.md",
 "uk_ons_regional_m2.xlsx": "https://www.ons.gov.uk/file?uri=/economy/inflationandpriceindices/datasets/regionalhousepricelevelestimatespersquaremetre/current/regionalhousepricelevels.xlsx",
 "at_oenb_report_6_6.html": "https://www.oenb.at/isawebstat/stabfrage/createReport?report=6.6",
 "uk_ons_regional_m2.html": "https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/regionalhousepricelevelestimatespersquaremetre",
}
for y in range(2015, 2026):
    F[f"at_wohnungspreise_{y}.ods"] = f"https://www.statistik.at/fileadmin/pages/222/Wohnungspreise{y}.ods"
H2 = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
      "Accept": "*/*", "Referer": "https://www.ons.gov.uk/"}
for k, u in F.items():
    if os.path.exists(f"{R}/{k}") and not k.startswith("uk_ons"): continue
    try:
        b = urllib.request.urlopen(urllib.request.Request(u, headers=H2 if "ons.gov.uk" in u else H), timeout=180).read()
        open(f"{R}/{k}", "wb").write(b); print("ok", k, len(b))
    except Exception as e:
        print("ERREUR", k, e)
