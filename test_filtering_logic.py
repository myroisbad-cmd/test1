#!/usr/bin/env python3
"""
Test pour vérifier que le filtrage par cutoff_date fonctionne correctement
avec seulement le filtrage final des sets/games
"""

from datetime import datetime
from typing import Optional, Dict, List

def _parse_cutoff_date(cutoff_date: Optional[str]) -> Optional[datetime]:
    """Parse et valide la cutoff_date"""
    if not cutoff_date:
        return None
    
    try:
        # Essayer différents formats de date
        for date_format in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y', '%d/%m/%Y %H:%M:%S']:
            try:
                parsed_date = datetime.strptime(cutoff_date, date_format)
                return parsed_date
            except ValueError:
                continue
        return None
    except Exception:
        return None

def _parse_tournament_date(date_str: str) -> Optional[datetime]:
    """Parse une date de tournoi depuis l'API"""
    if not date_str:
        return None
    
    try:
        # Format ISO 8601 avec Z
        if isinstance(date_str, str):
            if date_str.endswith('Z'):
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                dt = datetime.fromisoformat(date_str)
            # Convertir en naive datetime pour la comparaison
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            return dt
        elif isinstance(date_str, (int, float)):
            # Timestamp en millisecondes ou secondes
            dt = datetime.fromtimestamp(date_str / 1000 if date_str > 1e10 else date_str)
            return dt
    except (ValueError, TypeError):
        pass
    
    return None

def test_new_filtering_logic():
    """Test de la nouvelle logique : pas de filtrage de tournois, seulement des sets"""
    print("=== Test de la nouvelle logique de filtrage ===")
    
    cutoff_date = _parse_cutoff_date("2025-05-30")
    if not cutoff_date:
        print("Erreur: impossible de parser la cutoff_date")
        return
    
    print(f"Cutoff date: {cutoff_date}")
    
    # Données de test basées sur l'exemple JSON fourni
    test_rows = [
        {
            "tournament_id": "151683",
            "tournament_title": "Tournoi Test",
            "tournament_startAt": "2025-05-29 14:39:37",  # Avant cutoff (doit être exclu)
            "match_id": "66297854",
            "set_number": "1",
            "game_winner": "Team A"
        },
        {
            "tournament_id": "151683", 
            "tournament_title": "Tournoi Test",
            "tournament_startAt": "2025-05-29 14:39:37",  # Avant cutoff (doit être exclu)
            "match_id": "66297854",
            "set_number": "2", 
            "game_winner": "Team B"
        },
        {
            "tournament_id": "151684",
            "tournament_title": "Tournoi Récent",
            "tournament_startAt": "2025-05-31 12:00:00",  # Après cutoff (doit être inclus)
            "match_id": "66297855",
            "set_number": "1",
            "game_winner": "Team C"
        },
        {
            "tournament_id": "151685",
            "tournament_title": "Tournoi Futur", 
            "tournament_startAt": "2025-06-01 10:00:00",  # Après cutoff (doit être inclus)
            "match_id": "66297856",
            "set_number": "1",
            "game_winner": "Team D"
        }
    ]
    
    print(f"\\nDonnées originales: {len(test_rows)} lignes")
    for i, row in enumerate(test_rows):
        print(f"  {i+1}. Tournoi {row['tournament_id']}, Set {row['set_number']}, Date: {row['tournament_startAt']}")
    
    # Simuler le filtrage final
    filtered_rows = []
    excluded_count = 0
    
    for row in test_rows:
        tournament_start_str = row.get('tournament_startAt')
        if not tournament_start_str:
            filtered_rows.append(row)
            continue
        
        try:
            tournament_date = _parse_tournament_date(tournament_start_str + "Z")  # Ajouter Z pour ISO format
            if tournament_date and tournament_date < cutoff_date:
                excluded_count += 1
                print(f"  ❌ Exclu: Tournoi {row['tournament_id']}, Set {row['set_number']} (date: {tournament_date})")
                continue
            
            filtered_rows.append(row)
            print(f"  ✅ Inclus: Tournoi {row['tournament_id']}, Set {row['set_number']} (date: {tournament_date})")
            
        except Exception as e:
            print(f"  ⚠️  Erreur: {e}, inclusion par défaut")
            filtered_rows.append(row)
    
    print(f"\\n📊 Résultat du filtrage:")
    print(f"   - Lignes originales: {len(test_rows)}")
    print(f"   - Lignes conservées: {len(filtered_rows)}")  
    print(f"   - Lignes exclues: {excluded_count}")
    
    print(f"\\n✅ Comportement attendu:")
    print(f"   - Tous les tournois sont traités (pas de filtrage au niveau tournoi)")
    print(f"   - Seuls les sets/games antérieurs à {cutoff_date.strftime('%Y-%m-%d')} sont supprimés")
    print(f"   - Dans cet exemple: 2 sets exclus, 2 sets conservés")

if __name__ == "__main__":
    test_new_filtering_logic()