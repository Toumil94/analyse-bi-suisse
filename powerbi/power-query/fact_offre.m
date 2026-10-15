// Offre hôtelière par mois et canton : établissements, chambres, lits, nuitées-chambres
// et capacité offerte (chambres-jours et lits-jours) reconstituée pour retrouver le taux d'occupation de l'OFS.
let
    Source = Csv.Document(Web.Contents(BaseUrl, [RelativePath = "fact_offre.csv"]), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Entetes = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    // une cellule vide (mois sans taux publié) devient null au lieu de provoquer une erreur de type
    Vides = Table.TransformColumns(Entetes, {}, each if _ = "" then null else _),
    Types = Table.TransformColumnTypes(Vides, {
        {"date_key", type text}, {"canton_id", type text},
        {"etablissements", Int64.Type}, {"chambres", Int64.Type}, {"lits", Int64.Type},
        {"arrivees", Int64.Type}, {"nuitees", Int64.Type}, {"nuitees_chambres", Int64.Type},
        {"capacite_chambres_jours", Int64.Type}, {"capacite_lits_jours", Int64.Type},
        {"taux_occ_chambres_ofs", Currency.Type}, {"taux_occ_lits_ofs", Currency.Type}}, "en-US"),
    AvecDate = Table.AddColumn(Types, "date", each #date(Number.FromText(Text.Start([date_key], 4)), Number.FromText(Text.Middle([date_key], 4, 2)), 1), type date),
    SansCle = Table.RemoveColumns(AvecDate, {"date_key"})
in
    SansCle
