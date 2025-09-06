#!/usr/bin/env python3
"""
Configuration Manager for Fortnite Season 7 Emulator
Handles loading and managing configuration settings
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any

class ConfigManager:
    def __init__(self, config_file: str = None):
        if config_file is None:
            self.config_file = Path(__file__).parent.parent / "config.yaml"
        else:
            self.config_file = Path(config_file)
        
        self._config = None
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            if not self.config_file.exists():
                raise FileNotFoundError(f"Config file not found: {self.config_file}")
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
            
            # Validate required sections
            self._validate_config()
            
            return self._config
            
        except Exception as e:
            print(f"Error loading config: {e}")
            # Return default config
            return self._get_default_config()
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        if self._config is None:
            self.load_config()
        return self._config
    
    def get(self, key: str, default=None):
        """Get configuration value by key (supports dot notation)"""
        config = self.get_config()
        keys = key.split('.')
        
        current = config
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        
        return current
    
    def set(self, key: str, value: Any):
        """Set configuration value by key (supports dot notation)"""
        config = self.get_config()
        keys = key.split('.')
        
        current = config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
        self._config = config
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def _validate_config(self):
        """Validate configuration structure"""
        required_sections = ['server', 'fortnite', 'launch_args', 'endpoints']
        
        for section in required_sections:
            if section not in self._config:
                raise ValueError(f"Missing required config section: {section}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'server': {
                'host': '127.0.0.1',
                'port': 8080,
                'ssl_port': 8443,
                'debug': True
            },
            'fortnite': {
                'version': '7.40',
                'season': 7,
                'build_id': '4834769'
            },
            'launch_args': [
                '-AUTH_LOGIN=unused',
                '-AUTH_PASSWORD=unused',
                '-AUTH_TYPE=epic',
                '-epicapp=Fortnite',
                '-epicenv=Prod',
                '-epiclocale=en-us',
                '-epicportal',
                '-skippatchcheck',
                '-nobe',
                '-fromfl=eac',
                '-fltoken=none'
            ],
            'endpoints': {
                'oauth_token': '/account/api/oauth/token',
                'oauth_verify': '/account/api/oauth/verify',
                'fortnite_api': '/fortnite/api/game/v2/profile/{accountId}/client/{command}',
                'matchmaking': '/fortnite/api/matchmaking/session/findPlayer/{playerId}',
                'content_pages': '/content/api/pages/fortnite-game',
                'timeline': '/fortnite/api/calendar/v1/timeline'
            },
            'ssl': {
                'cert_file': 'certs/server.crt',
                'key_file': 'certs/server.key'
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/emulator.log',
                'max_size': '10MB',
                'backup_count': 5
            }
        }
    
    def get_server_url(self, use_ssl: bool = True) -> str:
        """Get server URL"""
        config = self.get_config()
        host = config['server']['host']
        
        if use_ssl:
            port = config['server']['ssl_port']
            return f"https://{host}:{port}"
        else:
            port = config['server']['port']
            return f"http://{host}:{port}"
    
    def get_launch_args(self) -> list:
        """Get Fortnite launch arguments"""
        return self.get('launch_args', [])
    
    def get_endpoint_url(self, endpoint_name: str, **kwargs) -> str:
        """Get full endpoint URL with formatting"""
        endpoint_path = self.get(f'endpoints.{endpoint_name}')
        if endpoint_path:
            # Format with provided kwargs
            formatted_path = endpoint_path.format(**kwargs)
            return self.get_server_url() + formatted_path
        return None