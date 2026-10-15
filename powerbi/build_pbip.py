"""Génère le projet Power BI (format PBIP) : modèle sémantique en TMDL et rapport en PBIR.

Le rapport est décrit ici en Python (« report as code ») : le modèle, les mesures DAX,
les pages et les visuels sont versionnés comme du code, relus en revue et régénérés
à l'identique. Power BI Desktop ouvre ensuite Tourisme-Suisse.pbip directement.

    python powerbi/build_pbip.py
"""
from __future__ import annotations

import json
import re
import shutil
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAME = "Tourisme-Suisse"
SM = HERE / f"{NAME}.SemanticModel"
RP = HERE / f"{NAME}.Report"
NS = uuid.UUID("6f1d3c2a-4b5e-4f60-9a7b-8c9d0e1f2a3b")
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric"
M = "_Mesures"


def guid(*parts: str) -> str:
    """Identifiant stable : le même objet garde le même lineageTag d'une génération à l'autre."""
    return str(uuid.uuid5(NS, "/".join(parts)))


def hexid(*parts: str) -> str:
    return guid(*parts).replace("-", "")[:20]


def q(name: str) -> str:
    """Nom TMDL : entre apostrophes dès qu'il contient autre chose que lettres, chiffres, _."""
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) and name.lower() not in {"date", "table", "column", "measure"}:
        return name
    return "'" + name.replace("'", "''") + "'"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, obj) -> None:
    write(path, json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def indent(text: str, tabs: int) -> str:
    return "\n".join(("\t" * tabs + line) if line.strip() else "" for line in text.strip("\n").splitlines())


# =============================================================================
# 1. Mesures DAX (source unique : elles sont aussi exportées dans mesures.dax)
# =============================================================================
INT, DEC2, DEC1, PCT1, PCT0 = "#,0", "0.00", "+0.0;-0.0;0.0", "0.0%", "0%"
EVOL = "+0.0%;-0.0%;0.0%"

MEASURES: list[tuple[str, str, str | None, str, str]] = [
    # (dossier, nom, format, expression, description)
    ("Volumes", "Nuitées", INT, "SUM ( fact_demande[nuitees] )", "Nombre de nuits passées à l'hôtel."),
    ("Volumes", "Arrivées", INT, "SUM ( fact_demande[arrivees] )", "Nombre de clients arrivés."),
    ("Volumes", "Durée moyenne de séjour", DEC2, "DIVIDE ( [Nuitées], [Arrivées] )", "Nuitées par arrivée, en nuits."),
    ("Volumes", "Nuitées étrangères", INT, 'CALCULATE ( [Nuitées], dim_pays[continent] <> "Suisse" )', "Nuitées des clients domiciliés hors de Suisse."),
    ("Volumes", "Part des visiteurs étrangers", PCT1, "DIVIDE ( [Nuitées étrangères], [Nuitées] )", "Part des nuitées faites par des clients domiciliés à l'étranger."),
    ("Occupation", "Taux d'occupation des chambres", PCT1,
     "DIVIDE ( SUM ( fact_offre[nuitees_chambres] ), SUM ( fact_offre[capacite_chambres_jours] ) )",
     "Recalculé à partir de ses composantes (jamais une moyenne de taux) : retrouve le taux publié par l'OFS."),
    ("Occupation", "Taux d'occupation des lits", PCT1,
     "DIVIDE ( SUM ( fact_offre[nuitees] ), SUM ( fact_offre[capacite_lits_jours] ) )", "Nuitées rapportées aux lits-jours offerts."),
    ("Occupation", "Taux d'occupation des chambres (Suisse)", PCT1,
     "CALCULATE ( [Taux d'occupation des chambres], REMOVEFILTERS ( dim_canton ) )", "Même taux, tous cantons confondus, pour comparer."),
    ("Occupation", "Chambres offertes (moyenne mensuelle)", INT,
     "AVERAGEX ( VALUES ( Calendrier[Année-mois] ), CALCULATE ( SUM ( fact_offre[chambres] ) ) )", "Nombre moyen de chambres offertes par mois."),
    ("Occupation", "Établissements ouverts (moyenne mensuelle)", INT,
     "AVERAGEX ( VALUES ( Calendrier[Année-mois] ), CALCULATE ( SUM ( fact_offre[etablissements] ) ) )", "Nombre moyen d'hôtels ouverts par mois."),
    ("Occupation", "Écart d'occupation vs Suisse (points)", DEC1,
     "( [Taux d'occupation des chambres] - [Taux d'occupation des chambres (Suisse)] ) * 100", "En points de pourcentage."),
    ("Temps", "Nuitées A-1", INT, "CALCULATE ( [Nuitées], SAMEPERIODLASTYEAR ( Calendrier[Date] ) )", "Mêmes jours, un an plus tôt."),
    ("Temps", "Évolution vs A-1", EVOL, "DIVIDE ( [Nuitées] - [Nuitées A-1], [Nuitées A-1] )", "Variation par rapport à la même période de l'année précédente."),
    ("Temps", "Nuitées cumul annuel", INT, "TOTALYTD ( [Nuitées], Calendrier[Date] )", "Depuis le 1er janvier."),
    ("Temps", "Nuitées 12 mois glissants", INT, """
VAR Fin = MAX ( Calendrier[Date] )
RETURN
    IF (
        Fin >= DATE ( 2005, 12, 31 ),
        CALCULATE ( [Nuitées], DATESINPERIOD ( Calendrier[Date], Fin, -12, MONTH ) )
    )""", "Somme des 12 derniers mois : lisse la saisonnalité (vide avant décembre 2005)."),
    ("Temps", "Nuitées même période 2019", INT, """
VAR MoisSelectionnes = VALUES ( Calendrier[Mois] )
RETURN
    CALCULATE (
        [Nuitées],
        REMOVEFILTERS ( Calendrier ),
        Calendrier[Année] = 2019,
        TREATAS ( MoisSelectionnes, Calendrier[Mois] )
    )""", "Mêmes mois de 2019, dernière année avant le COVID."),
    ("Temps", "Niveau vs 2019", PCT0, "DIVIDE ( [Nuitées], [Nuitées même période 2019] )", "100 % = niveau d'avant crise retrouvé."),
    ("Parts", "Part de marché du canton", PCT1, "DIVIDE ( [Nuitées], CALCULATE ( [Nuitées], REMOVEFILTERS ( dim_canton ) ) )", "Part des nuitées suisses."),
    ("Parts", "Part du marché de provenance", PCT1, "DIVIDE ( [Nuitées], CALCULATE ( [Nuitées], REMOVEFILTERS ( dim_pays ) ) )", "Part des nuitées du canton."),
    ("Parts", "Rang du canton", "0", """
IF (
    HASONEVALUE ( dim_canton[canton] ),
    RANKX ( ALL ( dim_canton[canton] ), [Nuitées], , DESC, DENSE )
)""", "Classement par nuitées."),
    ("Parts", "Contribution à la croissance", EVOL, """
DIVIDE (
    [Nuitées] - [Nuitées A-1],
    CALCULATE ( [Nuitées A-1], REMOVEFILTERS ( dim_pays ) )
)""", "Points de croissance apportés par un marché."),
    ("Affichage", "Titre période", None, """
VAR Debut = CALCULATE ( MIN ( fact_offre[date] ), ALLSELECTED ( Calendrier ) )
VAR Fin = CALCULATE ( MAX ( fact_offre[date] ), ALLSELECTED ( Calendrier ) )
RETURN
    SELECTEDVALUE ( dim_canton[canton], "Suisse" ) & " · de " & FORMAT ( Debut, "mmmm yyyy" ) & " à " & FORMAT ( Fin, "mmmm yyyy" )""",
     "Sous-titre dynamique des pages."),
    ("Affichage", "Dernier mois disponible", None,
     "\"Données OFS jusqu'à \" & FORMAT ( CALCULATE ( MAX ( fact_offre[date] ), REMOVEFILTERS () ), \"mmmm yyyy\" )", "Fraîcheur des données."),
    ("Affichage", "Couleur canton", None,
     'IF ( SELECTEDVALUE ( dim_canton[canton] ) = "Genève", "#D52B1E", "#B9BEC4" )', "Met Genève en rouge dans les classements."),
]

CALENDAR_SOURCE = "CALENDAR ( DATE ( 2005, 1, 1 ), EOMONTH ( MAX ( fact_offre[date] ), 0 ) )"
CALENDAR_COLUMNS = [
    # (nom, type, format, expression, colonne de tri)
    ("Année", "int64", "0", "YEAR ( [Date] )", None),
    ("Mois", "int64", "0", "MONTH ( [Date] )", None),
    ("Mois nom", "string", None, 'FORMAT ( [Date], "mmm" )', "Mois"),
    ("Mois début", "dateTime", "mmm yyyy", "DATE ( YEAR ( [Date] ), MONTH ( [Date] ), 1 )", None),
    ("Année-mois", "string", None, 'FORMAT ( [Date], "yyyy-mm" )', None),
    ("Trimestre", "string", None, '"T" & QUARTER ( [Date] )', None),
    ("Saison", "string", None, 'IF ( MONTH ( [Date] ) IN { 11, 12, 1, 2, 3, 4 }, "Hiver", "Été" )', None),
    ("Période COVID", "string", None, """
SWITCH (
    TRUE (),
    [Date] < DATE ( 2020, 3, 1 ), "1. Avant COVID",
    [Date] <= DATE ( 2021, 12, 31 ), "2. COVID",
    "3. Après COVID"
)""", None),
]


def export_dax() -> None:
    out = [
        "// =============================================================================",
        "// Mesures DAX du rapport « Tourisme hôtelier en Suisse »",
        "// Fichier généré par build_pbip.py : elles sont déjà dans Tourisme-Suisse.pbip.",
        "// =============================================================================",
        "",
        "// ----- Table calendrier (table calculée, marquée comme table de dates) -----",
        "// Les faits sont mensuels (au 1er du mois) : un calendrier journalier continu est",
        "// nécessaire pour que les fonctions d'intelligence temporelle fonctionnent.",
        "",
        f"Calendrier = {CALENDAR_SOURCE}",
    ]
    for n, _, _, e, _ in CALENDAR_COLUMNS:
        out.append(f"Calendrier[{n}] = {e.strip()}")
    folder = None
    for f, n, fmt, e, desc in MEASURES:
        if f != folder:
            out += ["", f"// ----- {f} " + "-" * (70 - len(f))]
            folder = f
        out += ["", f"// {desc}" + (f"  (format : {fmt})" if fmt else ""), f"{n} = {e.strip()}"]
    write(HERE / "mesures.dax", "\n".join(out) + "\n")


# =============================================================================
# 2. Modèle sémantique (TMDL)
# =============================================================================
def m_query(file: str) -> str:
    text = (HERE / "power-query" / file).read_text(encoding="utf-8")
    return "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("//")).strip()


def column(table: str, name: str, dtype: str, *, hidden=False, fmt=None, summarize="none",
           expression=None, source=None, sort_by=None, key=False, inferred=False) -> str:
    head = f"\tcolumn {q(name)}" + (f" = {expression.strip()}" if expression and "\n" not in expression.strip() else "")
    lines = [head]
    if expression and "\n" in expression.strip():
        lines = [f"\tcolumn {q(name)} =", indent(expression, 3)]
    lines.append(f"\t\tdataType: {dtype}")
    if key:
        lines.append("\t\tisKey")
    if hidden:
        lines.append("\t\tisHidden")
    if hidden and table.startswith("fact_"):
        lines.append("\t\tisAvailableInMdx: false")
    if fmt:
        lines.append(f"\t\tformatString: {fmt}")
    lines.append(f"\t\tlineageTag: {guid(table, name)}")
    lines.append(f"\t\tsummarizeBy: {summarize}")
    if inferred:
        lines.append("\t\tisNameInferred")
    if source:
        lines.append(f"\t\tsourceColumn: {source}")
    if sort_by:
        lines.append(f"\t\tsortByColumn: {q(sort_by)}")
    lines.append("")
    lines.append("\t\tannotation SummarizationSetBy = Automatic")
    if dtype == "dateTime":
        lines.append("")
        lines.append("\t\tannotation UnderlyingDateTimeDataType = Date")
    return "\n".join(lines) + "\n"


def m_table(name: str, cols: list[tuple], file: str, description: str) -> str:
    out = [f"/// {description}", f"table {name}", f"\tlineageTag: {guid(name)}", ""]
    for c in cols:
        n, dtype = c[0], c[1]
        opts = c[2] if len(c) > 2 else {}
        out.append(column(name, n, dtype, source=n, **opts))
    out += [f"\tpartition {name} = m", "\t\tmode: import", "\t\tsource =", indent(m_query(file), 4), "",
            "\tannotation PBI_ResultType = Table", ""]
    return "\n".join(out)


def build_model() -> None:
    if SM.exists():
        shutil.rmtree(SM)
    d = SM / "definition"
    hid = {"hidden": True}
    sm = {"summarize": "sum", "fmt": "#,0"}

    write(d / "database.tmdl", "database\n\tcompatibilityLevel: 1601\n\n")
    tables = ["Calendrier", "fact_demande", "fact_offre", "dim_canton", "dim_pays", M]
    write(d / "model.tmdl", "\n".join([
        "model Model",
        "\tculture: fr-FR",
        "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
        "\tdiscourageImplicitMeasures",
        "\tsourceQueryCulture: fr-CH",
        "\tdataAccessOptions",
        "\t\tlegacyRedirects",
        "\t\treturnErrorValuesAsNull",
        "",
        "annotation __PBI_TimeIntelligenceEnabled = 0",
        "",
        'annotation PBI_QueryOrder = ["BaseUrl","fact_demande","fact_offre","dim_canton","dim_pays"]',
        "",
        *[f"ref table {q(t)}" for t in tables],
        "",
        "ref cultureInfo fr-FR",
        "",
    ]))
    write(d / "cultures" / "fr-FR.tmdl", "cultureInfo fr-FR\n\n")

    base = (HERE / "power-query" / "00_BaseUrl.m").read_text(encoding="utf-8")
    base = [l for l in base.splitlines() if l.strip() and not l.lstrip().startswith("//")][0]
    url, meta = base.split(" meta ", 1)
    write(d / "expressions.tmdl", "\n".join([
        "/// D'où viennent les données : GitHub par défaut (mises à jour chaque mois par GitHub Actions).",
        f"expression BaseUrl = {url.strip()} meta {meta.strip()}",
        f"\tlineageTag: {guid('BaseUrl')}",
        "",
        "\tannotation PBI_ResultType = Text",
        "",
    ]))

    write(d / "tables" / "fact_demande.tmdl", m_table("fact_demande", [
        ("canton_id", "string", hid), ("pays_id", "string", hid),
        ("arrivees", "int64", {**sm, "hidden": True}), ("nuitees", "int64", {**sm, "hidden": True}),
        ("date", "dateTime", {"hidden": True, "fmt": "Short Date"}),
    ], "fact_demande.m", "Demande : arrivées et nuitées par mois, canton et pays de provenance."))

    offre_num = ["etablissements", "chambres", "lits", "arrivees", "nuitees", "nuitees_chambres",
                 "capacite_chambres_jours", "capacite_lits_jours"]
    write(d / "tables" / "fact_offre.tmdl", m_table("fact_offre", [
        ("canton_id", "string", hid),
        *[(c, "int64", {**sm, "hidden": True}) for c in offre_num],
        ("taux_occ_chambres_ofs", "decimal", {"hidden": True}), ("taux_occ_lits_ofs", "decimal", {"hidden": True}),
        ("date", "dateTime", {"hidden": True, "fmt": "Short Date"}),
    ], "fact_offre.m", "Offre : capacité et occupation par mois et canton."))

    write(d / "tables" / "dim_canton.tmdl", m_table("dim_canton", [
        ("canton_id", "string", {"hidden": True, "key": True}), ("canton", "string"), ("abreviation", "string"),
        ("grande_region", "string"), ("langue", "string"),
    ], "dim_canton.m", "Les 26 cantons."))

    write(d / "tables" / "dim_pays.tmdl", m_table("dim_pays", [
        ("pays_id", "string", {"hidden": True, "key": True}), ("pays", "string"), ("marche", "string"),
        ("continent", "string"),
    ], "dim_pays.m", "Pays de provenance, marché harmonisé et continent."))

    cal = ["/// Calendrier journalier continu, marqué comme table de dates.", "table Calendrier",
           f"\tlineageTag: {guid('Calendrier')}", "\tdataCategory: Time", "",
           column("Calendrier", "Date", "dateTime", fmt="dd.mm.yyyy", source="[Date]", key=True, inferred=True)]
    for n, dtype, fmt, e, sort_by in CALENDAR_COLUMNS:
        cal.append(column("Calendrier", n, dtype, fmt=fmt, expression=e, sort_by=sort_by, hidden=(n == "Mois")))
    cal += ["\tpartition Calendrier = calculated", "\t\tmode: import", f"\t\tsource = {CALENDAR_SOURCE}", ""]
    write(d / "tables" / "Calendrier.tmdl", "\n".join(cal))

    mes = ["/// Toutes les mesures du rapport.", f"table {M}", f"\tlineageTag: {guid(M)}", ""]
    for folder, n, fmt, e, desc in MEASURES:
        e = e.strip()
        mes.append(f"\t/// {desc}")
        if "\n" in e:
            mes += [f"\tmeasure {q(n)} =", indent(e, 3)]
        else:
            mes.append(f"\tmeasure {q(n)} = {e}")
        if fmt:
            mes.append(f"\t\tformatString: {fmt}")
        mes += [f"\t\tdisplayFolder: {folder}", f"\t\tlineageTag: {guid(M, n)}", ""]
        if not fmt:   # mesure texte : pas de format numérique à définir
            mes += ['\t\tannotation BestPracticeAnalyzer_IgnoreRules = {"RuleIDs":["PROVIDE_FORMAT_STRING_FOR_MEASURES"]}', ""]
    mes.append(column(M, "Colonne", "int64", hidden=True, fmt="0", source="[Colonne]", inferred=True))
    mes += [f"\tpartition {M} = calculated", "\t\tmode: import", '\t\tsource = ROW ( "Colonne", 0 )', ""]
    write(d / "tables" / f"{M}.tmdl", "\n".join(mes))

    rels = [("fact_demande", "date", "Calendrier", "Date"), ("fact_offre", "date", "Calendrier", "Date"),
            ("fact_demande", "canton_id", "dim_canton", "canton_id"), ("fact_offre", "canton_id", "dim_canton", "canton_id"),
            ("fact_demande", "pays_id", "dim_pays", "pays_id")]
    write(d / "relationships.tmdl", "\n".join(
        f"relationship {guid('rel', a, b, c)}\n\tfromColumn: {a}.{q(b)}\n\ttoColumn: {c}.{q(dc)}\n"
        for a, b, c, dc in rels))

    write_json(SM / "definition.pbism", {"version": "4.0", "settings": {"qnaEnabled": False}})
    write_json(SM / ".pbi" / "editorSettings.json", {"version": "1.0", "showHiddenFields": False,
                                                    "parallelQueryLoading": True, "relationshipImportEnabled": False})
    write_json(SM / ".platform", {
        "$schema": f"{SCHEMA}/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "SemanticModel", "displayName": NAME},
        "config": {"version": "2.0", "logicalId": guid("semanticModel")}})


# =============================================================================
# 3. Rapport (PBIR)
# =============================================================================
def lit(value: str) -> dict:
    return {"expr": {"Literal": {"Value": value}}}


def s(text: str) -> dict:
    return lit("'" + text.replace("'", "''") + "'")


def b(v: bool) -> dict:
    return lit("true" if v else "false")


def col(entity: str, prop: str) -> dict:
    return {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


def mea(prop: str) -> dict:
    return {"Measure": {"Expression": {"SourceRef": {"Entity": M}}, "Property": prop}}


def ref(field: dict) -> str:
    k = "Column" if "Column" in field else "Measure"
    return f"{field[k]['Expression']['SourceRef']['Entity']}.{field[k]['Property']}"


def proj(field: dict, name: str | None = None) -> dict:
    p = {"field": field, "queryRef": ref(field), "nativeQueryRef": field.get("Column", field.get("Measure"))["Property"]}
    if "Column" in field:
        p["active"] = True
    if name:
        p["displayName"] = name
    return p


def in_filter(entity: str, prop: str, values: list[str]) -> dict:
    return {"Version": 2, "From": [{"Name": "t", "Entity": entity, "Type": 0}],
            "Where": [{"Condition": {"In": {
                "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": prop}}],
                "Values": [[{"Literal": {"Value": v}}] for v in values]}}}]}


