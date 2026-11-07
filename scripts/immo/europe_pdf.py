"""Télécharge des rapports officiels PDF et en extrait le texte (pages + tableaux) -> data/europe/raw/pdf/*.txt"""
import os, urllib.request, io, pdfplumber
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"}
R = "data/europe/raw/pdf"; os.makedirs(R, exist_ok=True)
P = {
 "berlin_imb_2024_2025": "https://www.berlin.de/gutachterausschuss/_assets/amarktinformationen/amarktanalyse/04-03-010-2400.pdf",
 "berlin_imb_2022_2023": "https://www.berlin.de/gutachterausschuss/_assets/amarktinformationen/amarktanalyse/04-03-010-2200.pdf",
 "berlin_imb_2021_2022": "https://www.berlin.de/gutachterausschuss/_assets/amarktinformationen/amarktanalyse/04-03-010-2100.pdf",
 "omi_ri2025_residenziale": "https://www.informazionefiscale.it/IMG/pdf/ri2025_residenziale20250520.pdf",
 "roma_mercato_immobiliare_2018": "https://www.comune.roma.it/web-resources/cms/documents/11_MercatoImmobiliare_2018DEF_CMRC.pdf",
}
for yy in range(5, 26):  # toutes les éditions du rapport du comité d'évaluation de Berlin
    P.setdefault(f"berlin_imb_code_{yy:02d}00", f"https://www.berlin.de/gutachterausschuss/_assets/amarktinformationen/amarktanalyse/04-03-010-{yy:02d}00.pdf")
for k, u in P.items():
    if os.path.exists(f"{R}/{k}.txt"): continue
    try:
        b = urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=180).read()
        out = []
        with pdfplumber.open(io.BytesIO(b)) as pdf:
            for i, pg in enumerate(pdf.pages, 1):
                out.append(f"\n===== page {i} =====\n" + (pg.extract_text() or ""))
        open(f"{R}/{k}.txt", "w").write("".join(out)); print("ok", k, len(b), len(out))
    except Exception as e:
        print("ERREUR", k, e)
