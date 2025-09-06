#!/usr/bin/env python3
"""
Fortnite Season 7 Emulator - Main Entry Point
Starts the launcher GUI and backend services
"""

import sys
import os
import threading
import time
import socket
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logger
from utils.config_manager import ConfigManager
from utils.request_redirector import start_request_redirection
from utils.dll_injector import get_dll_injector, start_process_monitor
from backend.server import FortniteBackendServer
from launcher.main import FortniteEmulatorLauncher

def check_single_instance():
    """Check if another instance of the emulator is already running"""
    try:
        # Try to bind to a specific port to ensure single instance
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', 9999))  # Use port 9999 as instance lock
        return sock
    except socket.error:
        return None

def check_admin_privileges():
    """Check if running with administrator privileges"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def request_admin_privileges():
    """Request administrator privileges"""
    try:
        import ctypes
        if ctypes.windll.shell32.IsUserAnAdmin():
            return True
        else:
            # Re-run the program with admin rights
            print("Requesting administrator privileges...")
            result = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{sys.argv[0]}"', None, 1
            )
            if result > 32:  # Success
                print("Restarting as administrator...")
                sys.exit(0)
            else:
                print("Failed to get administrator privileges.")
                return False
    except Exception as e:
        print(f"Error requesting admin privileges: {e}")
        return False

def setup_environment():
    """Setup the emulator environment"""
    logger = setup_logger("main")
    
    # Check for admin privileges
    if not check_admin_privileges():
        logger.warning("Not running as administrator. Some features may not work properly.")
        logger.info("For full functionality, please run as administrator.")
    
    # Load configuration
    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    logger.info("Fortnite Season 7 Emulator starting...")
    logger.info(f"Version: {config['fortnite']['version']}")
    logger.info(f"Season: {config['fortnite']['season']}")
    
    return logger, config_manager

def start_backend_services(logger):
    """Start backend services in separate threads"""
    
    # Start request redirection
    def start_redirection():
        try:
            logger.info("Starting request redirection...")
            hosts_manager, redirector = start_request_redirection()
            logger.info("Request redirection started")
            return hosts_manager, redirector
        except Exception as e:
            logger.error(f"Failed to start request redirection: {e}")
            return None, None
    
    # Start backend server
    def start_backend():
        try:
            logger.info("Starting Season 7.40 backend server...")
            server = FortniteBackendServer()
            server.run()
        except Exception as e:
            logger.error(f"Backend server error: {e}")
    
    # Start DLL injection monitor
    def start_dll_monitor():
        try:
            logger.info("Starting DLL injection monitor...")
            start_process_monitor(auto_inject=True)
        except Exception as e:
            logger.error(f"DLL injection monitor error: {e}")
    
    # Start services in threads
    redirection_thread = threading.Thread(target=start_redirection, daemon=True)
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    dll_monitor_thread = threading.Thread(target=start_dll_monitor, daemon=True)
    
    redirection_thread.start()
    time.sleep(2)  # Give redirection time to start
    
    backend_thread.start()
    time.sleep(2)  # Give backend time to start
    
    logger.info("Season 7.40 backend services started")
    
    return redirection_thread, backend_thread

def main():
    """Main function to start the Fortnite Season 7 Emulator"""
    instance_lock = None
    try:
        # Check for single instance first
        instance_lock = check_single_instance()
        if instance_lock is None:
            print("Another instance of Fortnite Season 7 Emulator is already running.")
            print("Please close the existing instance before starting a new one.")
            input("Press Enter to exit...")
            return
        
        # Check and request admin privileges
        if not check_admin_privileges():
            print("Administrator privileges required for full functionality.")
            if request_admin_privileges():
                # If we successfully requested admin privileges, exit this instance
                return
            else:
                print("Failed to get administrator privileges. Some features may not work.")
                print("Continuing without admin privileges...")
                # Don't wait for input, just continue
        
        # Setup environment
        logger, config_manager = setup_environment()
        
        # Apply comprehensive SSL bypass methods
        logger.info("Applying comprehensive SSL bypass methods...")
        try:
            from utils.ssl_bypass import apply_ssl_bypass
            from utils.windows_ssl_bypass import apply_windows_ssl_bypass
            from utils.fortnite_ssl_fix import apply_fortnite_ssl_fix
            
            # Apply general SSL bypass
            general_success = apply_ssl_bypass()
            
            # Apply Windows-specific SSL bypass
            windows_success = apply_windows_ssl_bypass()
            
            # Apply Fortnite-specific SSL fixes
            fortnite_success, fortnite_results = apply_fortnite_ssl_fix()
            
            # Log all results
            for result in fortnite_results:
                logger.info(result)
            
            if general_success or windows_success or fortnite_success:
                logger.info("SSL bypass methods applied successfully")
            else:
                logger.warning("All SSL bypass methods failed")
                
        except Exception as e:
            logger.error(f"Failed to apply SSL bypass: {e}")
        
        # Start backend services
        redirection_thread, backend_thread = start_backend_services(logger)
        
        # Start GUI launcher
        logger.info("Starting GUI launcher...")
        app = FortniteEmulatorLauncher()
        
        # Run the application
        logger.info("Fortnite Season 7 Emulator ready!")
        app.run()
        
    except KeyboardInterrupt:
        print("\nShutting down Fortnite Season 7 Emulator...")
    except Exception as e:
        print(f"Error starting emulator: {e}")
        input("Press Enter to exit...")
    finally:
        # Cleanup
        try:
            from utils.request_redirector import HostsFileManager
            hosts_manager = HostsFileManager()
            hosts_manager.remove_redirections()
            print("Cleaned up domain redirections")
        except:
            pass
        
        # Close instance lock
        if instance_lock:
            try:
                instance_lock.close()
            except:
                pass

if __name__ == "__main__":
    # Check if we need to request admin privileges
    if len(sys.argv) > 1 and sys.argv[1] == "--request-admin":
        if not request_admin_privileges():
            sys.exit(1)
    
    main()
