"""Construit le modèle en étoile du tourisme hôtelier suisse à partir de l'OFS.

Sources (API PX-Web de l'Office fédéral de la statistique, statistique HESTA) :
  px-x-1003020000_102  arrivées et nuitées par année, mois, canton et pays de provenance
  px-x-1003020000_202  offre et demande par année, mois et canton (établissements, chambres, lits...)

Sorties dans data/ :
  fact_demande.csv   une ligne par mois x canton x pays de provenance
  fact_offre.csv     une ligne par mois x canton
  dim_date.csv, dim_canton.csv, dim_pays.csv
  controles.json     résultats des contrôles de qualité (repris dans la recette)
"""
from __future__ import annotations

import calendar
import csv
import json
import time
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
API = "https://www.pxweb.bfs.admin.ch/api/v1/fr/{t}/{t}.px"
T_DEMANDE = "px-x-1003020000_102"
T_OFFRE = "px-x-1003020000_202"
UA = {"User-Agent": "analyse-bi-suisse (github.com/Toumil94/analyse-bi-suisse)", "Content-Type": "application/json"}

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]

# Cantons : abréviation, grande région de l'OFS, langue principale
CANTONS = {
    "1": ("ZH", "Zurich", "allemand"), "2": ("BE", "Espace Mittelland", "allemand"), "3": ("LU", "Suisse centrale", "allemand"),
    "4": ("UR", "Suisse centrale", "allemand"), "5": ("SZ", "Suisse centrale", "allemand"), "6": ("OW", "Suisse centrale", "allemand"),
    "7": ("NW", "Suisse centrale", "allemand"), "8": ("GL", "Suisse orientale", "allemand"), "9": ("ZG", "Suisse centrale", "allemand"),
    "10": ("FR", "Espace Mittelland", "français"), "11": ("SO", "Espace Mittelland", "allemand"), "12": ("BS", "Suisse du Nord-Ouest", "allemand"),
    "13": ("BL", "Suisse du Nord-Ouest", "allemand"), "14": ("SH", "Suisse orientale", "allemand"), "15": ("AR", "Suisse orientale", "allemand"),
    "16": ("AI", "Suisse orientale", "allemand"), "17": ("SG", "Suisse orientale", "allemand"), "18": ("GR", "Suisse orientale", "allemand"),
    "19": ("AG", "Suisse du Nord-Ouest", "allemand"), "20": ("TG", "Suisse orientale", "allemand"), "21": ("TI", "Tessin", "italien"),
    "22": ("VD", "Région lémanique", "français"), "23": ("VS", "Région lémanique", "français"), "24": ("NE", "Espace Mittelland", "français"),
    "25": ("GE", "Région lémanique", "français"), "26": ("JU", "Espace Mittelland", "français"),
}

# La nomenclature des pays a changé au fil du temps (agrégats remplacés par des pays détaillés).
# On publie chaque catégorie telle quelle et on ajoute un « marché harmonisé » stable sur toute la période.
MARCHE = {
    "10": "Pays baltes", "85": "Pays baltes", "86": "Pays baltes", "87": "Pays baltes",
    "73": "Pays du Golfe", "60": "Pays du Golfe", "68": "Pays du Golfe", "69": "Pays du Golfe",
    "81": "Pays du Golfe", "88": "Pays du Golfe", "89": "Pays du Golfe",
    "71": "Océanie", "70": "Océanie", "79": "Océanie",
    "90": "Serbie et Monténégro", "98": "Serbie et Monténégro",
    "47": "Amérique centrale et Caraïbes", "49": "Amérique centrale et Caraïbes",
}
CONTINENT = {
    "1": "Suisse",
    **{k: "Europe" for k in "10 11 13 14 15 16 17 18 19 20 21 22 23 24 25 26 28 29 31 32 33 34 35 36 37 38 39 85 86 87 90 91 92 93 94 95 96 97 98".split()},
    **{k: "Amériques" for k in "40 41 42 43 44 45 47 48 49".split()},
    **{k: "Afrique" for k in "51 52 53 54".split()},
    **{k: "Asie" for k in "61 62 64 66 72 74 75 76 77 78 80 82 83 84".split()},
    **{k: "Pays du Golfe" for k in "60 68 69 73 81 88 89".split()},
    **{k: "Océanie" for k in "70 71 79".split()},
}


