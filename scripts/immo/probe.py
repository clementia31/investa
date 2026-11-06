"""Sonde de sources (listes de répertoires, premiers octets) -> data/immo/_probe.txt"""
import urllib.request
U = ["https://data.cquest.org/dgfip_dvf/201904/", "https://data.cquest.org/dgfip_dvf/202110/",
     "https://data.cquest.org/dgfip_dvf/202504/", "https://data.cquest.org/dgfip_dvf/LISEZ_MOI.txt"]
GZ = ["https://data.cquest.org/dgfip_dvf/dvf-2014-2018.csv.gz"]
out = []
for u in U:
    try:
        b = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "investa-immo-data/1.0"}), timeout=60).read()
        out.append(f"### {u}\n{b[:6000].decode('utf-8', 'ignore')}\n")
    except Exception as e:
        out.append(f"### {u}\nERREUR {e}\n")
import zlib
for u in GZ:
    try:
        b = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "x", "Range": "bytes=0-200000"}), timeout=60).read()
        out.append(f"### {u}\n" + zlib.decompressobj(31).decompress(b)[:3000].decode("utf-8", "ignore"))
    except Exception as e:
        out.append(f"### {u}\nERREUR {e}")
open("data/immo/_probe.txt", "w").write("\n".join(out))
