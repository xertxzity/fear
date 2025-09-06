#!/usr/bin/env python3
"""
MCP (Mission Control Protocol) Service for Fortnite Season 7.40 Emulator
Implements verified Season 7.40 MCP endpoints with exact URL patterns and response formats
"""

from flask import jsonify, request
import json
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from .database import get_database

class MCPService:
    def __init__(self):
        self.db = get_database()
        
        # Season 7.40 specific data
        self.season_number = 7
        self.season_version = "7.40"
        self.build_id = "4834769"
        
        # Profile templates for Season 7.40
        self.profile_templates = self._create_profile_templates()
        
        # Valid MCP operations for Season 7.40
        self.valid_operations = {
            'QueryProfile': self.handle_query_profile,
            'ClientQuestLogin': self.handle_client_quest_login,
            'SetMtxPlatform': self.handle_set_mtx_platform,
            'MarkItemSeen': self.handle_mark_item_seen,
            'SetBattleRoyaleBanner': self.handle_set_banner,
            'SetCosmeticLockerSlot': self.handle_set_locker_slot,
            'EquipBattleRoyaleCustomization': self.handle_equip_customization,
            'PurchaseCatalogEntry': self.handle_purchase_catalog_entry,
            'GiftCatalogEntry': self.handle_gift_catalog_entry,
            'ClaimMfaEnabled': self.handle_claim_mfa_enabled,
            'RefreshExpeditions': self.handle_refresh_expeditions,
            'ClaimCollectionBookPageRewards': self.handle_claim_collection_rewards
        }
    
    def _create_profile_templates(self) -> Dict[str, Dict[str, Any]]:
        """Create Season 7.40 specific profile templates"""
        return {
            'athena': {
                'profileRevision': 1,
                'profileId': 'athena',
                'profileChangesBaseRevision': 1,
                'profileChanges': [],
                'profileCommandRevision': 1,
                'serverTime': datetime.utcnow().isoformat() + 'Z',
                'responseVersion': 1,
                'items': {
                    # Default Season 7 Battle Royale items
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
                    },
                    'AthenaDance:EID_DanceMoves': {
                        'templateId': 'AthenaDance:EID_DanceMoves',
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
                        'quest_manager': {
                            'dailyLoginInterval': datetime.utcnow().isoformat() + 'Z',
                            'dailyQuestRerolls': 1
                        },
                        'book_level': 1,
                        'season_num': 7,
                        'season_update': 40,
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
                        'active_loadout_index': 0,
                        'past_seasons': []
                    }
                }
            },
            'common_core': {
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
                    },
                    'Currency:MtxComplimentary': {
                        'templateId': 'Currency:MtxComplimentary',
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
                        'mtx_purchase_history': {
                            'refundsUsed': 0,
                            'refundCredits': 3
                        },
                        'undo_cooldowns': [],
                        'mtx_affiliate_set_time': datetime.utcnow().isoformat() + 'Z',
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
            },
            'common_public': {
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
                        'homebase_name': 'Homebase',
                        'personal_offers': {},
                        'banner_icon_template': 'BannerIconTemplate:StandardBanner1',
                        'banner_color_template': 'BannerColorTemplate:DefaultColor1'
                    }
                }
            }
        }
    
    def handle_mcp_operation(self, account_id: str, operation: str, profile_id: str, rvn: int = -1) -> Dict[str, Any]:
        """Handle MCP operation request"""
        try:
            # Validate operation
            if operation not in self.valid_operations:
                return {
                    'errorCode': 'errors.com.epicgames.fortnite.operation_not_found',
                    'errorMessage': f'Operation {operation} not valid',
                    'messageVars': [operation],
                    'numericErrorCode': 16035,
                    'originatingService': 'fortnite',
                    'intent': 'prod-live'
                }, 400
            
            # Execute operation
            return self.valid_operations[operation](account_id, profile_id, rvn)
            
        except Exception as e:
            return {
                'errorCode': 'errors.com.epicgames.common.server_error',
                'errorMessage': 'Internal server error',
                'messageVars': [],
                'numericErrorCode': 1000,
                'originatingService': 'fortnite',
                'intent': 'prod-live'
            }, 500
    
    def handle_query_profile(self, account_id: str, profile_id: str, rvn: int = -1) -> Dict[str, Any]:
        """Handle QueryProfile operation - most critical for lobby entry"""
        try:
            # Get profile template
            if profile_id not in self.profile_templates:
                return {
                    'errorCode': 'errors.com.epicgames.fortnite.profile_not_found',
                    'errorMessage': f'Profile {profile_id} not found',
                    'messageVars': [profile_id],
                    'numericErrorCode': 12813,
                    'originatingService': 'fortnite',
                    'intent': 'prod-live'
                }, 404
            
            # Create profile response
            profile = self.profile_templates[profile_id].copy()
            profile['serverTime'] = datetime.utcnow().isoformat() + 'Z'
            
            # Update revision numbers
            if rvn != -1:
                profile['profileRevision'] = rvn + 1
                profile['profileCommandRevision'] = rvn + 1
            
            return profile
            
        except Exception as e:
            return {
                'errorCode': 'errors.com.epicgames.common.server_error',
                'errorMessage': 'Internal server error',
                'messageVars': [],
                'numericErrorCode': 1000,
                'originatingService': 'fortnite',
                'intent': 'prod-live'
            }, 500
    
    def handle_client_quest_login(self, account_id: str, profile_id: str, rvn: int = -1) -> Dict[str, Any]:
        """Handle ClientQuestLogin operation - called during login"""
        try:
            # Get base profile
            profile_response = self.handle_query_profile(account_id, profile_id, rvn)
            if isinstance(profile_response, tuple):
                return profile_response
            
            # Add login-specific changes
            profile_response['profileChanges'] = [{
                'changeType': 'statModified',
                'name': 'quest_manager',
                'value': {
                    'dailyLoginInterval': datetime.utcnow().isoformat() + 'Z',
                    'dailyQuestRerolls': 1
                }
            }]
            
            return profile_response
            
        except Exception as e:
            return {
                'errorCode': 'errors.com.epicgames.common.server_error',
                'errorMessage': 'Internal server error',
                'messageVars': [],
                'numericErrorCode': 1000,
                'originatingService': 'fortnite',
                'intent': 'prod-live'
            }, 500
    
    def handle_set_mtx_platform(self, account_id: str, profile_id: str, rvn: int = -1) -> Dict[str, Any]:
        """Handle SetMtxPlatform operation"""
        try:
            # Get request data
            data = request.get_json() or {}
            new_platform = data.get('newPlatform', 'EpicPC')
            
            # Get base profile
            profile_response = self.handle_query_profile(account_id, profile_id, rvn)
            if isinstance(profile_response, tuple):
                return profile_response
            
            # Update platform
            profile_response['profileChanges'] = [{
                'changeType': 'statModified',
                'name': 'current_mtx_platform',
                'value': new_platform
            }]
            
            return profile_response
            
        except Exception as e:
            return {
                'errorCode': 'errors.com.epicgames.common.server_error',
                'errorMessage': 'Internal server error',
                'messageVars': [],
                'numericErrorCode': 1000,
                'originatingService': 'fortnite',
                'intent': 'prod-live'
            }, 500
    
    def handle_mark_item_seen(self, account_id: str, profile_id: str, rvn: int = -1) -> Dict[str, Any]:
        """Handle MarkItemSeen operation"""
        try:
            data = request.get_json() or {}
            item_ids = data.get('itemIds', [])
            
            profile_response = self.handle_query_profile(account_id, profile_id, rvn)
            if isinstance(profile_response, tuple):
                return profile_response
            
            # Mark items as seen
            changes = []
            for item_id in item_ids:
                changes.append({
                    'changeType': 'itemAttrChanged',
                    'itemId': item_id,
                    'attributeName': 'item_seen',
                    'attributeValue': True
                })
            
            profile_response['profileChanges'] = changes
            return profile_response
            
        except Exception as e:
            return {
                'errorCode': 'errors.com.epicgames.common.server_error',
                'errorMessage': 'Internal server error',
                'messageVars': [],
                'numericErrorCode': 1000,
                'originatingService': 'fortnite',
                'intent': 'prod-live'
            }, 500
    
    def handle_set_banner(self, account_id: str, profile_id: str, rvn: int = -1) -> Dict[str, Any]:
        """Handle SetBattleRoyaleBanner operation"""
        try:
            data = request.get_json() or {}
            banner_icon = data.get('homebaseBannerIconId', 'StandardBanner1')
            banner_color = data.get('homebaseBannerColorId', 'DefaultColor1')
            
            profile_response = self.handle_query_profile(account_id, profile_id, rvn)
            if isinstance(profile_response, tuple):
                return profile_response
            
            profile_response['profileChanges'] = [
                {
                    'changeType': 'statModified',
                    'name': 'banner_icon',
                    'value': banner_icon
                },
                {
                    'changeType': 'statModified',
                    'name': 'banner_color',
                    'value': banner_color
                }
            ]
            
            return profile_response
            
        except Exception as e:
            return {
                'errorCode': 'errors.com.epicgames.common.server_error',
                'errorMessage': 'Internal server error',
                'messageVars': [],
                'numericErrorCode': 1000,
                'originatingService': 'fortnite',
                'intent': 'prod-live'
            }, 500
    
    def handle_set_locker_slot(self, account_id: str, profile_id: str, rvn: int = -1) -> Dict[str, Any]:
        """Handle SetCosmeticLockerSlot operation"""
        try:
            data = request.get_json() or {}
            
            profile_response = self.handle_query_profile(account_id, profile_id, rvn)
            if isinstance(profile_response, tuple):
                return profile_response
            
            # Simple locker slot update
            profile_response['profileChanges'] = [{
                'changeType': 'statModified',
                'name': 'active_loadout_index',
                'value': data.get('lockerItem', 0)
            }]
            
            return profile_response
            
        except Exception as e:
            return {
                'errorCode': 'errors.com.epicgames.common.server_error',
                'errorMessage': 'Internal server error',
                'messageVars': [],
                'numericErrorCode': 1000,
                'originatingService': 'fortnite',
                'intent': 'prod-live'
            }, 500
    
    def handle_equip_customization(self, account_id: str, profile_id: str, rvn: int = -1) -> Dict[str, Any]:
        """Handle EquipBattleRoyaleCustomization operation"""
        try:
            data = request.get_json() or {}
            
            profile_response = self.handle_query_profile(account_id, profile_id, rvn)
            if isinstance(profile_response, tuple):
                return profile_response
            
            # Simple customization equip
            profile_response['profileChanges'] = [{
                'changeType': 'statModified',
                'name': 'last_applied_loadout',
                'value': data.get('slotName', '')
            }]
            
            return profile_response
            
        except Exception as e:
            return {
                'errorCode': 'errors.com.epicgames.common.server_error',
                'errorMessage': 'Internal server error',
                'messageVars': [],
                'numericErrorCode': 1000,
                'originatingService': 'fortnite',
                'intent': 'prod-live'
            }, 500
    
    def handle_purchase_catalog_entry(self, account_id: str, profile_id: str, rvn: int = -1) -> Dict[str, Any]:
        """Handle PurchaseCatalogEntry operation"""
        try:
            profile_response = self.handle_query_profile(account_id, profile_id, rvn)
            if isinstance(profile_response, tuple):
                return profile_response
            
            # Simple purchase response
            profile_response['profileChanges'] = [{
                'changeType': 'statModified',
                'name': 'daily_purchases',
                'value': {}
            }]
            
            return profile_response
            
        except Exception as e:
            return {
                'errorCode': 'errors.com.epicgames.common.server_error',
                'errorMessage': 'Internal server error',
                'messageVars': [],
                'numericErrorCode': 1000,
                'originatingService': 'fortnite',
                'intent': 'prod-live'
            }, 500
    
    def handle_gift_catalog_entry(self, account_id: str, profile_id: str, rvn: int = -1) -> Dict[str, Any]:
        """Handle GiftCatalogEntry operation"""
        try:
            profile_response = self.handle_query_profile(account_id, profile_id, rvn)
            if isinstance(profile_response, tuple):
                return profile_response
            
            profile_response['profileChanges'] = [{
                'changeType': 'statModified',
                'name': 'gift_history',
                'value': {}
            }]
            
            return profile_response
            
        except Exception as e:
            return {
                'errorCode': 'errors.com.epicgames.common.server_error',
                'errorMessage': 'Internal server error',
                'messageVars': [],
                'numericErrorCode': 1000,
                'originatingService': 'fortnite',
                'intent': 'prod-live'
            }, 500
    
    def handle_claim_mfa_enabled(self, account_id: str, profile_id: str, rvn: int = -1) -> Dict[str, Any]:
        """Handle ClaimMfaEnabled operation"""
        try:
            profile_response = self.handle_query_profile(account_id, profile_id, rvn)
            if isinstance(profile_response, tuple):
                return profile_response
            
            profile_response['profileChanges'] = [{
                'changeType': 'statModified',
                'name': 'mfa_reward_claimed',
                'value': True
            }]
            
            return profile_response
            
        except Exception as e:
            return {
                'errorCode': 'errors.com.epicgames.common.server_error',
                'errorMessage': 'Internal server error',
                'messageVars': [],
                'numericErrorCode': 1000,
                'originatingService': 'fortnite',
                'intent': 'prod-live'
            }, 500
    
    def handle_refresh_expeditions(self, account_id: str, profile_id: str, rvn: int = -1) -> Dict[str, Any]:
        """Handle RefreshExpeditions operation (STW)"""
        try:
            profile_response = self.handle_query_profile(account_id, profile_id, rvn)
            if isinstance(profile_response, tuple):
                return profile_response
            
            # Empty changes for STW expedition refresh
            profile_response['profileChanges'] = []
            return profile_response
            
        except Exception as e:
            return {
                'errorCode': 'errors.com.epicgames.common.server_error',
                'errorMessage': 'Internal server error',
                'messageVars': [],
                'numericErrorCode': 1000,
                'originatingService': 'fortnite',
                'intent': 'prod-live'
            }, 500
    
    def handle_claim_collection_rewards(self, account_id: str, profile_id: str, rvn: int = -1) -> Dict[str, Any]:
        """Handle ClaimCollectionBookPageRewards operation (STW)"""
        try:
            profile_response = self.handle_query_profile(account_id, profile_id, rvn)
            if isinstance(profile_response, tuple):
                return profile_response
            
            # Empty changes for STW collection book
            profile_response['profileChanges'] = []
            return profile_response
            
        except Exception as e:
            return {
                'errorCode': 'errors.com.epicgames.common.server_error',
                'errorMessage': 'Internal server error',
                'messageVars': [],
                'numericErrorCode': 1000,
                'originatingService': 'fortnite',
                'intent': 'prod-live'
            }, 500