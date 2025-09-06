#!/usr/bin/env python3
"""
Presence Service for Fortnite Season 7 Emulator
Handles user presence, online status, and friend presence updates
"""

from flask import jsonify, request
import json
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from .database import get_database

class PresenceService:
    def __init__(self, websocket_handler=None):
        self.db = get_database()
        self.websocket_handler = websocket_handler
        
        # In-memory presence data for real-time operations
        self.user_presence: Dict[str, Dict[str, Any]] = {}
        self.presence_subscriptions: Dict[str, Set[str]] = {}  # account_id -> set of subscribers
        self.user_subscriptions: Dict[str, Set[str]] = {}  # account_id -> set of subscribed users
        
        # Presence states
        self.valid_states = {
            'online': 'Online',
            'away': 'Away', 
            'dnd': 'Do Not Disturb',
            'offline': 'Offline'
        }
        
        # Activity types for Season 7.40
        self.activity_types = {
            'lobby': 'In Lobby',
            'match': 'In Match',
            'creative': 'In Creative',
            'stw': 'Save the World',
            'party': 'In Party',
            'matchmaking': 'Matchmaking'
        }
    
    def set_presence(self, account_id: str, presence_data: Dict[str, Any]) -> Dict[str, Any]:
        """Set user presence"""
        try:
            # Validate presence state
            status = presence_data.get('status', 'online')
            if status not in self.valid_states:
                return {'error': f'Invalid status: {status}'}, 400
            
            # Create presence object
            presence = {
                'account_id': account_id,
                'status': status,
                'last_online': datetime.utcnow().isoformat() + 'Z',
                'properties': presence_data.get('properties', {}),
                'activities': presence_data.get('activities', []),
                'platform': presence_data.get('platform', 'WIN'),
                'session_id': presence_data.get('session_id', secrets.token_hex(16))
            }
            
            # Add Season 7.40 specific properties
            if 'activity' in presence_data:
                activity = presence_data['activity']
                if activity in self.activity_types:
                    presence['properties']['FortBasicInfo_j'] = {
                        'homeBaseRating': 1,
                        'bIsPlaying': status == 'online' and activity != 'lobby'
                    }
                    presence['properties']['FortLFG_I'] = {
                        'bInLFG': False
                    }
                    presence['properties']['party_id'] = presence_data.get('party_id', '')
                    presence['properties']['playlist'] = presence_data.get('playlist', 'None')
            
            # Store presence
            self.user_presence[account_id] = presence
            
            # Broadcast to subscribers
            self.broadcast_presence_update(account_id, presence)
            
            return {
                'account_id': account_id,
                'status': 'UPDATED',
                'presence': presence
            }
            
        except Exception as e:
            return {'error': f'Failed to set presence: {str(e)}'}, 500
    
    def get_presence(self, account_id: str) -> Dict[str, Any]:
        """Get user presence"""
        try:
            if account_id not in self.user_presence:
                # Return default offline presence
                return {
                    'account_id': account_id,
                    'status': 'offline',
                    'last_online': datetime.utcnow().isoformat() + 'Z',
                    'properties': {},
                    'activities': [],
                    'platform': 'WIN',
                    'session_id': ''
                }
            
            return self.user_presence[account_id]
            
        except Exception as e:
            return {'error': f'Failed to get presence: {str(e)}'}, 500
    
    def get_multiple_presence(self, account_ids: List[str]) -> List[Dict[str, Any]]:
        """Get presence for multiple users"""
        try:
            presences = []
            for account_id in account_ids:
                presence = self.get_presence(account_id)
                if 'error' not in presence:
                    presences.append(presence)
            
            return presences
            
        except Exception as e:
            return []
    
    def subscribe_to_presence(self, subscriber_id: str, target_ids: List[str]) -> Dict[str, Any]:
        """Subscribe to presence updates for specific users"""
        try:
            subscribed_count = 0
            
            for target_id in target_ids:
                # Add subscriber to target's subscription list
                if target_id not in self.presence_subscriptions:
                    self.presence_subscriptions[target_id] = set()
                self.presence_subscriptions[target_id].add(subscriber_id)
                
                # Add target to subscriber's subscription list
                if subscriber_id not in self.user_subscriptions:
                    self.user_subscriptions[subscriber_id] = set()
                self.user_subscriptions[subscriber_id].add(target_id)
                
                subscribed_count += 1
            
            return {
                'subscriber_id': subscriber_id,
                'subscribed_to': subscribed_count,
                'status': 'SUBSCRIBED'
            }
            
        except Exception as e:
            return {'error': f'Failed to subscribe to presence: {str(e)}'}, 500
    
    def unsubscribe_from_presence(self, subscriber_id: str, target_ids: List[str] = None) -> Dict[str, Any]:
        """Unsubscribe from presence updates"""
        try:
            unsubscribed_count = 0
            
            if target_ids is None:
                # Unsubscribe from all
                if subscriber_id in self.user_subscriptions:
                    target_ids = list(self.user_subscriptions[subscriber_id])
                else:
                    target_ids = []
            
            for target_id in target_ids:
                # Remove subscriber from target's subscription list
                if target_id in self.presence_subscriptions:
                    self.presence_subscriptions[target_id].discard(subscriber_id)
                    if not self.presence_subscriptions[target_id]:
                        del self.presence_subscriptions[target_id]
                
                # Remove target from subscriber's subscription list
                if subscriber_id in self.user_subscriptions:
                    self.user_subscriptions[subscriber_id].discard(target_id)
                
                unsubscribed_count += 1
            
            # Clean up empty subscription sets
            if subscriber_id in self.user_subscriptions and not self.user_subscriptions[subscriber_id]:
                del self.user_subscriptions[subscriber_id]
            
            return {
                'subscriber_id': subscriber_id,
                'unsubscribed_from': unsubscribed_count,
                'status': 'UNSUBSCRIBED'
            }
            
        except Exception as e:
            return {'error': f'Failed to unsubscribe from presence: {str(e)}'}, 500
    
    def broadcast_presence_update(self, account_id: str, presence: Dict[str, Any]):
        """Broadcast presence update to subscribers"""
        try:
            if account_id not in self.presence_subscriptions:
                return
            
            subscribers = self.presence_subscriptions[account_id]
            
            # Create presence update message
            update_message = {
                'type': 'presence_update',
                'account_id': account_id,
                'presence': presence,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
            
            # Send via WebSocket if available
            if self.websocket_handler:
                for subscriber_id in subscribers:
                    # Find WebSocket client for subscriber
                    for client_id, client_info in self.websocket_handler.connected_clients.items():
                        if client_info['account_id'] == subscriber_id:
                            self.websocket_handler.socketio.emit(
                                'presence_update', 
                                update_message, 
                                room=client_id
                            )
                            break
            
        except Exception as e:
            print(f"Error broadcasting presence update: {e}")
    
    def handle_user_disconnect(self, account_id: str):
        """Handle user disconnection - set to offline"""
        try:
            if account_id in self.user_presence:
                # Update to offline status
                offline_presence = self.user_presence[account_id].copy()
                offline_presence['status'] = 'offline'
                offline_presence['last_online'] = datetime.utcnow().isoformat() + 'Z'
                offline_presence['properties'] = {}
                offline_presence['activities'] = []
                
                self.user_presence[account_id] = offline_presence
                
                # Broadcast offline status
                self.broadcast_presence_update(account_id, offline_presence)
            
            # Clean up subscriptions
            self.unsubscribe_from_presence(account_id)
            
        except Exception as e:
            print(f"Error handling user disconnect: {e}")
    
    def get_friends_presence(self, account_id: str, friend_ids: List[str]) -> List[Dict[str, Any]]:
        """Get presence for friends list"""
        try:
            friends_presence = []
            
            for friend_id in friend_ids:
                presence = self.get_presence(friend_id)
                if 'error' not in presence:
                    # Add friend-specific information
                    friend_presence = presence.copy()
                    friend_presence['is_friend'] = True
                    friend_presence['can_join'] = (
                        presence['status'] == 'online' and 
                        presence.get('properties', {}).get('party_id', '') != ''
                    )
                    friends_presence.append(friend_presence)
            
            return friends_presence
            
        except Exception as e:
            return []
    
    def update_activity(self, account_id: str, activity: str, properties: Dict[str, Any] = None) -> Dict[str, Any]:
        """Update user activity (lobby, match, etc.)"""
        try:
            if account_id not in self.user_presence:
                # Create basic presence if doesn't exist
                self.user_presence[account_id] = {
                    'account_id': account_id,
                    'status': 'online',
                    'last_online': datetime.utcnow().isoformat() + 'Z',
                    'properties': {},
                    'activities': [],
                    'platform': 'WIN',
                    'session_id': secrets.token_hex(16)
                }
            
            presence = self.user_presence[account_id]
            
            # Update activity-specific properties
            if activity in self.activity_types:
                presence['properties']['current_activity'] = activity
                presence['properties']['activity_display'] = self.activity_types[activity]
                
                # Season 7.40 specific properties
                if activity == 'match':
                    presence['properties']['FortBasicInfo_j'] = {
                        'homeBaseRating': 1,
                        'bIsPlaying': True
                    }
                elif activity == 'lobby':
                    presence['properties']['FortBasicInfo_j'] = {
                        'homeBaseRating': 1,
                        'bIsPlaying': False
                    }
                
                # Add custom properties
                if properties:
                    presence['properties'].update(properties)
                
                # Update timestamp
                presence['last_online'] = datetime.utcnow().isoformat() + 'Z'
                
                # Broadcast update
                self.broadcast_presence_update(account_id, presence)
                
                return {
                    'account_id': account_id,
                    'activity': activity,
                    'status': 'UPDATED'
                }
            else:
                return {'error': f'Invalid activity: {activity}'}, 400
                
        except Exception as e:
            return {'error': f'Failed to update activity: {str(e)}'}, 500
    
    def cleanup_offline_users(self, offline_threshold_minutes: int = 30):
        """Clean up users who have been offline for too long"""
        try:
            current_time = datetime.utcnow()
            threshold = current_time - timedelta(minutes=offline_threshold_minutes)
            
            users_to_remove = []
            
            for account_id, presence in self.user_presence.items():
                if presence['status'] == 'offline':
                    last_online = datetime.fromisoformat(presence['last_online'].replace('Z', '+00:00'))
                    if last_online.replace(tzinfo=None) < threshold:
                        users_to_remove.append(account_id)
            
            # Remove old offline users
            for account_id in users_to_remove:
                del self.user_presence[account_id]
                self.unsubscribe_from_presence(account_id)
                
                # Also remove from others' subscriptions
                if account_id in self.presence_subscriptions:
                    del self.presence_subscriptions[account_id]
            
            return len(users_to_remove)
            
        except Exception as e:
            print(f"Error cleaning up offline users: {e}")
            return 0
    
    def get_presence_summary(self) -> Dict[str, Any]:
        """Get presence system summary"""
        try:
            online_count = sum(1 for p in self.user_presence.values() if p['status'] == 'online')
            away_count = sum(1 for p in self.user_presence.values() if p['status'] == 'away')
            dnd_count = sum(1 for p in self.user_presence.values() if p['status'] == 'dnd')
            offline_count = sum(1 for p in self.user_presence.values() if p['status'] == 'offline')
            
            return {
                'total_users': len(self.user_presence),
                'online': online_count,
                'away': away_count,
                'dnd': dnd_count,
                'offline': offline_count,
                'total_subscriptions': sum(len(subs) for subs in self.presence_subscriptions.values()),
                'last_updated': datetime.utcnow().isoformat() + 'Z'
            }
            
        except Exception as e:
            return {'error': f'Failed to get presence summary: {str(e)}'}