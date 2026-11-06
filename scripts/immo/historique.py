"""Prix au m² estimés avant 2014 (les ventes DVF ne sont publiques que depuis 2014).

Méthode : prix DVF 2014 de la zone × (indice Notaires-INSEE de l'année / indice 2014), moyenne annuelle
des indices trimestriels. On prend l'indice le plus proche de la zone :
  ville  : Paris (appartements), agglomérations de Lyon et de Marseille (appartements), de Lille (maisons, 2008 →)
  dép.   : départements d'Île-de-France (appartements, maisons)
  région : Île-de-France, Provence-Alpes-Côte d'Azur, Rhône-Alpes, Nord-Pas-de-Calais (2008 →)
  défaut : Province (villes-centres pour les appartements, ensemble pour les maisons)
Sortie : data/immo/prix_estimes.csv (niveau;code;annee;type;prix_m2_estime;indice;precision)
precision = ville | departement | region | province — à indiquer dans les visuels (« estimation »)."""
import pandas as pd
D = "data/immo"
ins = pd.read_csv(f"{D}/insee.csv", sep=";", dtype={"idbank": str})
ins["annee"] = ins.periode.str[:4].astype(int)
ins = ins.groupby(["idbank", "annee"]).valeur.mean()
ins_n = ins.groupby("idbank").size()
p = pd.read_csv(f"{D}/prix_dvf.csv", sep=";", dtype={"code": str})
com = pd.read_csv(f"{D}/communes.csv", sep=";", dtype={"code": str, "departement": str, "region": str})
B = {  # séries brutes, base 100 en 2015
    ("ville", "75056", "appartement"): "010567012",
    ("ville", "69123", "appartement"): "010567010", ("ville", "69266", "appartement"): "010567010",
    ("ville", "13055", "appartement"): "010567006", ("ville", "13001", "appartement"): "010567006",
    ("ville", "59350", "maison"): "010567008",
    ("dep", "77", "appartement"): "010567014", ("dep", "77", "maison"): "010567018",
    ("dep", "78", "appartement"): "010567020", ("dep", "78", "maison"): "010567024",
    ("dep", "91", "appartement"): "010567026", ("dep", "91", "maison"): "010567030",
    ("dep", "92", "appartement"): "010567032", ("dep", "92", "maison"): "010567036",
    ("dep", "93", "appartement"): "010567038", ("dep", "93", "maison"): "010567042",
    ("dep", "94", "appartement"): "010567044", ("dep", "94", "maison"): "010567048",
    ("dep", "95", "appartement"): "010567050", ("dep", "95", "maison"): "010567054",
    ("dep", "75", "appartement"): "010567012",
    ("reg", "11", "appartement"): "010567076", ("reg", "11", "maison"): "010567090",
    ("reg", "93", "appartement"): "010567110", ("reg", "93", "maison"): "010567114",
    ("reg", "84", "appartement"): "010567104", ("reg", "84", "maison"): "010567108",
    ("reg", "32", "appartement"): "010567098", ("reg", "32", "maison"): "010567102",
    ("prov", "", "appartement"): "010567070", ("prov", "", "maison"): "010567074",
    ("france", "FR", "appartement"): "010567056", ("france", "FR", "maison"): "010567060",
}
ref = com.set_index("code")


def choix(niveau, code, typ):
    if niveau == "france":
        return B[("france", "FR", typ)], "france"
    if niveau == "commune":
        if ("ville", code, typ) in B: return B[("ville", code, typ)], "ville"
        dep = ref.departement.get(code); reg = ref.region.get(code)
    elif niveau == "departement":
        dep = code; reg = com[com.departement == code].region.iloc[0] if (com.departement == code).any() else None
    else:
        dep = None; reg = code
    if dep and ("dep", dep, typ) in B: return B[("dep", dep, typ)], "departement"
    if reg and ("reg", reg, typ) in B: return B[("reg", reg, typ)], "region"
    return B[("prov", "", typ)], "province"


big = set(com[(com.population >= 20000) & com.niveau.eq("commune")].code)
base = p[(p.periode == "2014") & (p.nb_ventes >= 30) & (p.niveau.isin(["france", "region", "departement"]) | p.code.isin(big))]
rows = []
for r in base.itertuples():
    idb, prec = choix(r.niveau, r.code, r.type)
    s = ins.loc[idb]
    for an in range(2000, 2014):
        if an in s.index and 2014 in s.index:
            rows.append((r.niveau, r.code, an, r.type, round(r.prix_m2_median * s[an] / s[2014]), idb, prec))
out = pd.DataFrame(rows, columns=["niveau", "code", "annee", "type", "prix_m2_estime", "indice", "precision"])
out.to_csv(f"{D}/prix_estimes.csv", sep=";", index=False)
print(len(out), out.precision.value_counts().to_dict())
