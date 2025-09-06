#!/usr/bin/env python3
"""
Season 7.40 Matchmaking Service for Fortnite Emulator
Implements Season 7.40 specific matchmaking with correct playlist IDs and ticket creation
"""

from flask import jsonify, request
import json
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from .database import get_database

class Season7MatchmakingService:
    def __init__(self):
        self.db = get_database()
        
        # Season 7.40 specific playlist IDs
        self.season7_playlists = {
            # Battle Royale Playlists
            'playlist_defaultsolo': {
                'playlistName': 'Solo',
                'description': 'Battle Royale Solo',
                'gameType': 'BattleRoyale',
                'ratingType': 'None',
                'minPlayers': 1,
                'maxPlayers': 100,
                'maxTeams': 100,
                'maxTeamSize': 1,
                'maxSquadSize': 1,
                'isDefault': True,
                'isEnabled': True,
                'isVisible': True,
                'violator': '',
                'path': 'Athena_Solo'
            },
            'playlist_defaultduo': {
                'playlistName': 'Duos',
                'description': 'Battle Royale Duos',
                'gameType': 'BattleRoyale',
                'ratingType': 'None',
                'minPlayers': 2,
                'maxPlayers': 100,
                'maxTeams': 50,
                'maxTeamSize': 2,
                'maxSquadSize': 2,
                'isDefault': True,
                'isEnabled': True,
                'isVisible': True,
                'violator': '',
                'path': 'Athena_Duo'
            },
            'playlist_defaultsquad': {
                'playlistName': 'Squads',
                'description': 'Battle Royale Squads',
                'gameType': 'BattleRoyale',
                'ratingType': 'None',
                'minPlayers': 1,
                'maxPlayers': 100,
                'maxTeams': 25,
                'maxTeamSize': 4,
                'maxSquadSize': 4,
                'isDefault': True,
                'isEnabled': True,
                'isVisible': True,
                'violator': '',
                'path': 'Athena_Squad'
            },
            # Season 7 LTMs
            'playlist_ltm_close': {
                'playlistName': 'Close Encounters',
                'description': 'Shotguns and Jetpacks only!',
                'gameType': 'BattleRoyale',
                'ratingType': 'None',
                'minPlayers': 1,
                'maxPlayers': 100,
                'maxTeams': 100,
                'maxTeamSize': 1,
                'maxSquadSize': 1,
                'isDefault': False,
                'isEnabled': True,
                'isVisible': True,
                'violator': 'LTM',
                'path': 'Athena_CloseEncounters'
            },
            'playlist_ltm_disco': {
                'playlistName': 'Disco Domination',
                'description': 'Capture and hold the dance floors!',
                'gameType': 'BattleRoyale',
                'ratingType': 'None',
                'minPlayers': 1,
                'maxPlayers': 100,
                'maxTeams': 2,
                'maxTeamSize': 50,
                'maxSquadSize': 4,
                'isDefault': False,
                'isEnabled': True,
                'isVisible': True,
                'violator': 'LTM',
                'path': 'Athena_DiscoDomination'
            },
            # Creative Mode
            'playlist_creative': {
                'playlistName': 'Creative',
                'description': 'Build, play, and explore!',
                'gameType': 'Creative',
                'ratingType': 'None',
                'minPlayers': 1,
                'maxPlayers': 16,
                'maxTeams': 16,
                'maxTeamSize': 1,
                'maxSquadSize': 4,
                'isDefault': False,
                'isEnabled': True,
                'isVisible': True,
                'violator': 'NEW',
                'path': 'Creative_PlayOnly'
            },
            # Playground (Season 7)
            'playlist_playground': {
                'playlistName': 'Playground',
                'description': 'Practice and explore with friends!',
                'gameType': 'Playground',
                'ratingType': 'None',
                'minPlayers': 1,
                'maxPlayers': 16,
                'maxTeams': 4,
                'maxTeamSize': 4,
                'maxSquadSize': 4,
                'isDefault': False,
                'isEnabled': True,
                'isVisible': True,
                'violator': '',
                'path': 'Athena_Playground'
            }
        }
        
        # Active matchmaking tickets
        self.active_tickets: Dict[str, Dict[str, Any]] = {}
        
        # Matchmaking regions for Season 7.40
        self.regions = {
            'NAE': 'North America East',
            'NAW': 'North America West', 
            'EU': 'Europe',
            'OCE': 'Oceania',
            'BR': 'Brazil',
            'ASIA': 'Asia'
        }
    
    def get_playlists(self) -> Dict[str, Any]:
        """Get available playlists for Season 7.40"""
        try:
            return {
                'playlists': list(self.season7_playlists.values()),
                'lastModified': datetime.utcnow().isoformat() + 'Z',
                'cacheExpire': (datetime.utcnow() + timedelta(hours=1)).isoformat() + 'Z'
            }
        except Exception as e:
            return {
                'error': f'Failed to get playlists: {str(e)}'
            }
    
    def create_matchmaking_ticket(self, account_id: str, playlist_id: str, region: str = 'NAE', party_player_ids: List[str] = None) -> Dict[str, Any]:
        """Create matchmaking ticket for Season 7.40"""
        try:
            # Validate playlist
            if playlist_id not in self.season7_playlists:
                return {
                    'errorCode': 'errors.com.epicgames.fortnite.playlist_not_found',
                    'errorMessage': f'Playlist {playlist_id} not found',
                    'messageVars': [playlist_id],
                    'numericErrorCode': 16036,
                    'originatingService': 'fortnite',
                    'intent': 'prod-live'
                }, 404
            
            # Validate region
            if region not in self.regions:
                region = 'NAE'  # Default to NAE
            
            playlist = self.season7_playlists[playlist_id]
            
            # Create ticket ID
            ticket_id = secrets.token_hex(16)
            
            # Prepare party player IDs
            if party_player_ids is None:
                party_player_ids = [account_id]
            elif account_id not in party_player_ids:
                party_player_ids.append(account_id)
            
            # Validate party size
            if len(party_player_ids) > playlist['maxSquadSize']:
                return {
                    'errorCode': 'errors.com.epicgames.fortnite.party_too_large',
                    'errorMessage': f'Party size {len(party_player_ids)} exceeds maximum {playlist["maxSquadSize"]} for playlist {playlist_id}',
                    'messageVars': [str(len(party_player_ids)), str(playlist['maxSquadSize']), playlist_id],
                    'numericErrorCode': 16037,
                    'originatingService': 'fortnite',
                    'intent': 'prod-live'
                }, 400
            
            # Create ticket data
            ticket_data = {
                'ticketId': ticket_id,
                'matchmakingResult': 'Searching',
                'expectedWaitTimeSec': 30,
                'status': 'Waiting',
                'queuedPlayers': len(party_player_ids),
                'estimatedWaitTime': 30,
                'ticketType': 'mms-player',
                'payload': {
                    'playlistId': playlist_id,
                    'playlistName': playlist['playlistName'],
                    'region': region,
                    'partyPlayerIds': party_player_ids,
                    'bucketId': f'{playlist_id}:{region}',
                    'attributes': {
                        'player.skill': 1.0,
                        'player.option.spectator': 'false',
                        'player.option.crossplay': 'true',
                        'player.input': 'KBM',
                        'player.platform': 'Windows'
                    }
                },
                'createdAt': datetime.utcnow().isoformat() + 'Z',
                'updatedAt': datetime.utcnow().isoformat() + 'Z'
            }
            
            # Store ticket
            self.active_tickets[ticket_id] = ticket_data
            
            return ticket_data
            
        except Exception as e:
            return {
                'errorCode': 'errors.com.epicgames.common.server_error',
                'errorMessage': 'Internal server error',
                'messageVars': [],
                'numericErrorCode': 1000,
                'originatingService': 'fortnite',
                'intent': 'prod-live'
            }, 500
    
    def get_matchmaking_ticket(self, ticket_id: str) -> Dict[str, Any]:
        """Get matchmaking ticket status"""
        try:
            if ticket_id not in self.active_tickets:
                return {
                    'errorCode': 'errors.com.epicgames.fortnite.ticket_not_found',
                    'errorMessage': f'Ticket {ticket_id} not found',
                    'messageVars': [ticket_id],
                    'numericErrorCode': 16038,
                    'originatingService': 'fortnite',
                    'intent': 'prod-live'
                }, 404
            
            ticket = self.active_tickets[ticket_id]
            
            # Simulate matchmaking progression
            created_time = datetime.fromisoformat(ticket['createdAt'].replace('Z', '+00:00'))
            elapsed_seconds = (datetime.utcnow().replace(tzinfo=created_time.tzinfo) - created_time).total_seconds()
            
            if elapsed_seconds > 60:  # After 1 minute, simulate match found
                ticket['matchmakingResult'] = 'SessionAssignment'
                ticket['status'] = 'SessionAssignment'
                ticket['sessionId'] = secrets.token_hex(16)
                ticket['sessionKey'] = secrets.token_hex(32)
                ticket['serverAddress'] = '127.0.0.1:7777'
                ticket['serverPort'] = 7777
            elif elapsed_seconds > 30:  # After 30 seconds, show as matching
                ticket['matchmakingResult'] = 'Matching'
                ticket['status'] = 'Matching'
                ticket['expectedWaitTimeSec'] = max(0, 60 - int(elapsed_seconds))
            
            ticket['updatedAt'] = datetime.utcnow().isoformat() + 'Z'
            return ticket
            
        except Exception as e:
            return {
                'errorCode': 'errors.com.epicgames.common.server_error',
                'errorMessage': 'Internal server error',
                'messageVars': [],
                'numericErrorCode': 1000,
                'originatingService': 'fortnite',
                'intent': 'prod-live'
            }, 500
    
    def cancel_matchmaking_ticket(self, ticket_id: str) -> Dict[str, Any]:
        """Cancel matchmaking ticket"""
        try:
            if ticket_id not in self.active_tickets:
                return {
                    'errorCode': 'errors.com.epicgames.fortnite.ticket_not_found',
                    'errorMessage': f'Ticket {ticket_id} not found',
                    'messageVars': [ticket_id],
                    'numericErrorCode': 16038,
                    'originatingService': 'fortnite',
                    'intent': 'prod-live'
                }, 404
            
            # Remove ticket
            del self.active_tickets[ticket_id]
            
            return {
                'ticketId': ticket_id,
                'status': 'Cancelled',
                'cancelledAt': datetime.utcnow().isoformat() + 'Z'
            }
            
        except Exception as e:
            return {
                'errorCode': 'errors.com.epicgames.common.server_error',
                'errorMessage': 'Internal server error',
                'messageVars': [],
                'numericErrorCode': 1000,
                'originatingService': 'fortnite',
                'intent': 'prod-live'
            }, 500
    
    def find_player(self, player_id: str) -> List[Dict[str, Any]]:
        """Find player in matchmaking (Season 7.40 compatible)"""
        try:
            # Check if player has active tickets
            player_tickets = []
            for ticket_id, ticket in self.active_tickets.items():
                if player_id in ticket['payload']['partyPlayerIds']:
                    player_tickets.append({
                        'ticketId': ticket_id,
                        'status': ticket['status'],
                        'playlist': ticket['payload']['playlistId'],
                        'region': ticket['payload']['region']
                    })
            
            return player_tickets
            
        except Exception as e:
            return []
    
    def get_matchmaking_stats(self) -> Dict[str, Any]:
        """Get matchmaking statistics"""
        try:
            stats = {
                'activeTickets': len(self.active_tickets),
                'playlistStats': {},
                'regionStats': {},
                'lastUpdated': datetime.utcnow().isoformat() + 'Z'
            }
            
            # Count by playlist
            for ticket in self.active_tickets.values():
                playlist_id = ticket['payload']['playlistId']
                region = ticket['payload']['region']
                
                if playlist_id not in stats['playlistStats']:
                    stats['playlistStats'][playlist_id] = 0
                stats['playlistStats'][playlist_id] += 1
                
                if region not in stats['regionStats']:
                    stats['regionStats'][region] = 0
                stats['regionStats'][region] += 1
            
            return stats
            
        except Exception as e:
            return {
                'error': f'Failed to get matchmaking stats: {str(e)}'
            }
    
    def cleanup_expired_tickets(self, max_age_minutes: int = 10):
        """Clean up expired matchmaking tickets"""
        try:
            current_time = datetime.utcnow()
            expired_tickets = []
            
            for ticket_id, ticket in self.active_tickets.items():
                created_time = datetime.fromisoformat(ticket['createdAt'].replace('Z', '+00:00'))
                age_minutes = (current_time.replace(tzinfo=created_time.tzinfo) - created_time).total_seconds() / 60
                
                if age_minutes > max_age_minutes:
                    expired_tickets.append(ticket_id)
            
            # Remove expired tickets
            for ticket_id in expired_tickets:
                del self.active_tickets[ticket_id]
            
            return len(expired_tickets)
            
        except Exception as e:
            print(f"Error cleaning up expired tickets: {e}")
            return 0
    
    def handle_matchmaking_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle generic matchmaking request"""
        try:
            # Extract request parameters
            playlist_id = request_data.get('playlistId', 'playlist_defaultsolo')
            region = request_data.get('region', 'NAE')
            party_player_ids = request_data.get('partyPlayerIds', [])
            
            # Get account ID from first party member or generate one
            account_id = party_player_ids[0] if party_player_ids else secrets.token_hex(16)
            
            # Create matchmaking ticket
            return self.create_matchmaking_ticket(account_id, playlist_id, region, party_player_ids)
            
        except Exception as e:
            return {
                'errorCode': 'errors.com.epicgames.common.server_error',
                'errorMessage': 'Internal server error',
                'messageVars': [],
                'numericErrorCode': 1000,
                'originatingService': 'fortnite',
                'intent': 'prod-live'
            }, 500