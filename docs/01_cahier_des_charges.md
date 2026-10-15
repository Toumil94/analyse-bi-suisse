# Cahier des charges : tableau de bord du tourisme hôtelier genevois

> Cas d'étude. Le commanditaire est fictif, les données sont réelles (Office fédéral de la statistique, statistique de l'hébergement HESTA).

## 1. Contexte

L'hôtellerie genevoise vit d'une clientèle très internationale (organisations internationales, congrès, affaires, tourisme de luxe). La crise du COVID a fait chuter les nuitées plus fortement à Genève que dans la moyenne suisse, et la reprise a été inégale selon les marchés de provenance.

Aujourd'hui, les chiffres existent (l'OFS les publie chaque mois), mais ils sont dispersés dans des tableaux statistiques peu lisibles. Les décisions de promotion et de budget se prennent sans vue consolidée.

## 2. Commanditaire et parties prenantes

| Rôle | Attentes |
|---|---|
| Direction de l'office du tourisme (commanditaire) | Une vue mensuelle de la performance de Genève par rapport aux autres cantons, pour piloter et rendre compte. |
| Responsable marketing des marchés étrangers | Savoir quels pays de provenance progressent ou reculent, pour arbitrer le budget de promotion. |
| Association des hôteliers | Comprendre la saisonnalité de l'occupation et repérer les mois creux à remplir. |
| Analyste data (moi) | Construire un modèle fiable, documenté et mis à jour automatiquement. |

## 3. Questions métier

1. **Performance** : combien de nuitées Genève réalise-t-elle, et comment évoluent-elles d'une année sur l'autre ?
2. **Reprise** : où en est Genève par rapport à 2019, dernière année avant le COVID, et par rapport aux autres cantons ?
3. **Marchés** : quels pays de provenance pèsent le plus, lesquels sont en croissance et lesquels ne sont pas revenus ?
4. **Occupation** : quel est le taux d'occupation des chambres, mois par mois, et quels sont les mois creux ?
5. **Séjours** : combien de temps les clients restent-ils, et est-ce que cela change ?

## 4. Périmètre

| Inclus | Exclu |
|---|---|
| Hôtellerie (hôtels et établissements de cure) | Parahôtellerie (campings, appartements de vacances, Airbnb) |
| 26 cantons, 77 catégories de pays de provenance | Données par commune (disponibles seulement depuis 2013) |
| Données mensuelles depuis janvier 2005 | Chiffre d'affaires et prix des chambres (non publiés par l'OFS) |

## 5. Exigences fonctionnelles

| ID | Exigence | Priorité |
|---|---|---|
| EF-01 | Afficher les nuitées, les arrivées et la durée moyenne de séjour pour la période et le canton choisis. | Must |
| EF-02 | Comparer avec l'année précédente (même période) et avec 2019. | Must |
| EF-03 | Classer les cantons et situer Genève dans ce classement. | Must |
| EF-04 | Montrer les marchés de provenance avec leur part et leur évolution. | Must |
| EF-05 | Afficher le taux d'occupation des chambres et des lits, calculé comme l'OFS. | Must |
| EF-06 | Filtrer par année, saison touristique, canton, grande région, continent. | Must |
| EF-07 | Comparer des séries de pays stables dans le temps malgré les changements de nomenclature. | Should |
| EF-08 | Indiquer clairement la date des dernières données disponibles. | Should |
| EF-09 | Mettre à jour les données automatiquement chaque mois, sans intervention. | Should |

## 6. Exigences non fonctionnelles

- **Fiabilité** : les totaux du rapport doivent retrouver les totaux publiés par l'OFS (voir la recette).
- **Performance** : chaque page s'affiche en moins de 3 secondes dans Power BI Desktop.
- **Lisibilité** : une page = une question métier ; titre explicite et source sur chaque page.
- **Traçabilité** : chaque indicateur a une définition écrite (voir le dictionnaire des KPI).

## 7. User stories

- *En tant que directeur*, je veux voir en un coup d'œil les nuitées du mois et leur évolution, afin de rendre compte au conseil.
- *En tant que responsable marketing*, je veux classer les marchés selon leur croissance depuis 2019, afin de concentrer le budget sur ceux qui repartent.
- *En tant qu'hôtelier*, je veux connaître le taux d'occupation par mois, afin de planifier mes offres de basse saison.

## 8. Livrables

| Livrable | Emplacement |
|---|---|
| Modèle de données et pipeline mis à jour chaque mois | `pipeline/`, `data/`, `.github/workflows/` |
| Rapport Power BI (4 pages) | `powerbi/` |
| Dictionnaire des KPI | [`02_dictionnaire_kpi.md`](02_dictionnaire_kpi.md) |
| Modèle de données | [`03_modele_de_donnees.md`](03_modele_de_donnees.md) |
| Cahier de recette | [`04_recette.md`](04_recette.md) |
| Note de recommandations | [`05_recommandations.md`](05_recommandations.md) |
