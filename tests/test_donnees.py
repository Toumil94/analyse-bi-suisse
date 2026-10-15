"""Contrôles de qualité du modèle : ils bloquent la publication si un test échoue."""
import csv
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"


def rows(name):
    with (DATA / name).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_cles_uniques():
    d = rows("fact_demande.csv")
    assert len({(r["date_key"], r["canton_id"], r["pays_id"]) for r in d}) == len(d)
    o = rows("fact_offre.csv")
    assert len({(r["date_key"], r["canton_id"]) for r in o}) == len(o)


def test_integrite_referentielle():
    dates = {r["date_key"] for r in rows("dim_date.csv")}
    cantons = {r["canton_id"] for r in rows("dim_canton.csv")}
    pays = {r["pays_id"] for r in rows("dim_pays.csv")}
    for r in rows("fact_demande.csv"):
        assert r["date_key"] in dates and r["canton_id"] in cantons and r["pays_id"] in pays
    for r in rows("fact_offre.csv"):
        assert r["date_key"] in dates and r["canton_id"] in cantons


def test_26_cantons():
    assert len(rows("dim_canton.csv")) == 26


def test_valeurs_positives_et_coherentes():
    for r in rows("fact_offre.csv"):
        assert int(r["nuitees_chambres"]) <= int(r["chambres"]) * 31
        assert int(r["lits"]) >= int(r["chambres"]) > 0


def test_totaux_coherents_avec_ofs():
    c = json.loads((DATA / "controles.json").read_text(encoding="utf-8"))
    # la somme des pays doit retrouver le total publié (écart médian < 0,5 %)
    assert c["somme_pays_vs_total_canton_ecart_pct"]["mediane"] < 0.5
    assert c["somme_cantons_vs_total_suisse_ecart_pct"]["mediane"] < 0.5
    # le taux d'occupation recalculé doit retrouver celui de l'OFS à 1 point près (médiane)
    assert c["taux_occupation_recalcule_vs_ofs_ecart_points"]["mediane"] < 1
