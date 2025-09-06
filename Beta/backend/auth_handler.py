#!/usr/bin/env python3
"""
Authentication Handler for Fortnite Season 7 Emulator
Handles OAuth tokens, account verification, and login bypass
"""

from flask import jsonify, request
import json
import base64
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Any

class AuthHandler:
    def __init__(self):
        # Store active tokens
        self.active_tokens = {}
        self.refresh_tokens = {}
        
        # Default account info
        self.default_account = {
            'id': 'f0a1b2c3d4e5f6789abcdef012345678',
            'displayName': 'FortnitePlayer',
            'name': 'FortnitePlayer',
            'email': 'player@fortnite.local',
            'failedLoginAttempts': 0,
            'lastLogin': datetime.utcnow().isoformat() + 'Z',
            'numberOfDisplayNameChanges': 0,
            'ageGroup': 'UNKNOWN',
            'headless': False,
            'country': 'US',
            'lastName': 'Player',
            'preferredLanguage': 'en',
            'canUpdateDisplayName': True,
            'tfaEnabled': False,
            'emailVerified': True,
            'minorVerified': False,
            'minorExpected': False,
            'minorStatus': 'UNKNOWN'
        }
    
    def generate_access_token(self, account_id: str = None) -> str:
        """Generate a new access token"""
        if account_id is None:
            account_id = self.default_account['id']
        
        # Create token payload
        payload = {
            'sub': account_id,
            'iss': 'https://account-public-service-prod03.ol.epicgames.com',
            'aud': 'fortnite',
            'exp': int((datetime.utcnow() + timedelta(hours=8)).timestamp()),
            'iat': int(datetime.utcnow().timestamp()),
            'jti': secrets.token_hex(16)
        }
        
        # Simple base64 encoding (not real JWT for simplicity)
        token_data = json.dumps(payload)
        token = base64.b64encode(token_data.encode()).decode()
        
        # Store token
        self.active_tokens[token] = {
            'account_id': account_id,
            'created': datetime.utcnow(),
            'expires': datetime.utcnow() + timedelta(hours=8)
        }
        
        return token
    
    def generate_refresh_token(self, account_id: str = None) -> str:
        """Generate a new refresh token"""
        if account_id is None:
            account_id = self.default_account['id']
        
        refresh_token = secrets.token_hex(32)
        
        self.refresh_tokens[refresh_token] = {
            'account_id': account_id,
            'created': datetime.utcnow(),
            'expires': datetime.utcnow() + timedelta(days=30)
        }
        
        return refresh_token
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate an access token"""
        if token in self.active_tokens:
            token_info = self.active_tokens[token]
            if datetime.utcnow() < token_info['expires']:
                return token_info
            else:
                # Token expired
                del self.active_tokens[token]
        
        return None
    
    def handle_oauth_token(self, request):
        """Handle OAuth token request with precise Season 7 emulation"""
        try:
            # Extract all possible request data sources
            data = request.get_json() or request.form or request.args or {}
            
            # Extract key authentication parameters
            grant_type = data.get('grant_type', '')
            client_id = data.get('client_id', '')
            client_secret = data.get('client_secret', '')
            
            # Specific Season 7 client configuration with detailed requirements
            season7_clients = {
                'ec684b8c687f479fadea3cb2ad83f5c6': {  # Fortnite client
                    'name': 'Fortnite Client',
                    'allowed_grant_types': ['password', 'client_credentials', 'refresh_token'],
                    'secret_required': False,
                    'required_scopes': [
                        'basic_profile', 
                        'friends_list', 
                        'presence', 
                        'openid', 
                        'offline_access'
                    ]
                },
                '34a02cf8f4414e29b15921876da36f9a': {  # Launcher client
                    'name': 'Launcher Client',
                    'allowed_grant_types': ['password', 'client_credentials'],
                    'secret_required': True,
                    'required_scopes': [
                        'basic_profile', 
                        'offline_access'
                    ]
                },
                '319e1527d0be4457a1067829fc0ad86e': {  # Android client
                    'name': 'Android Client',
                    'allowed_grant_types': ['password', 'client_credentials'],
                    'secret_required': False,
                    'required_scopes': [
                        'basic_profile', 
                        'friends_list', 
                        'presence'
                    ]
                }
            }
            
            # Detailed logging for debugging
            print(f"OAuth Token Request Details:")
            print(f"Grant Type: {grant_type}")
            print(f"Client ID: {client_id}")
            print(f"Client Secret Provided: {bool(client_secret)}")
            
            # Validate client ID
            if client_id not in season7_clients:
                print(f"Unauthorized client ID: {client_id}")
                return jsonify({
                    'errorCode': 'errors.com.epicgames.common.oauth.unauthorized_client',
                    'errorMessage': f'Client ID {client_id} is not authorized',
                    'numericErrorCode': 1015
                }), 400
            
            # Get client configuration
            client_config = season7_clients[client_id]
            
            # Validate grant type
            if grant_type not in client_config['allowed_grant_types']:
                print(f"Unauthorized grant type for client {client_id}: {grant_type}")
                return jsonify({
                    'errorCode': 'errors.com.epicgames.common.oauth.unauthorized_client',
                    'errorMessage': f'Grant type {grant_type} not allowed for client {client_id}',
                    'numericErrorCode': 1015
                }), 400
            
            # Check client secret if required
            if client_config['secret_required'] and not client_secret:
                return jsonify({
                    'errorCode': 'errors.com.epicgames.common.oauth.invalid_request',
                    'errorMessage': 'Client secret is required',
                    'numericErrorCode': 1016
                }), 400
            
            # Client credentials flow
            if grant_type == 'client_credentials':
                return jsonify({
                    'access_token': f'client_token_{client_id}',
                    'token_type': 'bearer',
                    'expires_in': 3600,
                    'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat() + 'Z',
                    'client_id': client_id,
                    'internal_client': True,
                    'client_service': 'fortnite',
                    'scope': client_config['required_scopes']
                })
            
            # Password flow (login bypass)
            if grant_type == 'password':
                # Extract additional login parameters
                username = data.get('username', 'FortnitePlayer')
                password = data.get('password', '')
                
                # Always use default account for Season 7 emulation
                account_id = self.default_account['id']
                access_token = self.generate_access_token(account_id)
                refresh_token = self.generate_refresh_token(account_id)
                
                return jsonify({
                    'access_token': access_token,
                    'token_type': 'bearer',
                    'expires_in': 28800,  # 8 hours
                    'expires_at': (datetime.utcnow() + timedelta(hours=8)).isoformat() + 'Z',
                    'refresh_token': refresh_token,
                    'refresh_expires': 1800,
                    'refresh_expires_at': (datetime.utcnow() + timedelta(minutes=30)).isoformat() + 'Z',
                    'account_id': account_id,
                    'client_id': client_id,
                    'internal_client': True,
                    'client_service': 'fortnite',
                    'displayName': username,
                    'app': 'fortnite',
                    'in_app_id': account_id,
                    'scope': client_config['required_scopes']
                })
            
            # Refresh token flow
            if grant_type == 'refresh_token':
                refresh_token = data.get('refresh_token')
                
                if refresh_token in self.refresh_tokens:
                    token_info = self.refresh_tokens[refresh_token]
                    if datetime.utcnow() < token_info['expires']:
                        # Generate new tokens
                        new_access_token = self.generate_access_token(token_info['account_id'])
                        new_refresh_token = self.generate_refresh_token(token_info['account_id'])
                        
                        # Remove old refresh token
                        del self.refresh_tokens[refresh_token]
                        
                        return jsonify({
                            'access_token': new_access_token,
                            'token_type': 'bearer',
                            'expires_in': 28800,
                            'expires_at': (datetime.utcnow() + timedelta(hours=8)).isoformat() + 'Z',
                            'refresh_token': new_refresh_token,
                            'refresh_expires': 1800,
                            'refresh_expires_at': (datetime.utcnow() + timedelta(minutes=30)).isoformat() + 'Z',
                            'account_id': token_info['account_id'],
                            'client_id': client_id,
                            'internal_client': True,
                            'client_service': 'fortnite',
                            'scope': client_config['required_scopes']
                        })
                
                return jsonify({
                    'errorCode': 'errors.com.epicgames.account.oauth.invalid_token',
                    'errorMessage': 'Invalid refresh token',
                    'numericErrorCode': 18036
                }), 400
            
            # Fallback for any unhandled grant types
            print(f"Unhandled grant type: {grant_type}")
            return jsonify({
                'errorCode': 'errors.com.epicgames.common.oauth.unauthorized_client',
                'errorMessage': 'Unsupported grant type',
                'numericErrorCode': 1015
            }), 400
        
        except Exception as e:
            print(f"Error in OAuth token handler: {e}")
            return jsonify({
                'errorCode': 'errors.com.epicgames.common.server_error',
                'errorMessage': 'Internal server error during authentication',
                'numericErrorCode': 1000
            }), 500
    
    def handle_oauth_verify(self, request) -> Dict[str, Any]:
        """Handle OAuth token verification"""
        try:
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return jsonify({
                    'errorCode': 'errors.com.epicgames.common.authorization.authorization_failed',
                    'errorMessage': 'Authorization failed',
                    'messageVars': [],
                    'numericErrorCode': 1032,
                    'originatingService': 'account',
                    'intent': 'prod'
                }), 401
            
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            token_info = self.validate_token(token)
            
            if token_info:
                return jsonify({
                    'token': token,
                    'session_id': secrets.token_hex(16),
                    'token_type': 'bearer',
                    'client_id': 'fortnite',
                    'internal_client': True,
                    'client_service': 'fortnite',
                    'account_id': token_info['account_id'],
                    'expires_in': int((token_info['expires'] - datetime.utcnow()).total_seconds()),
                    'expires_at': token_info['expires'].isoformat() + 'Z',
                    'auth_method': 'password',
                    'display_name': self.default_account['displayName'],
                    'app': 'fortnite',
                    'in_app_id': token_info['account_id']
                })
            else:
                return jsonify({
                    'errorCode': 'errors.com.epicgames.account.oauth.invalid_token',
                    'errorMessage': 'Invalid or expired access token',
                    'messageVars': [],
                    'numericErrorCode': 18036,
                    'originatingService': 'account',
                    'intent': 'prod'
                }), 401
        
        except Exception as e:
            return jsonify({
                'errorCode': 'errors.com.epicgames.common.server_error',
                'errorMessage': 'Internal server error during token verification',
                'messageVars': [],
                'numericErrorCode': 1000,
                'originatingService': 'account',
                'intent': 'prod'
            }), 500
    
    def handle_get_account(self, account_id: str) -> Dict[str, Any]:
        """Handle get account info request"""
        try:
            # Return default account info for any account ID
            account_info = self.default_account.copy()
            account_info['id'] = account_id
            
            return jsonify(account_info)
        
        except Exception as e:
            return jsonify({
                'errorCode': 'errors.com.epicgames.account.account_not_found',
                'errorMessage': f'Account not found for account id {account_id}',
                'messageVars': [account_id],
                'numericErrorCode': 18007,
                'originatingService': 'account',
                'intent': 'prod'
            }), 404
    
    def handle_get_accounts(self, request) -> Dict[str, Any]:
        """Handle get multiple accounts request"""
        try:
            # Get account IDs from query parameters
            account_ids = request.args.getlist('accountId')
            
            accounts = []
            for account_id in account_ids:
                account_info = self.default_account.copy()
                account_info['id'] = account_id
                accounts.append(account_info)
            
            return jsonify(accounts)
        
        except Exception as e:
            return jsonify({
                'errorCode': 'errors.com.epicgames.common.server_error',
                'errorMessage': 'Internal server error',
                'messageVars': [],
                'numericErrorCode': 1000,
                'originatingService': 'account',
                'intent': 'prod'
            }), 500
    
    def get_account_from_token(self, request) -> str:
        """Extract account ID from authorization token"""
        try:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
                token_info = self.validate_token(token)
                if token_info:
                    return token_info['account_id']
            
            return self.default_account['id']
        
        except Exception:
            return self.default_account['id']