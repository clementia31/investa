"""Inflation et prix immobiliers en euros constants (France uniquement).

Sorties (data/immo/) :
  inflation.csv   annee ; ipc (moyenne annuelle, base 100 en 2015) ; inflation_pct (glissement de la moyenne annuelle)
                  ; indice_logements_anciens (France, ensemble, base 100 en 2015) ; inflation_immobiliere_pct
                  ; coef_euros_2025 (multiplier un prix de l'année pour l'exprimer en euros de 2025)
  prix_reels.csv  niveau ; code ; annee ; type ; prix_m2_courant ; prix_m2_euros_2025 ; source
                  (prix DVF, plus les années estimées avant 2014 avec source = estimation)
Sources : INSEE, indice des prix à la consommation, ensemble des ménages, France (base 2015, idbank 001759970) ;
INSEE / Notaires, indice des prix des logements anciens, France hors Mayotte, ensemble (idbank 010567118).
La série base 2015 de l'IPC s'arrête en décembre 2025 (passage à la base 2025) : les euros constants sont donc
exprimés en euros de 2025, dernière année complète.
"""
import pandas as pd

D = "data/immo"
ins = pd.read_csv(f"{D}/insee.csv", sep=";", dtype={"idbank": str})
ins["annee"] = ins.periode.str[:4].astype(int)
ins["valeur"] = pd.to_numeric(ins.valeur, errors="coerce")


def annuel(idb):
    d = ins[ins.idbank == idb]
    need = 4 if d.periode.str.contains("Q").any() else (12 if d.periode.str.len().max() == 7 else 1)
    s = d.groupby("annee").valeur.agg(["mean", "size"])
    return s.loc[s["size"] >= need, "mean"]


ipc = annuel("001759970")             # mensuel -> moyenne des 12 mois
log = annuel("010567118")             # trimestriel -> moyenne des 4 trimestres
REF = 2025
inf = pd.DataFrame({"ipc": ipc.round(2)})
inf["inflation_pct"] = (inf.ipc.pct_change() * 100).round(2)
inf = inf.join(pd.DataFrame({"indice_logements_anciens": log.round(2)}), how="outer")
inf["inflation_immobiliere_pct"] = (inf.indice_logements_anciens.pct_change() * 100).round(2)
inf["coef_euros_2025"] = (ipc[REF] / inf.ipc).round(4)
inf.index.name = "annee"
inf = inf[inf.index >= 1996]
inf.reset_index().to_csv(f"{D}/inflation.csv", sep=";", index=False)

coef = inf.coef_euros_2025.dropna()
p = pd.read_csv(f"{D}/prix_dvf.csv", sep=";", dtype={"code": str})
p = p[p.periode.str.len() == 4].assign(annee=lambda d: d.periode.astype(int), source="DVF")
p = p.rename(columns={"prix_m2_median": "prix_m2_courant"})
e = pd.read_csv(f"{D}/prix_estimes.csv", sep=";", dtype={"code": str})
e = e.rename(columns={"prix_m2_estime": "prix_m2_courant"}).assign(source=lambda d: "estimation (" + d.precision + ")")
r = pd.concat([e[["niveau", "code", "annee", "type", "prix_m2_courant", "source"]],
               p[["niveau", "code", "annee", "type", "prix_m2_courant", "source"]]])
r["prix_m2_euros_2025"] = (r.prix_m2_courant * r.annee.map(coef)).round(0).astype("Int64")
r = r.sort_values(["niveau", "code", "type", "annee"])
r.to_csv(f"{D}/prix_reels.csv", sep=";", index=False)
print(inf.tail(12).to_string())
