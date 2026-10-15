// Arrivées et nuitées par mois, canton et pays de provenance (source OFS, HESTA).
let
    Source = Csv.Document(Web.Contents(BaseUrl, [RelativePath = "fact_demande.csv"]), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Entetes = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Types = Table.TransformColumnTypes(Entetes, {{"date_key", type text}, {"canton_id", type text}, {"pays_id", type text}, {"arrivees", Int64.Type}, {"nuitees", Int64.Type}}, "en-US"),
    AvecDate = Table.AddColumn(Types, "date", each #date(Number.FromText(Text.Start([date_key], 4)), Number.FromText(Text.Middle([date_key], 4, 2)), 1), type date),
    SansCle = Table.RemoveColumns(AvecDate, {"date_key"})
in
    SansCle
