#!/usr/bin/env python3
"""
HTTPS Request Redirector for Fortnite Season 7 Emulator
Redirects Fortnite's HTTPS requests to local backend server
"""

import socket
import threading
import ssl
import time
from urllib.parse import urlparse
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.config_manager import ConfigManager
from utils.logger import setup_logger

class HTTPSRedirector:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.logger = setup_logger("redirector")
        
        # Epic domains to redirect
        self.epic_domains = [
            # Authentication domains
            'account-public-service-prod.ol.epicgames.com',
            'account-public-service-prod.ak.epicgames.com',
            'account-public-service-prod03.ol.epicgames.com',
            
            # Fortnite service domains
            'fortnite-public-service-prod11.ol.epicgames.com',
            'fortnite-public-service-prod.ak.epicgames.com',
            
            # Lightswitch and status domains
            'lightswitch-public-service-prod06.ol.epicgames.com',
            
            # Friends and party services
            'friends-public-service-prod06.ol.epicgames.com',
            'party-service-prod.ol.epicgames.com',
            
            # Entitlement and tracking
            'entitlement-public-service-prod08.ol.epicgames.com',
            'eulatracking-public-service-prod06.ol.epicgames.com',
            
            # Data routing
            'datarouter-public-service-prod06.ol.epicgames.com',
            'datarouter-prod.ak.epicgames.com',
            
            # Stats and content
            'statsproxy-public-service-live.ol.epicgames.com',
            'content-api-prod.ak.epicgames.com',
            
            # Additional domains from logs
            'account-public-service-prod.ol.epicgames.com',
            'datarouter.ol.epicgames.com',
            'account-public-service-prod.ak.epicgames.com'
        ]
        
        # Local backend info
        config = self.config_manager.get_config()
        self.local_host = config['server']['host']
        self.local_port = config['server']['port']  # Use HTTP port instead of SSL port
        
        # Proxy server
        self.proxy_host = '127.0.0.1'
        self.proxy_port = 8888
        self.proxy_server = None
        self.running = False
    
    def start_proxy_server(self):
        """Start the HTTPS proxy server"""
        try:
            self.proxy_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.proxy_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.proxy_server.bind((self.proxy_host, self.proxy_port))
            self.proxy_server.listen(5)
            
            self.running = True
            self.logger.info(f"HTTPS Proxy server started on {self.proxy_host}:{self.proxy_port}")
            
            while self.running:
                try:
                    client_socket, addr = self.proxy_server.accept()
                    self.logger.debug(f"Connection from {addr}")
                    
                    # Handle connection in separate thread
                    thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket,),
                        daemon=True
                    )
                    thread.start()
                    
                except socket.error as e:
                    if self.running:
                        self.logger.error(f"Proxy server error: {e}")
                    break
        
        except Exception as e:
            self.logger.error(f"Failed to start proxy server: {e}")
    
    def handle_client(self, client_socket):
        """Handle client connection"""
        try:
            # Read the initial request
            request = client_socket.recv(4096).decode('utf-8')
            
            if not request:
                return
            
            # Parse the request
            lines = request.split('\n')
            if not lines:
                return
            
            # Get the first line (method, URL, version)
            first_line = lines[0].strip()
            if not first_line:
                return
            
            # Handle CONNECT method (HTTPS tunneling)
            if first_line.startswith('CONNECT'):
                self.handle_connect(client_socket, first_line)
            else:
                # Handle regular HTTP request
                self.handle_http_request(client_socket, request)
        
        except Exception as e:
            self.logger.error(f"Error handling client: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
    
    def handle_connect(self, client_socket, connect_line):
        """Handle HTTPS CONNECT method"""
        try:
            # Parse CONNECT request
            parts = connect_line.split()
            if len(parts) < 2:
                return
            
            # Get target host and port
            target = parts[1]
            if ':' in target:
                host, port = target.split(':', 1)
                port = int(port)
            else:
                host = target
                port = 443
            
            self.logger.debug(f"CONNECT request to {host}:{port}")
            
            # Check if this is an Epic Games domain
            if self.should_redirect(host):
                self.logger.info(f"Redirecting {host} to local backend")
                # Redirect to local backend
                target_host = self.local_host
                target_port = self.local_port
            else:
                # Forward to original destination
                target_host = host
                target_port = port
            
            # Connect to target server
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_socket.connect((target_host, target_port))
            
            # Send 200 Connection established
            client_socket.send(b'HTTP/1.1 200 Connection established\r\n\r\n')
            
            # Start tunneling
            self.tunnel_data(client_socket, target_socket)
        
        except Exception as e:
            self.logger.error(f"Error in CONNECT handler: {e}")
    
    def handle_http_request(self, client_socket, request):
        """Handle regular HTTP request"""
        try:
            # Parse request to get host
            lines = request.split('\n')
            host = None
            
            for line in lines:
                if line.lower().startswith('host:'):
                    host = line.split(':', 1)[1].strip()
                    break
            
            if not host:
                return
            
            self.logger.debug(f"HTTP request to {host}")
            
            # Check if this should be redirected
            if self.should_redirect(host):
                self.logger.info(f"Redirecting HTTP request from {host} to local backend")
                # Modify request to point to local backend
                modified_request = self.modify_request(request, self.local_host, self.local_port)
                
                # Forward to local backend
                self.forward_request(client_socket, modified_request, self.local_host, self.local_port)
            else:
                # Forward to original destination
                self.forward_request(client_socket, request, host, 80)
        
        except Exception as e:
            self.logger.error(f"Error in HTTP handler: {e}")
    
    def should_redirect(self, host):
        """Check if host should be redirected to local backend"""
        return any(domain in host for domain in self.epic_domains)
    
    def modify_request(self, request, new_host, new_port):
        """Modify HTTP request to point to new host"""
        lines = request.split('\n')
        modified_lines = []
        
        for line in lines:
            if line.lower().startswith('host:'):
                modified_lines.append(f'Host: {new_host}:{new_port}')
            else:
                modified_lines.append(line)
        
        return '\n'.join(modified_lines)
    
    def forward_request(self, client_socket, request, target_host, target_port):
        """Forward HTTP request to target server"""
        try:
            # Connect to target
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_socket.connect((target_host, target_port))
            
            # Send request
            target_socket.send(request.encode('utf-8'))
            
            # Relay response
            self.tunnel_data(client_socket, target_socket)
        
        except Exception as e:
            self.logger.error(f"Error forwarding request: {e}")
    
    def tunnel_data(self, client_socket, target_socket):
        """Tunnel data between client and target"""
        def forward_data(source, destination):
            try:
                while True:
                    data = source.recv(4096)
                    if not data:
                        break
                    destination.send(data)
            except:
                pass
            finally:
                try:
                    source.close()
                    destination.close()
                except:
                    pass
        
        # Start forwarding in both directions
        thread1 = threading.Thread(target=forward_data, args=(client_socket, target_socket), daemon=True)
        thread2 = threading.Thread(target=forward_data, args=(target_socket, client_socket), daemon=True)
        
        thread1.start()
        thread2.start()
        
        # Wait for threads to complete
        thread1.join()
        thread2.join()
    
    def stop_proxy_server(self):
        """Stop the proxy server"""
        self.running = False
        if self.proxy_server:
            try:
                self.proxy_server.close()
            except:
                pass
        self.logger.info("HTTPS Proxy server stopped")

class HostsFileManager:
    """Manages Windows hosts file for domain redirection"""
    
    def __init__(self):
        self.logger = setup_logger("hosts_manager")
        self.hosts_file = Path("C:/Windows/System32/drivers/etc/hosts")
        self.backup_file = Path("C:/Windows/System32/drivers/etc/hosts.backup")
        
        # Epic domains to redirect (comprehensive list from logs)
        self.epic_domains = [
            # Authentication domains
            'account-public-service-prod.ol.epicgames.com',
            'account-public-service-prod.ak.epicgames.com',
            'account-public-service-prod03.ol.epicgames.com',
            
            # Fortnite service domains
            'fortnite-public-service-prod11.ol.epicgames.com',
            'fortnite-public-service-prod.ak.epicgames.com',
            
            # Lightswitch and status domains
            'lightswitch-public-service-prod06.ol.epicgames.com',
            
            # Friends and party services
            'friends-public-service-prod06.ol.epicgames.com',
            'party-service-prod.ol.epicgames.com',
            
            # Entitlement and tracking
            'entitlement-public-service-prod08.ol.epicgames.com',
            'eulatracking-public-service-prod06.ol.epicgames.com',
            
            # Data routing
            'datarouter-public-service-prod06.ol.epicgames.com',
            'datarouter-prod.ak.epicgames.com',
            'datarouter.ol.epicgames.com',
            
            # Stats and content
            'statsproxy-public-service-live.ol.epicgames.com',
            'content-api-prod.ak.epicgames.com',
            
            # Additional domains from logs
            'account-public-service-prod.ol.epicgames.com',
            'datarouter.ol.epicgames.com',
            'account-public-service-prod.ak.epicgames.com'
        ]
    
    def backup_hosts_file(self):
        """Create backup of hosts file"""
        try:
            if self.hosts_file.exists() and not self.backup_file.exists():
                import shutil
                shutil.copy2(self.hosts_file, self.backup_file)
                self.logger.info("Hosts file backed up")
        except Exception as e:
            self.logger.error(f"Failed to backup hosts file: {e}")
    
    def add_redirections(self, target_ip='127.0.0.1'):
        """Add Epic Games domain redirections to hosts file"""
        try:
            # Backup first
            self.backup_hosts_file()
            
            # Read current hosts file
            if self.hosts_file.exists():
                with open(self.hosts_file, 'r') as f:
                    content = f.read()
            else:
                content = ""
            
            # Add redirections
            redirections = []
            for domain in self.epic_domains:
                line = f"{target_ip} {domain}"
                if line not in content:
                    redirections.append(line)
            
            if redirections:
                # Add marker comments
                new_content = content + "\n\n# Fortnite Season 7 Emulator - START\n"
                new_content += "\n".join(redirections)
                new_content += "\n# Fortnite Season 7 Emulator - END\n"
                
                # Write back to hosts file
                with open(self.hosts_file, 'w') as f:
                    f.write(new_content)
                
                self.logger.info(f"Added {len(redirections)} domain redirections to hosts file")
                return True
            else:
                self.logger.info("All redirections already present in hosts file")
                return True
        
        except PermissionError:
            self.logger.error("Permission denied. Run as administrator to modify hosts file.")
            return False
        except Exception as e:
            self.logger.error(f"Failed to modify hosts file: {e}")
            return False
    
    def remove_redirections(self):
        """Remove Epic Games domain redirections from hosts file"""
        try:
            if not self.hosts_file.exists():
                return True
            
            # Read hosts file
            with open(self.hosts_file, 'r') as f:
                lines = f.readlines()
            
            # Remove lines between markers
            new_lines = []
            skip = False
            
            for line in lines:
                if "# Fortnite Season 7 Emulator - START" in line:
                    skip = True
                    continue
                elif "# Fortnite Season 7 Emulator - END" in line:
                    skip = False
                    continue
                
                if not skip:
                    new_lines.append(line)
            
            # Write back
            with open(self.hosts_file, 'w') as f:
                f.writelines(new_lines)
            
            self.logger.info("Removed domain redirections from hosts file")
            return True
        
        except PermissionError:
            self.logger.error("Permission denied. Run as administrator to modify hosts file.")
            return False
        except Exception as e:
            self.logger.error(f"Failed to remove redirections: {e}")
            return False
    
    def restore_hosts_file(self):
        """Restore hosts file from backup"""
        try:
            if self.backup_file.exists():
                import shutil
                shutil.copy2(self.backup_file, self.hosts_file)
                self.backup_file.unlink()  # Remove backup
                self.logger.info("Hosts file restored from backup")
                return True
            else:
                self.logger.warning("No backup file found")
                return False
        
        except PermissionError:
            self.logger.error("Permission denied. Run as administrator to restore hosts file.")
            return False
        except Exception as e:
            self.logger.error(f"Failed to restore hosts file: {e}")
            return False

def start_request_redirection():
    """Start the request redirection system"""
    # Start hosts file redirection
    hosts_manager = HostsFileManager()
    if hosts_manager.add_redirections():
        print("Domain redirection enabled via hosts file")
    else:
        print("Failed to enable domain redirection. Try running as administrator.")
    
    # Start HTTPS proxy (optional, for more advanced redirection)
    redirector = HTTPSRedirector()
    proxy_thread = threading.Thread(target=redirector.start_proxy_server, daemon=True)
    proxy_thread.start()
    
    return hosts_manager, redirector

if __name__ == "__main__":
    start_request_redirection()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping request redirection...")