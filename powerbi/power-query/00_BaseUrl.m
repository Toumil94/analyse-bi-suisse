// Paramètre : d'où viennent les données. Par défaut, directement depuis GitHub (mises à jour chaque mois).
// Les requêtes appellent Web.Contents(BaseUrl, [RelativePath = ...]) : l'adresse de base reste fixe,
// ce qui permet aussi l'actualisation planifiée dans le service Power BI.
"https://raw.githubusercontent.com/Toumil94/analyse-bi-suisse/main/data/" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]
