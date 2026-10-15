# Construire le rapport Power BI, pas à pas

Temps estimé : **1 h 30 à 2 h** la première fois. Tout est déjà prêt (données, requêtes, mesures, thème) : tu assembles et tu mets en forme. C'est voulu : en entretien, tu pourras dire honnêtement que tu as construit le rapport, et expliquer chaque choix.

Prérequis : **Power BI Desktop** (gratuit, Microsoft Store), sur Windows.

---

## Étape 1. Créer le fichier et appliquer le thème (5 min)

1. Ouvre Power BI Desktop, puis **Nouveau rapport**.
2. **Affichage**, puis **Thèmes** (flèche), puis **Parcourir les thèmes**, et choisis `powerbi/theme-suisse.json`.
3. Enregistre tout de suite sous `powerbi/Tourisme-Suisse.pbix`.

## Étape 2. Charger les données avec Power Query (15 min)

On va créer un paramètre, puis 4 requêtes en collant le code fourni.

1. **Accueil**, puis **Transformer les données** : l'éditeur Power Query s'ouvre.
2. **Le paramètre** : **Accueil**, puis **Gérer les paramètres**, puis **Nouveau**.
   - Nom : `BaseUrl`, Type : **Texte**
   - Valeur actuelle : `https://raw.githubusercontent.com/Toumil94/analyse-bi-suisse/main/data/`
3. **Les 4 tables** : pour chacune, **Nouvelle source**, puis **Requête vide**, puis **Éditeur avancé**. Colle le contenu du fichier, valide, puis renomme la requête (clic droit, Renommer) :

   | Fichier | Nom de la requête |
   |---|---|
   | `power-query/fact_demande.m` | `fact_demande` |
   | `power-query/fact_offre.m` | `fact_offre` |
   | `power-query/dim_canton.m` | `dim_canton` |
   | `power-query/dim_pays.m` | `dim_pays` |

4. Si Power BI demande comment se connecter à GitHub, choisis **Anonyme**, puis **Se connecter**.
5. **Fermer et appliquer**. Le chargement prend environ une minute (400 000 lignes).

## Étape 3. Le modèle (15 min)

1. **Le calendrier** : vue **Modèle**, puis **Modélisation**, puis **Nouvelle table**. Colle le bloc `Calendrier = ...` de `mesures.dax`.
2. Clic droit sur `Calendrier`, puis **Marquer comme table de dates**, colonne **Date**.
3. **Les relations** : vue **Modèle**. Glisse chaque colonne sur l'autre :

   | De (dimension) | Vers (fait) | Cardinalité |
   |---|---|---|
   | `Calendrier[Date]` | `fact_demande[date]` | 1 à plusieurs |
   | `Calendrier[Date]` | `fact_offre[date]` | 1 à plusieurs |
   | `dim_canton[canton_id]` | `fact_demande[canton_id]` | 1 à plusieurs |
   | `dim_canton[canton_id]` | `fact_offre[canton_id]` | 1 à plusieurs |
   | `dim_pays[pays_id]` | `fact_demande[pays_id]` | 1 à plusieurs |

   Vérifie que la **direction du filtre** est **unique** (une seule flèche, de la dimension vers le fait). Power BI crée parfois des relations automatiquement : supprime celles qui ne sont pas dans ce tableau.
4. **Trier les mois** : sélectionne la colonne `Calendrier[Mois nom]`, puis **Outils de colonne**, puis **Trier par colonne**, et choisis `Mois`.
5. **Masquer les colonnes techniques** (clic droit, Masquer) : les `canton_id`, `pays_id` et `date` des tables de faits. On filtre toujours par les dimensions.

## Étape 4. Les mesures DAX (20 min)

1. **Accueil**, puis **Entrer des données**, nomme la table `_Mesures`, puis **Charger**.
2. Pour chaque mesure de `mesures.dax` : sélectionne `_Mesures`, puis **Nouvelle mesure**, colle `Nom = formule`, et valide.
3. Applique le **format** indiqué en commentaire (Outils de mesure, puis Format) : nombre entier, pourcentage...
4. Supprime la colonne vide de `_Mesures` : la table passe en tête de liste avec une icône de calculatrice.

Teste tout de suite : un visuel **Carte** avec la mesure `Nuitées` doit afficher plus de 700 millions (toutes les années). Si c'est le cas, le modèle est bon.

## Étape 5. Les pages du rapport (45 min)

