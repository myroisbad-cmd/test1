import requests
import pandas as pd
import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import logging
import sys

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('matcherino_unified.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

class MatcherinoUnifiedManager:
    """Gestionnaire unifié pour les tournois Matcherino avec format CSV spécifique"""
    
    def __init__(self, org_id: int = 1180):
        self.org_id = org_id
        self.base_url = "https://api.matcherino.com/__api"
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://matcherino.com/',
            'Origin': 'https://matcherino.com',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Priority': 'u=4'
        }
        self.processed_tournaments = self._load_processed_tournaments()
        self.all_tournament_data = []  # Stocker toutes les données
        
    def _load_processed_tournaments(self) -> set:
        """Charge la liste des tournois déjà traités"""
        try:
            with open('processed_tournaments.json', 'r') as f:
                return set(json.load(f))
        except FileNotFoundError:
            return set()
    
    def _save_processed_tournaments(self):
        """Sauvegarde la liste des tournois traités"""
        with open('processed_tournaments.json', 'w') as f:
            json.dump(list(self.processed_tournaments), f)
    
    def get_tournaments_activities(self) -> List[Dict]:
        """Récupère la liste des activités/tournois"""
        url = f"{self.base_url}/events/activities"
        all_tournaments = []
        page = 0
        max_pages = 5  # Limiter pour éviter trop de requêtes
        
        while page < max_pages:
            params = {
                'orgId': self.org_id,
                'page': page,
                'pageSize': 50
            }
            
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                if 'body' in data and 'contents' in data['body']:
                    contents = data['body']['contents']
                    if not contents:
                        break
                    
                    # Filtrer pour ne garder que les tournois (bounty)
                    tournaments = [
                        item for item in contents 
                        if item.get('entityKind') == 'bounty' and 
                           item.get('bountyId') and 
                           item.get('bountyTitle')
                    ]
                    
                    all_tournaments.extend(tournaments)
                    
                    if len(contents) < 50:  # Dernière page
                        break
                    
                    page += 1
                else:
                    logging.warning("Format de réponse inattendu pour les activités")
                    break
                    
            except requests.RequestException as e:
                logging.error(f"Erreur lors de la récupération des activités (page {page}): {e}")
                break
            
            time.sleep(0.5)  # Pause entre les requêtes
        
        # Déduplication par bountyId
        unique_tournaments = {}
        for tournament in all_tournaments:
            bounty_id = tournament.get('bountyId')
            if bounty_id:
                unique_tournaments[bounty_id] = tournament
        
        tournaments_list = list(unique_tournaments.values())
        logging.info(f"Récupéré {len(tournaments_list)} tournois uniques")
        return tournaments_list
    
    def is_tournament_finished(self, tournament_activity: Dict) -> bool:
        """Vérifie si un tournoi est terminé en récupérant ses détails"""
        bounty_id = tournament_activity.get('bountyId')
        if not bounty_id:
            return False
        
        # Essayer de récupérer les brackets pour vérifier l'état
        try:
            brackets = self.get_tournament_brackets(bounty_id)
            if not brackets:
                return False
            
            # Vérifier si au moins un bracket est terminé
            for bracket in brackets:
                status = bracket.get('status', '').lower()
                if status in ['completed', 'done']:
                    return True
            
            return False
        except Exception as e:
            logging.debug(f"Impossible de vérifier l'état du tournoi {bounty_id}: {e}")
            return False
    
    def get_tournament_brackets(self, bounty_id: int) -> Optional[List[Dict]]:
        """Récupère les brackets d'un tournoi"""
        url = f"{self.base_url}/brackets"
        params = {
            'bountyId': bounty_id,
            'id': 0,
            'isAdmin': False
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            
            brackets_data = response.json()
            
            # Correction: La structure est {'status': 200, 'body': [bracket]}
            if isinstance(brackets_data, dict) and 'body' in brackets_data:
                brackets_data = brackets_data['body']
            
            if not brackets_data:
                logging.debug(f"Aucune donnée de bracket pour le tournoi {bounty_id}")
                return None
                
            if not isinstance(brackets_data, list):
                brackets_data = [brackets_data]
                
            logging.info(f"Récupéré {len(brackets_data)} brackets pour le tournoi {bounty_id}")
            return brackets_data
            
        except requests.RequestException as e:
            logging.debug(f"Erreur lors de la récupération des brackets pour {bounty_id}: {e}")
            return None
    
    def _has_complete_bans_and_picks(self, row: Dict) -> bool:
        """Vérifie si une ligne a des bans et picks complets"""
        # Vérifier les bans des deux équipes
        if not row.get('banned_brawlers_a') or not row.get('banned_brawlers_b'):
            return False
        
        # Vérifier que chaque équipe a au moins un joueur avec un brawler sélectionné
        team_a_has_picks = False
        team_b_has_picks = False
        
        for i in range(1, 4):  # 3 joueurs par équipe
            if row.get(f'team_a_player_{i}_brawler'):
                team_a_has_picks = True
            if row.get(f'team_b_player_{i}_brawler'):
                team_b_has_picks = True
        
        return team_a_has_picks and team_b_has_picks
    
    def process_tournament_to_csv_format(self, brackets: List[Dict], tournament_activity: Dict) -> List[Dict]:
        """Traite les données du tournoi selon le format CSV spécifié"""
        if not brackets:
            return []
        
        all_rows = []
        
        for bracket in brackets:
            # Construire les mappings pour remplacer les IDs par les noms
            entrant_id_to_name, tag_to_display = self._build_name_mappings(bracket)
            tournament_info = {
                'tournament_id': tournament_activity.get('bountyId', ''),
                'tournament_title': tournament_activity.get('bountyTitle', ''),
                'tournament_status': bracket.get('status', ''),
                'tournament_kind': bracket.get('kind', ''),
                'tournament_startAt': self._format_timestamp(bracket.get('startAt', ''))
            }
            
            matches = bracket.get('matches', [])
            
            for match in matches:
                # Informations de base du match
                match_info = {
                    'match_id': match.get('id', ''),
                    'match_num': match.get('matchNum', ''),
                    'match_status': match.get('status', ''),
                    # Remplacer au maximum les IDs par les noms
                    'winner': entrant_id_to_name.get(match.get('winner', ''), match.get('winner', '')),
                    'entrant_a_id': entrant_id_to_name.get(match.get('entrantA', {}).get('entrantId', ''), match.get('entrantA', {}).get('entrantId', '')),
                    'entrant_a_score': match.get('entrantA', {}).get('score', ''),
                    'entrant_b_id': entrant_id_to_name.get(match.get('entrantB', {}).get('entrantId', ''), match.get('entrantB', {}).get('entrantId', '')),
                    'entrant_b_score': match.get('entrantB', {}).get('score', '')
                }
                
                # Traiter les reports (jeux individuels)
                reports = match.get('reports', [])
                
                if not reports:
                    # Si pas de reports, créer une ligne de base
                    row = {**tournament_info, **match_info}
                    row.update(self._get_empty_game_data())
                    all_rows.append(row)
                else:
                    # Grouper par set_number pour avoir une ligne par set
                    set_groups: Dict[Any, List[Dict]] = {}
                    for report in reports:
                        set_num = report.get('setNumber', 0)
                        set_groups.setdefault(set_num, []).append(report)

                    entrant_a_id = match.get('entrantA', {}).get('entrantId', '')
                    entrant_b_id = match.get('entrantB', {}).get('entrantId', '')

                    for set_num, set_reports in set_groups.items():
                        # Choisir le premier report du set pour extraire bans/picks/map/mode
                        first_report = set_reports[0]

                        # Calculer le score du set (nombre de games gagnés)
                        wins_a = 0
                        wins_b = 0
                        draws = 0
                        for r in set_reports:
                            winner_id = r.get('winner', 0)
                            if winner_id == entrant_a_id:
                                wins_a += 1
                            elif winner_id == entrant_b_id:
                                wins_b += 1
                            else:
                                # Egalité explicite si scoreDraw > 0
                                try:
                                    draws += int(r.get('scoreDraw', 0) or 0)
                                except Exception:
                                    pass

                        # Déterminer le vainqueur du set
                        if wins_a > wins_b:
                            set_winner = entrant_id_to_name.get(entrant_a_id, entrant_a_id)
                        elif wins_b > wins_a:
                            set_winner = entrant_id_to_name.get(entrant_b_id, entrant_b_id)
                        else:
                            set_winner = ''

                        game_info = {
                            'game_number': '',
                            'set_number': set_num,
                            'score_a': wins_a,
                            'score_b': wins_b,
                            'score_draw': draws,
                            'game_winner': set_winner
                        }

                        # Extraire les données détaillées (picks/bans/map/mode) depuis le premier report du set
                        game_details = self._extract_game_details(first_report, match, tag_to_display)

                        # Créer la ligne complète
                        row = {**tournament_info, **match_info, **game_details, **game_info}

                        # Filtrer les lignes avec bans/picks manquants
                        if self._has_complete_bans_and_picks(row):
                            all_rows.append(row)
                        else:
                            logging.debug(f"Ligne filtrée (bans/picks manquants) - Match {match_info.get('match_id', 'N/A')} Set {set_num}")
        
        return all_rows
    
    def _extract_game_details(self, report: Dict, match: Dict, tag_to_display: Dict[str, str]) -> Dict:
        """Extrait les détails d'un jeu (bans, picks, stats)"""
        details = self._get_empty_game_data()
        
        # Correction: Les bans sont dans les équipes du report, pas dans le match
        properties = report.get('properties', {})
        teams = properties.get('teams', [])
        
        # Extraire les bans et les données des équipes
        if len(teams) >= 2:
            # Bans de l'équipe A
            team_a_bans = teams[0].get('bans', [])
            if team_a_bans:
                banned_names_a = [ban.get('name', '') for ban in team_a_bans if ban.get('name')]
                details['banned_brawlers_a'] = ', '.join(banned_names_a)
                # Ban1..Ban3
                for i, ban in enumerate(team_a_bans[:3]):
                    details[f'Ban{i+1}'] = ban.get('name', '')
            
            # Bans de l'équipe B
            team_b_bans = teams[1].get('bans', [])
            if team_b_bans:
                banned_names_b = [ban.get('name', '') for ban in team_b_bans if ban.get('name')]
                details['banned_brawlers_b'] = ', '.join(banned_names_b)
                # Ban4..Ban6
                for i, ban in enumerate(team_b_bans[:3]):
                    details[f'Ban{i+4}'] = ban.get('name', '')
        
        # Extraire les informations de la partie (mode de jeu, carte, durée)
        if 'location' in properties:
            location = properties['location']
            details['mode'] = location.get('gameMode', '')
            details['map'] = location.get('name', '')
        
        details['duration'] = properties.get('duration', '')
        
        # Extraire les données des joueurs
        if len(teams) >= 2:
            # Équipe A (index 0)
            team_a = teams[0]
            team_a_players = team_a.get('players', [])
            for i, player in enumerate(team_a_players[:3]):  # Max 3 joueurs
                player_prefix = f'team_a_player_{i+1}'
                details[f'{player_prefix}_tag'] = player.get('tag', '')
                
                brawler_info = player.get('brawler', {})
                details[f'{player_prefix}_brawler'] = brawler_info.get('name', '')
                
                gadget_info = brawler_info.get('gadget', {})
                details[f'{player_prefix}_gadget'] = gadget_info.get('name', '')
                
                starpower_info = brawler_info.get('starPower', {})
                details[f'{player_prefix}_starpower'] = starpower_info.get('name', '')
                
                stats = player.get('statistics', {})
                details[f'{player_prefix}_kills'] = stats.get('kills', 0)
                details[f'{player_prefix}_deaths'] = stats.get('deaths', 0)
                details[f'{player_prefix}_damage'] = stats.get('damageDealt', 0)
                # P1..P3 (noms), Brawler1..Brawler3, Tag1..Tag3
                tag_value = player.get('tag', '')
                details[f'P{i+1}'] = tag_to_display.get(tag_value, tag_value)
                details[f'Brawler{i+1}'] = brawler_info.get('name', '')
                details[f'Tag{i+1}'] = tag_value
            
            # Équipe B (index 1)
            team_b = teams[1]
            team_b_players = team_b.get('players', [])
            for i, player in enumerate(team_b_players[:3]):  # Max 3 joueurs
                player_prefix = f'team_b_player_{i+1}'
                details[f'{player_prefix}_tag'] = player.get('tag', '')
                
                brawler_info = player.get('brawler', {})
                details[f'{player_prefix}_brawler'] = brawler_info.get('name', '')
                
                gadget_info = brawler_info.get('gadget', {})
                details[f'{player_prefix}_gadget'] = gadget_info.get('name', '')
                
                starpower_info = brawler_info.get('starPower', {})
                details[f'{player_prefix}_starpower'] = starpower_info.get('name', '')
                
                stats = player.get('statistics', {})
                details[f'{player_prefix}_kills'] = stats.get('kills', 0)
                details[f'{player_prefix}_deaths'] = stats.get('deaths', 0)
                details[f'{player_prefix}_damage'] = stats.get('damageDealt', 0)
                # P4..P6 (noms), Brawler4..Brawler6, Tag4..Tag6
                tag_value = player.get('tag', '')
                details[f'P{i+4}'] = tag_to_display.get(tag_value, tag_value)
                details[f'Brawler{i+4}'] = brawler_info.get('name', '')
                details[f'Tag{i+4}'] = tag_value
        
        return details

    def _build_name_mappings(self, bracket: Dict) -> (Dict[Any, str], Dict[str, str]):
        """Construit des mappings utiles: entrantId->teamName, tag->displayName"""
        entrant_id_to_name: Dict[Any, str] = {}
        tag_to_display: Dict[str, str] = {}
        entrants = bracket.get('entrants', []) or []
        for entrant in entrants:
            entrant_id = entrant.get('id') or entrant.get('entrantId')
            team_name = (
                (entrant.get('team') or {}).get('name')
                or entrant.get('name')
                or ''
            )
            if entrant_id is not None and team_name:
                entrant_id_to_name[entrant_id] = team_name
            # Récupérer les noms des joueurs par tag
            team = entrant.get('team') or {}
            members = team.get('members') or []
            for m in members:
                display_name = m.get('displayName') or ''
                participant_info = m.get('participantInfo') or {}
                tag = participant_info.get('gameUsername') or ''
                if tag:
                    tag_to_display[tag] = display_name or tag
        return entrant_id_to_name, tag_to_display
    
    def _get_empty_game_data(self) -> Dict:
        """Retourne un dictionnaire avec toutes les colonnes de jeu vides"""
        return {
            'game_number': '',
            'set_number': '',
            'score_a': '',
            'score_b': '',
            'score_draw': '',
            'game_winner': '',
            'banned_brawlers_a': '',
            'banned_brawlers_b': '',
            'mode': '',
            'map': '',
            'duration': '',
            'P1': '', 'P2': '', 'P3': '', 'P4': '', 'P5': '', 'P6': '',
            'Brawler1': '', 'Brawler2': '', 'Brawler3': '', 'Brawler4': '', 'Brawler5': '', 'Brawler6': '',
            'Ban1': '', 'Ban2': '', 'Ban3': '', 'Ban4': '', 'Ban5': '', 'Ban6': '',
            'Tag1': '', 'Tag2': '', 'Tag3': '', 'Tag4': '', 'Tag5': '', 'Tag6': '',
            'team_a_player_1_tag': '',
            'team_a_player_1_brawler': '',
            'team_a_player_1_gadget': '',
            'team_a_player_1_starpower': '',
            'team_a_player_1_kills': '',
            'team_a_player_1_deaths': '',
            'team_a_player_1_damage': '',
            'team_a_player_2_tag': '',
            'team_a_player_2_brawler': '',
            'team_a_player_2_gadget': '',
            'team_a_player_2_starpower': '',
            'team_a_player_2_kills': '',
            'team_a_player_2_deaths': '',
            'team_a_player_2_damage': '',
            'team_a_player_3_tag': '',
            'team_a_player_3_brawler': '',
            'team_a_player_3_gadget': '',
            'team_a_player_3_starpower': '',
            'team_a_player_3_kills': '',
            'team_a_player_3_deaths': '',
            'team_a_player_3_damage': '',
            'team_b_player_1_tag': '',
            'team_b_player_1_brawler': '',
            'team_b_player_1_gadget': '',
            'team_b_player_1_starpower': '',
            'team_b_player_1_kills': '',
            'team_b_player_1_deaths': '',
            'team_b_player_1_damage': '',
            'team_b_player_2_tag': '',
            'team_b_player_2_brawler': '',
            'team_b_player_2_gadget': '',
            'team_b_player_2_starpower': '',
            'team_b_player_2_kills': '',
            'team_b_player_2_deaths': '',
            'team_b_player_2_damage': '',
            'team_b_player_3_tag': '',
            'team_b_player_3_brawler': '',
            'team_b_player_3_gadget': '',
            'team_b_player_3_starpower': '',
            'team_b_player_3_kills': '',
            'team_b_player_3_deaths': '',
            'team_b_player_3_damage': ''
        }
    
    def _format_timestamp(self, timestamp) -> str:
        """Formate un timestamp en date lisible"""
        if not timestamp:
            return ''
        
        try:
            if isinstance(timestamp, str):
                # Format ISO 8601
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(timestamp, (int, float)):
                dt = datetime.fromtimestamp(timestamp / 1000 if timestamp > 1e10 else timestamp)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError) as e:
            logging.warning(f"Erreur de formatage de timestamp {timestamp}: {e}")
        
        return str(timestamp)
    
    def save_all_tournament_data(self) -> str:
        """Sauvegarde toutes les données des tournois dans un seul fichier CSV"""
        if not self.all_tournament_data:
            logging.warning("Aucune donnée à sauvegarder")
            return ""
        
        filename = "matcherino_all_tournament.csv"
        
        try:
            df = pd.DataFrame(self.all_tournament_data)
            
            # S'assurer que toutes les colonnes du format sont présentes
            expected_columns = [
                'tournament_id', 'tournament_title', 'tournament_status', 'tournament_kind',
                'tournament_startAt',
                # Placer les infos de map/mode au début
                'map', 'mode', 'duration',
                # Infos match
                'match_id', 'match_num', 'match_status', 'winner',
                'entrant_a_id', 'entrant_a_score', 'entrant_b_id', 'entrant_b_score',
                # Infos jeu
                'game_number', 'set_number', 'score_a', 'score_b', 'score_draw', 'game_winner',
                # Joueurs et picks
                'P1','P2','P3','P4','P5','P6',
                'Brawler1','Brawler2','Brawler3','Brawler4','Brawler5','Brawler6',
                # Bans et tags
                'Ban1','Ban2','Ban3','Ban4','Ban5','Ban6',
                'Tag1','Tag2','Tag3','Tag4','Tag5','Tag6',
                # Compatibilité
                'banned_brawlers_a', 'banned_brawlers_b'
            ]
            
            # Ajouter les colonnes des joueurs détaillées (legacy)
            for team in ['team_a', 'team_b']:
                for player_num in range(1, 4):
                    for stat in ['tag', 'brawler', 'gadget', 'starpower', 'kills', 'deaths', 'damage']:
                        expected_columns.append(f'{team}_player_{player_num}_{stat}')
            
            # S'assurer que toutes les colonnes existent, même vides, puis réordonner
            for col in expected_columns:
                if col not in df.columns:
                    df[col] = ''
            df = df[expected_columns]

            # Mode append si le fichier existe déjà
            mode = 'a' if os.path.exists(filename) else 'w'
            header = not os.path.exists(filename)
            df.to_csv(filename, index=False, encoding='utf-8', mode=mode, header=header)
            logging.info(f"Toutes les données sauvegardées dans {filename} ({len(df)} lignes)")
            return filename
            
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde: {e}")
            return ""
    
    def run_complete_process(self):
        """Processus complet : récupération, vérification et traitement"""
        logging.info("Démarrage du processus complet Matcherino")
        
        # Récupérer la liste des tournois
        tournaments = self.get_tournaments_activities()
        if not tournaments:
            logging.info("Aucun tournoi trouvé")
            return
        
        processed_count = 0
        total_games = 0
        filtered_games = 0
        
        for tournament in tournaments:
            bounty_id = tournament.get('bountyId')
            bounty_title = tournament.get('bountyTitle', 'Tournoi sans nom')
            
            if not bounty_id:
                continue
            
            # Vérifier si déjà traité
            if bounty_id in self.processed_tournaments:
                logging.debug(f"Tournoi {bounty_id} déjà traité, ignoré")
                continue
            
            logging.info(f"Vérification du tournoi: '{bounty_title}' (ID: {bounty_id})")
            
            # Vérifier si le tournoi est terminé
            if not self.is_tournament_finished(tournament):
                logging.info(f"Tournoi '{bounty_title}' pas encore terminé")
                continue
            
            logging.info(f"Traitement du tournoi terminé: '{bounty_title}'")
            
            # Récupérer les données complètes du tournoi
            brackets = self.get_tournament_brackets(bounty_id)
            if not brackets:
                logging.warning(f"Impossible de récupérer les brackets pour {bounty_id}")
                continue
            
            # Traiter les données selon le format spécifié
            csv_rows = self.process_tournament_to_csv_format(brackets, tournament)
            
            if csv_rows:
                # Ajouter les données au dataset global
                self.all_tournament_data.extend(csv_rows)
                total_games += len(csv_rows)
                
                # Marquer comme traité
                self.processed_tournaments.add(bounty_id)
                processed_count += 1
                logging.info(f"✅ Tournoi {bounty_id} traité avec succès ({len(csv_rows)} jeux ajoutés)")
            else:
                logging.warning(f"⚠️ Aucune donnée valide pour le tournoi {bounty_id}")
                filtered_games += 1
            
            # Pause entre les traitements pour éviter de surcharger l'API
            time.sleep(2)
        
        # Sauvegarder toutes les données dans un seul fichier CSV
        if self.all_tournament_data:
            csv_file = self.save_all_tournament_data()
            if csv_file:
                logging.info(f"📄 Fichier CSV unifié créé: {csv_file}")
        
        # Sauvegarder la liste des tournois traités
        self._save_processed_tournaments()
        
        logging.info(f"🏁 Processus terminé.")
        logging.info(f"📊 Statistiques:")
        logging.info(f"   - {processed_count} nouveaux tournois traités")
        logging.info(f"   - {total_games} jeux au total")
        logging.info(f"   - {len(self.all_tournament_data)} jeux conservés (avec bans/picks complets)")
        logging.info(f"   - {total_games - len(self.all_tournament_data)} jeux filtrés (bans/picks manquants)")
        
        if processed_count == 0:
            logging.info("ℹ️ Aucun nouveau tournoi terminé à traiter.")

def main():
    """Fonction principale"""
    try:
        manager = MatcherinoUnifiedManager(org_id=1180)
        manager.run_complete_process()
    except KeyboardInterrupt:
        logging.info("Processus interrompu par l'utilisateur")
    except Exception as e:
        logging.error(f"Erreur inattendue: {e}")

if __name__ == "__main__":
    main()