"""Prix au m² estimés avant 2014 (les ventes DVF ne sont publiques que depuis 2014).

Méthode : prix DVF 2014 de la zone × (indice Notaires-INSEE de l'année / indice 2014), moyenne annuelle
des indices trimestriels. On prend l'indice le plus proche de la zone :
  ville  : Paris (appartements), agglomérations de Lyon et de Marseille (appartements), de Lille (maisons, 2008 →)
  dép.   : départements d'Île-de-France (appartements, maisons)
  région : Île-de-France, Provence-Alpes-Côte d'Azur, Rhône-Alpes, Nord-Pas-de-Calais (2008 →)
  défaut : Province (villes-centres pour les appartements, ensemble pour les maisons)
Sortie : data/immo/prix_estimes.csv (niveau;code;annee;type;prix_m2_estime;indice;precision)
precision = ville | notaires | departement | region | province — à indiquer dans les visuels (« estimation »).

Pour les grandes villes sans indice INSEE propre (Lyon, Marseille, Bordeaux, Toulouse, Nice, Nantes, Montpellier, Rennes, Lille, Grenoble, Dijon, Nîmes,
Clermont-Ferrand, Toulon, Reims, Amiens, Limoges ; Paris garde son indice Notaires-INSEE),
2009-2013 suivent les prix médians au m² des appartements anciens publiés par les Notaires de France
(notes de conjoncture immobilière de janvier 2011, 2012, 2013 et 2015, 3e trimestre ; les années manquantes
sont déduites de l'évolution sur un an publiée). Avant le premier point notarial : indice régional depuis ce point d'ancrage."""
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


# Notaires de France, appartements anciens, prix médian au m² du 3e trimestre
NOTAIRES = {  # Notaires de France, prix médian au m² des appartements anciens, 3e trimestre
    "69123": {2009: 2744, 2010: 2961, 2011: 3224, 2012: 3280, 2013: 3297, 2014: 3310},  # Lyon
    "13055": {2009: 2377, 2010: 2501, 2011: 2631, 2012: 2500, 2013: 2414, 2014: 2310},  # Marseille
    "33063": {2009: 2481, 2010: 2591, 2011: 2907, 2012: 3040, 2013: 2995, 2014: 3040},  # Bordeaux
    "31555": {2009: 2262, 2010: 2409, 2011: 2570, 2012: 2500, 2013: 2502, 2014: 2540},  # Toulouse
    "06088": {2009: 3265, 2010: 3500, 2011: 3773, 2012: 3740, 2013: 3614, 2014: 3560},  # Nice
    "44109": {2009: 2273, 2010: 2496, 2011: 2696, 2012: 2660, 2013: 2598, 2014: 2650},  # Nantes
    "34172": {2009: 2396, 2010: 2558, 2011: 2632, 2012: 2680, 2013: 2769, 2014: 2570},  # Montpellier
    "35238": {2009: 2079, 2010: 2267, 2011: 2333, 2012: 2460, 2013: 2404, 2014: 2430},  # Rennes
    "59350": {2009: 2675, 2010: 2902, 2011: 3197, 2012: 3130, 2013: 3139, 2014: 3010},  # Lille
    "38185": {2009: 2376, 2010: 2485, 2011: 2470, 2012: 2370, 2013: 2283, 2014: 2260},  # Grenoble
    "21231": {2009: 2064, 2010: 2190, 2011: 2190, 2012: 2140, 2013: 2124, 2014: 2120},  # Dijon
    "30189": {2010: 1867, 2011: 1972, 2012: 1750, 2013: 1652, 2014: 1550},              # Nîmes
    "63113": {2009: 1434, 2010: 1564, 2011: 1604, 2012: 1600, 2013: 1713, 2014: 1610},  # Clermont-Ferrand
    "83137": {2009: 2282, 2010: 2366, 2011: 2463, 2012: 2290, 2013: 2196, 2014: 2260},  # Toulon
    "51454": {2009: 1979, 2010: 2167, 2011: 2152, 2012: 2110, 2013: 2063, 2014: 2080},  # Reims
    "80021": {2010: 2162, 2011: 2404, 2012: 2310, 2013: 2163, 2014: 2340},              # Amiens
    "87085": {2009: 1276, 2010: 1226, 2011: 1248, 2012: 1320, 2013: 1295, 2014: 1150},  # Limoges
}
big = set(com[(com.population >= 20000) & com.niveau.eq("commune")].code)
base = p[(p.periode == "2014") & (p.nb_ventes >= 30) & (p.niveau.isin(["france", "region", "departement"]) | p.code.isin(big))]
rows = []
for r in base.itertuples():
    idb, prec = choix(r.niveau, r.code, r.type)
    s = ins.loc[idb]
    n = NOTAIRES.get(r.code) if r.type == "appartement" and r.niveau == "commune" else None
    if n:
        first = min(n)
        anc = {an: r.prix_m2_median * n[an] / n[2014] for an in n if an < 2014}
        for an, v in anc.items():
            rows.append((r.niveau, r.code, an, r.type, round(v), "notaires-de-france", "notaires"))
        for an in range(2000, first):
            if an in s.index and first in s.index:
                rows.append((r.niveau, r.code, an, r.type, round(anc[first] * s[an] / s[first]), idb, prec))
        continue
    for an in range(2000, 2014):
        if an in s.index and 2014 in s.index:
            rows.append((r.niveau, r.code, an, r.type, round(r.prix_m2_median * s[an] / s[2014]), idb, prec))
out = pd.DataFrame(rows, columns=["niveau", "code", "annee", "type", "prix_m2_estime", "indice", "precision"])
out.to_csv(f"{D}/prix_estimes.csv", sep=";", index=False)
print(len(out), out.precision.value_counts().to_dict())
