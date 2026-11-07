"""Prix des logements dans les grandes villes européennes, harmonisés en €/m² (méthode « à la française »).

Règle : on part toujours d'un niveau officiel en €/m² (ou £/m²) publié par l'organisme public du pays,
et on ne prolonge dans le temps (règle de trois) qu'avec l'indice officiel de la même ville.
Sortie : data/europe/prix_villes_europe.csv
  ville;pays;annee;prix_m2_eur;prix_m2_local;devise;nature;methode;source

Villes et sources
  Paris      DVF (DGFiP) médiane appartements anciens 2014 → ; avant : indice Notaires-INSEE Paris
  Londres    ONS prix au m² des appartements 2004-2016 ; après 2016 et avant 2004 : UK HPI (HM Land Registry),
  Manchester   prix moyen des appartements de la ville ; conversion £ -> € au taux annuel moyen de la BCE
  Madrid     Ministère espagnol du Logement : valeur expertisée moyenne au m² (tasación), toutes les
  Barcelone    expertises de logements libres, moyenne des 4 trimestres, 2005 →
  Milan      Agenzia delle Entrate (OMI) : moyenne des cotations « abitazioni civili, état normal » des zones
               de la ville (milieu de fourchette, surface brute), moyenne des 2 semestres, 2004 →
  Vienne     Statistik Austria : prix médian au m² des appartements (transactions du registre foncier) 2015 → ;
               avant 2015 : indice OeNB des appartements anciens de Vienne
"""
import re
import pandas as pd

R = "data/europe/raw"
rows = []


def add(ville, pays, an, eur, loc, dev, nature, methode, source):
    rows.append(dict(ville=ville, pays=pays, annee=int(an), prix_m2_eur=round(eur), prix_m2_local=round(loc),
                     devise=dev, nature=nature, methode=methode, source=source))


# ---------------------------------------------------------------- Paris (base française)
p = pd.read_csv("data/immo/prix_dvf.csv", sep=";", dtype={"code": str})
p = p[(p.code == "75056") & (p.type == "appartement") & (p.periode.str.len() == 4)]
for r in p.itertuples():
    add("Paris", "France", r.periode, r.prix_m2_median, r.prix_m2_median, "EUR", "transactions",
        "direct", "DVF (DGFiP), médiane des ventes d'appartements anciens")
e = pd.read_csv("data/immo/prix_estimes.csv", sep=";", dtype={"code": str})
for r in e[(e.code == "75056") & (e.type == "appartement")].itertuples():
    add("Paris", "France", r.annee, r.prix_m2_estime, r.prix_m2_estime, "EUR", "transactions",
        "indice officiel (règle de trois)", "Notaires-INSEE, indice des prix des appartements anciens à Paris")

# ---------------------------------------------------------------- Royaume-Uni
fx = pd.read_csv(f"{R}/ecb_gbp_eur_annuel.csv")[["TIME_PERIOD", "OBS_VALUE"]]
gbp_per_eur = dict(zip(fx.TIME_PERIOD.astype(int), fx.OBS_VALUE))
ons = pd.read_excel(f"{R}/uk_ons_prix_m2_2004_2016.xls", sheet_name=["Table2", "Table11"], header=None)
t2, t11 = ons["Table2"], ons["Table11"]
years = list(range(2004, 2017))
lon = t2[t2[1].astype(str).str.strip() == "London"].iloc[0, 2:15].astype(float).tolist()
man = t11[t11[3].astype(str).str.strip() == "Manchester"].iloc[0, 4:17].astype(float).tolist()
hpi = pd.read_csv(f"{R}/uk_hpi_flats_london_manchester.csv")
hpi["annee"] = pd.to_datetime(hpi.Date, dayfirst=True).dt.year
flat = hpi.groupby(["RegionName", "annee"]).FlatPrice.mean()
for ville, region, serie in [("Londres", "London", lon), ("Manchester", "Manchester", man)]:
    ons_y = dict(zip(years, serie))
    f = flat.loc[region]
    last = int(f.index.max()) if f.index.max() < 2026 else 2025
    for an in range(1999, last + 1):
        if an in ons_y:
            gbp, meth = ons_y[an], "direct"
        elif an > 2016:
            gbp, meth = ons_y[2016] * f[an] / f[2016], "indice officiel (règle de trois)"
        else:
            gbp, meth = ons_y[2004] * f[an] / f[2004], "indice officiel (règle de trois)"
        src = ("ONS, prix au m² des appartements" if meth == "direct"
               else "ONS (niveau) et UK HPI / HM Land Registry (évolution du prix des appartements)")
        add(ville, "Royaume-Uni", an, gbp / gbp_per_eur[an], gbp, "GBP", "transactions", meth,
            src + " ; taux de change BCE")

