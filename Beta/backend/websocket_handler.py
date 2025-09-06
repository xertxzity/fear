#!/usr/bin/env python3
"""
WebSocket Handler for Fortnite Season 7 Emulator
Handles real-time lobby communication, party chat, and XMPP-like messaging
"""

import asyncio
import json
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Set, Any, Optional
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask import request

class WebSocketHandler:
    def __init__(self, app):
        self.socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
        self.connected_clients: Dict[str, Dict[str, Any]] = {}
        self.party_rooms: Dict[str, Set[str]] = {}
        self.presence_data: Dict[str, Dict[str, Any]] = {}
        
        # Setup event handlers
        self.setup_handlers()
        
    def setup_handlers(self):
        """Setup WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect(auth=None):
            """Handle client connection"""
            client_id = request.sid
            account_id = self.extract_account_id(auth)
            
            if not account_id:
                disconnect()
                return False
                
            # Store client info
            self.connected_clients[client_id] = {
                'account_id': account_id,
                'connected_at': datetime.utcnow().isoformat(),
                'presence': 'online',
                'party_id': None,
                'platform': auth.get('platform', 'PC') if auth else 'PC'
            }
            
            # Update presence
            self.update_presence(account_id, 'online', {
                'status': 'In Lobby',
                'platform': self.connected_clients[client_id]['platform'],
                'joinable': True
            })
            
            # Send connection confirmation
            emit('connected', {
                'account_id': account_id,
                'server_time': datetime.utcnow().isoformat() + 'Z',
                'features': ['party_chat', 'presence', 'lobby_updates']
            })
            
            print(f"Client connected: {account_id} ({client_id})")
            
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            client_id = request.sid
            
            if client_id in self.connected_clients:
                client_info = self.connected_clients[client_id]
                account_id = client_info['account_id']
                
                # Leave party room if in one
                if client_info.get('party_id'):
                    self.leave_party_room(client_id, client_info['party_id'])
                
                # Update presence to offline
                self.update_presence(account_id, 'offline')
                
                # Remove from connected clients
                del self.connected_clients[client_id]
                
                print(f"Client disconnected: {account_id} ({client_id})")
        
        @self.socketio.on('join_party')
        def handle_join_party(data):
            """Handle joining a party room"""
            client_id = request.sid
            party_id = data.get('party_id')
            
            if not party_id or client_id not in self.connected_clients:
                emit('error', {'message': 'Invalid party ID or not connected'})
                return
                
            self.join_party_room(client_id, party_id)
            
        @self.socketio.on('leave_party')
        def handle_leave_party(data):
            """Handle leaving a party room"""
            client_id = request.sid
            party_id = data.get('party_id')
            
            if client_id in self.connected_clients:
                current_party = self.connected_clients[client_id].get('party_id')
                if current_party:
                    self.leave_party_room(client_id, current_party)
        
        @self.socketio.on('party_chat')
        def handle_party_chat(data):
            """Handle party chat messages"""
            client_id = request.sid
            
            if client_id not in self.connected_clients:
                return
                
            client_info = self.connected_clients[client_id]
            party_id = client_info.get('party_id')
            
            if not party_id:
                emit('error', {'message': 'Not in a party'})
                return
                
            message = {
                'type': 'party_chat',
                'from': client_info['account_id'],
                'message': data.get('message', ''),
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'party_id': party_id
            }
            
            # Broadcast to party room
            self.socketio.emit('party_message', message, room=f'party_{party_id}')
            
        @self.socketio.on('update_presence')
        def handle_update_presence(data):
            """Handle presence updates"""
            client_id = request.sid
            
            if client_id not in self.connected_clients:
                return
                
            account_id = self.connected_clients[client_id]['account_id']
            status = data.get('status', 'online')
            properties = data.get('properties', {})
            
            self.update_presence(account_id, status, properties)
            
        @self.socketio.on('lobby_ready')
        def handle_lobby_ready(data):
            """Handle lobby ready state changes"""
            client_id = request.sid
            
            if client_id not in self.connected_clients:
                return
                
            client_info = self.connected_clients[client_id]
            party_id = client_info.get('party_id')
            
            if party_id:
                ready_state = {
                    'type': 'lobby_ready',
                    'account_id': client_info['account_id'],
                    'ready': data.get('ready', False),
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
                
                # Broadcast to party
                self.socketio.emit('party_update', ready_state, room=f'party_{party_id}')
    
    def extract_account_id(self, auth: Optional[Dict]) -> Optional[str]:
        """Extract account ID from auth data"""
        if not auth:
            return None
            
        # Try different auth methods
        if 'account_id' in auth:
            return auth['account_id']
        elif 'token' in auth:
            # In a real implementation, you'd validate the token
            # For emulator purposes, we'll generate a dummy account ID
            return f"account_{secrets.token_hex(8)}"
            
        return None
    
    def join_party_room(self, client_id: str, party_id: str):
        """Join a party room"""
        if client_id not in self.connected_clients:
            return
            
        client_info = self.connected_clients[client_id]
        
        # Leave current party if in one
        if client_info.get('party_id'):
            self.leave_party_room(client_id, client_info['party_id'])
        
        # Join new party room
        room_name = f'party_{party_id}'
        join_room(room_name, sid=client_id)
        
        # Update client info
        client_info['party_id'] = party_id
        
        # Add to party room tracking
        if party_id not in self.party_rooms:
            self.party_rooms[party_id] = set()
        self.party_rooms[party_id].add(client_id)
        
        # Notify party members
        self.socketio.emit('party_member_joined', {
            'account_id': client_info['account_id'],
            'party_id': party_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }, room=room_name)
        
        # Send party info to joining client
        self.socketio.emit('party_joined', {
            'party_id': party_id,
            'members': [self.connected_clients[cid]['account_id'] 
                       for cid in self.party_rooms[party_id] 
                       if cid in self.connected_clients]
        }, room=client_id)
    
    def leave_party_room(self, client_id: str, party_id: str):
        """Leave a party room"""
        if client_id not in self.connected_clients:
            return
            
        client_info = self.connected_clients[client_id]
        room_name = f'party_{party_id}'
        
        # Leave the room
        leave_room(room_name, sid=client_id)
        
        # Update client info
        client_info['party_id'] = None
        
        # Remove from party room tracking
        if party_id in self.party_rooms:
            self.party_rooms[party_id].discard(client_id)
            
            # Clean up empty party rooms
            if not self.party_rooms[party_id]:
                del self.party_rooms[party_id]
            else:
                # Notify remaining party members
                self.socketio.emit('party_member_left', {
                    'account_id': client_info['account_id'],
                    'party_id': party_id,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }, room=room_name)
    
    def update_presence(self, account_id: str, status: str, properties: Dict[str, Any] = None):
        """Update user presence"""
        if properties is None:
            properties = {}
            
        presence_info = {
            'account_id': account_id,
            'status': status,
            'last_online': datetime.utcnow().isoformat() + 'Z',
            'properties': properties
        }
        
        self.presence_data[account_id] = presence_info
        
        # Broadcast presence update to friends/party members
        self.broadcast_presence_update(account_id, presence_info)
    
    def broadcast_presence_update(self, account_id: str, presence_info: Dict[str, Any]):
        """Broadcast presence update to relevant clients"""
        # In a real implementation, you'd check friend lists
        # For emulator, broadcast to all connected clients
        self.socketio.emit('presence_update', presence_info, broadcast=True)
    
    def get_presence(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get presence data for an account"""
        return self.presence_data.get(account_id)
    
    def send_party_invitation(self, from_account: str, to_account: str, party_id: str):
        """Send party invitation"""
        invitation = {
            'type': 'party_invitation',
            'from': from_account,
            'to': to_account,
            'party_id': party_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'expires_at': (datetime.utcnow() + timedelta(minutes=5)).isoformat() + 'Z'
        }
        
        # Find target client and send invitation
        for client_id, client_info in self.connected_clients.items():
            if client_info['account_id'] == to_account:
                self.socketio.emit('party_invitation', invitation, room=client_id)
                break
    
    def run(self, host='127.0.0.1', port=8081, debug=False):
        """Run the WebSocket server"""
        self.socketio.run(host=host, port=port, debug=debug)