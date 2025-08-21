# Filtrage strict des données - v4.py

## Nouvelle fonctionnalité ajoutée

Le script `v4.py` inclut maintenant un **filtrage strict des données** qui supprime automatiquement les lignes avec des valeurs manquantes sur les éléments essentiels.

## Données vérifiées par le filtrage strict

Le filtrage vérifie que **TOUTES** ces données sont présentes et non vides :

### 1. **Noms des joueurs (P1-P6)**
- `P1`, `P2`, `P3` : Joueurs de l'équipe A  
- `P4`, `P5`, `P6` : Joueurs de l'équipe B

### 2. **Brawlers sélectionnés (Brawler1-Brawler6)**
- `Brawler1`, `Brawler2`, `Brawler3` : Brawlers équipe A
- `Brawler4`, `Brawler5`, `Brawler6` : Brawlers équipe B

### 3. **Tags des joueurs (Tag1-Tag6)**
- `Tag1`, `Tag2`, `Tag3` : Tags équipe A
- `Tag4`, `Tag5`, `Tag6` : Tags équipe B

### 4. **Bans individuels (Ban1-Ban6)**
- `Ban1`, `Ban2`, `Ban3` : Bans de l'équipe A
- `Ban4`, `Ban5`, `Ban6` : Bans de l'équipe B

### 5. **Bans groupés**
- `banned_brawlers_a` : Liste des bans équipe A
- `banned_brawlers_b` : Liste des bans équipe B

### 6. **Données détaillées des joueurs**
- `team_a_player_1_tag`, `team_a_player_1_brawler`
- `team_a_player_2_tag`, `team_a_player_2_brawler`  
- `team_a_player_3_tag`, `team_a_player_3_brawler`
- `team_b_player_1_tag`, `team_b_player_1_brawler`
- `team_b_player_2_tag`, `team_b_player_2_brawler`
- `team_b_player_3_tag`, `team_b_player_3_brawler`

## Configuration

### Option 1 : Configuration dans le fichier (ligne 28)
```python
# Filtrage strict des données (supprime les lignes avec données manquantes)
STRICT_DATA_FILTERING = True   # ← Modifiez cette ligne
```

**Valeurs possibles :**
- `True` : **Filtrage strict** - Supprimer toutes les lignes avec des données manquantes
- `False` : **Filtrage minimal** - Garder les lignes avec au moins quelques bans/picks

### Option 2 : Paramètres en ligne de commande
```bash
# Activer le filtrage strict
python3 v4.py --strict-filtering

# Désactiver le filtrage strict  
python3 v4.py --no-strict-filtering

# Utiliser avec cutoff_date
python3 v4.py --cutoff-date "2024-01-01" --strict-filtering
```

## Comportement

### ✅ Avec filtrage strict (STRICT_DATA_FILTERING = True)
- **Supprime** toutes les lignes où il manque des P, brawlers, tags ou bans
- **Garantit** des données complètes dans le fichier CSV final
- **Peut réduire** significativement le nombre de lignes conservées
- **Recommandé** pour des analyses nécessitant des données complètes

### ⚠️ Avec filtrage minimal (STRICT_DATA_FILTERING = False)  
- **Conserve** les lignes avec au moins quelques bans/picks
- **Permet** d'avoir plus de données même si incomplètes
- **Peut inclure** des lignes avec des champs vides
- **Recommandé** pour maximiser la quantité de données

## Exemples d'utilisation

```bash
# Configuration par défaut (selon le fichier)
python3 v4.py

# Forcer le filtrage strict
python3 v4.py --strict-filtering

# Désactiver le filtrage strict pour cette exécution
python3 v4.py --no-strict-filtering

# Combinaison avec cutoff_date
python3 v4.py --cutoff-date "2024-06-01" --strict-filtering
```

## Logs et traçabilité

Le script affiche dans les logs :
- Le type de filtrage activé au démarrage
- Le nombre de lignes filtrées pour chaque tournoi
- Les statistiques finales de filtrage

Exemple de log :
```
2024-01-01 12:00:00 - INFO - Filtrage strict activé : suppression des lignes avec données manquantes (P, brawlers, tags, bans)
2024-01-01 12:00:05 - DEBUG - Ligne filtrée (données manquantes) - Match 66297854 Set 1
```

## Impact sur les performances

- **Filtrage strict** : Plus de vérifications = légèrement plus lent mais données de meilleure qualité
- **Filtrage minimal** : Moins de vérifications = plus rapide mais données potentiellement incomplètes

## Recommandations

- **Utilisez le filtrage strict** si vous avez besoin de données complètes pour vos analyses
- **Utilisez le filtrage minimal** si vous préférez avoir plus de données même incomplètes
- **Testez les deux modes** pour voir lequel convient le mieux à vos besoins