# ---------------------------------------------------------------- Espagne
xs = pd.read_excel(f"{R}/es_valor_tasado_municipios.xls", sheet_name=None, header=None)
es = []
for k, d in xs.items():
    m = re.match(r"T(\d)A(\d{4})", k.strip())
    if not m:
        continue
    col = 3 if d.shape[1] <= 6 else 5  # colonne « Total »
    for ville in ("Madrid", "Barcelona"):
        hit = d[d[2].astype(str).str.strip() == ville]
        if len(hit):
            v = pd.to_numeric(hit.iloc[0, col], errors="coerce")
            if pd.notna(v):
                es.append((ville, int(m.group(2)), int(m.group(1)), float(v)))
es = pd.DataFrame(es, columns=["ville", "annee", "trim", "v"])
for (ville, an), g in es.groupby(["ville", "annee"]):
    if len(g) < 4:
        continue  # année incomplète
    add({"Madrid": "Madrid", "Barcelona": "Barcelone"}[ville], "Espagne", an, g.v.mean(), g.v.mean(), "EUR",
        "expertises", "direct", "Ministerio de Vivienda, valor tasado medio de vivienda libre")

# ---------------------------------------------------------------- Milan (OMI)
mi = pd.read_csv(f"{R}/it_milano_omi_riepilogo.csv", sep=";", dtype=str)
mi = mi[(mi.Descr_Tipologia == "Abitazioni civili") & (mi.Stato == "NORMALE")]
mi["mid"] = (pd.to_numeric(mi.Compr_min) + pd.to_numeric(mi.Compr_max)) / 2
sem = mi.groupby(["Anno", "Periodo"]).mid.mean().reset_index()
for an, g in sem.groupby("Anno"):
    if len(g) < 2:
        continue
    add("Milan", "Italie", an, g.mid.mean(), g.mid.mean(), "EUR", "cotations officielles", "moyenne des zones",
        "Agenzia delle Entrate (OMI), abitazioni civili, état normal")

# ---------------------------------------------------------------- Vienne
VIENNE = {2015: 3333, 2016: 3624, 2017: 3828, 2018: 4007, 2019: 4217, 2020: 4538, 2021: 5009, 2022: 5516,
          2023: 5000, 2024: 4940, 2025: 5212}  # Statistik Austria, communiqué du 28 mai 2026
for an, v in VIENNE.items():
    add("Vienne", "Autriche", an, v, v, "EUR", "transactions", "direct",
        "Statistik Austria, prix médian des appartements (registre foncier)")
o = pd.read_csv(f"{R}/at_oenb_wohnimmobilienpreisindex.csv", sep=";", encoding="latin-1", dtype=str)
o = o[(o.Periode == "Jahr") & (o.Indikator == "IMOP Wien, Preise für gebrauchte Eigentumswohnungen, 2000=100")]
idx = dict(zip(o.Jahr.astype(int), pd.to_numeric(o.Werte.str.replace(",", "."), errors="coerce")))
for an in range(1999, 2015):
    if an in idx:
        v = VIENNE[2015] * idx[an] / idx[2015]
        add("Vienne", "Autriche", an, v, v, "EUR", "transactions", "indice officiel (règle de trois)",
            "Statistik Austria (niveau 2015) et OeNB, indice des appartements anciens à Vienne")

out = pd.DataFrame(rows).sort_values(["ville", "annee"])
out.to_csv("data/europe/prix_villes_europe.csv", sep=";", index=False)
print(out.pivot_table(index="ville", columns="annee", values="prix_m2_eur")
      .reindex(columns=[2000, 2005, 2008, 2010, 2015, 2020, 2024, 2025]).to_string())