Règle commune : **une page = une question**, un titre qui répond à la question, et la mention « Source : OFS, HESTA » en bas. Ajoute sur chaque page un segment **Année** et un segment **Canton**, avec Genève sélectionné par défaut.

### Page 1. Vue d'ensemble : « Comment va l'hôtellerie genevoise ? »

- **4 cartes** (ou cartes multiligne) : `Nuitées`, `Évolution vs A-1`, `Niveau vs 2019`, `Taux d'occupation des chambres`.
- **Graphique en courbes** : axe X `Calendrier[Date]` (hiérarchie Année, puis Mois), valeur `Nuitées 12 mois glissants`. La courbe lisse la saisonnalité et montre la tendance de fond.
- **Histogramme groupé** : axe `Calendrier[Année]`, valeurs `Nuitées`, info-bulle `Évolution vs A-1`.
- **Zone de texte** avec la mesure `Dernier mois disponible`.

### Page 2. Benchmark : « Où se situe Genève parmi les cantons ? »

- **Barres horizontales** : axe `dim_canton[canton]`, valeur `Niveau vs 2019`, triées par valeur décroissante. Mise en forme conditionnelle : Genève en rouge (couleur des barres, puis règles, puis par valeur du champ canton).
- **Tableau** : canton, `Nuitées`, `Part de marché du canton`, `Rang du canton`, `Taux d'occupation des chambres`, `Durée moyenne de séjour`, `Écart d'occupation vs Suisse (points)` avec des icônes vert/rouge.
- **Nuage de points** : X `Taux d'occupation des chambres`, Y `Évolution vs A-1`, taille `Nuitées`, détails `dim_canton[abreviation]`. Les quatre quadrants racontent l'histoire : cantons pleins et en croissance en haut à droite.

### Page 3. Marchés : « D'où viennent les clients, et qui revient ? »

- **Barres** : axe `dim_pays[marche]`, valeur `Nuitées`, Top N = 15 (filtre du visuel).
- **Matrice** : lignes `dim_pays[continent]` puis `marche`, valeurs `Nuitées`, `Part du marché de provenance`, `Niveau vs 2019`, `Contribution à la croissance`. Mise en forme conditionnelle en dégradé sur `Niveau vs 2019`.
- **Courbes** : axe `Calendrier[Année]`, valeur `Nuitées`, légende `dim_pays[continent]`.
- **Segment** `dim_pays[continent]`.

### Page 4. Saisonnalité : « Quels mois remplir ? »

- **Matrice en carte de chaleur** : lignes `Calendrier[Année]`, colonnes `Calendrier[Mois nom]`, valeur `Taux d'occupation des chambres`, mise en forme conditionnelle en dégradé de couleur d'arrière-plan.
- **Courbes** : axe `Calendrier[Mois nom]`, valeur `Taux d'occupation des chambres`. Ajoute une 2e courbe pour la Suisse en dupliquant la mesure avec `CALCULATE(..., REMOVEFILTERS(dim_canton))`.
- **Histogramme** : axe `Calendrier[Saison]`, valeurs `Durée moyenne de séjour`.

## Étape 6. Finitions et publication (10 min)

1. **Vérifie la recette** : compare tes chiffres avec ceux de [`docs/04_recette.md`](../docs/04_recette.md). Ils doivent être identiques.
2. **Captures d'écran** des 4 pages, au format PNG : enregistre-les dans `docs/images/powerbi-1.png` à `powerbi-4.png`. Envoie-les-moi, je les ajoute au README.
3. **Enregistre** le `.pbix` dans `powerbi/`. Je l'ajouterai au dépôt pour que n'importe qui puisse le télécharger.

## Actualiser les données

Chaque mois, GitHub Actions met à jour les CSV. Dans Power BI : **Accueil**, puis **Actualiser**. C'est tout.

## Pour aller plus loin (questions d'entretien)

- **Pourquoi deux tables de faits ?** L'offre n'existe pas par pays de provenance. Voir [`docs/03_modele_de_donnees.md`](../docs/03_modele_de_donnees.md).
- **Pourquoi un calendrier journalier pour des données mensuelles ?** Les fonctions d'intelligence temporelle exigent une table de dates continue.
- **Pourquoi ne pas faire la moyenne des taux d'occupation ?** Un petit canton pèserait autant que Zurich. On divise la somme des nuitées-chambres par la somme des capacités.
- **Pourquoi `TREATAS` dans « Nuitées même période 2019 » ?** Pour comparer exactement les mêmes mois de 2019, y compris quand l'année en cours n'est pas terminée.
