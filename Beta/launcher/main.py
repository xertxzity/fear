#!/usr/bin/env python3
"""
Fortnite Season 7 Emulator Launcher
Main GUI application for launching Fortnite with custom backend
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import subprocess
import threading
import yaml
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.config_manager import ConfigManager
from utils.process_manager import ProcessManager
from utils.logger import setup_logger

class FortniteEmulatorLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Fortnite Season 7 Emulator Launcher")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.process_manager = ProcessManager()
        self.logger = setup_logger("launcher")
        
        # Variables
        self.fortnite_path = tk.StringVar()
        self.backend_status = tk.StringVar(value="Stopped")
        self.game_status = tk.StringVar(value="Not Running")
        
        # Load saved settings
        self.load_settings()
        
        # Setup GUI
        self.setup_gui()
        
        # Backend server is started by main.py, just set status
        self.backend_status.set("Running")
    
    def setup_gui(self):
        """Setup the main GUI interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Fortnite Season 7 Emulator", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Fortnite Path Selection
        ttk.Label(main_frame, text="Fortnite Executable:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.fortnite_path, width=50).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 5))
        ttk.Button(main_frame, text="Browse", command=self.browse_fortnite_exe).grid(row=1, column=2, pady=5)
        
        # Status Section
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        status_frame.columnconfigure(1, weight=1)
        
        ttk.Label(status_frame, text="Backend Server:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(status_frame, textvariable=self.backend_status).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(status_frame, text="Game Status:").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(status_frame, textvariable=self.game_status).grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        # Launch Arguments Section
        args_frame = ttk.LabelFrame(main_frame, text="Launch Arguments", padding="10")
        args_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        args_frame.columnconfigure(0, weight=1)
        
        self.args_text = tk.Text(args_frame, height=8, width=70)
        self.args_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar for args
        args_scrollbar = ttk.Scrollbar(args_frame, orient="vertical", command=self.args_text.yview)
        args_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.args_text.configure(yscrollcommand=args_scrollbar.set)
        
        # Load default arguments
        self.load_launch_args()
        
        # Control Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=20)
        
        self.launch_button = ttk.Button(button_frame, text="Launch Fortnite", 
                                       command=self.launch_fortnite, style="Accent.TButton")
        self.launch_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Stop Game", 
                                     command=self.stop_fortnite, state="disabled")
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Restart Backend", 
                  command=self.restart_backend).pack(side=tk.LEFT, padx=5)
        
        self.restore_button = ttk.Button(button_frame, text="Restore System", 
                                        command=self.restore_system)
        self.restore_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Open Logs", 
                  command=self.open_logs).pack(side=tk.LEFT, padx=5)
        
        # Log Output
        log_frame = ttk.LabelFrame(main_frame, text="Log Output", padding="10")
        log_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = tk.Text(log_frame, height=10, state="disabled")
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        # Configure main frame row weights
        main_frame.rowconfigure(5, weight=1)
    
    def browse_fortnite_exe(self):
        """Browse for Fortnite executable"""
        filename = filedialog.askopenfilename(
            title="Select Fortnite Executable",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")],
            initialdir="C:/"
        )
        if filename:
            self.fortnite_path.set(filename)
            self.save_settings()
    
    def load_launch_args(self):
        """Load launch arguments from config"""
        try:
            config = self.config_manager.get_config()
            args = config.get('launch_args', [])
            args_text = '\n'.join(args)
            
            self.args_text.delete(1.0, tk.END)
            self.args_text.insert(1.0, args_text)
        except Exception as e:
            self.log_message(f"Error loading launch args: {e}")
    
    def get_launch_args(self):
        """Get launch arguments from text widget"""
        args_text = self.args_text.get(1.0, tk.END).strip()
        return [arg.strip() for arg in args_text.split('\n') if arg.strip()]
    
    def launch_fortnite(self):
        """Launch Fortnite with custom arguments"""
        if not self.fortnite_path.get():
            messagebox.showerror("Error", "Please select Fortnite executable first!")
            return
        
        exe_path = self.fortnite_path.get()
        if not os.path.exists(exe_path):
            messagebox.showerror("Error", "Fortnite executable not found!")
            return
        
        # Validate executable
        if not exe_path.lower().endswith('.exe'):
            messagebox.showerror("Error", "Please select a valid executable file (.exe)")
            return
        
        # Check if it's likely the correct Fortnite executable
        exe_name = os.path.basename(exe_path).lower()
        if 'fortnite' not in exe_name and 'fortniteclient' not in exe_name:
            result = messagebox.askyesno(
                "Warning", 
                f"The selected file '{os.path.basename(exe_path)}' doesn't appear to be a Fortnite executable.\n\n"
                "Are you sure you want to continue?"
            )
            if not result:
                return
        
        try:
            # Base arguments (from config)
            config_args = self.config_manager.get_launch_args()
            args = config_args

            # Add explicit anti-cheat bypasses
            if "-nobe" not in args:
                args.append("-nobe") # Disable BattleEye
            if "-noeac" not in args:
                args.append("-noeac") # Disable EasyAntiCheat
            
            # Add additional backend redirection arguments
            if "-epicapp" not in args:
                args.append("-epicapp=Fortnite")
            if "-epicenv" not in args:
                args.append("-epicenv=Prod")
            if "-epiclocale" not in args:
                args.append("-epiclocale=en-us")
            if "-epicportal" not in args:
                args.append("-epicportal")
            if "-skippatchcheck" not in args:
                args.append("-skippatchcheck")

            # Add backend server URL - use HTTPS for proper SSL handling
            config = self.config_manager.get_config()
            backend_url = f"https://{config['server']['host']}:{config['server']['ssl_port']}"
            
            # Ensure -epicbackend is present and correctly set
            found_epicbackend = False
            for i, arg in enumerate(args):
                if arg.lower().startswith("-epicbackend="):
                    args[i] = f"-epicbackend={backend_url}"
                    found_epicbackend = True
                    break
            if not found_epicbackend:
                args.append(f"-epicbackend={backend_url}")
            
            # Add additional backend redirection arguments for all Epic services
            backend_args = [
                f"-epicbackend={backend_url}",
                f"-epicbackendurl={backend_url}",
                f"-epicbackendhost={config['server']['host']}",
                f"-epicbackendport={config['server']['ssl_port']}",
                f"-epicbackendprotocol=https",
                f"-epicbackendssl=true"
            ]
            
            for backend_arg in backend_args:
                if not any(arg.lower().startswith(backend_arg.split('=')[0].lower() + '=') for arg in args):
                    args.append(backend_arg)
            
            # Log launch details
            self.log_message("=== LAUNCHING FORTNITE ===")
            self.log_message(f"Executable: {exe_path}")
            self.log_message(f"Working Directory: {os.path.dirname(exe_path)}")
            self.log_message(f"Backend URL: {backend_url}")
            self.log_message(f"Launch Arguments: {len(args)} arguments")
            
            # Launch Fortnite
            self.log_message("Starting Fortnite process...")
            success = self.process_manager.launch_fortnite(exe_path, args)
            
            if success:
                self.game_status.set("Running")
                self.launch_button.config(state="disabled")
                self.stop_button.config(state="normal")
                self.log_message("✓ Fortnite launched successfully!")
                
                # Start monitoring thread
                threading.Thread(target=self.monitor_game_process, daemon=True).start()
            else:
                self.log_message("✗ Failed to launch Fortnite!")
                self.log_message("Check the troubleshooting tips above.")
                messagebox.showerror(
                    "Launch Failed", 
                    "Fortnite failed to start. Common issues:\n\n"
                    "1. Wrong executable selected\n"
                    "2. Not Fortnite Season 7 (Version 7.40)\n"
                    "3. Missing game files\n"
                    "4. Need administrator privileges\n\n"
                    "Check the log output for more details."
                )
                
        except Exception as e:
            self.log_message(f"✗ Error launching Fortnite: {e}")
            messagebox.showerror("Launch Error", f"An error occurred while launching Fortnite:\n\n{str(e)}")
    
    def stop_fortnite(self):
        """Stop Fortnite process"""
        try:
            if self.process_manager.stop_fortnite():
                self.log_message("Fortnite stopped successfully")
            else:
                self.log_message("No Fortnite process found")
                
            self.game_status.set("Not Running")
            self.launch_button.config(state="normal")
            self.stop_button.config(state="disabled")
            
        except Exception as e:
            self.log_message(f"Error stopping Fortnite: {e}")
    
    def monitor_game_process(self):
        """Monitor Fortnite process in background"""
        while self.process_manager.is_fortnite_running():
            threading.Event().wait(2)  # Check every 2 seconds
        
        # Game process ended
        self.root.after(0, self.on_game_ended)
    
    def on_game_ended(self):
        """Called when game process ends"""
        self.game_status.set("Not Running")
        self.launch_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.log_message("Fortnite process ended")
    
    # Backend server methods removed - backend is now managed by main.py
    
    def restart_backend(self):
        """Restart backend server"""
        self.backend_status.set("Running")
        self.log_message("Backend server is managed by main process - restart the entire emulator to restart backend")
    
    def open_logs(self):
        """Open logs directory"""
        logs_dir = Path(__file__).parent.parent / "logs"
        if logs_dir.exists():
            os.startfile(str(logs_dir))
        else:
            messagebox.showinfo("Info", "Logs directory not found")
    
    def log_message(self, message):
        """Add message to log output"""
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"[{self.get_timestamp()}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
        
        # Also log to file
        self.logger.info(message)
    
    def get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
    
    def load_settings(self):
        """Load saved settings"""
        settings_file = Path(__file__).parent.parent / "launcher_settings.json"
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    self.fortnite_path.set(settings.get('fortnite_path', ''))
            except Exception as e:
                self.logger.error(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save current settings"""
        settings_file = Path(__file__).parent.parent / "launcher_settings.json"
        try:
            settings = {
                'fortnite_path': self.fortnite_path.get()
            }
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
    
    def run(self):
        """Start the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def restore_system(self):
        """Restore system to original state"""
        result = messagebox.askyesno(
            "Restore System",
            "This will restore your system to its original state by:\n\n"
            "• Removing SSL bypass modifications\n"
            "• Restoring hosts file\n"
            "• Clearing SSL certificates\n"
            "• Removing launch arguments\n"
            "• Clearing environment variables\n\n"
            "⚠️ This will undo all emulator modifications!\n\n"
            "Continue?"
        )
        
        if result:
            try:
                self.log_message("Starting system restoration...")
                
                # Import system restore functionality
                from utils.system_restore import restore_system_to_normal
                
                success, results = restore_system_to_normal()
                
                # Log all results
                for result_msg in results:
                    self.log_message(result_msg)
                
                if success:
                    self.log_message("✅ System restored successfully")
                    messagebox.showinfo(
                        "Success", 
                        "System has been restored to original state!\n\n"
                        "All SSL bypass modifications have been removed.\n"
                        "You may need to restart your computer for all changes to take effect."
                    )
                else:
                    self.log_message("⚠️ System restore completed with issues")
                    messagebox.showwarning(
                        "Partial Success", 
                        "System restoration completed but some operations failed.\n\n"
                        "Check the log output for details."
                    )
                    
            except Exception as e:
                self.log_message(f"✗ Error during system restore: {e}")
                messagebox.showerror(
                    "Error", 
                    f"An error occurred during system restore:\n\n{str(e)}\n\n"
                    "You may need to manually restore some settings."
                )
    
    def on_closing(self):
        """Handle application closing"""
        self.save_settings()
        if self.process_manager.is_fortnite_running():
            if messagebox.askokcancel("Quit", "Fortnite is still running. Stop it before closing?"):
                self.stop_fortnite()
        self.root.destroy()

if __name__ == "__main__":
    app = FortniteEmulatorLauncher()
    app.run()