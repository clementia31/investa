"""Aperçu des colonnes de chaque source (premières lignes) -> data/immo/_heads.txt"""
import gzip, io, urllib.request
UA = {"User-Agent": "investa-immo-data/1.0"}
def head(url, n=4, nbytes=60000, gz=False):
    req = urllib.request.Request(url, headers={**UA, "Range": f"bytes=0-{nbytes}"})
    b = urllib.request.urlopen(req, timeout=120).read()
    if gz:
        b = gzip.GzipFile(fileobj=io.BytesIO(b)).read(nbytes) if False else _gz_partial(b)
    t = b.decode("utf-8", "ignore") if not b[:3] == b"\xef\xbb\xbf" else b[3:].decode("utf-8", "ignore")
    try: t2 = t if t.count("\n") > 1 else b.decode("latin-1")
    except Exception: t2 = t
    return "\n".join(t2.splitlines()[:n])
def _gz_partial(b):
    import zlib
    d = zlib.decompressobj(16 + zlib.MAX_WBITS)
    return d.decompress(b)
S = {
 "dvf_stats_mensuelles": ("https://data-pipeline-open.s3.sbg.io.cloud.ovh.net/dvf/stats_dvf.csv", {}),
 "dvf_stats_totales": ("https://data-pipeline-open.s3.sbg.io.cloud.ovh.net/dvf/stats_whole_period.csv", {}),
 "dvf_2025": ("https://static.data.gouv.fr/resources/demandes-de-valeurs-foncieres-geolocalisees/20261020-114721/full-2025.csv.gz", {"gz": True}),
 "loyers_2025_app": ("https://static.data.gouv.fr/resources/carte-des-loyers-indicateurs-de-loyers-dannonce-par-commune-en-2025/20251211-145010/pred-app-mef-dhup.csv", {}),
 "loyers_2018_app": ("https://static.data.gouv.fr/resources/carte-des-loyers-indicateurs-de-loyers-dannonce-par-commune-en-2018/20201203-114600/indicateurs-loyers-appartements.csv", {}),
 "oll_2025": ("https://www.observatoires-des-loyers.org/datagouv/2025/Base_OP_2025_Nationale.csv", {}),
 "zonage_abc": ("https://static.data.gouv.fr/resources/liste-des-communes-selon-le-zonage-abc/20260703-091314/liste-ensemble-des-communes-zonage-abc-en-vigueur-26-juin-2026.csv", {}),
 "fiscalite_locale": ("https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/fiscalite-locale-des-particuliers/exports/csv?limit=3", {}),
 "geo_communes": ("https://geo.api.gouv.fr/communes?fields=nom,code,population,codeDepartement,codeRegion,codesPostaux,codeEpci&format=json", {"n": 1, "nbytes": 1500}),
 "insee_irl": ("https://bdm.insee.fr/series/sdmx/data/IRL?lastNObservations=2", {"n": 40, "nbytes": 8000}),
 "insee_ipla": ("https://bdm.insee.fr/series/sdmx/data/IPLA-IPLNA-2015?lastNObservations=1", {"n": 200, "nbytes": 400000}),
 "insee_parc": ("https://bdm.insee.fr/series/sdmx/data/PARC-LOGEMENTS?lastNObservations=1", {"n": 60, "nbytes": 30000}),
 "insee_series_loyers": ("https://bdm.insee.fr/series/sdmx/data/SERIES_LOYERS?lastNObservations=1", {"n": 60, "nbytes": 30000}),
}
out = []
for k, (u, kw) in S.items():
    try: out.append(f"### {k}\n{head(u, **kw)}\n")
    except Exception as e: out.append(f"### {k}\nERREUR {e}\n")
open("data/immo/_heads.txt", "w").write("\n".join(out)); print("ok")