def container(title: str | None = None, background=True) -> dict:
    o = {}
    if title:
        o["title"] = [{"properties": {"show": b(True), "text": s(title)}}]
    else:
        o["title"] = [{"properties": {"show": b(False)}}]
    if not background:
        o["background"] = [{"properties": {"show": b(False)}}]
    return o


class Page:
    def __init__(self, key: str, display: str):
        self.name = hexid("page", key)
        self.key = key
        self.display = display
        self.visuals: list[dict] = []
        self.interactions: list[dict] = []
        self.z = 0

    def add(self, key: str, x, y, w, h, visual: dict, filters: list | None = None) -> str:
        self.z += 1000
        name = hexid(self.key, key)
        v = {"$schema": f"{SCHEMA}/item/report/definition/visualContainer/2.0.0/schema.json",
             "name": name,
             "position": {"x": x, "y": y, "z": self.z, "height": h, "width": w, "tabOrder": self.z},
             "visual": {**visual, "drillFilterOtherVisuals": True}}
        if filters:
            v["filterConfig"] = {"filters": filters}
        self.visuals.append(v)
        return name

    def no_filter(self, source: str, *targets: str) -> None:
        self.interactions += [{"source": source, "target": t, "type": "NoFilter"} for t in targets]


def textbox(runs: list[tuple[str, str, str, bool]]) -> dict:
    """runs : (texte, taille, couleur, gras) ; un paragraphe par élément."""
    return {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": [
        {"textRuns": [{"value": t, "textStyle": {"fontSize": size, "color": color,
                                                  **({"fontWeight": "bold"} if bold else {})}}]}
        for t, size, color, bold in runs]}}]},
        "visualContainerObjects": container(background=False)}


