#!/usr/bin/env python3
"""
SSL Bypass Utilities for Fortnite Season 7 Emulator
Provides comprehensive SSL certificate verification bypass methods
"""

import ssl
import os
import sys
from pathlib import Path
from typing import Tuple, List

def apply_ssl_bypass() -> bool:
    """
    Apply comprehensive SSL bypass methods for the emulator
    
    Returns:
        bool: True if bypass was successful, False otherwise
    """
    try:
        print("Applying SSL bypass methods...")
        
        # Method 1: Disable SSL verification in Python
        ssl._create_default_https_context = ssl._create_unverified_context
        
        # Method 2: Set environment variables to disable SSL verification
        ssl_env_vars = {
            'PYTHONHTTPSVERIFY': '0',
            'CURL_CA_BUNDLE': '',
            'SSL_VERIFY': '0',
            'NODE_TLS_REJECT_UNAUTHORIZED': '0',
            'REQUESTS_CA_BUNDLE': '',
            'SSL_CERT_FILE': '',
            'SSL_CERT_DIR': '',
            'OPENSSL_CONF': '',
            'LIBCURL_SSL_VERIFY': '0',
            'CURLOPT_SSL_VERIFYPEER': '0',
            'CURLOPT_SSL_VERIFYHOST': '0'
        }
        
        for var, value in ssl_env_vars.items():
            os.environ[var] = value
        
        # Method 3: Monkey patch requests library
        try:
            import requests
            from requests.adapters import HTTPAdapter
            from urllib3.util.ssl_ import create_urllib3_context
            
            class SSLAdapter(HTTPAdapter):
                def init_poolmanager(self, *args, **kwargs):
                    context = create_urllib3_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    kwargs['ssl_context'] = context
                    return super().init_poolmanager(*args, **kwargs)
            
            # Apply the adapter globally
            session = requests.Session()
            session.mount('https://', SSLAdapter())
            session.mount('http://', SSLAdapter())
            
            # Monkey patch the default session
            requests.sessions.Session = lambda: session
            
        except ImportError:
            print("Requests library not available for SSL bypass")
        
        # Method 4: Disable SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        print("✓ SSL bypass methods applied successfully")
        return True
        
    except Exception as e:
        print(f"✗ Failed to apply SSL bypass: {e}")
        return False

def create_unverified_ssl_context() -> ssl.SSLContext:
    """
    Create an unverified SSL context for maximum compatibility
    
    Returns:
        ssl.SSLContext: Unverified SSL context
    """
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # Additional settings for maximum compatibility (with error handling)
        try:
            context.options |= ssl.OP_ALLOW_UNSAFE_LEGACY_RENEGOTIATION
        except AttributeError:
            pass  # Not available in this Python version
        
        try:
            context.options |= ssl.OP_DONT_INSERT_EMPTY_FRAGMENTS
        except AttributeError:
            pass  # Not available in this Python version
        
        try:
            context.options |= ssl.OP_LEGACY_SERVER_CONNECT
        except AttributeError:
            pass  # Not available in this Python version
        
        return context
        
    except Exception as e:
        print(f"Error creating unverified SSL context: {e}")
        return ssl.create_default_context()

def disable_ssl_verification():
    """Disable SSL verification globally"""
    try:
        # Disable SSL verification in Python
        ssl._create_default_https_context = ssl._create_unverified_context
        
        # Disable urllib3 warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        print("✓ SSL verification disabled globally")
        
    except Exception as e:
        print(f"✗ Failed to disable SSL verification: {e}")

def restore_ssl_verification():
    """Restore SSL verification to default state"""
    try:
        # Restore default SSL context
        ssl._create_default_https_context = ssl.create_default_context
        
        print("✓ SSL verification restored to default")
        
    except Exception as e:
        print(f"✗ Failed to restore SSL verification: {e}")

def get_ssl_bypass_status() -> dict:
    """
    Get current SSL bypass status
    
    Returns:
        dict: Status information
    """
    try:
        status = {
            'ssl_verification_disabled': ssl._create_default_https_context == ssl._create_unverified_context,
            'environment_vars_set': {},
            'warnings_disabled': False
        }
        
        # Check environment variables
        ssl_vars = ['PYTHONHTTPSVERIFY', 'CURL_CA_BUNDLE', 'SSL_VERIFY', 'NODE_TLS_REJECT_UNAUTHORIZED']
        for var in ssl_vars:
            status['environment_vars_set'][var] = var in os.environ
        
        # Check urllib3 warnings
        try:
            import urllib3
            status['warnings_disabled'] = not urllib3.exceptions.InsecureRequestWarning.__module__
        except:
            pass
        
        return status
        
    except Exception as e:
        return {'error': str(e)}

if __name__ == "__main__":
    print("Testing SSL bypass methods...")
    
    success = apply_ssl_bypass()
    if success:
        print("SSL bypass test successful!")
        status = get_ssl_bypass_status()
        print(f"Status: {status}")
    else:
        print("SSL bypass test failed!")
    
    input("Press Enter to exit...")

