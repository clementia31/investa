"""Investa — base de statistiques immobilières françaises (sources publiques gratuites).

Produit des CSV propres dans data/immo/ (séparateur ';', point décimal, UTF-8) :
  communes.csv     référentiel des communes (+ arrondissements), population, zonage ABC
  zones.csv        France, régions, départements (codes et noms)
  prix_dvf.csv     prix au m² (médiane, moyenne) et nombre de ventes, par an depuis 2014, appartements / maisons,
                   à la commune, au département, à la région et pour la France (DVF, DGFiP / Etalab)
  loyers.csv       loyers d'annonce au m² par commune (carte des loyers, ministère du Logement)
  oll.csv          loyers des observatoires locaux des loyers par agglomération (2014 →)
  fiscalite.csv    taux de taxe foncière (TFB, TFNB), TEOM, TH résidences secondaires par commune (DGFiP)
  insee.csv        séries INSEE : IRL, indices Notaires-INSEE des prix des logements anciens et neufs,
                   ILC / ILAT / ICC, évolution des loyers…   (+ insee_catalogue.csv)
Chaque source est traitée indépendamment : une source en échec n'empêche pas les autres (voir _build_log.txt).
"""
import csv, gzip, io, json, os, re, sys, time, traceback, urllib.request
import pandas as pd

OUT = "data/immo"
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "investa-immo-data/1.0 (+https://myinvesta.fr)"}
LOG = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.append(s)


def fetch(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=600) as r:
                return r.read()
        except Exception as e:
            log(f"  essai {i + 1} échoué {url[:90]} : {e}")
            time.sleep(5 * (i + 1))
    raise RuntimeError(f"téléchargement impossible : {url}")


def save(df, name):
    df.to_csv(f"{OUT}/{name}", sep=";", index=False)
    log(f"  -> {name} : {len(df):,} lignes, {os.path.getsize(f'{OUT}/{name}') / 1e6:.1f} Mo")


