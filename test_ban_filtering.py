#!/usr/bin/env python3
"""
Script de test pour vérifier le filtrage des bans Ban1-Ban6
"""

import sys
import os

# Ajouter le répertoire parent au path pour importer le module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importer la classe depuis v5(2).py
exec(open('v5 (2).py').read())

def test_ban_filtering():
    """Teste le filtrage des bans Ban1-Ban6"""
    
    # Créer une instance du manager
    manager = MatcherinoUnifiedManager()
    
    # Test 1: Ligne avec tous les bans présents (devrait être acceptée)
    row_complete = {
        'banned_brawlers_a': 'Shelly, Colt',
        'banned_brawlers_b': 'Bull, Rosa',
        'Ban1': 'Shelly',
        'Ban2': 'Colt', 
        'Ban3': 'Bull',
        'Ban4': 'Rosa',
        'Ban5': 'Spike',
        'Ban6': 'Leon',
        'team_a_player_1_brawler': 'Edgar',
        'team_b_player_1_brawler': 'Mortis'
    }
    
    # Test 2: Ligne avec des bans manquants (devrait être rejetée)
    row_incomplete = {
        'banned_brawlers_a': 'Shelly, Colt',
        'banned_brawlers_b': 'Bull, Rosa', 
        'Ban1': 'Shelly',
        'Ban2': 'Colt',
        'Ban3': 'Bull',
        'Ban4': 'Rosa',
        'Ban5': '',  # Ban manquant
        'Ban6': '',  # Ban manquant
        'team_a_player_1_brawler': 'Edgar',
        'team_b_player_1_brawler': 'Mortis'
    }
    
    # Test 3: Ligne similaire à l'exemple de l'utilisateur (tous les bans vides)
    row_like_user_example = {
        'banned_brawlers_a': '',
        'banned_brawlers_b': '',
        'Ban1': '',
        'Ban2': '',
        'Ban3': '',
        'Ban4': '',
        'Ban5': '',
        'Ban6': '',
        'team_a_player_1_brawler': 'Edgar',
        'team_b_player_1_brawler': 'Mortis'
    }
    
    print("=== Test du filtrage des bans ===")
    
    # Test avec filtrage strict
    print("\n1. Test avec STRICT_DATA_FILTERING=True:")
    result1 = manager._has_complete_data(row_complete)
    result2 = manager._has_complete_data(row_incomplete) 
    result3 = manager._has_complete_data(row_like_user_example)
    
    print(f"   Ligne complète: {result1} (attendu: False car P1-P6 manquants)")
    print(f"   Ligne incomplète: {result2} (attendu: False)")
    print(f"   Ligne comme exemple utilisateur: {result3} (attendu: False)")
    
    # Test avec filtrage minimal
    print("\n2. Test avec filtrage minimal (_has_complete_bans_and_picks):")
    result4 = manager._has_complete_bans_and_picks(row_complete)
    result5 = manager._has_complete_bans_and_picks(row_incomplete)
    result6 = manager._has_complete_bans_and_picks(row_like_user_example)
    
    print(f"   Ligne complète: {result4} (attendu: True)")
    print(f"   Ligne incomplète: {result5} (attendu: False)")
    print(f"   Ligne comme exemple utilisateur: {result6} (attendu: False)")
    
    print("\n=== Résumé ===")
    print("✅ Modification appliquée: _has_complete_bans_and_picks vérifie maintenant Ban1-Ban6")
    print("✅ Les lignes sans bans complets seront maintenant filtrées même en mode minimal")
    
    return result4 and not result5 and not result6

if __name__ == "__main__":
    success = test_ban_filtering()
    if success:
        print("\n🎉 Test réussi! Le filtrage fonctionne correctement.")
    else:
        print("\n❌ Test échoué!")
        sys.exit(1)