def card(measure: str, label: str | None = None, size="26", color="#16191D") -> dict:
    return {"visualType": "card",
            "query": {"queryState": {"Values": {"projections": [proj(mea(measure), label)]}}},
            "objects": {"labels": [{"properties": {"fontSize": lit(f"'{size}'"), "color": {"solid": {"color": lit(f"'{color}'")}}}}],
                        "categoryLabels": [{"properties": {"show": b(True), "fontSize": lit("'10'")}}]},
            "visualContainerObjects": container()}


def text_card(measure: str, size="10", color="#59626D") -> dict:
    c = card(measure, size=size, color=color)
    c["objects"]["categoryLabels"] = [{"properties": {"show": b(False)}}]
    c["visualContainerObjects"] = container(background=False)
    return c


def slicer(entity: str, prop: str, group: str, default: list[str] | None, dropdown=True, title=None) -> dict:
    obj = {"data": [{"properties": {"mode": s("Dropdown" if dropdown else "Basic")}}],
           "selection": [{"properties": {"singleSelect": b(dropdown), "strictSingleSelect": b(False)}}]}
    if default:
        obj["general"] = [{"properties": {"filter": {"filter": in_filter(entity, prop, default)}}}]
    return {"visualType": "slicer",
            "query": {"queryState": {"Values": {"projections": [proj(col(entity, prop))]}},
                      "sortDefinition": {"sort": [{"field": col(entity, prop),
                                                   "direction": "Descending" if prop == "Année" else "Ascending"}]}},
            "objects": obj, "syncGroup": {"groupName": group, "fieldChanges": True, "filterChanges": True},
            "visualContainerObjects": container(title)}


