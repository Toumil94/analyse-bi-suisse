# Modèle de données

Un schéma en étoile avec deux tables de faits qui partagent les mêmes dimensions (on parle de « constellation »).

```mermaid
erDiagram
    Calendrier ||--o{ fact_demande : "date"
    Calendrier ||--o{ fact_offre : "date"
    dim_canton ||--o{ fact_demande : "canton_id"
    dim_canton ||--o{ fact_offre : "canton_id"
    dim_pays ||--o{ fact_demande : "pays_id"

    fact_demande {
        date date "1er du mois"
        string canton_id
        string pays_id
        int arrivees
        int nuitees
    }
    fact_offre {
        date date "1er du mois"
        string canton_id
        int etablissements
        int chambres
        int lits
        int nuitees_chambres
        int capacite_chambres_jours
        int capacite_lits_jours
        float taux_occ_chambres_ofs
    }
    dim_canton {
        string canton_id
        string canton
        string abreviation
        string grande_region
        string langue
    }
    dim_pays {
        string pays_id
        string pays
        string marche "harmonisé dans le temps"
        string continent
    }
    Calendrier {
        date Date "journalier, marqué comme table de dates"
        int Annee
        int Mois
        string Saison
        string Periode_COVID
    }
```

## Grain

| Table | Une ligne représente | Volume |
|---|---|---|
| `fact_demande` | un mois × un canton × un pays de provenance | environ 400 000 lignes |
| `fact_offre` | un mois × un canton | environ 6 800 lignes |

**Pourquoi deux tables de faits et pas une ?** L'offre (chambres, lits) n'existe pas par pays de provenance : la mettre dans la même table que la demande obligerait à la répéter pour chaque pays et fausserait les sommes. Deux faits au grain naturel, reliés par les dimensions communes, évitent ce piège.

## Choix de modélisation

- **Calendrier journalier.** Les faits sont mensuels (datés au 1er du mois), mais les fonctions d'intelligence temporelle de DAX (`SAMEPERIODLASTYEAR`, `TOTALYTD`) exigent une table de dates continue. Le calendrier est donc une table DAX journalière, marquée comme table de dates.
- **Relations à sens unique**, de la dimension vers le fait. `dim_pays` ne filtre que `fact_demande`.
- **Pas de total Suisse stocké.** Les totaux sont toujours calculés par somme, ce qui évite les doubles comptes. Les totaux publiés par l'OFS servent uniquement aux contrôles.
- **Source unique.** Power Query lit les CSV directement sur GitHub (paramètre `BaseUrl`). Une actualisation dans Power BI suffit pour obtenir le dernier mois publié.

## Chaîne de traitement

```mermaid
flowchart LR
    A[API PX-Web de l'OFS<br/>HESTA] -->|GitHub Actions<br/>chaque mois| B[build.py<br/>extraction par année]
    B --> C[CSV en étoile<br/>data/]
    C --> D[Contrôles qualité<br/>pytest]
    D -->|si tout passe| E[Publication<br/>commit]
    E --> F[Power Query<br/>lecture sur GitHub]
    F --> G[Modèle Power BI<br/>mesures DAX]
    G --> H[Rapport 4 pages]
```
