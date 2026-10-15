// Script Tabular Editor : si le modèle TMDL se charge, on affiche son contenu et on contrôle quelques règles.
var errors = 0;
foreach (var m in Model.AllMeasures) {
    if (string.IsNullOrWhiteSpace(m.Expression)) { Error("Mesure vide : " + m.Name); errors++; }
}
foreach (var t in Model.Tables) {
    foreach (var c in t.Columns) {
        if (c.Name.EndsWith("_id") && !c.IsHidden) { Error("Clé technique visible : " + t.Name + "." + c.Name); errors++; }
    }
}
if (!Model.Tables["Calendrier"].DataCategory.Equals("Time")) { Error("Calendrier non marqué comme table de dates"); errors++; }
Info(string.Format("Modèle chargé : {0} tables, {1} relations, {2} mesures, {3} erreur(s)",
    Model.Tables.Count, Model.Relationships.Count, Model.AllMeasures.Count(), errors));