def dec(b):
    for enc in ("utf-8", "cp1252"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            pass
    return b.decode("latin-1")


# --------------------------------------------------------------------------- référentiel
def build_communes():
    base = "https://geo.api.gouv.fr"
    regs = json.loads(fetch(f"{base}/regions"))
    deps = json.loads(fetch(f"{base}/departements"))
    zones = [{"niveau": "france", "code": "FR", "nom": "France", "parent": ""}]
    zones += [{"niveau": "region", "code": r["code"], "nom": r["nom"], "parent": "FR"} for r in regs]
    zones += [{"niveau": "departement", "code": d["code"], "nom": d["nom"], "parent": d["codeRegion"]} for d in deps]
    save(pd.DataFrame(zones), "zones.csv")

    f = "nom,code,population,codeDepartement,codeRegion,codesPostaux,codeEpci"
    com = json.loads(fetch(f"{base}/communes?fields={f}&format=json"))
    arr = json.loads(fetch(f"{base}/communes?type=arrondissement-municipal&fields={f},codeParent&format=json"))
    rows = []
    for c in com:
        rows.append({"code": c["code"], "nom": c["nom"], "niveau": "commune", "commune_parent": "",
                     "departement": c.get("codeDepartement", ""), "region": c.get("codeRegion", ""),
                     "epci": c.get("codeEpci", ""), "population": c.get("population"),
                     "codes_postaux": " ".join(c.get("codesPostaux") or [])})
    for c in arr:
        rows.append({"code": c["code"], "nom": c["nom"], "niveau": "arrondissement",
                     "commune_parent": c.get("codeParent", ""),
                     "departement": c.get("codeDepartement", ""), "region": c.get("codeRegion", ""),
                     "epci": c.get("codeEpci", ""), "population": c.get("population"),
                     "codes_postaux": " ".join(c.get("codesPostaux") or [])})
    df = pd.DataFrame(rows)
    # zonage ABC (tension du marché : Abis, A, B1, B2, C)
    try:
        z = pd.read_csv(io.StringIO(dec(fetch(
            "https://static.data.gouv.fr/resources/liste-des-communes-selon-le-zonage-abc/20260703-091314/"
            "liste-ensemble-des-communes-zonage-abc-en-vigueur-26-juin-2026.csv"))), sep=";", dtype=str)
        z = z.rename(columns={z.columns[0]: "code", z.columns[-1]: "zonage_abc"})[["code", "zonage_abc"]]
        df = df.merge(z, on="code", how="left")
        # les arrondissements héritent du zonage de leur commune
        par = df.set_index("code")["zonage_abc"]
        m = df["niveau"].eq("arrondissement")
        df.loc[m, "zonage_abc"] = df.loc[m, "commune_parent"].map(par)
    except Exception as e:
        log("  zonage ABC indisponible :", e)
        df["zonage_abc"] = ""
    df["population"] = df["population"].astype("Int64")
    save(df, "communes.csv")
    return df


# --------------------------------------------------------------------------- DVF
G = "https://static.data.gouv.fr/resources/demandes-de-valeurs-foncieres-geolocalisees/"
C = "https://data.cquest.org/dgfip_dvf/"   # archives des livraisons DGFiP (format brut, séparateur |)
DVF = {
    "2014": [("raw", C + "201904/valeursfoncieres-2014.txt")],
    "2015": [("raw", C + "201904/valeursfoncieres-2015.txt")],
    "2016": [("raw", C + "202110/valeursfoncieres-2016.txt")],
    "2017": [("raw", C + "202110/valeursfoncieres-2017.txt")],
    "2018": [("raw", C + "202110/valeursfoncieres-2018.txt")],
    "2019": [("raw", C + "202110/valeursfoncieres-2019.txt")],
    "2020": [("raw", C + "202110/valeursfoncieres-2020.txt")],
    "2021": [("raw", C + "202110/valeursfoncieres-2021-s1.txt"), ("geo", G + "20261020-113024/full-2021-s2.csv.gz")],
    "2022": [("geo", G + "20261020-114218/full-2022.csv.gz")],
    "2023": [("geo", G + "20261020-114336/full-2023.csv.gz")],
    "2024": [("geo", G + "20261020-114532/full-2024.csv.gz")],
    "2025": [("geo", G + "20261020-114721/full-2025.csv.gz")],
    "2026-S1": [("geo", G + "20261020-114825/full-2026-s1.csv.gz")],
}
CITY = {"751": "75056", "132": "13055", "693": "69123"}  # arrondissements -> Paris, Marseille, Lyon
KEEP = ["Vente"]  # logements anciens uniquement (les ventes sur plan, VEFA, faussent les comparaisons)


def download(url):
    import shutil, tempfile
    for i in range(4):
        try:
            f = tempfile.NamedTemporaryFile(delete=False, dir="/tmp")
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=900) as r:
                shutil.copyfileobj(r, f, 1 << 22)
            f.close()
            return f.name
        except Exception as e:
            log(f"  essai {i + 1} échoué {url[-60:]} : {e}")
            time.sleep(10 * (i + 1))
    raise RuntimeError(f"téléchargement impossible : {url}")


def sales_geo(url):
    cols = ["id_mutation", "nature_mutation", "valeur_fonciere", "code_commune", "type_local",
            "surface_reelle_bati", "nombre_pieces_principales", "adresse_numero", "adresse_nom_voie", "id_parcelle"]
    path = download(url)
    parts = []
    for ch in pd.read_csv(path, compression="gzip", usecols=cols, dtype=str, chunksize=500_000):
        parts.append(ch[ch["nature_mutation"].isin(KEEP) & ch["type_local"].notna()])
    os.remove(path)
    d = pd.concat(parts).rename(columns={"code_commune": "commune"})
    return d, ["id_mutation", "type_local", "surface_reelle_bati", "nombre_pieces_principales",
               "adresse_numero", "adresse_nom_voie", "id_parcelle"]


