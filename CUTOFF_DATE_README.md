# Fonctionnalité Cutoff Date - v4.py

## Résumé des modifications

Le fichier `v4.py` a été modifié pour ajouter une fonctionnalité de **cutoff_date** qui permet de supprimer toutes les lignes de données antérieures à une date spécifiée.

## Nouvelles fonctionnalités

### 1. Paramètre cutoff_date dans le constructeur
- Nouveau paramètre optionnel `cutoff_date` dans `MatcherinoUnifiedManager.__init__()`
- Support de multiples formats de date

### 2. Filtrage à deux niveaux
- **Niveau tournoi** : Les tournois antérieurs à la cutoff_date sont exclus du traitement
- **Niveau données** : Les lignes individuelles antérieures à la cutoff_date sont filtrées

### 3. Interface en ligne de commande
- Nouveau paramètre `--cutoff-date` pour spécifier la date de coupure
- Paramètre `--org-id` pour changer l'organisation (défaut: 1180)
- Aide détaillée avec exemples d'utilisation

## Formats de date supportés

- `YYYY-MM-DD` (ex: 2024-01-01)
- `YYYY-MM-DD HH:MM:SS` (ex: 2024-01-01 12:00:00)
- `DD/MM/YYYY` (ex: 01/01/2024)
- `DD/MM/YYYY HH:MM:SS` (ex: 01/01/2024 12:00:00)

## Exemples d'utilisation

```bash
# Exécution normale sans filtre
python3 v4.py

# Filtrer les données antérieures au 1er janvier 2024
python3 v4.py --cutoff-date "2024-01-01"

# Filtrer avec une heure spécifique
python3 v4.py --cutoff-date "2024-01-01 12:00:00"

# Format français
python3 v4.py --cutoff-date "01/01/2024"

# Changer l'organisation et la date
python3 v4.py --org-id 1180 --cutoff-date "2024-06-01"

# Afficher l'aide
python3 v4.py --help
```

## Méthodes ajoutées

### `_parse_cutoff_date(cutoff_date: str) -> Optional[datetime]`
Parse et valide la cutoff_date fournie en paramètre.

### `_should_exclude_tournament_by_date(tournament_activity: Dict) -> bool`
Vérifie si un tournoi doit être exclu basé sur sa date de début.

### `_parse_tournament_date(date_str: str) -> Optional[datetime]`
Parse les dates de tournoi depuis l'API Matcherino (formats ISO 8601 et timestamps).

### `_filter_data_by_cutoff_date(data_rows: List[Dict]) -> List[Dict]`
Filtre les lignes de données finales basé sur la cutoff_date.

## Logique de filtrage

1. **Parsing de la cutoff_date** : La date est parsée au démarrage et convertie en objet datetime
2. **Filtrage des tournois** : Avant de traiter un tournoi, sa date est comparée à la cutoff_date
3. **Filtrage final** : Après traitement de tous les tournois, les lignes individuelles sont filtrées
4. **Gestion des erreurs** : En cas d'erreur de parsing, les données sont incluses par défaut
5. **Logging** : Toutes les exclusions sont loggées pour traçabilité

## Compatibilité

- Les modifications sont rétrocompatibles
- Sans paramètre `--cutoff-date`, le comportement reste identique à la version précédente
- Toutes les fonctionnalités existantes sont préservées

## Gestion des timezones

Les dates avec timezone sont automatiquement converties en datetime naïfs pour éviter les erreurs de comparaison.