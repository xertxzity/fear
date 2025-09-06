#!/usr/bin/env python3
"""
Friends Service for Fortnite Season 7 Emulator
Handles friend requests, friend management, blocked users, and social interactions
"""

from flask import jsonify, request
import json
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from .database import get_database

class FriendsService:
    def __init__(self, websocket_handler=None, presence_service=None):
        self.db = get_database()
        self.websocket_handler = websocket_handler
        self.presence_service = presence_service
        
        # In-memory data for real-time operations
        self.friend_lists: Dict[str, Set[str]] = {}  # account_id -> set of friend_ids
        self.blocked_users: Dict[str, Set[str]] = {}  # account_id -> set of blocked_ids
        self.friend_requests: Dict[str, List[Dict[str, Any]]] = {}  # account_id -> list of requests
        self.pending_requests: Dict[str, Dict[str, Any]] = {}  # request_id -> request_data
        
        # Load existing data from database
        self._load_friends_data()
    
    def _load_friends_data(self):
        """Load friends data from database on startup"""
        try:
            # This would load from database in a real implementation
            # For emulator purposes, we'll start with empty data
            pass
        except Exception as e:
            print(f"Error loading friends data: {e}")
    
    def send_friend_request(self, from_account_id: str, to_account_id: str, message: str = '') -> Dict[str, Any]:
        """Send a friend request"""
        try:
            # Check if already friends
            if self.are_friends(from_account_id, to_account_id):
                return {'error': 'Users are already friends'}, 400
            
            # Check if user is blocked
            if self.is_blocked(to_account_id, from_account_id):
                return {'error': 'Cannot send friend request to this user'}, 403
            
            # Check if request already exists
            existing_request = self._find_existing_request(from_account_id, to_account_id)
            if existing_request:
                return {'error': 'Friend request already sent'}, 400
            
            # Create friend request
            request_id = secrets.token_hex(16)
            friend_request = {
                'id': request_id,
                'from_account_id': from_account_id,
                'to_account_id': to_account_id,
                'message': message,
                'status': 'PENDING',
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'expires_at': (datetime.utcnow() + timedelta(days=30)).isoformat() + 'Z'
            }
            
            # Store request
            self.pending_requests[request_id] = friend_request
            
            # Add to recipient's request list
            if to_account_id not in self.friend_requests:
                self.friend_requests[to_account_id] = []
            self.friend_requests[to_account_id].append(friend_request)
            
            # Send WebSocket notification
            if self.websocket_handler:
                self._send_friend_request_notification(friend_request)
            
            return {
                'request_id': request_id,
                'status': 'SENT',
                'to_account_id': to_account_id
            }
            
        except Exception as e:
            return {'error': f'Failed to send friend request: {str(e)}'}, 500
    
    def respond_to_friend_request(self, request_id: str, account_id: str, response: str) -> Dict[str, Any]:
        """Respond to a friend request (ACCEPT/DECLINE)"""
        try:
            if request_id not in self.pending_requests:
                return {'error': 'Friend request not found'}, 404
            
            friend_request = self.pending_requests[request_id]
            
            # Verify the request is for this user
            if friend_request['to_account_id'] != account_id:
                return {'error': 'Unauthorized to respond to this request'}, 403
            
            # Check if request is still valid
            expires_at = datetime.fromisoformat(friend_request['expires_at'].replace('Z', '+00:00'))
            if datetime.utcnow().replace(tzinfo=expires_at.tzinfo) > expires_at:
                return {'error': 'Friend request has expired'}, 400
            
            # Update request status
            friend_request['status'] = response.upper()
            friend_request['responded_at'] = datetime.utcnow().isoformat() + 'Z'
            
            result = {
                'request_id': request_id,
                'response': response.upper(),
                'from_account_id': friend_request['from_account_id']
            }
            
            if response.upper() == 'ACCEPT':
                # Add to friend lists
                self._add_friendship(friend_request['from_account_id'], friend_request['to_account_id'])
                result['status'] = 'FRIENDS_ADDED'
                
                # Subscribe to each other's presence
                if self.presence_service:
                    self.presence_service.subscribe_to_presence(
                        friend_request['from_account_id'], 
                        [friend_request['to_account_id']]
                    )
                    self.presence_service.subscribe_to_presence(
                        friend_request['to_account_id'], 
                        [friend_request['from_account_id']]
                    )
            
            # Clean up request
            self._remove_friend_request(request_id, account_id)
            
            # Send WebSocket notification
            if self.websocket_handler:
                self._send_friend_response_notification(friend_request, response.upper())
            
            return result
            
        except Exception as e:
            return {'error': f'Failed to respond to friend request: {str(e)}'}, 500
    
    def remove_friend(self, account_id: str, friend_id: str) -> Dict[str, Any]:
        """Remove a friend"""
        try:
            if not self.are_friends(account_id, friend_id):
                return {'error': 'Users are not friends'}, 400
            
            # Remove from both friend lists
            if account_id in self.friend_lists:
                self.friend_lists[account_id].discard(friend_id)
            
            if friend_id in self.friend_lists:
                self.friend_lists[friend_id].discard(account_id)
            
            # Unsubscribe from presence
            if self.presence_service:
                self.presence_service.unsubscribe_from_presence(account_id, [friend_id])
                self.presence_service.unsubscribe_from_presence(friend_id, [account_id])
            
            # Send WebSocket notification
            if self.websocket_handler:
                self._send_friend_removed_notification(account_id, friend_id)
            
            return {
                'status': 'REMOVED',
                'account_id': account_id,
                'friend_id': friend_id
            }
            
        except Exception as e:
            return {'error': f'Failed to remove friend: {str(e)}'}, 500
    
    def block_user(self, account_id: str, target_id: str) -> Dict[str, Any]:
        """Block a user"""
        try:
            # Remove from friends if they are friends
            if self.are_friends(account_id, target_id):
                self.remove_friend(account_id, target_id)
            
            # Add to blocked list
            if account_id not in self.blocked_users:
                self.blocked_users[account_id] = set()
            self.blocked_users[account_id].add(target_id)
            
            # Remove any pending friend requests
            self._remove_all_requests_between_users(account_id, target_id)
            
            return {
                'status': 'BLOCKED',
                'account_id': account_id,
                'blocked_id': target_id
            }
            
        except Exception as e:
            return {'error': f'Failed to block user: {str(e)}'}, 500
    
    def unblock_user(self, account_id: str, target_id: str) -> Dict[str, Any]:
        """Unblock a user"""
        try:
            if account_id not in self.blocked_users or target_id not in self.blocked_users[account_id]:
                return {'error': 'User is not blocked'}, 400
            
            # Remove from blocked list
            self.blocked_users[account_id].discard(target_id)
            
            # Clean up empty blocked list
            if not self.blocked_users[account_id]:
                del self.blocked_users[account_id]
            
            return {
                'status': 'UNBLOCKED',
                'account_id': account_id,
                'unblocked_id': target_id
            }
            
        except Exception as e:
            return {'error': f'Failed to unblock user: {str(e)}'}, 500
    
    def get_friends_list(self, account_id: str, include_presence: bool = True) -> List[Dict[str, Any]]:
        """Get user's friends list"""
        try:
            if account_id not in self.friend_lists:
                return []
            
            friends = []
            friend_ids = list(self.friend_lists[account_id])
            
            for friend_id in friend_ids:
                friend_data = {
                    'account_id': friend_id,
                    'display_name': f'Player_{friend_id[:8]}',
                    'status': 'ACCEPTED',
                    'created_at': datetime.utcnow().isoformat() + 'Z'  # In real implementation, store this
                }
                
                # Add presence information
                if include_presence and self.presence_service:
                    presence = self.presence_service.get_presence(friend_id)
                    if 'error' not in presence:
                        friend_data['presence'] = presence
                
                friends.append(friend_data)
            
            return friends
            
        except Exception as e:
            return []
    
    def get_friend_requests(self, account_id: str, request_type: str = 'incoming') -> List[Dict[str, Any]]:
        """Get friend requests (incoming or outgoing)"""
        try:
            if request_type == 'incoming':
                return self.friend_requests.get(account_id, [])
            elif request_type == 'outgoing':
                outgoing_requests = []
                for request in self.pending_requests.values():
                    if request['from_account_id'] == account_id and request['status'] == 'PENDING':
                        outgoing_requests.append(request)
                return outgoing_requests
            else:
                return {'error': 'Invalid request type'}, 400
                
        except Exception as e:
            return []
    
    def get_blocked_users(self, account_id: str) -> List[Dict[str, Any]]:
        """Get blocked users list"""
        try:
            if account_id not in self.blocked_users:
                return []
            
            blocked_list = []
            for blocked_id in self.blocked_users[account_id]:
                blocked_list.append({
                    'account_id': blocked_id,
                    'display_name': f'Player_{blocked_id[:8]}',
                    'blocked_at': datetime.utcnow().isoformat() + 'Z'  # In real implementation, store this
                })
            
            return blocked_list
            
        except Exception as e:
            return []
    
    def are_friends(self, account_id1: str, account_id2: str) -> bool:
        """Check if two users are friends"""
        return (
            account_id1 in self.friend_lists and 
            account_id2 in self.friend_lists[account_id1]
        )
    
    def is_blocked(self, account_id: str, target_id: str) -> bool:
        """Check if a user is blocked"""
        return (
            account_id in self.blocked_users and 
            target_id in self.blocked_users[account_id]
        )
    
    def get_mutual_friends(self, account_id1: str, account_id2: str) -> List[str]:
        """Get mutual friends between two users"""
        try:
            if account_id1 not in self.friend_lists or account_id2 not in self.friend_lists:
                return []
            
            friends1 = self.friend_lists[account_id1]
            friends2 = self.friend_lists[account_id2]
            
            return list(friends1.intersection(friends2))
            
        except Exception as e:
            return []
    
    def search_friends(self, account_id: str, query: str) -> List[Dict[str, Any]]:
        """Search for friends by display name or account ID"""
        try:
            if account_id not in self.friend_lists:
                return []
            
            friends = self.get_friends_list(account_id, include_presence=False)
            
            # Simple search implementation
            results = []
            query_lower = query.lower()
            
            for friend in friends:
                if (
                    query_lower in friend['account_id'].lower() or 
                    query_lower in friend['display_name'].lower()
                ):
                    results.append(friend)
            
            return results
            
        except Exception as e:
            return []
    
    def get_friends_summary(self, account_id: str) -> Dict[str, Any]:
        """Get friends summary for a user"""
        try:
            friends_count = len(self.friend_lists.get(account_id, set()))
            blocked_count = len(self.blocked_users.get(account_id, set()))
            incoming_requests = len(self.friend_requests.get(account_id, []))
            
            # Count outgoing requests
            outgoing_requests = 0
            for request in self.pending_requests.values():
                if request['from_account_id'] == account_id and request['status'] == 'PENDING':
                    outgoing_requests += 1
            
            # Count online friends
            online_friends = 0
            if self.presence_service and account_id in self.friend_lists:
                for friend_id in self.friend_lists[account_id]:
                    presence = self.presence_service.get_presence(friend_id)
                    if 'error' not in presence and presence.get('status') == 'online':
                        online_friends += 1
            
            return {
                'account_id': account_id,
                'friends_count': friends_count,
                'blocked_count': blocked_count,
                'incoming_requests': incoming_requests,
                'outgoing_requests': outgoing_requests,
                'online_friends': online_friends,
                'last_updated': datetime.utcnow().isoformat() + 'Z'
            }
            
        except Exception as e:
            return {'error': f'Failed to get friends summary: {str(e)}'}
    
    # Helper methods
    def _add_friendship(self, account_id1: str, account_id2: str):
        """Add friendship between two users"""
        if account_id1 not in self.friend_lists:
            self.friend_lists[account_id1] = set()
        if account_id2 not in self.friend_lists:
            self.friend_lists[account_id2] = set()
        
        self.friend_lists[account_id1].add(account_id2)
        self.friend_lists[account_id2].add(account_id1)
    
    def _find_existing_request(self, from_id: str, to_id: str) -> Optional[Dict[str, Any]]:
        """Find existing friend request between users"""
        for request in self.pending_requests.values():
            if (
                request['from_account_id'] == from_id and 
                request['to_account_id'] == to_id and 
                request['status'] == 'PENDING'
            ):
                return request
        return None
    
    def _remove_friend_request(self, request_id: str, account_id: str):
        """Remove friend request from all data structures"""
        if request_id in self.pending_requests:
            del self.pending_requests[request_id]
        
        if account_id in self.friend_requests:
            self.friend_requests[account_id] = [
                req for req in self.friend_requests[account_id] 
                if req['id'] != request_id
            ]
    
    def _remove_all_requests_between_users(self, account_id1: str, account_id2: str):
        """Remove all friend requests between two users"""
        requests_to_remove = []
        
        for request_id, request in self.pending_requests.items():
            if (
                (request['from_account_id'] == account_id1 and request['to_account_id'] == account_id2) or
                (request['from_account_id'] == account_id2 and request['to_account_id'] == account_id1)
            ):
                requests_to_remove.append(request_id)
        
        for request_id in requests_to_remove:
            if request_id in self.pending_requests:
                request = self.pending_requests[request_id]
                self._remove_friend_request(request_id, request['to_account_id'])
    
    def _send_friend_request_notification(self, friend_request: Dict[str, Any]):
        """Send friend request notification via WebSocket"""
        try:
            notification = {
                'type': 'friend_request',
                'request': friend_request,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
            
            # Find target user's WebSocket connection
            for client_id, client_info in self.websocket_handler.connected_clients.items():
                if client_info['account_id'] == friend_request['to_account_id']:
                    self.websocket_handler.socketio.emit(
                        'friend_request_received', 
                        notification, 
                        room=client_id
                    )
                    break
                    
        except Exception as e:
            print(f"Error sending friend request notification: {e}")
    
    def _send_friend_response_notification(self, friend_request: Dict[str, Any], response: str):
        """Send friend response notification via WebSocket"""
        try:
            notification = {
                'type': 'friend_response',
                'request_id': friend_request['id'],
                'response': response,
                'from_account_id': friend_request['to_account_id'],
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
            
            # Find sender's WebSocket connection
            for client_id, client_info in self.websocket_handler.connected_clients.items():
                if client_info['account_id'] == friend_request['from_account_id']:
                    self.websocket_handler.socketio.emit(
                        'friend_request_response', 
                        notification, 
                        room=client_id
                    )
                    break
                    
        except Exception as e:
            print(f"Error sending friend response notification: {e}")
    
    def _send_friend_removed_notification(self, account_id: str, friend_id: str):
        """Send friend removed notification via WebSocket"""
        try:
            notification = {
                'type': 'friend_removed',
                'account_id': account_id,
                'friend_id': friend_id,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
            
            # Notify both users
            for user_id in [account_id, friend_id]:
                for client_id, client_info in self.websocket_handler.connected_clients.items():
                    if client_info['account_id'] == user_id:
                        self.websocket_handler.socketio.emit(
                            'friend_removed', 
                            notification, 
                            room=client_id
                        )
                        break
                        
        except Exception as e:
            print(f"Error sending friend removed notification: {e}")
    
    def cleanup_expired_requests(self):
        """Clean up expired friend requests"""
        try:
            current_time = datetime.utcnow()
            expired_requests = []
            
            for request_id, request in self.pending_requests.items():
                expires_at = datetime.fromisoformat(request['expires_at'].replace('Z', '+00:00'))
                if current_time.replace(tzinfo=expires_at.tzinfo) > expires_at:
                    expired_requests.append(request_id)
            
            # Remove expired requests
            for request_id in expired_requests:
                if request_id in self.pending_requests:
                    request = self.pending_requests[request_id]
                    self._remove_friend_request(request_id, request['to_account_id'])
            
            return len(expired_requests)
            
        except Exception as e:
            print(f"Error cleaning up expired requests: {e}")
            return 0