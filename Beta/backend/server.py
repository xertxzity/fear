#!/usr/bin/env python3
"""
Fortnite Season 7 Emulator Backend Server
Handles all Fortnite API requests and provides authentication bypass
"""

from flask import Flask, request, jsonify, Response
import json
import ssl
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.config_manager import ConfigManager
from utils.logger import setup_logger
from backend.auth_handler import AuthHandler
from backend.game_handler import GameHandler
from backend.content_handler import ContentHandler
from backend.websocket_handler import WebSocketHandler
from backend.party_service import PartyService
from backend.presence_service import PresenceService
from backend.friends_service import FriendsService
from backend.mcp_service import MCPService
from backend.season7_matchmaking import Season7MatchmakingService

class FortniteBackendServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.config_manager = ConfigManager()
        self.logger = setup_logger("backend")
        
        # Initialize handlers
        self.auth_handler = AuthHandler()
        self.game_handler = GameHandler()
        self.content_handler = ContentHandler()
        self.websocket_handler = WebSocketHandler(self.app)
        self.party_service = PartyService(self.websocket_handler)
        self.presence_service = PresenceService(self.websocket_handler)
        self.friends_service = FriendsService(self.websocket_handler, self.presence_service)
        self.mcp_service = MCPService()
        self.matchmaking_service = Season7MatchmakingService()
        
        # Setup routes
        self.setup_routes()
        
        # Server state
        self.start_time = datetime.now()
        
    def setup_routes(self):
        """Setup all API routes"""
        
        # Health check
        @self.app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({
                'status': 'ok',
                'server': 'Fortnite Season 7 Emulator',
                'version': '1.0.0',
                'uptime': str(datetime.now() - self.start_time)
            })
        
        # CORS preflight
        @self.app.before_request
        def handle_preflight():
            if request.method == "OPTIONS":
                response = Response()
                response.headers.add("Access-Control-Allow-Origin", "*")
                response.headers.add('Access-Control-Allow-Headers', "*")
                response.headers.add('Access-Control-Allow-Methods', "*")
                return response
        
        @self.app.after_request
        def after_request(response):
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
            return response
        
        # Authentication endpoints
        @self.app.route('/account/api/oauth/token', methods=['POST'])
        def oauth_token():
            return self.auth_handler.handle_oauth_token(request)
        
        @self.app.route('/account/api/oauth/verify', methods=['GET'])
        def oauth_verify():
            return self.auth_handler.handle_oauth_verify(request)
        
        @self.app.route('/account/api/public/account/<account_id>', methods=['GET'])
        def get_account(account_id):
            return self.auth_handler.handle_get_account(account_id)
        
        @self.app.route('/account/api/public/account', methods=['GET'])
        def get_accounts():
            return self.auth_handler.handle_get_accounts(request)
        
        @self.app.route('/account/api/public/account/<account_id>/externalAuths', methods=['GET'])
        def get_external_auths(account_id):
            return jsonify([])
        
        @self.app.route('/account/api/epicdomains/ssodomains', methods=['GET'])
        def get_sso_domains():
            return jsonify([])
        
        # MCP (Mission Control Protocol) endpoints - Season 7.40 verified patterns
        @self.app.route('/fortnite/api/game/v2/profile/<account_id>/client/<operation>', methods=['POST'])
        def mcp_operation(account_id, operation):
            profile_id = request.args.get('profileId', 'athena')
            rvn = int(request.args.get('rvn', -1))
            
            # Use MCP service for known operations, fall back to game handler
            if operation in self.mcp_service.valid_operations:
                result = self.mcp_service.handle_mcp_operation(account_id, operation, profile_id, rvn)
                if isinstance(result, tuple):
                    return jsonify(result[0]), result[1]
                return jsonify(result)
            else:
                return self.game_handler.handle_profile_command(account_id, operation, request)
        
        @self.app.route('/fortnite/api/game/v2/profile/<account_id>/public/QueryProfile', methods=['POST'])
        def query_profile_public(account_id):
            profile_id = request.args.get('profileId', 'athena')
            rvn = int(request.args.get('rvn', -1))
            
            result = self.mcp_service.handle_query_profile(account_id, profile_id, rvn)
            if isinstance(result, tuple):
                return jsonify(result[0]), result[1]
            return jsonify(result)
        
        # Direct profile endpoint (GET request)
        @self.app.route('/fortnite/api/game/v2/profile/<account_id>/<profile_id>', methods=['GET'])
        def get_profile_direct(account_id, profile_id):
            rvn = int(request.args.get('rvn', -1))
            result = self.mcp_service.handle_query_profile(account_id, profile_id, rvn)
            if isinstance(result, tuple):
                return jsonify(result[0]), result[1]
            return jsonify(result)
        
        # Season 7.40 Matchmaking endpoints
        @self.app.route('/fortnite/api/matchmaking/session/findPlayer/<player_id>', methods=['GET'])
        def find_player(player_id):
            result = self.matchmaking_service.find_player(player_id)
            return jsonify(result)
        
        @self.app.route('/fortnite/api/matchmaking/session/matchMakingRequest', methods=['POST'])
        def matchmaking_request():
            data = request.get_json() or {}
            result = self.matchmaking_service.handle_matchmaking_request(data)
            if isinstance(result, tuple):
                return jsonify(result[0]), result[1]
            return jsonify(result)
        
        @self.app.route('/fortnite/api/game/v2/matchmakingservice/ticket/player/<account_id>', methods=['POST'])
        def create_matchmaking_ticket(account_id):
            data = request.get_json() or {}
            playlist_id = data.get('playlistId', 'playlist_defaultsolo')
            region = data.get('region', 'NAE')
            party_player_ids = data.get('partyPlayerIds', [account_id])
            
            result = self.matchmaking_service.create_matchmaking_ticket(account_id, playlist_id, region, party_player_ids)
            if isinstance(result, tuple):
                return jsonify(result[0]), result[1]
            return jsonify(result)
        
        @self.app.route('/fortnite/api/game/v2/matchmakingservice/ticket/player/<account_id>/<ticket_id>', methods=['GET'])
        def get_matchmaking_ticket(account_id, ticket_id):
            result = self.matchmaking_service.get_matchmaking_ticket(ticket_id)
            if isinstance(result, tuple):
                return jsonify(result[0]), result[1]
            return jsonify(result)
        
        @self.app.route('/fortnite/api/game/v2/matchmakingservice/ticket/player/<account_id>/<ticket_id>', methods=['DELETE'])
        def cancel_matchmaking_ticket(account_id, ticket_id):
            result = self.matchmaking_service.cancel_matchmaking_ticket(ticket_id)
            if isinstance(result, tuple):
                return jsonify(result[0]), result[1]
            return jsonify(result)
        
        @self.app.route('/fortnite/api/game/v2/enabled_features', methods=['GET'])
        def enabled_features():
            return jsonify([])
        
        # Lightswitch endpoint
        @self.app.route('/fortnite/api/lightswitch', methods=['GET'])
        def lightswitch():
            return jsonify({
                'serviceInstanceId': 'fortnite',
                'status': 'UP',
                'message': 'Service is up',
                'maintenanceUri': None,
                'overrideCatalogIds': [],
                'allowedActions': [],
                'banned': False,
                'launcherInfoDTO': {
                    'appName': 'Fortnite',
                    'catalogItemId': '4fe75bbc5a674f4f9b356b5c90567da5',
                    'namespace': 'fn'
                }
            })
        
        @self.app.route('/fortnite/api/game/v2/world/info', methods=['GET'])
        def world_info():
            return jsonify({
                'theaters': [{
                    'uniqueId': 'theater_campaign',
                    'displayName': 'Save the World',
                    'description': 'Save the World Campaign',
                    'requiredEventFlag': '',
                    'visibility': 'Public',
                    'blueprintType': 'Theater',
                    'environmentName': 'Campaign'
                }]
            })
        
        @self.app.route('/fortnite/api/game/v2/br-inventory/account/<account_id>', methods=['GET'])
        def br_inventory(account_id):
            return jsonify({
                'stash': {
                    'globalcash': 0
                }
            })
        
        # Content endpoints
        @self.app.route('/content/api/pages/fortnite-game', methods=['GET'])
        def content_pages():
            return self.content_handler.handle_content_pages()
        
        @self.app.route('/fortnite/api/calendar/v1/timeline', methods=['GET'])
        def timeline():
            return self.content_handler.handle_timeline()
        
        @self.app.route('/fortnite/api/storefront/v2/catalog', methods=['GET'])
        def catalog():
            return self.content_handler.handle_catalog()
        
        # Version and build info
        @self.app.route('/fortnite/api/version', methods=['GET'])
        def version_info():
            config = self.config_manager.get_config()
            return jsonify({
                'app': 'fortnite',
                'serverDate': datetime.utcnow().isoformat() + 'Z',
                'overridePropertiesVersion': 'unknown',
                'cln': config['fortnite']['build_id'],
                'build': config['fortnite']['version'],
                'moduleName': 'Fortnite-Core',
                'buildDate': '2019-02-14T17:36:10.335Z',
                'version': config['fortnite']['version'],
                'branch': 'Release-7.40',
                'modules': {
                    'Epic Games Launcher': '1.1.156-4834769+++Fortnite+Release-7.40',
                    'Fortnite-Core': '1.1.156-4834769+++Fortnite+Release-7.40'
                }
            })
        
        # Version check endpoint
        @self.app.route('/fortnite/api/v2/versioncheck/<platform>', methods=['GET'])
        def version_check(platform):
            return jsonify({
                'type': 'NO_UPDATE'
            })
        
        # Additional version check endpoint (without platform parameter)
        @self.app.route('/fortnite/api/versioncheck', methods=['GET'])
        def version_check_simple():
            return jsonify({
                'type': 'NO_UPDATE'
            })
        
        # Cloud storage endpoints
        @self.app.route('/fortnite/api/cloudstorage/system', methods=['GET'])
        def cloud_storage_system():
            return jsonify([])
        
        @self.app.route('/fortnite/api/cloudstorage/user/<account_id>', methods=['GET'])
        def cloud_storage_user(account_id):
            return jsonify([])
        
        # EULA tracking endpoint
        @self.app.route('/eulatracking/api/shared/agreements/fn', methods=['GET'])
        def get_eula_agreements():
            return jsonify([])
        
        # Data router endpoint (for analytics)
        @self.app.route('/datarouter/api/v1/public/data', methods=['POST'])
        def data_router():
            """Handle data routing for analytics and telemetry"""
            try:
                # Log the incoming data for debugging
                data = request.get_json() or request.form or {}
                print(f"Data Router Request: {data}")
                
                # Simulate successful data submission
                return '', 204  # No content response
            except Exception as e:
                print(f"Error in data router: {e}")
                return '', 204  # Still return no content to prevent retries

        # Additional data routing endpoint
        @self.app.route('/datarouter/api/v1/public/data', methods=['GET'])
        def data_router_get():
            """Handle GET requests for data routing"""
            return '', 204  # No content response

        # OAuth token endpoint with more robust handling
        @self.app.route('/account/api/oauth/token', methods=['POST'])
        def epic_oauth_token():
            """Epic OAuth token endpoint with enhanced logging"""
            try:
                data = request.get_json() or request.form or {}
                grant_type = data.get('grant_type', '')
                client_id = data.get('client_id', '')
                
                print(f"OAuth Token Request: grant_type={grant_type}, client_id={client_id}")
                
                # Simulate successful token generation for various grant types
                if grant_type == 'client_credentials':
                    return jsonify({
                        'access_token': 'emulator_client_token_12345',
                        'token_type': 'bearer',
                        'expires_in': 3600,
                        'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat() + 'Z'
                    })
                
                elif grant_type == 'password':
                    return jsonify({
                        'access_token': 'emulator_access_token_12345',
                        'token_type': 'bearer',
                        'expires_in': 3600,
                        'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat() + 'Z',
                        'refresh_token': 'emulator_refresh_token_12345',
                        'account_id': 'f0a1b2c3d4e5f6789abcdef012345678'
                    })
                
                else:
                    # Fallback for unknown grant types
                    return jsonify({
                        'access_token': 'emulator_fallback_token_12345',
                        'token_type': 'bearer',
                        'expires_in': 3600,
                        'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat() + 'Z'
                    })
            
            except Exception as e:
                print(f"Error in OAuth token endpoint: {e}")
                return jsonify({
                    'errorCode': 'errors.com.epicgames.common.server_error',
                    'errorMessage': 'Internal server error during authentication',
                    'numericErrorCode': 1000
                }), 500
        
        # Epic Account Service main endpoint (for direct /account requests)
        @self.app.route('/account', methods=['POST'])
        def epic_account_service():
            """Epic Account Service main endpoint"""
            data = request.get_json() or {}
            return jsonify({
                "access_token": "emulator_access_token_12345",
                "token_type": "bearer",
                "expires_in": 3600,
                "expires_at": "2025-12-31T23:59:59.000Z",
                "refresh_token": "emulator_refresh_token_12345",
                "account_id": "f0a1b2c3d4e5f6789abcdef012345678",
                "client_id": "fortnite",
                "internal_client": True,
                "client_service": "fortnite"
            })
        
        # Friends endpoints (basic)
        @self.app.route('/friends/api/public/friends/<account_id>', methods=['GET'])
        def get_friends(account_id):
            return jsonify([])
        
        @self.app.route('/friends/api/public/blocklist/<account_id>', methods=['GET'])
        def get_blocklist(account_id):
            return jsonify([])
        
        @self.app.route('/friends/api/public/list/fortnite/<account_id>/recentPlayers', methods=['GET'])
        def get_recent_players(account_id):
            return jsonify([])
        
        # Stats endpoints
        @self.app.route('/statsproxy/api/statsv2/account/<account_id>', methods=['GET'])
        def get_stats(account_id):
            return jsonify({})
        
        # Creative Mode endpoints
        @self.app.route('/fortnite/api/game/v2/creative/island/create', methods=['POST'])
        def create_island():
            account_id = self.auth_handler.get_account_from_token(request)
            return self.game_handler.handle_create_island(account_id, request)
        
        @self.app.route('/fortnite/api/game/v2/creative/island/<island_code>/publish', methods=['POST'])
        def publish_island(island_code):
            return self.game_handler.handle_publish_island(island_code, request)
        
        @self.app.route('/fortnite/api/game/v2/creative/discovery/islands', methods=['GET'])
        def discover_islands():
            return self.game_handler.handle_discover_islands(request)
        
        # Battle Pass endpoints
        @self.app.route('/fortnite/api/game/v2/profile/<account_id>/battlepass', methods=['GET'])
        def battle_pass_info(account_id):
            return self.game_handler.handle_battle_pass_info(account_id)
        
        @self.app.route('/fortnite/api/game/v2/profile/<account_id>/challenge/<challenge_id>/complete', methods=['POST'])
        def complete_challenge(account_id, challenge_id):
            return self.game_handler.handle_complete_challenge(account_id, challenge_id)
        
        # Party Service endpoints (Season 7.40 compatible)
        @self.app.route('/party/api/v1/Fortnite/parties', methods=['POST'])
        def create_party_v1():
            account_id = self.auth_handler.get_account_from_token(request)
            party_config = request.get_json() or {}
            result = self.party_service.create_party(account_id, party_config)
            if isinstance(result, tuple):
                return jsonify(result[0]), result[1]
            return jsonify(result)
        
        @self.app.route('/party/api/v1/Fortnite/parties/<party_id>', methods=['GET'])
        def get_party_v1(party_id):
            result = self.party_service.get_party(party_id)
            if isinstance(result, tuple):
                return jsonify(result[0]), result[1]
            return jsonify(result)
        
        @self.app.route('/party/api/v1/Fortnite/parties/<party_id>/members/<account_id>/join', methods=['POST'])
        def join_party_v1(party_id, account_id):
            connection_data = request.get_json() or {}
            result = self.party_service.join_party(party_id, account_id, connection_data)
            if isinstance(result, tuple):
                return jsonify(result[0]), result[1]
            return jsonify(result)
        
        @self.app.route('/party/api/v1/Fortnite/parties/<party_id>/members/<account_id>', methods=['DELETE'])
        def leave_party_v1(party_id, account_id):
            result = self.party_service.leave_party(party_id, account_id)
            if isinstance(result, tuple):
                return jsonify(result[0]), result[1]
            return jsonify(result)
        
        @self.app.route('/party/api/v1/Fortnite/user/<account_id>', methods=['GET'])
        def get_user_party(account_id):
            result = self.party_service.get_user_party(account_id)
            if isinstance(result, tuple):
                return jsonify(result[0]), result[1]
            return jsonify(result)
        
        @self.app.route('/party/api/v1/Fortnite/parties/<party_id>/invites', methods=['POST'])
        def send_party_invitation(party_id):
            from_account_id = self.auth_handler.get_account_from_token(request)
            data = request.get_json() or {}
            to_account_id = data.get('to_account_id')
            
            if not to_account_id:
                return jsonify({'error': 'Missing to_account_id'}), 400
            
            result = self.party_service.send_invitation(party_id, from_account_id, to_account_id)
            if isinstance(result, tuple):
                return jsonify(result[0]), result[1]
            return jsonify(result)
        
        @self.app.route('/party/api/v1/Fortnite/user/<account_id>/invites/<invitation_id>', methods=['POST'])
        def respond_to_invitation(account_id, invitation_id):
            data = request.get_json() or {}
            response = data.get('response', 'DECLINE')
            
            result = self.party_service.respond_to_invitation(invitation_id, account_id, response)
            if isinstance(result, tuple):
                return jsonify(result[0]), result[1]
            return jsonify(result)
        
        @self.app.route('/party/api/v1/Fortnite/user/<account_id>/invites', methods=['GET'])
        def get_user_invitations(account_id):
            invitations = self.party_service.get_user_invitations(account_id)
            return jsonify(invitations)
        
        @self.app.route('/party/api/v1/Fortnite/parties/<party_id>/members/<account_id>/meta', methods=['PATCH'])
        def update_party_member_meta(party_id, account_id):
            data = request.get_json() or {}
            
            # Handle ready state updates
            if 'Default:PartyMemberReady_j' in data:
                ready = data['Default:PartyMemberReady_j']
                result = self.party_service.update_member_ready_state(party_id, account_id, ready)
                if isinstance(result, tuple):
                    return jsonify(result[0]), result[1]
                return jsonify(result)
            
            return jsonify({'status': 'OK'})
        
        # Legacy party endpoints for backward compatibility
        @self.app.route('/fortnite/api/game/v2/party/create', methods=['POST'])
        def create_party_legacy():
            account_id = self.auth_handler.get_account_from_token(request)
            party_config = request.get_json() or {}
            result = self.party_service.create_party(account_id, party_config)
            if isinstance(result, tuple):
                return jsonify(result[0]), result[1]
            return jsonify(result)
        
        @self.app.route('/fortnite/api/game/v2/party/<party_id>/join', methods=['POST'])
        def join_party_legacy(party_id):
            account_id = self.auth_handler.get_account_from_token(request)
            result = self.party_service.join_party(party_id, account_id)
            if isinstance(result, tuple):
                return jsonify(result[0]), result[1]
            return jsonify(result)
        
        # Presence Service endpoints (Season 7.40 compatible)
        @self.app.route('/presence/api/v1/_/<account_id>/presence', methods=['PUT'])
        def set_presence(account_id):
            presence_data = request.get_json() or {}
            result = self.presence_service.set_presence(account_id, presence_data)
            if isinstance(result, tuple):
                return jsonify(result[0]), result[1]
            return jsonify(result)
        
        @self.app.route('/presence/api/v1/_/<account_id>/presence', methods=['GET'])
        def get_presence(account_id):
            result = self.presence_service.get_presence(account_id)
            if isinstance(result, tuple):
                return jsonify(result[0]), result[1]
            return jsonify(result)
        
        @self.app.route('/presence/api/v1/_/<account_id>/presence/bulk', methods=['POST'])
        def get_bulk_presence(account_id):
            data = request.get_json() or {}
            account_ids = data.get('account_ids', [])
            presences = self.presence_service.get_multiple_presence(account_ids)
            return jsonify(presences)
        
        @self.app.route('/presence/api/v1/_/<account_id>/subscriptions', methods=['POST'])
        def subscribe_to_presence(account_id):
            data = request.get_json() or {}
            target_ids = data.get('account_ids', [])
            result = self.presence_service.subscribe_to_presence(account_id, target_ids)
            if isinstance(result, tuple):
                return jsonify(result[0]), result[1]
            return jsonify(result)
        
        @self.app.route('/presence/api/v1/_/<account_id>/subscriptions', methods=['DELETE'])
        def unsubscribe_from_presence(account_id):
            data = request.get_json() or {}
            target_ids = data.get('account_ids')
            result = self.presence_service.unsubscribe_from_presence(account_id, target_ids)
            if isinstance(result, tuple):
                return jsonify(result[0]), result[1]
            return jsonify(result)
        
        @self.app.route('/presence/api/v1/_/<account_id>/activity', methods=['PUT'])
        def update_activity(account_id):
            data = request.get_json() or {}
            activity = data.get('activity', 'lobby')
            properties = data.get('properties', {})
            result = self.presence_service.update_activity(account_id, activity, properties)
            if isinstance(result, tuple):
                return jsonify(result[0]), result[1]
            return jsonify(result)
        
        @self.app.route('/presence/api/v1/summary', methods=['GET'])
        def presence_summary():
            summary = self.presence_service.get_presence_summary()
            return jsonify(summary)
        
        # Competitive endpoints
        @self.app.route('/fortnite/api/game/v2/arena/<account_id>', methods=['GET'])
        def arena_info(account_id):
            return self.game_handler.handle_arena_info(account_id)
        
        @self.app.route('/fortnite/api/game/v2/tournaments', methods=['GET'])
        def tournament_list():
            return self.game_handler.handle_tournament_list()
        
        # Store and Economy endpoints
        @self.app.route('/fortnite/api/storefront/v2/catalog/br', methods=['GET'])
        def item_shop():
            return self.content_handler.handle_item_shop()
        
        @self.app.route('/fortnite/api/game/v2/profile/<account_id>/purchase', methods=['POST'])
        def purchase_item(account_id):
            return self.content_handler.handle_purchase_item(account_id, request)
        
        @self.app.route('/fortnite/api/game/v2/profile/<account_id>/gift', methods=['POST'])
        def gift_item(account_id):
            return self.content_handler.handle_gift_item(account_id, request)
        
        @self.app.route('/fortnite/api/game/v2/profile/<account_id>/vbucks', methods=['GET'])
        def vbucks_balance(account_id):
            return self.content_handler.handle_vbucks_balance(account_id)
        
        # Platform Integration endpoints
        @self.app.route('/fortnite/api/game/v2/profile/<account_id>/platform/sync', methods=['POST'])
        def cross_platform_sync(account_id):
            return self.content_handler.handle_cross_platform_sync(account_id, request)
        
        @self.app.route('/fortnite/api/game/v2/profile/<account_id>/achievements', methods=['GET'])
        def achievements(account_id):
            return self.content_handler.handle_achievements(account_id)
        
        # Error handler
        @self.app.errorhandler(404)
        def not_found(error):
            self.logger.warning(f"404 - Endpoint not found: {request.method} {request.path}")
            return jsonify({
                'errorCode': 'errors.com.epicgames.common.not_found',
                'errorMessage': f'Sorry the resource you were trying to find could not be found',
                'messageVars': [],
                'numericErrorCode': 1004,
                'originatingService': 'fortnite',
                'intent': 'prod'
            }), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            self.logger.error(f"500 - Internal server error: {error}")
            return jsonify({
                'errorCode': 'errors.com.epicgames.common.server_error',
                'errorMessage': 'Internal server error',
                'messageVars': [],
                'numericErrorCode': 1000,
                'originatingService': 'fortnite',
                'intent': 'prod'
            }), 500
    
    def create_ssl_context(self):
        """Create SSL context for HTTPS"""
        try:
            config = self.config_manager.get_config()
            cert_file = Path(__file__).parent.parent / config['ssl']['cert_file']
            key_file = Path(__file__).parent.parent / config['ssl']['key_file']
            
            # Check if certificates exist
            if not cert_file.exists() or not key_file.exists():
                self.logger.warning("SSL certificates not found, generating self-signed certificates...")
                self.generate_ssl_certificates(cert_file, key_file)
            
            # Create extremely permissive SSL context for emulator
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(str(cert_file), str(key_file))
            
            # Disable ALL certificate verification and security checks
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            context.verify_flags = ssl.VERIFY_DEFAULT
            
            # Additional SSL context modifications for maximum compatibility
            try:
                context.set_default_verify_paths()
            except:
                pass
            
            # Allow all cipher suites and protocols (with compatibility check)
            try:
                context.set_ciphers('ALL:COMPLEMENTOFALL:+ADH:+AECDH:+aNULL:+eNULL:+LOW:+MEDIUM:+HIGH:+3DES:+DES:+RC4:+MD5:+EXP:@SECLEVEL=0')
            except Exception:
                # Fallback to basic cipher suite if the above fails
                try:
                    context.set_ciphers('ALL:!aNULL:!eNULL')
                except Exception:
                    pass  # Use default ciphers
            
            # Set minimum and maximum protocol versions to be as permissive as possible
            try:
                context.minimum_version = ssl.TLSVersion.SSLv3
                context.maximum_version = ssl.TLSVersion.TLSv1_3
            except:
                pass  # Ignore if not supported
            
            # Disable all security options (with compatibility checks)
            try:
                context.options |= ssl.OP_DONT_INSERT_EMPTY_FRAGMENTS
            except AttributeError:
                pass  # Not available in this Python version
            
            # Set additional options for maximum compatibility
            try:
                context.options |= ssl.OP_NO_COMPRESSION
                context.options |= ssl.OP_CIPHER_SERVER_PREFERENCE
                # Additional permissive options
                context.options |= ssl.OP_NO_SSLv2
                context.options |= ssl.OP_NO_SSLv3
                context.options |= ssl.OP_SINGLE_DH_USE
                context.options |= ssl.OP_SINGLE_ECDH_USE
            except:
                pass
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error creating SSL context: {e}")
            return None
    
    def generate_ssl_certificates(self, cert_file: Path, key_file: Path):
        """Generate self-signed SSL certificates"""
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            import ipaddress
            
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            
            # Create certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Fortnite Emulator"),
                x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=365)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName("localhost"),
                    x509.DNSName("127.0.0.1"),
                    x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            # Add Epic Games domains for compatibility
            x509.DNSName("account-public-service-prod.ol.epicgames.com"),
            x509.DNSName("account-public-service-prod.ak.epicgames.com"),
            x509.DNSName("account-public-service-prod03.ol.epicgames.com"),
            x509.DNSName("fortnite-public-service-prod11.ol.epicgames.com"),
            x509.DNSName("fortnite-public-service-prod.ak.epicgames.com"),
            x509.DNSName("datarouter.ol.epicgames.com"),
            x509.DNSName("datarouter-prod.ak.epicgames.com"),
            x509.DNSName("datarouter-public-service-prod06.ol.epicgames.com"),
            x509.DNSName("lightswitch-public-service-prod06.ol.epicgames.com"),
            x509.DNSName("friends-public-service-prod06.ol.epicgames.com"),
            x509.DNSName("party-service-prod.ol.epicgames.com"),
            x509.DNSName("entitlement-public-service-prod08.ol.epicgames.com"),
            x509.DNSName("eulatracking-public-service-prod06.ol.epicgames.com"),
            x509.DNSName("statsproxy-public-service-live.ol.epicgames.com"),
            x509.DNSName("content-api-prod.ak.epicgames.com"),
            x509.DNSName("*.ol.epicgames.com"),
            x509.DNSName("*.ak.epicgames.com"),
            x509.DNSName("*.epicgames.com"),
                ]),
                critical=False,
            ).sign(private_key, hashes.SHA256())
            
            # Ensure directory exists
            cert_file.parent.mkdir(exist_ok=True)
            
            # Write certificate
            with open(cert_file, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            # Write private key
            with open(key_file, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            self.logger.info("Generated self-signed SSL certificates")
            
        except Exception as e:
            self.logger.error(f"Error generating SSL certificates: {e}")
            raise
    
    def run(self):
        """Start the backend server"""
        config = self.config_manager.get_config()
        
        # Start HTTP server in thread
        http_thread = threading.Thread(
            target=self._run_http_server,
            args=(config['server']['host'], config['server']['port']),
            daemon=True
        )
        http_thread.start()
        
        # Start HTTPS server on port 8443 in thread
        https_thread = threading.Thread(
            target=self._run_https_server,
            args=(config['server']['host'], config['server']['ssl_port']),
            daemon=True
        )
        https_thread.start()

        # Start HTTPS server on standard port 443 in thread
        https_standard_thread = threading.Thread(
            target=self._run_https_server,
            args=(config['server']['host'], 443),
            daemon=True
        )
        https_standard_thread.start()
        
        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Shutting down server...")
    
    def _run_http_server(self, host: str, port: int):
        """Run HTTP server"""
        try:
            self.logger.info(f"Starting HTTP server on {host}:{port}")
            self.app.run(
                host=host,
                port=port,
                debug=False,
                use_reloader=False,
                threaded=True
            )
        except Exception as e:
            self.logger.error(f"HTTP server error: {e}")
    
    def _run_https_server(self, host: str, port: int):
        """Run HTTPS server"""
        try:
            ssl_context = self.create_ssl_context()
            if ssl_context:
                self.logger.info(f"Starting HTTPS server on {host}:{port}")
                self.app.run(
                    host=host,
                    port=port,
                    debug=False,
                    use_reloader=False,
                    threaded=True,
                    ssl_context=ssl_context
                )
            else:
                self.logger.error("Could not create SSL context, HTTPS server not started")
        except Exception as e:
            self.logger.error(f"HTTPS server error: {e}")

def start_server():
    """Start the Fortnite backend server"""
    server = FortniteBackendServer()
    server.run()

if __name__ == "__main__":
    start_server()