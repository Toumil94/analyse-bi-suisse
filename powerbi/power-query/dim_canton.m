let
    Source = Csv.Document(Web.Contents(BaseUrl & "dim_canton.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Entetes = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Types = Table.TransformColumnTypes(Entetes, {{"canton_id", type text}, {"canton", type text}, {"abreviation", type text}, {"grande_region", type text}, {"langue", type text}})
in
    Types
