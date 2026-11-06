"""Prépare les morceaux JSON (≤ 20 000 lignes) importés dans Supabase par immo_import(table, n).
Les CSV complets restent dans data/immo/ ; la base garde une version allégée (voir FILTRES)."""
import glob, json, os, pandas as pd
D = "data/immo"; OUT = f"{D}/db"; N = 20000
for f in glob.glob(f"{OUT}/*.json"): os.remove(f)
rd = lambda f, **k: pd.read_csv(f"{D}/{f}", sep=";", dtype={"code": str, "parent": str, "commune_parent": str,
                                                          "departement": str, "region": str, "epci": str, "idbank": str}, **k)
com = rd("communes.csv")
pop = com.set_index("code")["population"]
tables = {}
tables["immo_zones"] = rd("zones.csv")
tables["immo_communes"] = com
tables["immo_prix"] = rd("prix_dvf.csv")
lo = rd("loyers.csv")
# 2025 : toutes les communes, 4 types ; historique : appartements et maisons des communes de 5 000 hab. et plus
big = set(pop[pop >= 5000].index) | set(com.loc[com.niveau.eq("arrondissement"), "code"])
last = lo.annee.max()
tables["immo_loyers"] = lo[(lo.annee == last) | (lo.type.isin(["appartement", "maison"]) & lo.code.isin(big))]
tables["immo_fiscalite"] = rd("fiscalite.csv")
o = rd("oll.csv")
# OLL : résultats d'ensemble et par nombre de pièces / type d'habitat (sans les croisements fins)
tables["immo_oll"] = o[o.zone.isna() & o.epoque_construction.isna() & o.anciennete_locataire.isna()]
tables["immo_insee_series"] = rd("insee_catalogue.csv")
tables["immo_insee"] = rd("insee.csv")
man = {}
for t, df in tables.items():
    for c in df.columns:  # entiers lus en flottants à cause des vides -> entiers
        if df[c].dtype.kind == "f" and (df[c].dropna() % 1 == 0).all():
            df[c] = df[c].astype("Int64")
    df = df.astype(object).where(df.notna(), None)
    recs = df.to_dict("records")
    parts = [recs[i:i + N] for i in range(0, len(recs), N)] or [[]]
    for k, p in enumerate(parts, 1):
        json.dump(p, open(f"{OUT}/{t}_{k:02d}.json", "w"), ensure_ascii=False, separators=(",", ":"), default=str)
    man[t] = {"lignes": len(recs), "morceaux": len(parts)}
    print(t, len(recs), len(parts))
json.dump(man, open(f"{OUT}/manifest.json", "w"), indent=1, ensure_ascii=False)
