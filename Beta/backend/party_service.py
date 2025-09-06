#!/usr/bin/env python3
"""
Party Service for Fortnite Season 7 Emulator
Handles party creation, management, invitations, and member operations
"""

from flask import jsonify, request
import json
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from .database import get_database

class PartyService:
    def __init__(self, websocket_handler=None):
        self.db = get_database()
        self.websocket_handler = websocket_handler
        
        # In-memory party data for real-time operations
        self.active_parties: Dict[str, Dict[str, Any]] = {}
        self.party_invitations: Dict[str, List[Dict[str, Any]]] = {}
        self.user_parties: Dict[str, str] = {}  # account_id -> party_id mapping
        
        # Party configuration
        self.max_party_size = 4
        self.invitation_timeout = 300  # 5 minutes
    
    def create_party(self, account_id: str, party_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a new party"""
        try:
            # Check if user is already in a party
            if account_id in self.user_parties:
                current_party_id = self.user_parties[account_id]
                if current_party_id in self.active_parties:
                    return {
                        'error': 'User already in party',
                        'current_party_id': current_party_id
                    }, 400
            
            party_id = secrets.token_hex(16)
            
            # Default party configuration
            default_config = {
                'privacy': 'PRIVATE',
                'max_size': self.max_party_size,
                'join_confirmation': True,
                'allow_friends_of_friends': False,
                'playlist': 'playlist_defaultsolo',
                'custom_key': ''
            }
            
            if party_config:
                default_config.update(party_config)
            
            # Create party data
            party_data = {
                'id': party_id,
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'updated_at': datetime.utcnow().isoformat() + 'Z',
                'config': default_config,
                'members': [{
                    'account_id': account_id,
                    'display_name': f'Player_{account_id[:8]}',
                    'role': 'CAPTAIN',
                    'joined_at': datetime.utcnow().isoformat() + 'Z',
                    'ready': False,
                    'platform': 'WIN',
                    'location': 'PreLobby'
                }],
                'invitations': [],
                'meta': {
                    'schema': {
                        'Default:PartyMemberReady_j': {
                            'type': 'boolean'
                        },
                        'Default:PartyMemberLocation_s': {
                            'type': 'string'
                        }
                    }
                }
            }
            
            # Store party
            self.active_parties[party_id] = party_data
            self.user_parties[account_id] = party_id
            
            # Save to database
            self.db.save_party(party_id, party_data)
            
            return {
                'id': party_id,
                'created_at': party_data['created_at'],
                'updated_at': party_data['updated_at'],
                'config': party_data['config'],
                'members': party_data['members'],
                'invitations': party_data['invitations'],
                'meta': party_data['meta']
            }
            
        except Exception as e:
            return {'error': f'Failed to create party: {str(e)}'}, 500
    
    def get_party(self, party_id: str) -> Dict[str, Any]:
        """Get party information"""
        try:
            if party_id not in self.active_parties:
                # Try to load from database
                party_data = self.db.get_party(party_id)
                if not party_data:
                    return {'error': 'Party not found'}, 404
                self.active_parties[party_id] = party_data
            
            party = self.active_parties[party_id]
            return {
                'id': party['id'],
                'created_at': party['created_at'],
                'updated_at': party['updated_at'],
                'config': party['config'],
                'members': party['members'],
                'invitations': party['invitations'],
                'meta': party['meta']
            }
            
        except Exception as e:
            return {'error': f'Failed to get party: {str(e)}'}, 500
    
    def join_party(self, party_id: str, account_id: str, connection_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Join a party"""
        try:
            # Check if party exists
            if party_id not in self.active_parties:
                party_data = self.db.get_party(party_id)
                if not party_data:
                    return {'error': 'Party not found'}, 404
                self.active_parties[party_id] = party_data
            
            party = self.active_parties[party_id]
            
            # Check if user is already in the party
            for member in party['members']:
                if member['account_id'] == account_id:
                    return {'error': 'User already in party'}, 400
            
            # Check party size limit
            if len(party['members']) >= party['config']['max_size']:
                return {'error': 'Party is full'}, 400
            
            # Check if user is already in another party
            if account_id in self.user_parties:
                current_party_id = self.user_parties[account_id]
                if current_party_id != party_id and current_party_id in self.active_parties:
                    return {'error': 'User already in another party'}, 400
            
            # Add member to party
            member_data = {
                'account_id': account_id,
                'display_name': f'Player_{account_id[:8]}',
                'role': 'MEMBER',
                'joined_at': datetime.utcnow().isoformat() + 'Z',
                'ready': False,
                'platform': connection_data.get('platform', 'WIN') if connection_data else 'WIN',
                'location': 'PreLobby'
            }
            
            party['members'].append(member_data)
            party['updated_at'] = datetime.utcnow().isoformat() + 'Z'
            
            # Update mappings
            self.user_parties[account_id] = party_id
            
            # Save to database
            self.db.save_party(party_id, party)
            
            # Notify WebSocket clients
            if self.websocket_handler:
                self.websocket_handler.socketio.emit('party_member_joined', {
                    'party_id': party_id,
                    'member': member_data,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }, room=f'party_{party_id}')
            
            return {
                'status': 'JOINED',
                'party_id': party_id,
                'member': member_data
            }
            
        except Exception as e:
            return {'error': f'Failed to join party: {str(e)}'}, 500
    
    def leave_party(self, party_id: str, account_id: str) -> Dict[str, Any]:
        """Leave a party"""
        try:
            if party_id not in self.active_parties:
                return {'error': 'Party not found'}, 404
            
            party = self.active_parties[party_id]
            
            # Find and remove member
            member_to_remove = None
            for i, member in enumerate(party['members']):
                if member['account_id'] == account_id:
                    member_to_remove = party['members'].pop(i)
                    break
            
            if not member_to_remove:
                return {'error': 'User not in party'}, 400
            
            # Update party
            party['updated_at'] = datetime.utcnow().isoformat() + 'Z'
            
            # Remove from user mapping
            if account_id in self.user_parties:
                del self.user_parties[account_id]
            
            # If party is empty, delete it
            if not party['members']:
                del self.active_parties[party_id]
                self.db.delete_party(party_id)
            else:
                # If the captain left, promote someone else
                if member_to_remove['role'] == 'CAPTAIN' and party['members']:
                    party['members'][0]['role'] = 'CAPTAIN'
                
                # Save updated party
                self.db.save_party(party_id, party)
            
            # Notify WebSocket clients
            if self.websocket_handler:
                self.websocket_handler.socketio.emit('party_member_left', {
                    'party_id': party_id,
                    'account_id': account_id,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }, room=f'party_{party_id}')
            
            return {
                'status': 'LEFT',
                'party_id': party_id
            }
            
        except Exception as e:
            return {'error': f'Failed to leave party: {str(e)}'}, 500
    
    def send_invitation(self, party_id: str, from_account_id: str, to_account_id: str) -> Dict[str, Any]:
        """Send party invitation"""
        try:
            if party_id not in self.active_parties:
                return {'error': 'Party not found'}, 404
            
            party = self.active_parties[party_id]
            
            # Check if sender is in the party and has permission
            sender_member = None
            for member in party['members']:
                if member['account_id'] == from_account_id:
                    sender_member = member
                    break
            
            if not sender_member:
                return {'error': 'Sender not in party'}, 403
            
            # Check if target is already in a party
            if to_account_id in self.user_parties:
                return {'error': 'Target user already in a party'}, 400
            
            # Create invitation
            invitation_id = secrets.token_hex(8)
            invitation = {
                'id': invitation_id,
                'party_id': party_id,
                'from_account_id': from_account_id,
                'to_account_id': to_account_id,
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'expires_at': (datetime.utcnow() + timedelta(seconds=self.invitation_timeout)).isoformat() + 'Z',
                'status': 'PENDING'
            }
            
            # Store invitation
            party['invitations'].append(invitation)
            
            if to_account_id not in self.party_invitations:
                self.party_invitations[to_account_id] = []
            self.party_invitations[to_account_id].append(invitation)
            
            # Save party
            self.db.save_party(party_id, party)
            
            # Send WebSocket notification
            if self.websocket_handler:
                self.websocket_handler.send_party_invitation(from_account_id, to_account_id, party_id)
            
            return {
                'invitation_id': invitation_id,
                'status': 'SENT',
                'expires_at': invitation['expires_at']
            }
            
        except Exception as e:
            return {'error': f'Failed to send invitation: {str(e)}'}, 500
    
    def respond_to_invitation(self, invitation_id: str, account_id: str, response: str) -> Dict[str, Any]:
        """Respond to party invitation (ACCEPT/DECLINE)"""
        try:
            # Find invitation
            invitation = None
            party_id = None
            
            for party_id_key, party in self.active_parties.items():
                for inv in party['invitations']:
                    if inv['id'] == invitation_id and inv['to_account_id'] == account_id:
                        invitation = inv
                        party_id = party_id_key
                        break
                if invitation:
                    break
            
            if not invitation:
                return {'error': 'Invitation not found'}, 404
            
            # Check if invitation is still valid
            expires_at = datetime.fromisoformat(invitation['expires_at'].replace('Z', '+00:00'))
            if datetime.utcnow().replace(tzinfo=expires_at.tzinfo) > expires_at:
                return {'error': 'Invitation expired'}, 400
            
            # Update invitation status
            invitation['status'] = response.upper()
            invitation['responded_at'] = datetime.utcnow().isoformat() + 'Z'
            
            result = {'invitation_id': invitation_id, 'response': response.upper()}
            
            if response.upper() == 'ACCEPT':
                # Join the party
                join_result = self.join_party(party_id, account_id)
                if 'error' in join_result:
                    return join_result
                result['party_id'] = party_id
            
            # Clean up invitation from user's list
            if account_id in self.party_invitations:
                self.party_invitations[account_id] = [
                    inv for inv in self.party_invitations[account_id] 
                    if inv['id'] != invitation_id
                ]
            
            # Save party
            self.db.save_party(party_id, self.active_parties[party_id])
            
            return result
            
        except Exception as e:
            return {'error': f'Failed to respond to invitation: {str(e)}'}, 500
    
    def get_user_party(self, account_id: str) -> Dict[str, Any]:
        """Get the party that a user is currently in"""
        try:
            if account_id not in self.user_parties:
                return {'error': 'User not in any party'}, 404
            
            party_id = self.user_parties[account_id]
            return self.get_party(party_id)
            
        except Exception as e:
            return {'error': f'Failed to get user party: {str(e)}'}, 500
    
    def update_member_ready_state(self, party_id: str, account_id: str, ready: bool) -> Dict[str, Any]:
        """Update member ready state"""
        try:
            if party_id not in self.active_parties:
                return {'error': 'Party not found'}, 404
            
            party = self.active_parties[party_id]
            
            # Find and update member
            member_updated = False
            for member in party['members']:
                if member['account_id'] == account_id:
                    member['ready'] = ready
                    member_updated = True
                    break
            
            if not member_updated:
                return {'error': 'Member not found in party'}, 404
            
            party['updated_at'] = datetime.utcnow().isoformat() + 'Z'
            
            # Save party
            self.db.save_party(party_id, party)
            
            # Notify WebSocket clients
            if self.websocket_handler:
                self.websocket_handler.socketio.emit('party_member_ready_changed', {
                    'party_id': party_id,
                    'account_id': account_id,
                    'ready': ready,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }, room=f'party_{party_id}')
            
            return {
                'status': 'UPDATED',
                'account_id': account_id,
                'ready': ready
            }
            
        except Exception as e:
            return {'error': f'Failed to update ready state: {str(e)}'}, 500
    
    def get_user_invitations(self, account_id: str) -> List[Dict[str, Any]]:
        """Get pending invitations for a user"""
        try:
            if account_id not in self.party_invitations:
                return []
            
            # Filter out expired invitations
            current_time = datetime.utcnow()
            valid_invitations = []
            
            for invitation in self.party_invitations[account_id]:
                expires_at = datetime.fromisoformat(invitation['expires_at'].replace('Z', '+00:00'))
                if current_time.replace(tzinfo=expires_at.tzinfo) <= expires_at and invitation['status'] == 'PENDING':
                    valid_invitations.append(invitation)
            
            # Update the list to remove expired invitations
            self.party_invitations[account_id] = valid_invitations
            
            return valid_invitations
            
        except Exception as e:
            return []
    
    def cleanup_expired_invitations(self):
        """Clean up expired invitations (should be called periodically)"""
        try:
            current_time = datetime.utcnow()
            
            for account_id in list(self.party_invitations.keys()):
                valid_invitations = []
                for invitation in self.party_invitations[account_id]:
                    expires_at = datetime.fromisoformat(invitation['expires_at'].replace('Z', '+00:00'))
                    if current_time.replace(tzinfo=expires_at.tzinfo) <= expires_at:
                        valid_invitations.append(invitation)
                
                if valid_invitations:
                    self.party_invitations[account_id] = valid_invitations
                else:
                    del self.party_invitations[account_id]
            
            # Also clean up invitations from party data
            for party in self.active_parties.values():
                valid_invitations = []
                for invitation in party['invitations']:
                    expires_at = datetime.fromisoformat(invitation['expires_at'].replace('Z', '+00:00'))
                    if current_time.replace(tzinfo=expires_at.tzinfo) <= expires_at:
                        valid_invitations.append(invitation)
                party['invitations'] = valid_invitations
                
        except Exception as e:
            print(f"Error cleaning up expired invitations: {e}")