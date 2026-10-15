"""Explore les tables HESTA de l'OFS (API PX-Web) : enregistre leurs métadonnées."""
import json, sys, urllib.request
from pathlib import Path

BASE = "https://www.pxweb.bfs.admin.ch/api/v1/fr/{t}/{t}.px"
OUT = Path("probe"); OUT.mkdir(exist_ok=True)
summary = []
for t in sys.argv[1:]:
    try:
        with urllib.request.urlopen(urllib.request.Request(BASE.format(t=t), headers={"User-Agent": "analyse-bi-suisse"}), timeout=60) as r:
            meta = json.load(r)
        (OUT / f"{t}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        vars_ = [(v["code"], v["text"], len(v["values"]), v["valueTexts"][:4]) for v in meta["variables"]]
        summary.append(f"{t} | {meta.get('title')} | " + " ; ".join(f"{c} ({txt}, {n}: {ex})" for c, txt, n, ex in vars_))
    except Exception as e:
        summary.append(f"{t} | ERREUR {e}")
(OUT / "summary.txt").write_text("\n".join(summary))
print("\n".join(summary))
