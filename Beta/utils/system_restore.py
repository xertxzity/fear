#!/usr/bin/env python3
"""
System Restore Utility for Fortnite Season 7 Emulator
Restores system to original state by removing all emulator modifications
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Tuple, List

class SystemRestore:
    def __init__(self):
        self.logger = None
        self.results = []
        
    def setup_logger(self):
        """Setup logger for restore operations"""
        try:
            from utils.logger import setup_logger
            self.logger = setup_logger("system_restore")
        except:
            # Fallback logger
            class SimpleLogger:
                def info(self, msg): print(f"[INFO] {msg}")
                def warning(self, msg): print(f"[WARNING] {msg}")
                def error(self, msg): print(f"[ERROR] {msg}")
            self.logger = SimpleLogger()
    
    def restore_system_to_normal(self) -> Tuple[bool, List[str]]:
        """
        Restore system to original state
        
        Returns:
            Tuple[bool, List[str]]: (success, results)
        """
        self.setup_logger()
        self.results = []
        
        try:
            self.logger.info("Starting system restoration...")
            
            # Restore hosts file
            hosts_success = self._restore_hosts_file()
            
            # Clear SSL certificates
            ssl_success = self._clear_ssl_certificates()
            
            # Restore Windows SSL settings
            windows_ssl_success = self._restore_windows_ssl_settings()
            
            # Clear environment variables
            env_success = self._clear_environment_variables()
            
            # Remove generated files
            files_success = self._remove_generated_files()
            
            # Overall success
            overall_success = any([hosts_success, ssl_success, windows_ssl_success, env_success, files_success])
            
            if overall_success:
                self.results.append("✅ System restoration completed successfully")
            else:
                self.results.append("⚠️ System restoration completed with issues")
            
            return overall_success, self.results
            
        except Exception as e:
            error_msg = f"❌ Error during system restoration: {e}"
            self.results.append(error_msg)
            self.logger.error(error_msg)
            return False, self.results
    
    def _restore_hosts_file(self) -> bool:
        """Restore hosts file from backup"""
        try:
            hosts_file = Path("C:/Windows/System32/drivers/etc/hosts")
            backup_file = Path("C:/Windows/System32/drivers/etc/hosts.backup")
            
            if backup_file.exists():
                shutil.copy2(backup_file, hosts_file)
                backup_file.unlink()  # Remove backup
                self.results.append("✅ Hosts file restored from backup")
                self.logger.info("Hosts file restored from backup")
                return True
            else:
                # Try to remove emulator entries manually
                if hosts_file.exists():
                    with open(hosts_file, 'r') as f:
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
                    
                    with open(hosts_file, 'w') as f:
                        f.writelines(new_lines)
                    
                    self.results.append("✅ Hosts file cleaned (manual removal)")
                    self.logger.info("Hosts file cleaned manually")
                    return True
                else:
                    self.results.append("⚠️ Hosts file not found")
                    return False
                    
        except PermissionError:
            self.results.append("❌ Permission denied - run as administrator to restore hosts file")
            self.logger.error("Permission denied - run as administrator to restore hosts file")
            return False
        except Exception as e:
            self.results.append(f"❌ Error restoring hosts file: {e}")
            self.logger.error(f"Error restoring hosts file: {e}")
            return False
    
    def _clear_ssl_certificates(self) -> bool:
        """Clear generated SSL certificates"""
        try:
            certs_dir = Path(__file__).parent.parent / "certs"
            if certs_dir.exists():
                shutil.rmtree(certs_dir)
                self.results.append("✅ SSL certificates removed")
                self.logger.info("SSL certificates removed")
                return True
            else:
                self.results.append("ℹ️ No SSL certificates found to remove")
                return True
                
        except Exception as e:
            self.results.append(f"❌ Error removing SSL certificates: {e}")
            self.logger.error(f"Error removing SSL certificates: {e}")
            return False
    
    def _restore_windows_ssl_settings(self) -> bool:
        """Restore Windows SSL settings"""
        try:
            from utils.windows_ssl_bypass import restore_windows_ssl_bypass
            success = restore_windows_ssl_bypass()
            
            if success:
                self.results.append("✅ Windows SSL settings restored")
                self.logger.info("Windows SSL settings restored")
            else:
                self.results.append("⚠️ Windows SSL settings restoration failed")
                self.logger.warning("Windows SSL settings restoration failed")
            
            return success
            
        except Exception as e:
            self.results.append(f"❌ Error restoring Windows SSL settings: {e}")
            self.logger.error(f"Error restoring Windows SSL settings: {e}")
            return False
    
    def _clear_environment_variables(self) -> bool:
        """Clear SSL bypass environment variables"""
        try:
            ssl_vars = [
                'PYTHONHTTPSVERIFY',
                'CURL_CA_BUNDLE',
                'SSL_VERIFY',
                'NODE_TLS_REJECT_UNAUTHORIZED',
                'REQUESTS_CA_BUNDLE',
                'SSL_CERT_FILE',
                'SSL_CERT_DIR',
                'OPENSSL_CONF',
                'LIBCURL_SSL_VERIFY',
                'CURLOPT_SSL_VERIFYPEER',
                'CURLOPT_SSL_VERIFYHOST',
                'WINHTTP_OPTION_SECURITY_FLAGS',
                'INTERNET_FLAG_IGNORE_CERT_CN_INVALID',
                'INTERNET_FLAG_IGNORE_CERT_DATE_INVALID',
                'INTERNET_FLAG_IGNORE_REDIRECT_TO_HTTPS',
                'INTERNET_FLAG_IGNORE_REDIRECT_TO_HTTP',
                'INTERNET_OPTION_SECURITY_FLAGS',
                'INTERNET_OPTION_IGNORE_CERT_CN_INVALID',
                'INTERNET_OPTION_IGNORE_CERT_DATE_INVALID'
            ]
            
            cleared_count = 0
            for var in ssl_vars:
                if var in os.environ:
                    del os.environ[var]
                    cleared_count += 1
            
            if cleared_count > 0:
                self.results.append(f"✅ Cleared {cleared_count} environment variables")
                self.logger.info(f"Cleared {cleared_count} environment variables")
            else:
                self.results.append("ℹ️ No environment variables to clear")
            
            return True
            
        except Exception as e:
            self.results.append(f"❌ Error clearing environment variables: {e}")
            self.logger.error(f"Error clearing environment variables: {e}")
            return False
    
    def _remove_generated_files(self) -> bool:
        """Remove generated files and logs"""
        try:
            files_to_remove = [
                "launcher_settings.json",
                "logs/",
                "certs/",
                "FortniteGame.log",
                "utils/FortniteGame.log"
            ]
            
            removed_count = 0
            for file_path in files_to_remove:
                path = Path(__file__).parent.parent / file_path
                if path.exists():
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                    removed_count += 1
            
            if removed_count > 0:
                self.results.append(f"✅ Removed {removed_count} generated files")
                self.logger.info(f"Removed {removed_count} generated files")
            else:
                self.results.append("ℹ️ No generated files found to remove")
            
            return True
            
        except Exception as e:
            self.results.append(f"❌ Error removing generated files: {e}")
            self.logger.error(f"Error removing generated files: {e}")
            return False

def restore_system_to_normal() -> Tuple[bool, List[str]]:
    """Main function to restore system to normal state"""
    restore = SystemRestore()
    return restore.restore_system_to_normal()

if __name__ == "__main__":
    print("Fortnite Season 7 Emulator - System Restore")
    print("=" * 50)
    
    success, results = restore_system_to_normal()
    
    print("\nRestoration Results:")
    for result in results:
        print(f"  {result}")
    
    if success:
        print("\n✅ System restoration completed successfully!")
        print("You may need to restart your computer for all changes to take effect.")
    else:
        print("\n⚠️ System restoration completed with issues.")
        print("Some operations may have failed. Check the results above.")
    
    input("\nPress Enter to exit...")