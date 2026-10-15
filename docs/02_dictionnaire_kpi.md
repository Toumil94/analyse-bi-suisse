# Dictionnaire des KPI

Chaque indicateur du rapport, avec sa définition métier, sa formule et ses pièges. Les formules DAX complètes sont dans [`powerbi/mesures.dax`](../powerbi/mesures.dax).

| KPI | Définition métier | Formule | Source | À savoir |
|---|---|---|---|---|
| **Nuitées** | Nombre de nuits passées par les clients dans les hôtels. | Somme de `nuitees` | `fact_demande` | Indicateur principal de l'activité hôtelière. |
| **Arrivées** | Nombre de clients enregistrés à leur arrivée. | Somme de `arrivees` | `fact_demande` | Un même client qui change d'hôtel compte deux fois. |
| **Durée moyenne de séjour** | Nombre moyen de nuits par client. | Nuitées / Arrivées | `fact_demande` | Courte en ville (affaires), plus longue en montagne. |
| **Part des visiteurs étrangers** | Part des nuitées réalisées par des clients domiciliés hors de Suisse. | Nuitées hors Suisse / Nuitées | `fact_demande`, `dim_pays` | Le pays est celui du domicile, pas la nationalité. |
| **Taux d'occupation des chambres** | Part des chambres offertes réellement occupées. | Nuitées-chambres / Capacité chambres-jours | `fact_offre` | Calculé à partir des composantes, jamais comme une moyenne de taux. |
| **Taux d'occupation des lits** | Part des lits offerts réellement occupés. | Nuitées / Capacité lits-jours | `fact_offre` | Toujours plus bas que celui des chambres (chambres doubles occupées par une personne). |
| **Évolution vs A-1** | Variation par rapport à la même période de l'année précédente. | (Nuitées − Nuitées A-1) / Nuitées A-1 | Mesure DAX | Compare des périodes de même durée, y compris pour l'année en cours. |
| **Niveau vs 2019** | Niveau d'activité par rapport à la même période de 2019, dernière année avant le COVID. | Nuitées / Nuitées même période 2019 | Mesure DAX | 100 % = niveau d'avant crise retrouvé. |
| **Part de marché du canton** | Poids du canton dans les nuitées suisses. | Nuitées canton / Nuitées Suisse | Mesure DAX | |
| **Part du marché de provenance** | Poids d'un pays dans les nuitées du périmètre filtré. | Nuitées pays / Nuitées tous pays | Mesure DAX | |
| **Contribution à la croissance** | Combien un marché a apporté à l'évolution totale, en points. | (Nuitées − Nuitées A-1) du marché / Nuitées A-1 totales | Mesure DAX | La somme des contributions donne l'évolution totale. |
| **Écart d'occupation vs Suisse** | Différence de taux d'occupation entre le canton et la Suisse. | Taux canton − Taux Suisse, en points | Mesure DAX | |

## Règles de gestion

- **Pourquoi « capacité reconstituée » ?** L'OFS calcule le taux d'occupation sur les jours où les hôtels sont réellement ouverts, une donnée qu'il ne publie pas. Diviser par « chambres × jours du mois » sous-estime le taux d'environ 1,1 point (médiane). Le pipeline reconstitue donc la capacité exacte à partir du taux publié : `capacité = nuitées-chambres × 100 / taux OFS`. Le taux agrégé dans Power BI retrouve alors celui de l'OFS à n'importe quel niveau (mois, canton, Suisse).
- **Marchés harmonisés.** La nomenclature des pays a changé au fil du temps (par exemple, « Pays du Golfe » a été remplacé par le détail Qatar, Émirats arabes unis, Arabie saoudite...). La colonne `marche` regroupe ces catégories pour comparer 2019 et aujourd'hui sur une base stable.
- **Saison touristique.** Hiver = novembre à avril, été = mai à octobre (convention de l'OFS).
- **Période COVID.** De mars 2020 à décembre 2021.
- **Valeurs confidentielles.** Les cellules masquées par l'OFS (secret statistique) sont exclues ; les totaux restent cohérents (voir la recette).