def sales_raw(url):
    path = download(url)
    head = open(path, encoding="utf-8", errors="ignore").readline().strip().split("|")
    want = {"No disposition": "dispo", "Date mutation": "date", "Nature mutation": "nature_mutation",
            "Valeur fonciere": "valeur_fonciere", "No voie": "adresse_numero", "Voie": "adresse_nom_voie",
            "Code departement": "dep", "Code commune": "com", "Section": "section", "No plan": "plan",
            "Type local": "type_local", "Surface reelle bati": "surface_reelle_bati",
            "Nombre pieces principales": "nombre_pieces_principales"}
    use = [c for c in head if c in want]
    parts = []
    for ch in pd.read_csv(path, sep="|", usecols=use, dtype=str, chunksize=500_000, encoding="utf-8",
                          encoding_errors="ignore"):
        ch = ch.rename(columns=want)
        parts.append(ch[ch["nature_mutation"].isin(KEEP) & ch["type_local"].notna()])
    os.remove(path)
    d = pd.concat(parts)
    d["valeur_fonciere"] = d["valeur_fonciere"].str.replace(",", ".", regex=False)
    d["surface_reelle_bati"] = d["surface_reelle_bati"].str.replace(",", ".", regex=False)
    d["commune"] = d["dep"].str[:2] + d["com"].str.zfill(3)
    d["id_mutation"] = d["date"] + "|" + d["valeur_fonciere"].fillna("") + "|" + d["commune"] + "|" + d["dispo"].fillna("")
    d["id_parcelle"] = d["commune"] + d["section"].fillna("") + d["plan"].fillna("")
    return d, ["id_mutation", "type_local", "surface_reelle_bati", "nombre_pieces_principales",
               "adresse_numero", "adresse_nom_voie", "id_parcelle"]


def clean_sales(d, dedup):
    d = d.drop_duplicates(dedup)
    logts = d[d["type_local"].isin(["Appartement", "Maison"])]
    autres = d[d["type_local"].str.startswith("Local industriel")]
    # une seule habitation par mutation (dépendances tolérées), pas de local commercial : méthode Etalab
    n = logts.groupby("id_mutation").size()
    seul = set(n[n == 1].index) - set(autres["id_mutation"])
    v = logts[logts["id_mutation"].isin(seul)].copy()
    v["valeur"] = pd.to_numeric(v["valeur_fonciere"], errors="coerce")
    v["surface"] = pd.to_numeric(v["surface_reelle_bati"], errors="coerce")
    v = v[(v["surface"] >= 9) & (v["valeur"] > 1000)]
    v["prix_m2"] = v["valeur"] / v["surface"]
    v = v[(v["prix_m2"] >= 150) & (v["prix_m2"] <= 30000)]
    v["type"] = v["type_local"].str.lower()
    return v[["commune", "type", "prix_m2"]]


def aggregate(periode, v, communes):
    ref = communes.set_index("code")
    v = v.copy()
    v["departement"] = v["commune"].map(ref["departement"])
    dep = v["commune"].str[:2].where(~v["commune"].str.startswith("97"), v["commune"].str[:3])
    v["departement"] = v["departement"].fillna(dep)  # anciennes communes fusionnées depuis
    dep_reg = communes.dropna(subset=["departement"]).groupby("departement")["region"].first()
    v["region"] = v["commune"].map(ref["region"]).fillna(v["departement"].map(dep_reg))
    v["ville"] = v["commune"].str[:3].map(CITY)
    v["fr"] = "FR"
    out = []
    for niveau, key in [("commune", "commune"), ("commune", "ville"), ("departement", "departement"),
                        ("region", "region"), ("france", "fr")]:
        g = v.dropna(subset=[key]).groupby([key, "type"])["prix_m2"]
        r = pd.DataFrame({"nb_ventes": g.size(), "prix_m2_median": g.median().round(0),
                          "prix_m2_moyen": g.mean().round(0)}).reset_index().rename(columns={key: "code"})
        r.insert(0, "niveau", niveau)
        out.append(r)
    r = pd.concat(out)
    r.insert(2, "periode", periode)
    for c in ["nb_ventes", "prix_m2_median", "prix_m2_moyen"]:
        r[c] = r[c].astype(int)
    log(f"  DVF {periode} : {len(v):,} ventes retenues, {len(r):,} lignes")
    return r


def build_dvf(communes):
    res = []
    for p, srcs in DVF.items():
        try:
            vs = []
            for kind, u in srcs:
                d, dedup = (sales_raw if kind == "raw" else sales_geo)(u)
                vs.append(clean_sales(d, dedup))
                del d
            res.append(aggregate(p, pd.concat(vs), communes))
        except Exception as e:
            log(f"  DVF {p} ÉCHEC : {e}")
            traceback.print_exc()
    df = pd.concat(res)[["niveau", "code", "periode", "type", "nb_ventes", "prix_m2_median", "prix_m2_moyen"]]
    df = df.sort_values(["niveau", "code", "type", "periode"])
    save(df, "prix_dvf.csv")


