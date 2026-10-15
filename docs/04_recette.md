# Cahier de recette

La recette vérifie que le rapport affiche des chiffres justes. Deux niveaux :

1. **Contrôles automatiques** du pipeline, à chaque mise à jour mensuelle (`tests/`). Si un seul échoue, rien n'est publié.
2. **Tests de recette du rapport Power BI**, à faire à la main après la construction ou après une modification du modèle.

## 1. Contrôles automatiques (dernière exécution)

| Contrôle | Résultat attendu | Résultat obtenu |
|---|---|---|
| Somme des pays de provenance = total publié par l'OFS, pour chaque canton et chaque mois | écart médian < 0,5 % | **0,000 %** sur 6 760 combinaisons |
| Somme des 26 cantons = total suisse publié par l'OFS, pour chaque mois | écart médian < 0,5 % | **0,000 %** sur 260 mois |
| Taux d'occupation recalculé avec la capacité reconstituée = taux OFS | écart < 0,2 point | conforme sur toutes les lignes |
| Taux « naïf » (chambres × jours du mois) vs taux OFS | information | écart médian de **1,1 point** : d'où la capacité reconstituée |
| Unicité des clés des tables de faits | aucune ligne en double | conforme |
| Intégrité référentielle (chaque fait renvoie à une date, un canton, un pays existants) | 100 % | conforme |
| 26 cantons dans la dimension | 26 | conforme |

Le détail chiffré est publié à chaque exécution dans [`data/controles.json`](../data/controles.json).

## 2. Tests de recette du rapport

Valeurs de référence calculées indépendamment en Python ([`pipeline/analyse.py`](../pipeline/analyse.py)), sur les données de janvier 2005 à août 2026. Le rapport doit afficher exactement les mêmes.

| ID | Filtres | Mesure | Valeur attendue | OK ? |
|---|---|---|---|---|
| R-01 | aucun | Nuitées | 792 232 720 | ☐ |
| R-02 | Année 2025, Suisse | Nuitées | 43 930 146 | ☐ |
| R-03 | Année 2024, Suisse | Nuitées | 42 830 588 | ☐ |
| R-04 | Année 2025, Genève | Nuitées | 3 851 477 | ☐ |
| R-05 | Année 2025, Genève | Arrivées | 1 996 533 | ☐ |
| R-06 | Année 2025, Genève | Durée moyenne de séjour | 1,93 | ☐ |
| R-07 | Année 2025, Genève | Évolution vs A-1 | +1,7 % | ☐ |
| R-08 | Année 2025, Genève | Niveau vs 2019 | 120 % | ☐ |
| R-09 | Année 2025, Genève | Taux d'occupation des chambres | 68,0 % | ☐ |
| R-10 | Année 2025, Suisse | Taux d'occupation des chambres | 56,8 % | ☐ |
| R-11 | Année 2025, Genève | Taux d'occupation des lits | 55,0 % | ☐ |
| R-12 | Année 2025, Genève | Part de marché du canton | 8,8 % | ☐ |
| R-13 | Année 2025, Genève | Rang du canton (nuitées) | 5 | ☐ |
| R-14 | Année 2025, Genève | Part des visiteurs étrangers | 72,9 % | ☐ |
| R-15 | Année 2025, Genève, marché États-Unis | Nuitées | 404 564 | ☐ |
| R-16 | Année 2026, Genève | Nuitées (janvier à août) | 2 567 634 | ☐ |
| R-17 | Année 2026, Genève | Évolution vs A-1 (doit comparer à janvier-août 2025, pas à 2025 entier) | -0,3 % | ☐ |

**Comment tester** : un visuel **Carte** avec la mesure, plus des segments pour les filtres. Si une valeur diffère, vérifier d'abord les relations (étape 3 du guide) et le marquage de la table de dates.

## 3. Tests fonctionnels

| ID | Scénario | Résultat attendu | OK ? |
|---|---|---|---|
| F-01 | Choisir un autre canton dans le segment | Toutes les pages se mettent à jour, le titre reste juste | ☐ |
| F-02 | Sélectionner la saison « Hiver » | Les mois affichés vont de novembre à avril | ☐ |
| F-03 | Cliquer sur un continent dans la page Marchés | Les autres visuels se filtrent sur ce continent | ☐ |
| F-04 | Actualiser le rapport | Les données du dernier mois publié par l'OFS apparaissent, sans erreur | ☐ |
| F-05 | Ouvrir le rapport sur un autre PC | Le rapport fonctionne sans fichier local (données lues sur GitHub) | ☐ |