def chart(vtype: str, roles: dict[str, list[dict]], title: str, sort: tuple[dict, str] | None = None,
          objects: dict | None = None) -> dict:
    v = {"visualType": vtype,
         "query": {"queryState": {r: {"projections": [proj(f) for f in fs]} for r, fs in roles.items()}},
         "visualContainerObjects": container(title)}
    if sort:
        v["query"]["sortDefinition"] = {"sort": [{"field": sort[0], "direction": sort[1]}]}
    if objects:
        v["objects"] = objects
    return v


def year_from(year: int) -> dict:
    f = col("Calendrier", "Année")
    return {"name": hexid("filtre", str(year)), "field": f, "type": "Advanced",
            "filter": {"Version": 2, "From": [{"Name": "c", "Entity": "Calendrier", "Type": 0}],
                       "Where": [{"Condition": {"Comparison": {
                           "ComparisonKind": 2,
                           "Left": {"Column": {"Expression": {"SourceRef": {"Source": "c"}}, "Property": "Année"}},
                           "Right": {"Literal": {"Value": f"{year}L"}}}}}]}}


INK, SLATE, RED = "#16191D", "#59626D", "#D52B1E"


def header(p: Page, title: str, question: str, canton=True) -> tuple[str, str | None]:
    p.add("titre", 24, 12, 760, 64, textbox([(title, "20pt", INK, True), (question, "11pt", SLATE, False)]))
    p.add("periode", 24, 74, 760, 30, text_card("Titre période", size="11", color=RED))
    an = p.add("seg_annee", 1060 if canton else 1100, 14, 196 if canton else 156, 58,
               slicer("Calendrier", "Année", "Annee", ["2025L"], title="Année"))
    ct = None
    if canton:
        ct = p.add("seg_canton", 850, 14, 196, 58, slicer("dim_canton", "canton", "Canton", ["'Genève'"], title="Canton"))
    p.add("source", 24, 690, 1232, 26, textbox([(
        "Source : Office fédéral de la statistique (OFS), statistique HESTA. Rapport : Lyes Toumi, "
        "github.com/Toumil94/analyse-bi-suisse", "8pt", SLATE, False)]))
    return an, ct


