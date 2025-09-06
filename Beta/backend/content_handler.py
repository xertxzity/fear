#!/usr/bin/env python3
"""
Content Handler for Fortnite Season 7 Emulator
Handles game content like item shop, timeline, and news feeds
"""

from flask import jsonify
import json
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, List
from .database import get_database

class ContentHandler:
    def __init__(self):
        # Database connection
        self.db = get_database()
        
        # Season 7 specific content
        self.season_7_content = self._create_season_7_content()
        
        # Store and economy data
        self.item_shop_rotation = self._create_item_shop_rotation()
        
        # Platform integration (in-memory for session data)
        self.cross_platform_data = {}
        self.achievements = self._create_achievements()
    
    def _create_season_7_content(self) -> Dict[str, Any]:
        """Create Season 7 specific content data"""
        return {
            'battleroyalenews': {
                'news': {
                    'motds': [
                        {
                            'entryType': 'Website',
                            'image': 'https://cdn2.unrealengine.com/Fortnite/fortnite-game/battleroyalenews/BR07_News_Featured_CreativeMode-1920x1080-1920x1080-c2c8091418b5c2b32ca4214a2a04b86a8e5e8f2a.jpg',
                            'tileImage': 'https://cdn2.unrealengine.com/Fortnite/fortnite-game/battleroyalenews/BR07_News_Featured_CreativeMode-1024x512-1024x512-c2c8091418b5c2b32ca4214a2a04b86a8e5e8f2a.jpg',
                            'videoMute': False,
                            'hidden': False,
                            'tabTitleOverride': 'Creative Mode',
                            'buttonTextOverride': 'Learn More',
                            'sortingPriority': 0,
                            'id': 'creative-mode-announcement',
                            'videoAutoplay': False,
                            'videoFullscreen': False,
                            'spotlight': False,
                            'title': 'Creative Mode is Here!',
                            'body': 'Build your own island and play with friends in Creative mode. Your island, your friends, your rules.',
                            'websiteURL': '',
                            'websiteButtonText': 'Learn More'
                        },
                        {
                            'entryType': 'Text',
                            'image': 'https://cdn2.unrealengine.com/Fortnite/fortnite-game/battleroyalenews/BR07_News_Featured_Planes-1920x1080-1920x1080-c2c8091418b5c2b32ca4214a2a04b86a8e5e8f2a.jpg',
                            'tileImage': 'https://cdn2.unrealengine.com/Fortnite/fortnite-game/battleroyalenews/BR07_News_Featured_Planes-1024x512-1024x512-c2c8091418b5c2b32ca4214a2a04b86a8e5e8f2a.jpg',
                            'hidden': False,
                            'sortingPriority': 1,
                            'id': 'season-7-planes',
                            'spotlight': True,
                            'title': 'Season 7 - X-4 Stormwing',
                            'body': 'Take to the skies with the new X-4 Stormwing plane! Soar through the air and rain down fire on your enemies.'
                        }
                    ]
                },
                'jcr:isCheckedOut': True,
                'lastModified': '2019-02-14T17:36:10.335Z',
                '_title': 'battleroyalenews',
                '_activeDate': '2018-12-06T14:00:00.000Z',
                'lastModifiedBy': 'system',
                '_locale': 'en-US'
            },
            'emergencynotice': {
                'news': {
                    'platform_messages': [],
                    'emergency_notices': []
                },
                'jcr:isCheckedOut': True,
                'lastModified': '2019-02-14T17:36:10.335Z',
                '_title': 'emergencynotice',
                '_activeDate': '2018-12-06T14:00:00.000Z',
                'lastModifiedBy': 'system',
                '_locale': 'en-US'
            }
        }
    
    def handle_content_pages(self) -> Dict[str, Any]:
        """Handle content pages request"""
        try:
            return jsonify(self.season_7_content)
        
        except Exception as e:
            return jsonify({
                'errorCode': 'errors.com.epicgames.common.server_error',
                'errorMessage': 'Internal server error',
                'messageVars': [],
                'numericErrorCode': 1000,
                'originatingService': 'fortnite',
                'intent': 'prod'
            }), 500
    
    def handle_timeline(self) -> Dict[str, Any]:
        """Handle timeline request - Season 7.40 specific"""
        try:
            current_time = datetime.utcnow().isoformat() + 'Z'
            
            return jsonify({
                'channels': {
                    'client-matchmaking': {
                        'states': [{
                            'validFrom': '2018-12-06T14:00:00.000Z',
                            'activeEvents': [],
                            'state': {
                                'region': {
                                    'NAE': {'eventFlagsForcedOff': []},
                                    'NAW': {'eventFlagsForcedOff': []},
                                    'EU': {'eventFlagsForcedOff': []}
                                }
                            }
                        }],
                        'cacheExpire': '9999-12-31T23:59:59.999Z'
                    },
                    'client-events': {
                        'states': [{
                            'validFrom': '2018-12-06T14:00:00.000Z',
                            'activeEvents': [{
                                'eventType': 'EventFlag.Season7Launch',
                                'activeUntil': '2019-02-28T14:00:00.000Z',
                                'activeSince': '2018-12-06T14:00:00.000Z'
                            }, {
                                'eventType': 'EventFlag.CreativeMode',
                                'activeUntil': '9999-12-31T23:59:59.999Z',
                                'activeSince': '2018-12-06T14:00:00.000Z'
                            }],
                            'state': {
                                'activeStorefronts': ['BRWeeklyStorefront', 'BRDailyStorefront'],
                                'eventNamedWeights': {},
                                'seasonNumber': 7,
                                'seasonTemplateId': 'AthenaSeason:athenaseason7',
                                'matchXpBonusPoints': 0,
                                'seasonBegin': '2018-12-06T14:00:00Z',
                                'seasonEnd': '2019-02-28T14:00:00Z',
                                'seasonDisplayedEnd': '2019-02-28T14:00:00Z',
                                'weeklyStoreEnd': current_time,
                                'stwEventStoreEnd': '9999-12-31T23:59:59.999Z',
                                'stwWeeklyStoreEnd': '9999-12-31T23:59:59.999Z',
                                'dailyStoreEnd': current_time,
                                'rmtPromotion': 'RMTPromotion:BattlePass.Season7',
                                'storeEnd': current_time
                            }
                        }],
                        'cacheExpire': '9999-12-31T23:59:59.999Z'
                    },
                    'tk': {
                        'states': [{
                            'validFrom': '2018-12-06T14:00:00.000Z',
                            'activeEvents': [],
                            'state': {
                                'k': [
                                    '0x90D0BB0E1A6F3F9E',
                                    '0x7E2E9F8A5F6B8C4D',
                                    '0x3A1B5C9D8E7F2A6B'
                                ]
                            }
                        }],
                        'cacheExpire': '9999-12-31T23:59:59.999Z'
                    }
                },
                'eventsTimeOffsetHrs': 0,
                'cacheIntervalMins': 10,
                'currentTime': current_time
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
    
    def handle_catalog(self) -> Dict[str, Any]:
        """Handle item shop catalog request"""
        try:
            # Season 7 item shop data
            catalog_data = {
                'refreshIntervalHrs': 24,
                'dailyPurchaseHrs': 24,
                'expiration': (datetime.utcnow() + timedelta(hours=24)).isoformat() + 'Z',
                'storefronts': [
                    {
                        'name': 'BRDailyStorefront',
                        'catalogEntries': [
                            {
                                'devName': 'Featured Item 1',
                                'offerId': 'featured_item_1',
                                'fulfillmentIds': [],
                                'dailyLimit': -1,
                                'weeklyLimit': -1,
                                'monthlyLimit': -1,
                                'categories': ['Panel 01'],
                                'prices': [
                                    {
                                        'currencyType': 'MtxCurrency',
                                        'currencySubType': '',
                                        'regularPrice': 1200,
                                        'finalPrice': 1200,
                                        'saleExpiration': '9999-12-31T23:59:59.999Z',
                                        'basePrice': 1200
                                    }
                                ],
                                'matchFilter': '',
                                'filterWeight': 0,
                                'appStoreId': [],
                                'requirements': [],
                                'offerType': 'StaticPrice',
                                'giftInfo': {
                                    'bIsEnabled': True,
                                    'forcedGiftBoxTemplateId': '',
                                    'purchaseRequirements': [],
                                    'giftRecordIds': []
                                },
                                'refundable': True,
                                'metaInfo': [
                                    {
                                        'key': 'SectionId',
                                        'value': 'Featured'
                                    },
                                    {
                                        'key': 'TileSize',
                                        'value': 'Normal'
                                    }
                                ],
                                'catalogGroup': '',
                                'catalogGroupPriority': 0,
                                'sortPriority': 0,
                                'title': 'Featured Skin',
                                'shortDescription': 'A cool skin from Season 7',
                                'description': 'This is a featured skin available in the item shop.',
                                'displayAssetPath': '',
                                'itemGrants': [
                                    {
                                        'templateId': 'AthenaCharacter:CID_028_Athena_Commando_F',
                                        'quantity': 1
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'name': 'BRWeeklyStorefront',
                        'catalogEntries': []
                    }
                ]
            }
            
            return jsonify(catalog_data)
        
        except Exception as e:
            return jsonify({
                'errorCode': 'errors.com.epicgames.common.server_error',
                'errorMessage': 'Internal server error',
                'messageVars': [],
                'numericErrorCode': 1000,
                'originatingService': 'fortnite',
                'intent': 'prod'
            }), 500
    
    def get_season_7_events(self) -> List[Dict[str, Any]]:
        """Get Season 7 specific events"""
        return [
            {
                'eventType': 'EventFlag.Season7Launch',
                'activeUntil': '2019-02-28T14:00:00.000Z',
                'activeSince': '2018-12-06T14:00:00.000Z'
            },
            {
                'eventType': 'EventFlag.CreativeMode',
                'activeUntil': '9999-12-31T23:59:59.999Z',
                'activeSince': '2018-12-06T14:00:00.000Z'
            },
            {
                'eventType': 'EventFlag.Planes',
                'activeUntil': '2019-02-28T14:00:00.000Z',
                'activeSince': '2018-12-06T14:00:00.000Z'
            }
        ]
    
    def get_season_7_playlists(self) -> List[Dict[str, Any]]:
        """Get Season 7 available playlists"""
        return [
            {
                'playlistName': 'Playlist_DefaultSolo',
                'enabled': True,
                'hidden': False,
                'override_playlist_name': 'Solo',
                'description': 'Every player for themselves.',
                'display_subname': '',
                'gameType': 'BattleRoyale',
                'minPlayers': 1,
                'maxPlayers': 100,
                'maxTeams': 100,
                'maxTeamSize': 1,
                'maxSquads': 100,
                'maxSquadSize': 1
            },
            {
                'playlistName': 'Playlist_DefaultDuo',
                'enabled': True,
                'hidden': False,
                'override_playlist_name': 'Duos',
                'description': 'Partner up.',
                'display_subname': '',
                'gameType': 'BattleRoyale',
                'minPlayers': 2,
                'maxPlayers': 100,
                'maxTeams': 50,
                'maxTeamSize': 2,
                'maxSquads': 50,
                'maxSquadSize': 2
            },
            {
                'playlistName': 'Playlist_DefaultSquad',
                'enabled': True,
                'hidden': False,
                'override_playlist_name': 'Squads',
                'description': 'Team up with friends.',
                'display_subname': '',
                'gameType': 'BattleRoyale',
                'minPlayers': 1,
                'maxPlayers': 100,
                'maxTeams': 25,
                'maxTeamSize': 4,
                'maxSquads': 25,
                'maxSquadSize': 4
            },
            {
                'playlistName': 'Playlist_Creative',
                'enabled': True,
                'hidden': False,
                'override_playlist_name': 'Creative',
                'description': 'Build and play with friends.',
                'display_subname': 'Season 7',
                'gameType': 'Creative',
                'minPlayers': 1,
                'maxPlayers': 16,
                'maxTeams': 16,
                'maxTeamSize': 1,
                'maxSquads': 16,
                'maxSquadSize': 1
            }
        ]
    
    def _create_item_shop_rotation(self) -> Dict[str, Any]:
        """Create item shop rotation data"""
        return {
            'daily': {
                'featured': [
                    {
                        'id': 'CID_028_Athena_Commando_F',
                        'name': 'Ramirez',
                        'description': 'Default outfit',
                        'price': 0,
                        'currency': 'vbucks',
                        'rarity': 'common',
                        'type': 'outfit'
                    }
                ],
                'daily': [
                    {
                        'id': 'Pickaxe_ID_015_Athena',
                        'name': 'Default Pickaxe',
                        'description': 'Default harvesting tool',
                        'price': 0,
                        'currency': 'vbucks',
                        'rarity': 'common',
                        'type': 'pickaxe'
                    }
                ]
            },
            'last_rotation': datetime.utcnow().isoformat() + 'Z'
        }
    
    def _create_achievements(self) -> List[Dict[str, Any]]:
        """Create platform achievements"""
        return [
            {
                'id': 'first_win',
                'name': 'Victory Royale',
                'description': 'Win your first match',
                'unlocked': False,
                'progress': 0,
                'target': 1
            },
            {
                'id': 'eliminations_100',
                'name': 'Eliminator',
                'description': 'Eliminate 100 opponents',
                'unlocked': False,
                'progress': 0,
                'target': 100
            }
        ]
    
    # Store and Economy APIs
    def handle_item_shop(self) -> Dict[str, Any]:
        """Get current item shop"""
        try:
            return jsonify({
                'shop': self.item_shop_rotation['daily'],
                'last_rotation': self.item_shop_rotation['last_rotation'],
                'next_rotation': (datetime.utcnow() + timedelta(hours=24)).isoformat() + 'Z'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def handle_purchase_item(self, account_id: str, request) -> Dict[str, Any]:
        """Purchase an item from the shop"""
        try:
            data = request.get_json() or {}
            item_id = data.get('item_id')
            
            if not item_id:
                return jsonify({'error': 'Item ID required'}), 400
            
            # Initialize player V-Bucks if not exists
            if account_id not in self.player_vbucks:
                self.player_vbucks[account_id] = 1000  # Default V-Bucks
            
            # Find item in shop
            item = None
            for category in self.item_shop_rotation['daily'].values():
                for shop_item in category:
                    if shop_item['id'] == item_id:
                        item = shop_item
                        break
            
            if not item:
                return jsonify({'error': 'Item not found in shop'}), 404
            
            # Check if player has enough V-Bucks
            if self.player_vbucks[account_id] < item['price']:
                return jsonify({'error': 'Insufficient V-Bucks'}), 400
            
            # Process purchase
            self.player_vbucks[account_id] -= item['price']
            
            # Add to purchase history
            if account_id not in self.purchase_history:
                self.purchase_history[account_id] = []
            
            purchase_record = {
                'item_id': item_id,
                'item_name': item['name'],
                'price': item['price'],
                'currency': item['currency'],
                'purchased_at': datetime.utcnow().isoformat() + 'Z'
            }
            
            self.purchase_history[account_id].append(purchase_record)
            
            return jsonify({
                'status': 'purchased',
                'item': item,
                'remaining_vbucks': self.player_vbucks[account_id],
                'purchase_record': purchase_record
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def handle_gift_item(self, account_id: str, request) -> Dict[str, Any]:
        """Gift an item to another player"""
        try:
            data = request.get_json() or {}
            item_id = data.get('item_id')
            recipient_id = data.get('recipient_id')
            message = data.get('message', '')
            
            if not item_id or not recipient_id:
                return jsonify({'error': 'Item ID and recipient ID required'}), 400
            
            # Process gift (simplified)
            gift_record = {
                'gift_id': secrets.token_hex(8),
                'item_id': item_id,
                'sender_id': account_id,
                'recipient_id': recipient_id,
                'message': message,
                'sent_at': datetime.utcnow().isoformat() + 'Z',
                'claimed': False
            }
            
            if account_id not in self.gift_history:
                self.gift_history[account_id] = []
            
            self.gift_history[account_id].append(gift_record)
            
            return jsonify({
                'status': 'sent',
                'gift_record': gift_record
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def handle_vbucks_balance(self, account_id: str) -> Dict[str, Any]:
        """Get player's V-Bucks balance"""
        try:
            if account_id not in self.player_vbucks:
                self.player_vbucks[account_id] = 1000  # Default V-Bucks
            
            return jsonify({
                'account_id': account_id,
                'vbucks': self.player_vbucks[account_id],
                'currency': 'vbucks'
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Platform Integration APIs
    def handle_cross_platform_sync(self, account_id: str, request) -> Dict[str, Any]:
        """Sync cross-platform data"""
        try:
            data = request.get_json() or {}
            platform = data.get('platform', 'pc')
            
            if account_id not in self.cross_platform_data:
                self.cross_platform_data[account_id] = {
                    'linked_platforms': [],
                    'primary_platform': platform,
                    'sync_enabled': True
                }
            
            platform_data = self.cross_platform_data[account_id]
            
            if platform not in platform_data['linked_platforms']:
                platform_data['linked_platforms'].append(platform)
            
            return jsonify({
                'status': 'synced',
                'platform_data': platform_data
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def handle_achievements(self, account_id: str) -> Dict[str, Any]:
        """Get player achievements"""
        try:
            return jsonify({
                'account_id': account_id,
                'achievements': self.achievements,
                'total_unlocked': len([a for a in self.achievements if a['unlocked']]),
                'total_available': len(self.achievements)
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500