# --------------------------------------------------------------------------- carte des loyers
LOYERS_SLUGS = {2018: "carte-des-loyers-indicateurs-de-loyers-dannonce-par-commune-en-2018",
                2022: "carte-des-loyers-indicateurs-de-loyers-dannonce-par-commune-en-2022",
                2023: "carte-des-loyers-indicateurs-de-loyers-dannonce-par-commune-en-2023",
                2024: "carte-des-loyers-indicateurs-de-loyers-dannonce-par-commune-en-2024",
                2025: "carte-des-loyers-indicateurs-de-loyers-dannonce-par-commune-en-2025"}


def loyer_type(url):
    u = url.lower()
    if "app12" in u: return "appartement_1_2p"
    if "app3" in u: return "appartement_3p_plus"
    if "pred-app" in u or "appartements" in u: return "appartement"
    if "pred-mai" in u or "maisons" in u: return "maison"
    return None


def build_loyers():
    res = []
    for an, slug in LOYERS_SLUGS.items():
        try:
            ds = json.loads(fetch(f"https://www.data.gouv.fr/api/1/datasets/{slug}/"))
            for r in ds["resources"]:
                t = loyer_type(r["url"])
                if not t or not r["url"].lower().endswith(".csv"):
                    continue
                df = pd.read_csv(io.StringIO(dec(fetch(r["url"]))), sep=";", dtype=str)
                df.columns = [c.strip().strip('"') for c in df.columns]
                low = {c.lower(): c for c in df.columns}
                code = low.get("insee_c") or low.get("insee") or low.get("codgeo")
                num = lambda c: pd.to_numeric(df[low[c]].str.replace(",", ".", regex=False), errors="coerce") if c in low else None
                nbobs = next((low[c] for c in ("nbobs_com", "nbobs_commune") if c in low), None)
                out = pd.DataFrame({
                    "annee": an,
                    "code": df[code].str.strip().apply(lambda s: s.zfill(5) if s.isdigit() else s),
                    "type": t,
                    "loyer_m2": num("loypredm2").round(2),
                    "loyer_m2_bas": num("lwr.ipm2").round(2),
                    "loyer_m2_haut": num("upr.ipm2").round(2),
                    "prediction": df[low["typpred"]].str.strip() if "typpred" in low else "",
                    "nb_obs_commune": pd.to_numeric(df[nbobs], errors="coerce").astype("Int64") if nbobs else pd.NA,
                })
                res.append(out)
                log(f"  loyers {an} {t} : {len(out):,}")
        except Exception as e:
            log(f"  loyers {an} ÉCHEC : {e}")
    df = pd.concat(res).drop_duplicates(["annee", "code", "type"]).sort_values(["code", "type", "annee"])
    save(df, "loyers.csv")


# --------------------------------------------------------------------------- observatoires locaux des loyers
def build_oll():
    res = []
    for an in range(2014, 2031):
        try:
            b = fetch(f"https://www.observatoires-des-loyers.org/datagouv/{an}/Base_OP_{an}_Nationale.csv", tries=2)
        except Exception:
            continue
        df = pd.read_csv(io.StringIO(dec(b)), sep=";", dtype=str)
        df.columns = [c.strip() for c in df.columns]
        res.append(df)
        log(f"  OLL {an} : {len(df):,}")
    df = pd.concat(res, ignore_index=True)
    ren = {"Observatory": "observatoire", "Data_year": "annee", "agglomeration": "agglomeration",
           "Zone_complementaire": "zone", "Type_habitat": "type_habitat",
           "epoque_construction_homogene": "epoque_construction", "anciennete_locataire_homogene": "anciennete_locataire",
           "nombre_pieces_homogene": "pieces", "loyer_median": "loyer_m2_median", "loyer_moyen": "loyer_m2_moyen",
           "loyer_1_quartile": "loyer_m2_q1", "loyer_3_quartile": "loyer_m2_q3",
           "loyer_mensuel_median": "loyer_mensuel_median", "moyenne_loyer_mensuel": "loyer_mensuel_moyen",
           "surface_moyenne": "surface_moyenne", "nombre_observations": "nb_observations",
           "nombre_logements": "nb_logements", "methodologie_production": "methode"}
    df = df[[c for c in ren if c in df.columns]].rename(columns=ren)
    for c in ["loyer_m2_median", "loyer_m2_moyen", "loyer_m2_q1", "loyer_m2_q3", "loyer_mensuel_median",
              "loyer_mensuel_moyen", "surface_moyenne", "nb_observations", "nb_logements"]:
        if c in df:
            df[c] = pd.to_numeric(df[c].str.replace(",", ".", regex=False).str.replace(" ", "", regex=False), errors="coerce")
    save(df, "oll.csv")


