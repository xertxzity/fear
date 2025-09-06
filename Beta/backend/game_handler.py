#!/usr/bin/env python3
"""
Game Handler for Fortnite Season 7 Emulator
Handles game profiles, matchmaking, and player data
"""

from flask import jsonify, request
import json
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, List
from .database import get_database

class GameHandler:
    def __init__(self):
        # Database connection
        self.db = get_database()
        
        # Default profile data for Season 7
        self.default_profiles = {
            'athena': self._create_athena_profile(),
            'common_core': self._create_common_core_profile(),
            'common_public': self._create_common_public_profile(),
            'campaign': self._create_campaign_profile(),
            'metadata': self._create_metadata_profile(),
            'creative': self._create_creative_profile()
        }
        
        # Store player profiles (in-memory cache)
        self.player_profiles = {}
        
        # Battle Pass data
        self.battle_pass_data = self._create_battle_pass_data()
        
        # Social features (temporary in-memory for real-time features)
        self.parties = {}
        self.friend_requests = {}
        self.player_presence = {}
        
        # Competitive data
        self.arena_divisions = self._create_arena_divisions()
        self.tournaments = {}
        self.leaderboards = {}
    
    def _create_athena_profile(self) -> Dict[str, Any]:
        """Create default Athena (Battle Royale) profile"""
        return {
            'profileRevision': 1,
            'profileId': 'athena',
            'profileChangesBaseRevision': 1,
            'profileChanges': [],
            'profileCommandRevision': 1,
            'serverTime': datetime.utcnow().isoformat() + 'Z',
            'responseVersion': 1,
            'items': {
                # Default Season 7 items
                'AthenaCharacter:CID_028_Athena_Commando_F': {
                    'templateId': 'AthenaCharacter:CID_028_Athena_Commando_F',
                    'attributes': {
                        'max_level_bonus': 0,
                        'level': 1,
                        'item_seen': True,
                        'xp': 0,
                        'variants': [],
                        'favorite': False
                    },
                    'quantity': 1
                },
                'AthenaPickaxe:DefaultPickaxe': {
                    'templateId': 'AthenaPickaxe:DefaultPickaxe',
                    'attributes': {
                        'level': 1,
                        'item_seen': True,
                        'favorite': False
                    },
                    'quantity': 1
                },
                'AthenaGlider:DefaultGlider': {
                    'templateId': 'AthenaGlider:DefaultGlider',
                    'attributes': {
                        'level': 1,
                        'item_seen': True,
                        'favorite': False
                    },
                    'quantity': 1
                }
            },
            'stats': {
                'attributes': {
                    'season_match_boost': 0,
                    'loadouts': [],
                    'rested_xp_overflow': 0,
                    'mfa_reward_claimed': True,
                    'quest_manager': {},
                    'book_level': 1,
                    'season_num': 7,
                    'season_update': 0,
                    'book_xp': 0,
                    'permissions': [],
                    'season': {
                        'numWins': 0,
                        'numHighBracket': 0,
                        'numLowBracket': 0
                    },
                    'vote_data': {},
                    'lifetime_wins': 0,
                    'party_assist_quest': '',
                    'purchased_battle_pass_tier_offers': {},
                    'rested_xp_exchange': 1,
                    'level': 1,
                    'rested_xp': 0,
                    'rested_xp_mult': 1.25,
                    'accountLevel': 1,
                    'competitive_identity': {},
                    'inventory_limit_bonus': 0,
                    'last_applied_loadout': '',
                    'daily_rewards': {},
                    'xp': 0,
                    'season_friend_match_boost': 0,
                    'active_loadout_index': 0
                }
            }
        }
    
    def _create_common_core_profile(self) -> Dict[str, Any]:
        """Create default Common Core profile"""
        return {
            'profileRevision': 1,
            'profileId': 'common_core',
            'profileChangesBaseRevision': 1,
            'profileChanges': [],
            'profileCommandRevision': 1,
            'serverTime': datetime.utcnow().isoformat() + 'Z',
            'responseVersion': 1,
            'items': {
                'Currency:MtxPurchased': {
                    'templateId': 'Currency:MtxPurchased',
                    'attributes': {
                        'platform': 'Shared'
                    },
                    'quantity': 0
                }
            },
            'stats': {
                'attributes': {
                    'survey_data': {},
                    'personal_offers': {},
                    'intro_game_played': True,
                    'import_friends_claimed': {},
                    'mtx_purchase_history': {},
                    'undo_cooldowns': {},
                    'mtx_affiliate_set_time': '2019-02-14T17:36:10.335Z',
                    'inventory_limit_bonus': 0,
                    'current_mtx_platform': 'EpicPC',
                    'mtx_affiliate': '',
                    'weekly_purchases': {},
                    'daily_purchases': {},
                    'ban_history': {},
                    'in_app_purchases': {},
                    'permissions': [],
                    'undo_timeout': '9999-12-31T23:59:59.999Z',
                    'monthly_purchases': {},
                    'allowed_to_send_gifts': True,
                    'mfa_enabled': True,
                    'allowed_to_receive_gifts': True,
                    'gift_history': {}
                }
            }
        }
    
    def _create_common_public_profile(self) -> Dict[str, Any]:
        """Create default Common Public profile"""
        return {
            'profileRevision': 1,
            'profileId': 'common_public',
            'profileChangesBaseRevision': 1,
            'profileChanges': [],
            'profileCommandRevision': 1,
            'serverTime': datetime.utcnow().isoformat() + 'Z',
            'responseVersion': 1,
            'items': {},
            'stats': {
                'attributes': {
                    'banner_icon': 'StandardBanner1',
                    'banner_color': 'DefaultColor1',
                    'homebase_name': 'FortnitePlayer\'s Homebase',
                    'personal_offers': {},
                    'banner_icon_template': '',
                    'banner_color_template': ''
                }
            }
        }
    
    def _create_campaign_profile(self) -> Dict[str, Any]:
        """Create default Campaign (Save the World) profile"""
        return {
            'profileRevision': 1,
            'profileId': 'campaign',
            'profileChangesBaseRevision': 1,
            'profileChanges': [],
            'profileCommandRevision': 1,
            'serverTime': datetime.utcnow().isoformat() + 'Z',
            'responseVersion': 1,
            'items': {},
            'stats': {
                'attributes': {
                    'game_purchased': False,
                    'book_purchased': False,
                    'level': 1,
                    'xp': 0,
                    'homebase_name': 'FortnitePlayer\'s Homebase'
                }
            }
        }
    
    def _create_metadata_profile(self) -> Dict[str, Any]:
        """Create default Metadata profile"""
        return {
            'profileRevision': 1,
            'profileId': 'metadata',
            'profileChangesBaseRevision': 1,
            'profileChanges': [],
            'profileCommandRevision': 1,
            'serverTime': datetime.utcnow().isoformat() + 'Z',
            'responseVersion': 1,
            'items': {},
            'stats': {
                'attributes': {}
            }
        }
    
    def _create_creative_profile(self) -> Dict[str, Any]:
        """Create Creative Mode profile"""
        return {
            'profileRevision': 1,
            'profileId': 'creative',
            'profileChangesBaseRevision': 1,
            'profileChanges': [],
            'profileCommandRevision': 1,
            'serverTime': datetime.utcnow().isoformat() + 'Z',
            'responseVersion': 1,
            'items': {
                'CreativeIsland:DefaultIsland': {
                    'templateId': 'CreativeIsland:DefaultIsland',
                    'attributes': {
                        'island_code': 'DEFAULT',
                        'island_name': 'My Island',
                        'created_at': datetime.utcnow().isoformat() + 'Z',
                        'published': False,
                        'plays': 0,
                        'likes': 0
                    },
                    'quantity': 1
                }
            },
            'stats': {
                'attributes': {
                    'islands_created': 1,
                    'islands_published': 0,
                    'total_plays': 0
                }
            }
        }
    
    def _create_battle_pass_data(self) -> Dict[str, Any]:
        """Create Season 7 Battle Pass data"""
        return {
            'season': 7,
            'max_tier': 100,
            'tiers': {
                str(i): {
                    'tier': i,
                    'stars_required': 10 if i <= 100 else 0,
                    'free_reward': f'FreeReward_T{i:02d}',
                    'premium_reward': f'PremiumReward_T{i:02d}' if i <= 100 else None,
                    'unlocked': False
                } for i in range(1, 101)
            },
            'challenges': {
                'daily': self._create_daily_challenges(),
                'weekly': self._create_weekly_challenges()
            }
        }
    
    def _create_arena_divisions(self) -> Dict[str, Any]:
        """Create Arena divisions for competitive play"""
        return {
            'open': {'name': 'Open League', 'min_points': 0, 'max_points': 124},
            'contender': {'name': 'Contender League', 'min_points': 125, 'max_points': 1999},
            'champion': {'name': 'Champion League', 'min_points': 2000, 'max_points': 9999}
        }
    
    def _create_daily_challenges(self) -> List[Dict[str, Any]]:
        """Create daily challenges"""
        return [
            {
                'id': 'daily_1',
                'name': 'Deal damage to opponents',
                'description': 'Deal 500 damage to opponents',
                'progress': 0,
                'target': 500,
                'reward': 'BattlePassXP:500',
                'completed': False
            },
            {
                'id': 'daily_2',
                'name': 'Outlast opponents',
                'description': 'Outlast 150 opponents',
                'progress': 0,
                'target': 150,
                'reward': 'BattlePassXP:500',
                'completed': False
            }
        ]
    
    def _create_weekly_challenges(self) -> List[Dict[str, Any]]:
        """Create weekly challenges"""
        return [
            {
                'id': 'week1_1',
                'name': 'Search chests',
                'description': 'Search 7 chests',
                'progress': 0,
                'target': 7,
                'reward': 'BattlePassStar:5',
                'completed': False
            },
            {
                'id': 'week1_2',
                'name': 'Eliminate opponents',
                'description': 'Eliminate 10 opponents',
                'progress': 0,
                'target': 10,
                'reward': 'BattlePassStar:5',
                'completed': False
            }
        ]
    
    def get_player_profile(self, account_id: str, profile_id: str) -> Dict[str, Any]:
        """Get or create player profile"""
        if account_id not in self.player_profiles:
            self.player_profiles[account_id] = {}
        
        if profile_id not in self.player_profiles[account_id]:
            # Create new profile from default
            if profile_id in self.default_profiles:
                self.player_profiles[account_id][profile_id] = json.loads(
                    json.dumps(self.default_profiles[profile_id])
                )
            else:
                # Unknown profile, return empty
                self.player_profiles[account_id][profile_id] = {
                    'profileRevision': 1,
                    'profileId': profile_id,
                    'profileChangesBaseRevision': 1,
                    'profileChanges': [],
                    'profileCommandRevision': 1,
                    'serverTime': datetime.utcnow().isoformat() + 'Z',
                    'responseVersion': 1,
                    'items': {},
                    'stats': {'attributes': {}}
                }
        
        return self.player_profiles[account_id][profile_id]
    
    def handle_profile_command(self, account_id: str, command: str, request) -> Dict[str, Any]:
        """Handle profile command requests"""
        try:
            # Get request data
            data = request.get_json() or {}
            profile_id = data.get('profileId', 'athena')
            
            # Get player profile
            profile = self.get_player_profile(account_id, profile_id)
            
            # Update server time
            profile['serverTime'] = datetime.utcnow().isoformat() + 'Z'
            
            # Handle specific commands
            if command == 'QueryProfile':
                return jsonify(profile)
            
            elif command == 'ClientQuestLogin':
                # Handle quest login
                profile['profileChanges'] = []
                return jsonify(profile)
            
            elif command == 'MarkItemSeen':
                # Mark items as seen
                item_ids = data.get('itemIds', [])
                for item_id in item_ids:
                    if item_id in profile['items']:
                        profile['items'][item_id]['attributes']['item_seen'] = True
                
                profile['profileRevision'] += 1
                profile['profileCommandRevision'] += 1
                return jsonify(profile)
            
            elif command == 'SetItemFavoriteStatusBatch':
                # Set item favorite status
                item_favorite_status_pairs = data.get('itemFavoriteStatusPairs', [])
                for pair in item_favorite_status_pairs:
                    item_id = pair.get('itemId')
                    favorite = pair.get('bFavorite', False)
                    
                    if item_id in profile['items']:
                        profile['items'][item_id]['attributes']['favorite'] = favorite
                
                profile['profileRevision'] += 1
                profile['profileCommandRevision'] += 1
                return jsonify(profile)
            
            elif command == 'EquipBattleRoyaleCustomization':
                # Handle cosmetic equipping
                slot_name = data.get('slotName', '')
                item_to_slot = data.get('itemToSlot', '')
                index_within_slot = data.get('indexWithinSlot', 0)
                
                # Update loadout (simplified)
                if 'loadouts' not in profile['stats']['attributes']:
                    profile['stats']['attributes']['loadouts'] = []
                
                profile['profileRevision'] += 1
                profile['profileCommandRevision'] += 1
                return jsonify(profile)
            
            elif command == 'SetBattleRoyaleBanner':
                # Set banner
                banner_icon_template = data.get('homebaseBannerIconId', '')
                banner_color_template = data.get('homebaseBannerColorId', '')
                
                profile['stats']['attributes']['banner_icon_template'] = banner_icon_template
                profile['stats']['attributes']['banner_color_template'] = banner_color_template
                
                profile['profileRevision'] += 1
                profile['profileCommandRevision'] += 1
                return jsonify(profile)
            
            else:
                # Unknown command, return profile as-is
                return jsonify(profile)
        
        except Exception as e:
            return jsonify({
                'errorCode': 'errors.com.epicgames.fortnite.operation_forbidden',
                'errorMessage': f'Operation {command} is not supported',
                'messageVars': [command],
                'numericErrorCode': 16027,
                'originatingService': 'fortnite',
                'intent': 'prod'
            }), 403
    
    def handle_query_profile(self, account_id: str, request) -> Dict[str, Any]:
        """Handle query profile request"""
        try:
            data = request.get_json() or {}
            profile_id = data.get('profileId', 'athena')
            
            profile = self.get_player_profile(account_id, profile_id)
            profile['serverTime'] = datetime.utcnow().isoformat() + 'Z'
            
            return jsonify(profile)
        
        except Exception as e:
            return jsonify({
                'errorCode': 'errors.com.epicgames.common.server_error',
                'errorMessage': 'Internal server error',
                'messageVars': [],
                'numericErrorCode': 1000,
                'originatingService': 'fortnite',
                'intent': 'prod'
            }), 500
    
    def handle_find_player(self, player_id: str) -> Dict[str, Any]:
        """Handle find player request for matchmaking"""
        try:
            # Return empty result (player not in matchmaking)
            return jsonify([])
        
        except Exception as e:
            return jsonify({
                'errorCode': 'errors.com.epicgames.common.server_error',
                'errorMessage': 'Internal server error',
                'messageVars': [],
                'numericErrorCode': 1000,
                'originatingService': 'fortnite',
                'intent': 'prod'
            }), 500
    
    def handle_matchmaking_request(self, request) -> Dict[str, Any]:
        """Handle matchmaking request"""
        try:
            # Basic matchmaking response
            return jsonify({
                'playlist': 'playlist_defaultsolo',
                'sessionId': secrets.token_hex(16),
                'status': 'Waiting',
                'ticketId': secrets.token_hex(8),
                'queuedPlayers': 1,
                'estimatedWaitTime': 30,
                'queueType': 'Solo'
            })
        
        except Exception as e:
            return jsonify({
                'errorCode': 'errors.com.epicgames.common.server_error',
                'errorMessage': 'Internal server error',
                'messageVars': [],
                'numericErrorCode': 1000,
                'originatingService': 'fortnite',
                'intent': 'prod'
            }), 500
    
    # Creative Mode APIs
    def handle_create_island(self, account_id: str, request) -> Dict[str, Any]:
        """Create a new Creative island"""
        try:
            data = request.get_json() or {}
            island_name = data.get('name', 'Untitled Island')
            description = data.get('description', '')
            
            # Generate unique island code
            island_code = None
            for _ in range(10):  # Try up to 10 times to get unique code
                candidate_code = secrets.token_hex(4).upper()
                if not self.db.get_island(candidate_code):
                    island_code = candidate_code
                    break
            
            if not island_code:
                return jsonify({'error': 'Failed to generate unique island code'}), 500
            
            # Create island data with actual game-relevant information
            island_data = {
                'version': '1.0',
                'game_mode': data.get('game_mode', 'creative'),
                'max_players': data.get('max_players', 16),
                'time_limit': data.get('time_limit', 0),  # 0 = no limit
                'spawn_locations': data.get('spawn_locations', [{'x': 0, 'y': 0, 'z': 100}]),
                'objectives': data.get('objectives', []),
                'settings': {
                    'allow_building': data.get('allow_building', True),
                    'allow_editing': data.get('allow_editing', True),
                    'respawn_enabled': data.get('respawn_enabled', True),
                    'fall_damage': data.get('fall_damage', False)
                },
                'tags': data.get('tags', []),
                'thumbnail': data.get('thumbnail', '')
            }
            
            # Save to database
            success = self.db.create_island(
                island_code=island_code,
                owner_id=account_id,
                island_name=island_name,
                description=description,
                island_data=island_data
            )
            
            if not success:
                return jsonify({'error': 'Failed to create island'}), 500
            
            # Get the created island from database
            created_island = self.db.get_island(island_code)
            
            return jsonify({
                'island_code': island_code,
                'status': 'created',
                'island_data': created_island
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def handle_publish_island(self, island_code: str, request) -> Dict[str, Any]:
        """Publish a Creative island"""
        try:
            # Check if island exists
            island = self.db.get_island(island_code)
            if not island:
                return jsonify({'error': 'Island not found'}), 404
            
            # Validate island data before publishing
            island_data = island.get('island_data', {})
            if not island_data.get('spawn_locations'):
                return jsonify({'error': 'Island must have at least one spawn location'}), 400
            
            # Publish the island
            success = self.db.publish_island(island_code)
            if not success:
                return jsonify({'error': 'Failed to publish island'}), 500
            
            return jsonify({
                'status': 'published',
                'island_code': island_code,
                'published_at': datetime.utcnow().isoformat() + 'Z'
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def handle_discover_islands(self, request) -> Dict[str, Any]:
        """Discover published Creative islands"""
        try:
            # Get query parameters
            limit = min(int(request.args.get('limit', 20)), 50)  # Max 50 results
            search_term = request.args.get('search', '').strip()
            game_mode = request.args.get('game_mode', '')
            
            # Get published islands from database
            published_islands = self.db.get_published_islands(limit=limit)
            
            # Filter by search term if provided
            if search_term:
                published_islands = [
                    island for island in published_islands
                    if search_term.lower() in island['island_name'].lower() or
                       search_term.lower() in island.get('description', '').lower()
                ]
            
            # Add additional metadata for discovery
            for island in published_islands:
                island['featured'] = island['plays'] > 1000  # Featured if popular
                island['rating'] = min(5.0, island['likes'] / max(1, island['plays']) * 5)  # Simple rating
            
            return jsonify({
                'islands': published_islands,
                'total': len(published_islands),
                'search_term': search_term,
                'filters': {
                    'game_mode': game_mode,
                    'limit': limit
                }
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Battle Pass APIs
    def handle_battle_pass_info(self, account_id: str) -> Dict[str, Any]:
        """Get Battle Pass information"""
        try:
            # Get battle pass progress from database
            progress = self.db.get_battle_pass_progress(account_id, season=7)
            
            # Calculate unlocked tiers based on battle stars
            battle_stars = progress['battle_stars']
            current_tier = min(100, max(1, (battle_stars // 10) + 1))
            
            # Update current tier if it changed
            if current_tier != progress['current_tier']:
                unlocked_tiers = list(range(1, current_tier + 1))
                progress_data = progress['progress_data']
                progress_data['unlocked_tiers'] = unlocked_tiers
                
                self.db.update_battle_pass_progress(
                    account_id=account_id,
                    season=7,
                    current_tier=current_tier,
                    progress_data=progress_data
                )
                progress['current_tier'] = current_tier
                progress['progress_data'] = progress_data
            
            # Get available rewards for current tier
            tier_rewards = []
            for tier in range(1, progress['current_tier'] + 1):
                tier_data = self.battle_pass_data['tiers'].get(str(tier), {})
                if tier_data:
                    tier_rewards.append({
                        'tier': tier,
                        'free_reward': tier_data.get('free_reward'),
                        'premium_reward': tier_data.get('premium_reward') if progress['premium_purchased'] else None,
                        'unlocked': tier <= progress['current_tier']
                    })
            
            return jsonify({
                'season': 7,
                'current_tier': progress['current_tier'],
                'battle_stars': progress['battle_stars'],
                'premium_purchased': progress['premium_purchased'],
                'unlocked_tiers': progress['progress_data'].get('unlocked_tiers', [1]),
                'tier_rewards': tier_rewards,
                'challenges': self.battle_pass_data['challenges'],
                'stars_to_next_tier': 10 - (progress['battle_stars'] % 10) if progress['current_tier'] < 100 else 0
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def handle_complete_challenge(self, account_id: str, challenge_id: str) -> Dict[str, Any]:
        """Complete a Battle Pass challenge"""
        try:
            # Find the challenge in our data
            challenge_found = False
            challenge_data = None
            
            # Check daily challenges
            for challenge in self.battle_pass_data['challenges']['daily']:
                if challenge['id'] == challenge_id:
                    challenge_data = challenge.copy()
                    challenge_found = True
                    break
            
            # Check weekly challenges if not found in daily
            if not challenge_found:
                for challenge in self.battle_pass_data['challenges']['weekly']:
                    if challenge['id'] == challenge_id:
                        challenge_data = challenge.copy()
                        challenge_found = True
                        break
            
            if not challenge_found:
                return jsonify({'error': 'Challenge not found'}), 404
            
            # Get current battle pass progress
            progress = self.db.get_battle_pass_progress(account_id, season=7)
            completed_challenges = progress['progress_data'].get('completed_challenges', [])
            
            # Check if challenge already completed
            if challenge_id in completed_challenges:
                return jsonify({'error': 'Challenge already completed'}), 400
            
            # Mark challenge as completed
            completed_challenges.append(challenge_id)
            progress['progress_data']['completed_challenges'] = completed_challenges
            
            # Award reward
            reward = challenge_data['reward']
            stars_awarded = 0
            xp_awarded = 0
            
            if 'BattlePassStar' in reward:
                stars_awarded = int(reward.split(':')[1])
                new_battle_stars = progress['battle_stars'] + stars_awarded
            elif 'BattlePassXP' in reward:
                xp_awarded = int(reward.split(':')[1])
                # Convert XP to stars (500 XP = 1 star)
                stars_awarded = xp_awarded // 500
                new_battle_stars = progress['battle_stars'] + stars_awarded
            else:
                new_battle_stars = progress['battle_stars']
            
            # Calculate new tier
            new_tier = min(100, max(1, (new_battle_stars // 10) + 1))
            tier_increased = new_tier > progress['current_tier']
            
            # Update progress in database
            self.db.update_battle_pass_progress(
                account_id=account_id,
                season=7,
                current_tier=new_tier,
                battle_stars=new_battle_stars,
                progress_data=progress['progress_data']
            )
            
            response_data = {
                'status': 'completed',
                'challenge_id': challenge_id,
                'challenge_name': challenge_data['name'],
                'reward': reward,
                'stars_awarded': stars_awarded,
                'xp_awarded': xp_awarded,
                'new_battle_stars': new_battle_stars,
                'new_tier': new_tier,
                'tier_increased': tier_increased
            }
            
            # Add tier rewards if tier increased
            if tier_increased:
                tier_rewards = []
                for tier in range(progress['current_tier'] + 1, new_tier + 1):
                    tier_data = self.battle_pass_data['tiers'].get(str(tier), {})
                    if tier_data:
                        tier_rewards.append({
                            'tier': tier,
                            'free_reward': tier_data.get('free_reward'),
                            'premium_reward': tier_data.get('premium_reward') if progress['premium_purchased'] else None
                        })
                response_data['tier_rewards_unlocked'] = tier_rewards
            
            return jsonify(response_data)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Social APIs
    def handle_create_party(self, account_id: str, request) -> Dict[str, Any]:
        """Create a new party"""
        try:
            party_id = secrets.token_hex(8)
            
            party_data = {
                'party_id': party_id,
                'leader_id': account_id,
                'members': [account_id],
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'max_members': 4,
                'privacy': request.get_json().get('privacy', 'public') if request.get_json() else 'public'
            }
            
            self.parties[party_id] = party_data
            
            return jsonify({
                'party_id': party_id,
                'status': 'created',
                'party_data': party_data
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def handle_join_party(self, party_id: str, account_id: str) -> Dict[str, Any]:
        """Join an existing party"""
        try:
            if party_id not in self.parties:
                return jsonify({'error': 'Party not found'}), 404
            
            party = self.parties[party_id]
            
            if len(party['members']) >= party['max_members']:
                return jsonify({'error': 'Party is full'}), 400
            
            if account_id not in party['members']:
                party['members'].append(account_id)
            
            return jsonify({
                'status': 'joined',
                'party_data': party
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Competitive APIs
    def handle_arena_info(self, account_id: str) -> Dict[str, Any]:
        """Get Arena information for player"""
        try:
            # Default arena stats
            arena_stats = {
                'points': 0,
                'division': 'open',
                'matches_played': 0,
                'wins': 0,
                'top_10': 0,
                'eliminations': 0
            }
            
            current_division = None
            for div_key, div_data in self.arena_divisions.items():
                if div_data['min_points'] <= arena_stats['points'] <= div_data['max_points']:
                    current_division = div_data
                    break
            
            return jsonify({
                'arena_stats': arena_stats,
                'current_division': current_division,
                'divisions': self.arena_divisions
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def handle_tournament_list(self) -> Dict[str, Any]:
        """Get list of available tournaments"""
        try:
            # Sample tournaments for Season 7
            tournaments = [
                {
                    'id': 'winter_royale_2018',
                    'name': 'Winter Royale 2018',
                    'description': 'Compete for glory in the Winter Royale tournament',
                    'start_time': (datetime.utcnow() + timedelta(days=1)).isoformat() + 'Z',
                    'end_time': (datetime.utcnow() + timedelta(days=3)).isoformat() + 'Z',
                    'prize_pool': '$1,000,000',
                    'max_participants': 10000,
                    'current_participants': 2847
                }
            ]
            
            return jsonify({
                'tournaments': tournaments,
                'total': len(tournaments)
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500