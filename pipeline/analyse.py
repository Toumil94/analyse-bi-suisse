"""Analyse des données HESTA : chiffres clés (analyse/chiffres.json) et graphiques (docs/images/).

Les mêmes calculs sont reproduits par les mesures DAX du rapport Power BI : ce script
sert de référence pour la recette (les deux doivent donner les mêmes chiffres).
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
IMG = ROOT / "docs" / "images"
OUT = ROOT / "analyse"
GE = "25"

INK, SLATE, RULE, BLUE, RED, GREY = "#16191D", "#59626D", "#D6D9D3", "#2A78D6", "#D52B1E", "#B9BEC4"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": RULE, "axes.labelcolor": SLATE,
    "xtick.color": SLATE, "ytick.color": SLATE, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": "#ECEEEA", "grid.linewidth": 0.8, "axes.axisbelow": True,
    "figure.dpi": 150, "savefig.bbox": "tight", "axes.titleweight": "bold", "axes.titlesize": 12,
    "axes.titlelocation": "left", "axes.titlecolor": INK,
})


def load():
    d = pd.read_csv(DATA / "fact_demande.csv", dtype={"date_key": str, "canton_id": str, "pays_id": str})
    o = pd.read_csv(DATA / "fact_offre.csv", dtype={"date_key": str, "canton_id": str})
    c = pd.read_csv(DATA / "dim_canton.csv", dtype={"canton_id": str})
    p = pd.read_csv(DATA / "dim_pays.csv", dtype={"pays_id": str})
    for df in (d, o):
        df["annee"] = df["date_key"].str[:4].astype(int)
        df["mois"] = df["date_key"].str[4:6].astype(int)
    return d.merge(p, on="pays_id"), o.merge(c, on="canton_id"), c


def pct(x):
    return round(100 * float(x), 1)


def main() -> None:
    IMG.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(exist_ok=True)
    d, o, cantons = load()
    last = o["date_key"].max()
    ly, lm = int(last[:4]), int(last[4:6])
    full_year = ly - 1 if lm < 12 else ly          # dernière année complète
    mois_ytd = list(range(1, lm + 1))
    fr_mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    k = {"dernier_mois": f"{fr_mois[lm - 1]} {ly}", "derniere_annee_complete": full_year}

    # --- 1. Tendance : Suisse et Genève, base 100 en 2019 ---------------------------------
    an = d[d["annee"] <= full_year].groupby(["annee"])["nuitees"].sum()
    an_ge = d[(d["annee"] <= full_year) & (d["canton_id"] == GE)].groupby("annee")["nuitees"].sum()
    k["suisse_nuitees_annee"] = int(an[full_year])
    k["suisse_vs_2019"] = pct(an[full_year] / an[2019])
    k["geneve_nuitees_annee"] = int(an_ge[full_year])
    k["geneve_vs_2019"] = pct(an_ge[full_year] / an_ge[2019])
    k["geneve_part_suisse"] = pct(an_ge[full_year] / an[full_year])
    k["geneve_creux_2020_vs_2019"] = pct(an_ge[2020] / an_ge[2019])
    k["suisse_creux_2020_vs_2019"] = pct(an[2020] / an[2019])

    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.plot(an.index, 100 * an / an[2019], color=GREY, lw=2, label="Suisse")
    ax.plot(an_ge.index, 100 * an_ge / an_ge[2019], color=RED, lw=2.4, label="Genève")
    ax.axhline(100, color=SLATE, lw=0.8, ls=(0, (3, 3)))
    ax.text(an.index[-1] + 0.3, 100 * an.iloc[-1] / an[2019], "Suisse", color=SLATE, va="center", fontsize=9)
    ax.text(an_ge.index[-1] + 0.3, 100 * an_ge.iloc[-1] / an_ge[2019], "Genève", color=RED, va="center", fontsize=9, fontweight="bold")
    ax.set_title("Nuitées hôtelières, indice 100 = 2019")
    ax.set_xlim(an.index[0], an.index[-1] + 2)
    ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(5))
    ax.xaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%d"))
    ax.set_ylabel("")
    fig.savefig(IMG / "01_tendance.png")
    plt.close(fig)

    # --- 2. Reprise par canton : nuitées de la dernière année complète vs 2019 ----------------
    by = d[d["annee"].isin([2019, full_year])].groupby(["canton_id", "annee"])["nuitees"].sum().unstack()
    by = by.merge(cantons, left_index=True, right_on="canton_id")
    by["niveau"] = 100 * by[full_year] / by[2019]
    by = by.sort_values("niveau")
    k["rang_geneve_reprise"] = int(by["niveau"].rank(ascending=False)[by["canton_id"] == GE].iloc[0])
    k["meilleure_reprise"] = {"canton": by.iloc[-1]["canton"], "niveau": round(by.iloc[-1]["niveau"], 1)}
    k["plus_faible_reprise"] = {"canton": by.iloc[0]["canton"], "niveau": round(by.iloc[0]["niveau"], 1)}

    fig, ax = plt.subplots(figsize=(8, 6.2))
    colors = [RED if c == GE else GREY for c in by["canton_id"]]
    ax.barh(by["abreviation"], by["niveau"] - 100, left=100, color=colors, height=0.7)
    ax.axvline(100, color=INK, lw=1)
    for i, (v, c) in enumerate(zip(by["niveau"], by["canton_id"])):
        ax.text(v + (0.5 if v >= 100 else -0.5), i, f"{v:.0f}", va="center", ha="left" if v >= 100 else "right",
                fontsize=8, color=RED if c == GE else SLATE, fontweight="bold" if c == GE else "normal")
    ax.set_title(f"Nuitées {full_year} par canton, indice 100 = 2019")
    ax.set_xlim(min(by["niveau"].min() - 4, 96), by["niveau"].max() + 4)
    ax.grid(axis="y", visible=False)
    fig.savefig(IMG / "02_reprise_cantons.png")
    plt.close(fig)

    # --- 3. Genève : marchés de provenance ------------------------------------------------
    ge = d[d["canton_id"] == GE]
    m = ge[ge["annee"].isin([2019, full_year])].groupby(["marche", "annee"])["nuitees"].sum().unstack().fillna(0)
    m["part"] = m[full_year] / m[full_year].sum()
    m["niveau"] = 100 * m[full_year] / m[2019].replace(0, float("nan"))
    top = m.sort_values(full_year, ascending=False).head(12)
    k["geneve_top_marches"] = [
        {"marche": i, "nuitees": int(r[full_year]), "part": pct(r["part"]), "vs_2019": round(r["niveau"], 1)}
        for i, r in top.iterrows()
    ]
    etr = ge[ge["annee"] == full_year]
    k["geneve_part_etrangers"] = pct(etr[etr["continent"] != "Suisse"]["nuitees"].sum() / etr["nuitees"].sum())
    ch = d[d["annee"] == full_year]
    k["suisse_part_etrangers"] = pct(ch[ch["continent"] != "Suisse"]["nuitees"].sum() / ch["nuitees"].sum())

    fig, ax = plt.subplots(figsize=(8, 4.6))
    t = top.iloc[::-1]
    ax.barh(t.index, t["part"] * 100, color=BLUE, height=0.65)
    for i, (part, niv) in enumerate(zip(t["part"], t["niveau"])):
        lab = f"{100 * part:.1f} %   ({niv:.0f} vs 2019)" if niv == niv else f"{100 * part:.1f} %"
        ax.text(100 * part + 0.3, i, lab, va="center", fontsize=8, color=SLATE)
    ax.set_title(f"Genève : part des nuitées {full_year} par marché (et niveau vs 2019)")
    ax.set_xlim(0, top["part"].max() * 100 * 1.45)
    ax.grid(axis="y", visible=False)
    fig.savefig(IMG / "03_marches_geneve.png")
    plt.close(fig)

    # --- 4. Saisonnalité de l'occupation : Genève vs Suisse --------------------------------
    rec = o[o["annee"].between(full_year - 2, full_year)]
    def occ(df):
        g = df.groupby("mois")[["nuitees_chambres", "capacite_chambres_jours"]].sum()
        return 100 * g["nuitees_chambres"] / g["capacite_chambres_jours"]
    occ_ge, occ_ch = occ(rec[rec["canton_id"] == GE]), occ(rec)
    k["geneve_occupation_moyenne"] = round(float(
        rec[rec["canton_id"] == GE]["nuitees_chambres"].sum() / rec[rec["canton_id"] == GE]["capacite_chambres_jours"].sum() * 100), 1)
    k["suisse_occupation_moyenne"] = round(float(rec["nuitees_chambres"].sum() / rec["capacite_chambres_jours"].sum() * 100), 1)
    k["geneve_mois_plus_creux"] = {"mois": fr_mois[int(occ_ge.idxmin()) - 1], "taux": round(float(occ_ge.min()), 1)}
    k["geneve_mois_plus_plein"] = {"mois": fr_mois[int(occ_ge.idxmax()) - 1], "taux": round(float(occ_ge.max()), 1)}
    k["periode_saisonnalite"] = f"{full_year - 2}-{full_year}"

    fig, ax = plt.subplots(figsize=(8, 3.6))
    x = list(range(1, 13))
    ax.plot(x, occ_ch.reindex(x), color=GREY, lw=2, marker="o", ms=4)
    ax.plot(x, occ_ge.reindex(x), color=RED, lw=2.4, marker="o", ms=4)
    ax.text(12.25, occ_ch[12], "Suisse", color=SLATE, va="center", fontsize=9)
    ax.text(12.25, occ_ge[12], "Genève", color=RED, va="center", fontsize=9, fontweight="bold")
    ax.set_xticks(x, ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."])
    ax.set_xlim(0.6, 13.2)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f} %")
    ax.set_title(f"Taux d'occupation des chambres par mois, moyenne {full_year - 2}-{full_year}")
    fig.savefig(IMG / "04_saisonnalite.png")
    plt.close(fig)

    # --- 5. Durée de séjour et année en cours ------------------------------------------------
    y = d[d["annee"] == full_year]
    k["geneve_duree_sejour"] = round(float(y[y["canton_id"] == GE]["nuitees"].sum() / y[y["canton_id"] == GE]["arrivees"].sum()), 2)
    k["suisse_duree_sejour"] = round(float(y["nuitees"].sum() / y["arrivees"].sum()), 2)
    cur = d[(d["annee"] == ly) & d["mois"].isin(mois_ytd)]
    prev = d[(d["annee"] == ly - 1) & d["mois"].isin(mois_ytd)]
    k["annee_en_cours"] = {
        "periode": f"janvier-{fr_mois[lm - 1]} {ly}",
        "suisse_vs_a1": pct(cur["nuitees"].sum() / prev["nuitees"].sum() - 1),
        "geneve_vs_a1": pct(cur[cur["canton_id"] == GE]["nuitees"].sum() / prev[prev["canton_id"] == GE]["nuitees"].sum() - 1),
    }

    (OUT / "chiffres.json").write_text(json.dumps(k, ensure_ascii=False, indent=2))
    print(json.dumps(k, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