# --------------------------------------------------------------------------- fiscalité locale
def build_fiscalite():
    url = ("https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/fiscalite-locale-des-particuliers/exports/csv"
           "?select=exercice,insee_com,taux_global_tfb,taux_global_tfnb,taux_plein_teom,taux_global_th&delimiter=%3B")
    df = pd.read_csv(io.BytesIO(fetch(url)), sep=";", dtype=str)
    df = df.rename(columns={"exercice": "annee", "insee_com": "code"})
    for c in ["taux_global_tfb", "taux_global_tfnb", "taux_plein_teom", "taux_global_th"]:
        df[c] = pd.to_numeric(df[c].str.replace(",", ".", regex=False), errors="coerce").round(2)
    df["annee"] = pd.to_numeric(df["annee"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["annee", "code"]).drop_duplicates(["annee", "code"]).sort_values(["code", "annee"])
    log(f"  fiscalité : années {df['annee'].min()}–{df['annee'].max()}")
    save(df, "fiscalite.csv")


# --------------------------------------------------------------------------- INSEE (SDMX BDM)
INSEE_FLOWS = ["IRL", "IPLA-IPLNA-2015", "ILC-ILAT-ICC", "INDICES_LOYERS", "SERIES_LOYERS", "PARC-LOGEMENTS"]


def build_insee():
    cat, obs = [], []
    for fl in INSEE_FLOWS:
        try:
            x = dec(fetch(f"https://bdm.insee.fr/series/sdmx/data/{fl}"))
        except Exception as e:
            log(f"  INSEE {fl} ÉCHEC : {e}")
            continue
        n = 0
        for m in re.finditer(r"<Series ([^>]*)>(.*?)</Series>", x, re.S):
            a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
            idb = a.get("IDBANK")
            cat.append({"idbank": idb, "flux": fl, "titre": a.get("TITLE_FR", ""), "unite": a.get("UNIT_MEASURE", ""),
                        "frequence": a.get("FREQ", ""), "derniere_maj": a.get("LAST_UPDATE", "")})
            for o in re.finditer(r"<Obs ([^>]*)/>", m.group(2)):
                b = dict(re.findall(r'(\w+)="([^"]*)"', o.group(1)))
                if b.get("OBS_VALUE") not in (None, "", "NaN"):
                    obs.append({"idbank": idb, "periode": b["TIME_PERIOD"], "valeur": b["OBS_VALUE"]})
            n += 1
        log(f"  INSEE {fl} : {n} séries")
    save(pd.DataFrame(cat).drop_duplicates("idbank"), "insee_catalogue.csv")
    save(pd.DataFrame(obs).drop_duplicates(["idbank", "periode"]).sort_values(["idbank", "periode"]), "insee.csv")


# --------------------------------------------------------------------------- main
STEPS = {"communes": None, "dvf": None, "loyers": build_loyers, "oll": build_oll,
         "fiscalite": build_fiscalite, "insee": build_insee}

if __name__ == "__main__":
    only = set(filter(None, os.environ.get("ONLY", "").split(",")))
    communes = None
    if not only or "communes" in only or "dvf" in only:
        try:
            log("== communes")
            communes = build_communes()
        except Exception as e:
            log("communes ÉCHEC", e); traceback.print_exc()
    for k, fn in STEPS.items():
        if k == "communes" or (only and k not in only):
            continue
        log(f"== {k}")
        try:
            if k == "dvf":
                if communes is None:
                    communes = pd.read_csv(f"{OUT}/communes.csv", sep=";", dtype=str)
                build_dvf(communes)
            else:
                fn()
        except Exception as e:
            log(f"{k} ÉCHEC : {e}")
            traceback.print_exc()
    open(f"{OUT}/_build_log.txt", "w").write("\n".join(LOG) + "\n")