def build_pages() -> list[Page]:
    pages = []

    # --- Page 1 : vue d'ensemble -------------------------------------------------------
    p = Page("p1", "Vue d'ensemble")
    an, ct = header(p, "Vue d'ensemble", "Comment va l'hôtellerie du canton ?")
    for i, (m, label) in enumerate([("Nuitées", None), ("Évolution vs A-1", None), ("Niveau vs 2019", None),
                                    ("Taux d'occupation des chambres", "Occupation des chambres")]):
        p.add(f"carte{i}", 24 + i * 311, 112, 299, 110, card(m, label))
    trend = p.add("tendance", 24, 236, 760, 444, chart(
        "lineChart", {"Category": [col("Calendrier", "Mois début")], "Y": [mea("Nuitées 12 mois glissants")]},
        "Nuitées sur 12 mois glissants : la tendance de fond, sans la saisonnalité"))
    annual = p.add("annuel", 796, 236, 460, 400, chart(
        "clusteredColumnChart", {"Category": [col("Calendrier", "Année")], "Y": [mea("Nuitées")],
                                 "Tooltips": [mea("Évolution vs A-1"), mea("Niveau vs 2019")]},
        "Nuitées par année", sort=(col("Calendrier", "Année"), "Ascending")))
    p.add("fraicheur", 796, 644, 460, 36, text_card("Dernier mois disponible"))
    p.no_filter(an, trend, annual)
    pages.append(p)

    # --- Page 2 : benchmark des cantons -----------------------------------------------------
    p = Page("p2", "Benchmark cantons")
    an, _ = header(p, "Benchmark des cantons", "Où se situe Genève parmi les 26 cantons ?", canton=False)
    color = {"dataPoint": [{"properties": {"fill": {"solid": {"color": {"expr": mea("Couleur canton")}}}},
                            "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}}],
             "labels": [{"properties": {"show": b(True)}}]}
    p.add("reprise", 24, 112, 400, 568, chart(
        "clusteredBarChart", {"Category": [col("dim_canton", "canton")], "Y": [mea("Niveau vs 2019")]},
        "Niveau des nuitées vs 2019 (100 % = avant crise)", sort=(mea("Niveau vs 2019"), "Descending"), objects=color))
    p.add("tableau", 436, 112, 820, 300, chart(
        "tableEx", {"Values": [col("dim_canton", "canton"), mea("Nuitées"), mea("Part de marché du canton"),
                               mea("Rang du canton"), mea("Taux d'occupation des chambres"),
                               mea("Écart d'occupation vs Suisse (points)"), mea("Durée moyenne de séjour")]},
        "Indicateurs par canton", sort=(mea("Nuitées"), "Descending")))
    p.add("nuage", 436, 424, 820, 256, chart(
        "scatterChart", {"Category": [col("dim_canton", "abreviation")], "X": [mea("Taux d'occupation des chambres")],
                         "Y": [mea("Évolution vs A-1")], "Size": [mea("Nuitées")]},
        "Occupation (X) et croissance (Y) : en haut à droite, les cantons pleins et en croissance"))
    pages.append(p)

    # --- Page 3 : marchés de provenance ----------------------------------------------------
    p = Page("p3", "Marchés")
    an, ct = header(p, "Marchés de provenance", "D'où viennent les clients, et qui revient ?")
    p.add("seg_continent", 24, 112, 300, 210, slicer("dim_pays", "continent", "Continent", None, dropdown=False,
                                                       title="Continent"))
    p.add("marches", 24, 334, 300, 346, chart(
        "clusteredBarChart", {"Category": [col("dim_pays", "marche")], "Y": [mea("Nuitées")]},
        "Nuitées par marché", sort=(mea("Nuitées"), "Descending")))
    p.add("matrice", 336, 112, 920, 300, chart(
        "pivotTable", {"Rows": [col("dim_pays", "continent"), col("dim_pays", "marche")],
                       "Values": [mea("Nuitées"), mea("Part du marché de provenance"), mea("Niveau vs 2019"),
                                  mea("Contribution à la croissance")]},
        "Poids, reprise et contribution de chaque marché", sort=(mea("Nuitées"), "Descending")))
    evol = p.add("continents", 336, 424, 920, 256, chart(
        "lineChart", {"Category": [col("Calendrier", "Année")], "Y": [mea("Nuitées")],
                      "Series": [col("dim_pays", "continent")]},
        "Nuitées par continent de provenance", sort=(col("Calendrier", "Année"), "Ascending")))
    p.no_filter(an, evol)
    pages.append(p)

    # --- Page 4 : saisonnalité ---------------------------------------------------------------
    p = Page("p4", "Saisonnalité")
    an, ct = header(p, "Saisonnalité", "Quels mois faut-il remplir ?")
    taux = mea("Taux d'occupation des chambres")
    heat = {"values": [{"properties": {"backColor": {"solid": {"color": {"expr": {"FillRule": {
        "Input": taux,
        "FillRule": {"linearGradient2": {
            "min": {"color": {"Literal": {"Value": "'#F3F4F1'"}}},
            "max": {"color": {"Literal": {"Value": "'#2A78D6'"}}},
            "nullColoringStrategy": {"strategy": {"Literal": {"Value": "'asZero'"}}}}}}}}}}},
        "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": ref(taux)}}]}
    carte = p.add("chaleur", 24, 112, 760, 568, chart(
        "pivotTable", {"Rows": [col("Calendrier", "Année")], "Columns": [col("Calendrier", "Mois nom")], "Values": [taux]},
        "Taux d'occupation des chambres par année et par mois", sort=(col("Calendrier", "Année"), "Descending"),
        objects=heat), filters=[year_from(2015)])
    p.add("profil", 796, 112, 460, 330, chart(
        "lineChart", {"Category": [col("Calendrier", "Mois nom")],
                      "Y": [taux, mea("Taux d'occupation des chambres (Suisse)")]},
        "Occupation par mois : canton et Suisse", sort=(col("Calendrier", "Mois nom"), "Ascending")))
    p.add("saisons", 796, 454, 460, 226, chart(
        "clusteredColumnChart", {"Category": [col("Calendrier", "Saison")], "Y": [mea("Durée moyenne de séjour")]},
        "Durée moyenne de séjour par saison (nuits)", objects={"labels": [{"properties": {"show": b(True)}}]}))
    p.no_filter(an, carte)
    pages.append(p)
    return pages


def build_report() -> None:
    if RP.exists():
        shutil.rmtree(RP)
    d = RP / "definition"
    theme = json.loads((HERE / "theme-suisse.json").read_text(encoding="utf-8"))
    theme_file = "theme-suisse.json"
    write_json(RP / "StaticResources" / "RegisteredResources" / theme_file, theme)

    write_json(RP / "definition.pbir", {
        "$schema": f"{SCHEMA}/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0", "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}})
    write_json(RP / ".platform", {
        "$schema": f"{SCHEMA}/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "Report", "displayName": NAME},
        "config": {"version": "2.0", "logicalId": guid("report")}})
    write_json(d / "version.json", {"$schema": f"{SCHEMA}/item/report/definition/versionMetadata/1.0.0/schema.json",
                                    "version": "2.0.0"})

    base = HERE / "assets" / "CY24SU10.json"
    report = {
        "$schema": f"{SCHEMA}/item/report/definition/report/1.3.0/schema.json",
        "themeCollection": {"customTheme": {"name": theme_file, "reportVersionAtImport": "5.61",
                                            "type": "RegisteredResources"}},
        "layoutOptimization": "None",
        "resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources",
                              "items": [{"name": theme_file, "path": theme_file, "type": "CustomTheme"}]}],
        "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized",
                     "defaultDrillFilterOtherVisuals": True, "allowChangeFilterTypes": True,
                     "useEnhancedTooltips": True, "useDefaultAggregateDisplayName": True},
    }
    if base.exists():   # thème de base Microsoft, copié tel que Power BI l'écrit
        write_json(RP / "StaticResources" / "SharedResources" / "BaseThemes" / "CY24SU10.json",
                   json.loads(base.read_text(encoding="utf-8")))
        report["themeCollection"]["baseTheme"] = {"name": "CY24SU10", "reportVersionAtImport": "5.61",
                                                  "type": "SharedResources"}
        report["resourcePackages"].insert(0, {"name": "SharedResources", "type": "SharedResources", "items": [
            {"name": "CY24SU10", "path": "BaseThemes/CY24SU10.json", "type": "BaseTheme"}]})
    write_json(d / "report.json", report)

    pages = build_pages()
    write_json(d / "pages" / "pages.json", {
        "$schema": f"{SCHEMA}/item/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": [p.name for p in pages], "activePageName": pages[0].name})
    for p in pages:
        page = {"$schema": f"{SCHEMA}/item/report/definition/page/1.4.0/schema.json",
                "name": p.name, "displayName": p.display, "displayOption": "FitToPage", "height": 720, "width": 1280}
        if p.interactions:
            page["visualInteractions"] = p.interactions
        write_json(d / "pages" / p.name / "page.json", page)
        for v in p.visuals:
            write_json(d / "pages" / p.name / "visuals" / v["name"] / "visual.json", v)

    write_json(HERE / f"{NAME}.pbip", {
        "$schema": f"{SCHEMA}/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0", "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
        "settings": {"enableAutoRecovery": True}})


if __name__ == "__main__":
    export_dax()
    build_model()
    build_report()
    print(f"Projet généré : {HERE / (NAME + '.pbip')}")
