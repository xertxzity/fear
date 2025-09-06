#!/usr/bin/env python3
"""
Process Manager for Fortnite Season 7 Emulator
Handles launching and managing Fortnite processes
"""

import subprocess
import psutil
import os
import time
from pathlib import Path
from typing import List, Optional

class ProcessManager:
    def __init__(self):
        self.fortnite_process = None
        self.fortnite_pid = None
    
    def launch_fortnite(self, executable_path: str, launch_args: List[str]) -> bool:
        """
        Launch Fortnite with specified arguments
        
        Args:
            executable_path: Path to Fortnite executable
            launch_args: List of launch arguments
            
        Returns:
            bool: True if launch successful, False otherwise
        """
        try:
            # Validate executable exists
            if not os.path.exists(executable_path):
                raise FileNotFoundError(f"Fortnite executable not found: {executable_path}")
            
            # Prepare command
            cmd = [executable_path] + launch_args
            
            # Get working directory (Fortnite's directory)
            working_dir = os.path.dirname(executable_path)
            
            print(f"Launching Fortnite with command: {' '.join(cmd)}")
            print(f"Working directory: {working_dir}")
            
            # Launch process - don't capture stdout/stderr so game can display
            self.fortnite_process = subprocess.Popen(
                cmd,
                cwd=working_dir,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            self.fortnite_pid = self.fortnite_process.pid
            print(f"Fortnite process started with PID: {self.fortnite_pid}")
            print(f"Command: {' '.join(cmd)}")
            
            # Wait a moment to check if process started successfully
            time.sleep(3)
            
            if self.fortnite_process.poll() is None:
                print(f"Fortnite is running successfully with PID: {self.fortnite_pid}")
                return True
            else:
                # Process ended immediately, likely an error
                print(f"Fortnite failed to start. Exit code: {self.fortnite_process.returncode}")
                print("Common issues:")
                print("1. Make sure you selected the correct Fortnite executable (FortniteClient-Win64-Shipping.exe)")
                print("2. Ensure you have Fortnite Season 7 (Version 7.40)")
                print("3. Check if the game files are corrupted")
                print("4. Try running the emulator as Administrator")
                print("5. Check Windows Event Viewer for detailed error information")
                return False
                
        except Exception as e:
            print(f"Error launching Fortnite: {e}")
            return False
    
    def stop_fortnite(self) -> bool:
        """
        Stop the Fortnite process
        
        Returns:
            bool: True if stopped successfully, False if no process found
        """
        try:
            # Try to stop our tracked process first
            if self.fortnite_process and self.fortnite_process.poll() is None:
                self.fortnite_process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.fortnite_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't terminate gracefully
                    self.fortnite_process.kill()
                    self.fortnite_process.wait()
                
                self.fortnite_process = None
                self.fortnite_pid = None
                return True
            
            # If no tracked process, try to find and kill Fortnite processes
            killed_any = False
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    if proc.info['name'] and 'fortnite' in proc.info['name'].lower():
                        proc.terminate()
                        killed_any = True
                        print(f"Terminated Fortnite process: {proc.info['name']} (PID: {proc.info['pid']})")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return killed_any
            
        except Exception as e:
            print(f"Error stopping Fortnite: {e}")
            return False
    
    def is_fortnite_running(self) -> bool:
        """
        Check if Fortnite is currently running
        
        Returns:
            bool: True if Fortnite is running, False otherwise
        """
        try:
            # Check our tracked process first
            if self.fortnite_process and self.fortnite_process.poll() is None:
                return True
            
            # Check for any Fortnite processes
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'] and 'fortnite' in proc.info['name'].lower():
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return False
            
        except Exception as e:
            print(f"Error checking Fortnite status: {e}")
            return False
    
    def get_fortnite_processes(self) -> List[dict]:
        """
        Get list of all Fortnite processes
        
        Returns:
            List of process info dictionaries
        """
        processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'create_time']):
                try:
                    if proc.info['name'] and 'fortnite' in proc.info['name'].lower():
                        processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'exe': proc.info['exe'],
                            'create_time': proc.info['create_time']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            print(f"Error getting Fortnite processes: {e}")
        
        return processes
    
    def wait_for_process_end(self, timeout: Optional[int] = None) -> bool:
        """
        Wait for the Fortnite process to end
        
        Args:
            timeout: Maximum time to wait in seconds (None for no timeout)
            
        Returns:
            bool: True if process ended, False if timeout
        """
        try:
            if self.fortnite_process:
                try:
                    self.fortnite_process.wait(timeout=timeout)
                    return True
                except subprocess.TimeoutExpired:
                    return False
            return True  # No process to wait for
            
        except Exception as e:
            print(f"Error waiting for process: {e}")
            return False
    
    def get_process_info(self) -> Optional[dict]:
        """
        Get information about the current Fortnite process
        
        Returns:
            Dictionary with process info or None if no process
        """
        try:
            if self.fortnite_process and self.fortnite_process.poll() is None:
                proc = psutil.Process(self.fortnite_pid)
                return {
                    'pid': proc.pid,
                    'name': proc.name(),
                    'status': proc.status(),
                    'create_time': proc.create_time(),
                    'memory_info': proc.memory_info(),
                    'cpu_percent': proc.cpu_percent()
                }
        except (psutil.NoSuchProcess, psutil.AccessDenied, Exception) as e:
            print(f"Error getting process info: {e}")
        
        return None
    
    def cleanup(self):
        """
        Clean up resources and stop any running processes
        """
        if self.is_fortnite_running():
            self.stop_fortnite()