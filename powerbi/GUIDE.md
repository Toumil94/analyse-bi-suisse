# Le rapport Power BI

Le rapport est livré **prêt à ouvrir**, au format projet Power BI (PBIP) : le modèle sémantique est décrit en TMDL, le rapport en PBIR, et tout est généré par [`build_pbip.py`](build_pbip.py). C'est l'approche « report as code » : chaque mesure, relation et visuel est versionné, relu et contrôlé automatiquement par GitHub Actions.

Prérequis : **Power BI Desktop** (gratuit, Microsoft Store), sur Windows, version récente.

## Ouvrir le rapport (5 minutes)

1. Télécharge le dépôt : bouton vert **Code**, puis **Download ZIP**, et décompresse-le.
2. Double-clique sur `powerbi/Tourisme-Suisse.pbip`.
3. Power BI affiche un message indiquant que les données ne sont pas encore chargées : clique sur **Actualiser** (onglet Accueil).
4. Si Power BI demande comment se connecter à `raw.githubusercontent.com`, choisis **Anonyme**, puis **Se connecter**.
5. Le chargement prend environ une minute (400 000 lignes lues directement sur GitHub).

Si Power BI refuse d'ouvrir le fichier : **Fichier**, puis **Options et paramètres**, puis **Options**, puis **Fonctionnalités en préversion**, et coche **Format de rapport Power BI amélioré (PBIR)** et **Stockage du modèle sémantique au format TMDL**. Redémarre Power BI. Dans les versions récentes, ces formats sont activés par défaut.

## Ce que contient le rapport

Chaque page répond à une question. Segments **Année** (2025 par défaut) et **Canton** (Genève par défaut), synchronisés entre les pages.

| Page | Question | Visuels |
|---|---|---|
| 1. Vue d'ensemble | Comment va l'hôtellerie du canton ? | 4 cartes (nuitées, évolution, niveau vs 2019, occupation), tendance sur 12 mois glissants, nuitées par année |
| 2. Benchmark cantons | Où se situe Genève parmi les 26 cantons ? | Reprise par canton (Genève en rouge), tableau des indicateurs, nuage occupation et croissance |
| 3. Marchés | D'où viennent les clients, et qui revient ? | Segment continent, nuitées par marché, matrice poids, reprise et contribution, évolution par continent |
| 4. Saisonnalité | Quels mois faut-il remplir ? | Carte de chaleur année par mois, profil mensuel canton et Suisse, durée de séjour par saison |

Les visuels de tendance ignorent volontairement le segment Année (interactions désactivées), pour toujours montrer la série complète.

## Le modèle

- **Tables de faits** : `fact_demande` (mois, canton, pays) et `fact_offre` (mois, canton).
- **Dimensions** : `Calendrier` (table calculée, journalière, marquée comme table de dates), `dim_canton`, `dim_pays`.
- **Mesures** : la table `_Mesures` regroupe les 24 mesures, rangées en dossiers (Volumes, Occupation, Temps, Parts, Affichage). Le fichier [`mesures.dax`](mesures.dax) en donne la liste lisible.
- **Données** : le paramètre `BaseUrl` pointe vers les CSV du dépôt, mis à jour chaque mois.

## Vérifier les chiffres (recette)

Compare les cartes de la page 1 avec le [cahier de recette](../docs/04_recette.md). Avec Genève et 2025 : 3 851 477 nuitées, +1,7 % vs A-1, 120 % du niveau 2019, 68,0 % d'occupation des chambres.

## Modifier le rapport

Deux façons, au choix :

- **Dans Power BI Desktop**, comme n'importe quel rapport, puis **Enregistrer** : les fichiers du projet sont mis à jour et le changement apparaît dans Git.
- **Dans le code** : modifie `build_pbip.py` (mesures, pages, visuels), puis lance `python powerbi/build_pbip.py`. Le workflow GitHub Actions « Rapport Power BI » valide alors les fichiers du rapport contre les schémas officiels de Microsoft et charge le modèle dans Tabular Editor.

## Questions d'entretien

- **Pourquoi un projet PBIP plutôt qu'un .pbix ?** Le .pbix est un fichier binaire : impossible de voir ce qui a changé. Le PBIP est un ensemble de fichiers texte : revue de code, historique, contrôles automatiques, comme pour du logiciel.
- **Pourquoi deux tables de faits ?** L'offre n'existe pas par pays de provenance. Voir [`docs/03_modele_de_donnees.md`](../docs/03_modele_de_donnees.md).
- **Pourquoi un calendrier journalier pour des données mensuelles ?** Les fonctions d'intelligence temporelle exigent une table de dates continue. Il s'arrête au dernier mois publié, pour que l'évolution de l'année en cours compare les mêmes mois.
- **Pourquoi ne pas faire la moyenne des taux d'occupation ?** Un petit canton pèserait autant que Zurich. On divise la somme des nuitées-chambres par la somme des capacités.
- **Pourquoi `TREATAS` dans « Nuitées même période 2019 » ?** Pour comparer exactement les mêmes mois de 2019, y compris quand l'année en cours n'est pas terminée.
- **Pourquoi `Web.Contents(BaseUrl, [RelativePath = ...])` ?** Une adresse de base fixe permet l'actualisation planifiée dans le service Power BI, qui refuse les sources construites dynamiquement.