def meta(table: str) -> dict:
    with urllib.request.urlopen(urllib.request.Request(API.format(t=table), headers=UA), timeout=60) as r:
        return {v["code"]: v for v in json.load(r)["variables"]}


def query(table: str, selection: dict[str, list[str]]) -> list[tuple[list[str], list[str]]]:
    body = {
        "query": [{"code": c, "selection": {"filter": "item", "values": v}} for c, v in selection.items()],
        "response": {"format": "json"},
    }
    req = urllib.request.Request(API.format(t=table), data=json.dumps(body).encode(), headers=UA, method="POST")
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                j = json.load(r)
            time.sleep(1.2)  # l'API limite le nombre d'appels par période
            return [(row["key"], row["values"]) for row in j["data"]]
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                time.sleep(10 * (attempt + 1))
                continue
            raise
    raise RuntimeError(f"API indisponible pour {table}")


def num(s: str) -> float | None:
    s = (s or "").strip()
    if s in ("", ".", "..", "...", "-", "…"):
        return None  # valeur absente ou confidentielle
    return float(s)


def write_csv(name: str, header: list[str], rows: list) -> None:
    with (DATA / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"{name} : {len(rows):,} lignes".replace(",", "'"))


def main() -> None:
    DATA.mkdir(exist_ok=True)
    md = meta(T_DEMANDE)
    mo = meta(T_OFFRE)
    years = md["Jahr"]["values"]
    months = [m for m in md["Monat"]["values"] if m != "YYYY"]
    cantons = md["Kanton"]["values"]          # inclut 8100 = Suisse, gardé pour les contrôles
    pays = md["Herkunftsland"]["values"]      # inclut 00 = total, gardé pour les contrôles
    pays_txt = dict(zip(pays, md["Herkunftsland"]["valueTexts"]))
    ind_offre = dict(zip(mo["Indikator"]["values"], mo["Indikator"]["valueTexts"]))

    demande: dict[tuple, list] = {}
    offre: dict[tuple, dict] = {}
    for y in years:
        for key, vals in query(T_DEMANDE, {"Jahr": [y], "Monat": months, "Kanton": cantons, "Herkunftsland": pays, "Indikator": ["1", "2"]}):
            yy, m, k, p, ind = key
            v = num(vals[0])
            if v is None:
                continue
            demande.setdefault((yy, m, k, p), [None, None])[int(ind) - 1] = v
        for key, vals in query(T_OFFRE, {"Jahr": [y], "Monat": months, "Kanton": cantons, "Indikator": list(ind_offre)}):
            yy, m, k, ind = key
            v = num(vals[0])
            if v is not None:
                offre.setdefault((yy, m, k), {})[ind] = v
        print(f"{y} : {len(demande):,} cellules de demande".replace(",", "'"))

    # ----- faits -----
    def dkey(y, m):
        return f"{y}{int(m):02d}01"

    fact_d = [
        [dkey(y, m), k, p, int(a or 0), int(n or 0)]
        for (y, m, k, p), (a, n) in sorted(demande.items())
        if k != "8100" and p != "00" and (a or n)
    ]
    fact_o = []
    for (y, m, k), d in sorted(offre.items()):
        if k == "8100" or not d.get("2"):
            continue  # mois sans établissement ouvert, ou total suisse
        # L'OFS calcule le taux d'occupation sur les jours d'ouverture effectifs, que la table ne publie pas.
        # On reconstitue donc la capacité exacte (chambres-jours et lits-jours offerts) à partir du taux publié :
        # ainsi, le taux agrégé dans Power BI (somme des nuitées / somme des capacités) retrouve celui de l'OFS.
        cap_ch = round(d["6"] * 100 / d["7"]) if d.get("6") and d.get("7") else None
        cap_li = round(d["5"] * 100 / d["8"]) if d.get("5") and d.get("8") else None
        fact_o.append([dkey(y, m), k, int(d.get("1") or 0), int(d.get("2") or 0), int(d.get("3") or 0),
                       int(d.get("4") or 0), int(d.get("5") or 0), int(d.get("6") or 0),
                       cap_ch, cap_li, d.get("7"), d.get("8")])
    periods = sorted({r[0] for r in fact_o} | {r[0] for r in fact_d})
    write_csv("fact_demande.csv", ["date_key", "canton_id", "pays_id", "arrivees", "nuitees"], fact_d)
    write_csv("fact_offre.csv", ["date_key", "canton_id", "etablissements", "chambres", "lits", "arrivees",
                                 "nuitees", "nuitees_chambres", "capacite_chambres_jours", "capacite_lits_jours",
                                 "taux_occ_chambres_ofs", "taux_occ_lits_ofs"], fact_o)

    # ----- dimensions -----
    dim_date = []
    for dk in periods:
        y, m = int(dk[:4]), int(dk[4:6])
        saison = "Hiver" if m in (11, 12, 1, 2, 3, 4) else "Été"
        annee_saison = f"Hiver {y}/{(y + 1) % 100:02d}" if m >= 11 else (f"Hiver {y - 1}/{y % 100:02d}" if m <= 4 else f"Été {y}")
        periode = "Avant COVID" if (y, m) < (2020, 3) else ("COVID" if (y, m) <= (2021, 12) else "Après COVID")
        dim_date.append([dk, date(y, m, 1).isoformat(), y, m, MOIS[m - 1], f"T{(m - 1) // 3 + 1}", saison, annee_saison,
                         calendar.monthrange(y, m)[1], periode])
    write_csv("dim_date.csv", ["date_key", "date", "annee", "mois", "mois_nom", "trimestre", "saison", "saison_touristique",
                               "jours_dans_mois", "periode_covid"], dim_date)
    write_csv("dim_canton.csv", ["canton_id", "canton", "abreviation", "grande_region", "langue"],
              [[k, t, *CANTONS[k]] for k, t in zip(md["Kanton"]["values"], md["Kanton"]["valueTexts"]) if k != "8100"])
    write_csv("dim_pays.csv", ["pays_id", "pays", "marche", "continent"],
              [[p, pays_txt[p], MARCHE.get(p, pays_txt[p]), CONTINENT.get(p, "Autres")] for p in pays if p != "00"])

    # ----- contrôles de qualité -----
    def total(y, m, k, p, i):
        v = demande.get((y, m, k, p))
        return v[i] if v and v[i] is not None else None

    ecarts_pays, ecarts_canton = [], []
    for (y, m, k, p), _ in demande.items():
        if p == "00" and k != "8100":
            ref = total(y, m, k, "00", 1)
            s = sum((demande.get((y, m, k, q), [0, 0])[1] or 0) for q in pays if q != "00")
            if ref:
                ecarts_pays.append(abs(s - ref) / ref)
        if p == "00" and k == "8100":
            ref = total(y, m, "8100", "00", 1)
            s = sum((demande.get((y, m, c, "00"), [0, 0])[1] or 0) for c in cantons if c != "8100")
            if ref:
                ecarts_canton.append(abs(s - ref) / ref)
    occ = []
    for (y, m, k), d in offre.items():
        if k != "8100" and d.get("2") and d.get("6") and d.get("7"):
            jours = calendar.monthrange(int(y), int(m))[1]
            occ.append(abs(100 * d["6"] / (d["2"] * jours) - d["7"]))

    def stats(xs, pct=True):
        xs = sorted(xs)
        if not xs:
            return {}
        f = (lambda v: round(100 * v, 3)) if pct else (lambda v: round(v, 2))
        return {"n": len(xs), "moyenne": f(sum(xs) / len(xs)), "mediane": f(xs[len(xs) // 2]), "max": f(xs[-1])}

    controles = {
        "date_extraction": date.today().isoformat(),
        "periode": [periods[0], periods[-1]],
        "lignes": {"fact_demande": len(fact_d), "fact_offre": len(fact_o)},
        "somme_pays_vs_total_canton_ecart_pct": stats(ecarts_pays),
        "somme_cantons_vs_total_suisse_ecart_pct": stats(ecarts_canton),
        # taux « naïf » (chambres x jours du mois) comparé au taux OFS (jours d'ouverture) :
        # l'écart justifie la reconstitution de la capacité exacte dans fact_offre.
        "taux_occupation_naif_vs_ofs_ecart_points": stats(occ, pct=False),
    }
    (DATA / "controles.json").write_text(json.dumps(controles, ensure_ascii=False, indent=2))
    print(json.dumps(controles, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
