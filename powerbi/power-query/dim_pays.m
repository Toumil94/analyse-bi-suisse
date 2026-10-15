// « marche » regroupe les catégories dont la nomenclature OFS a changé avec le temps
// (ex. « Pays du Golfe » avant le détail par pays) pour comparer des séries stables.
let
    Source = Csv.Document(Web.Contents(BaseUrl & "dim_pays.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Entetes = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Types = Table.TransformColumnTypes(Entetes, {{"pays_id", type text}, {"pays", type text}, {"marche", type text}, {"continent", type text}})
in
    Types
