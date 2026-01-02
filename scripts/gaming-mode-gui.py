#!/usr/bin/env python3
"""
Lightweight GUI for managing Local AI Gaming Mode
Run with: python gaming-mode-gui.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
import time
from typing import Optional, Dict, Any

MANAGER_URL = "http://localhost:8000"
REFRESH_INTERVAL = 2  # seconds


class GamingModeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Local AI Gaming Mode")
        self.root.geometry("400x500")
        self.root.resizable(False, False)
        
        # Try to set window icon (optional)
        try:
            self.root.iconbitmap(default="")  # Remove default icon
        except:
            pass
        
        # Status variables
        self.status_data: Optional[Dict[str, Any]] = None
        self.last_error: Optional[str] = None
        
        # Create UI
        self.create_widgets()
        
        # Start auto-refresh
        self.refresh_status()
        self.schedule_refresh()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        # Header
        header = tk.Frame(self.root, bg="#2b2b2b", height=60)
        header.pack(fill=tk.X, padx=0, pady=0)
        
        title = tk.Label(
            header,
            text="Local AI Gaming Mode",
            font=("Arial", 16, "bold"),
            bg="#2b2b2b",
            fg="#ffffff"
        )
        title.pack(pady=15)
        
        # Main content frame
        content = tk.Frame(self.root, bg="#1e1e1e", padx=20, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Status section
        status_frame = tk.LabelFrame(
            content,
            text="Status",
            font=("Arial", 10, "bold"),
            bg="#1e1e1e",
            fg="#ffffff",
            padx=10,
            pady=10
        )
        status_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Gaming mode status
        self.gaming_mode_label = tk.Label(
            status_frame,
            text="Gaming Mode: Checking...",
            font=("Arial", 11),
            bg="#1e1e1e",
            fg="#888888",
            anchor="w"
        )
        self.gaming_mode_label.pack(fill=tk.X, pady=5)
        
        # Safe to game status
        self.safe_label = tk.Label(
            status_frame,
            text="Safe to Game: Checking...",
            font=("Arial", 11, "bold"),
            bg="#1e1e1e",
            fg="#888888",
            anchor="w"
        )
        self.safe_label.pack(fill=tk.X, pady=5)
        
        # Running models section
        models_frame = tk.LabelFrame(
            content,
            text="Running Models",
            font=("Arial", 10, "bold"),
            bg="#1e1e1e",
            fg="#ffffff",
            padx=10,
            pady=10
        )
        models_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Models listbox with scrollbar
        listbox_frame = tk.Frame(models_frame, bg="#1e1e1e")
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.models_listbox = tk.Listbox(
            listbox_frame,
            font=("Consolas", 9),
            bg="#2b2b2b",
            fg="#ffffff",
            selectbackground="#4a9eff",
            yscrollcommand=scrollbar.set,
            borderwidth=0,
            highlightthickness=0
        )
        self.models_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.models_listbox.yview)
        
        # Buttons frame
        buttons_frame = tk.Frame(content, bg="#1e1e1e")
        buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Enable/Disable gaming mode button
        self.gaming_mode_button = tk.Button(
            buttons_frame,
            text="Enable Gaming Mode",
            font=("Arial", 10, "bold"),
            bg="#4a9eff",
            fg="#ffffff",
            activebackground="#5aaeff",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.toggle_gaming_mode
        )
        self.gaming_mode_button.pack(fill=tk.X, pady=(0, 10))
        
        # Stop all models button
        self.stop_all_button = tk.Button(
            buttons_frame,
            text="Stop All Models",
            font=("Arial", 10),
            bg="#ff6b6b",
            fg="#ffffff",
            activebackground="#ff7b7b",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.stop_all_models
        )
        self.stop_all_button.pack(fill=tk.X, pady=(0, 10))
        
        # Refresh button
        refresh_button = tk.Button(
            buttons_frame,
            text="Refresh Status",
            font=("Arial", 9),
            bg="#555555",
            fg="#ffffff",
            activebackground="#666666",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2",
            command=self.refresh_status
        )
        refresh_button.pack(fill=tk.X)
        
        # Error label (hidden by default)
        self.error_label = tk.Label(
            content,
            text="",
            font=("Arial", 9),
            bg="#1e1e1e",
            fg="#ff6b6b",
            wraplength=360,
            justify=tk.LEFT
        )
        self.error_label.pack(fill=tk.X, pady=(10, 0))
    
    def get_status(self) -> Optional[Dict[str, Any]]:
        """Fetch status from manager API."""
        try:
            response = requests.get(f"{MANAGER_URL}/status", timeout=2)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            return None
        except requests.exceptions.Timeout:
            return None
        except Exception as e:
            self.last_error = f"Error: {str(e)}"
            return None
    
    def refresh_status(self):
        """Refresh status in background thread."""
        def refresh():
            status = self.get_status()
            self.root.after(0, lambda: self.update_ui(status))
        
        thread = threading.Thread(target=refresh, daemon=True)
        thread.start()
    
    def update_ui(self, status: Optional[Dict[str, Any]]):
        """Update UI with new status data."""
        self.status_data = status
        
        if status is None:
            # Connection error
            self.gaming_mode_label.config(
                text="Gaming Mode: ❌ Not Connected",
                fg="#ff6b6b"
            )
            self.safe_label.config(
                text="Safe to Game: ❌ Cannot Check",
                fg="#ff6b6b"
            )
            self.models_listbox.delete(0, tk.END)
            self.models_listbox.insert(0, "Cannot connect to manager")
            self.models_listbox.insert(1, f"Check: {MANAGER_URL}")
            self.error_label.config(
                text="⚠️ Cannot connect to Local AI Manager. Make sure it's running."
            )
            self.gaming_mode_button.config(state=tk.DISABLED)
            self.stop_all_button.config(state=tk.DISABLED)
            return
        
        # Clear error
        self.error_label.config(text="")
        
        # Update gaming mode status
        gaming_mode = status.get("gaming_mode", False)
        if gaming_mode:
            self.gaming_mode_label.config(
                text="Gaming Mode: ✅ ENABLED (new models blocked)",
                fg="#4a9eff"
            )
            self.gaming_mode_button.config(
                text="Disable Gaming Mode",
                bg="#ff6b6b",
                activebackground="#ff7b7b"
            )
        else:
            self.gaming_mode_label.config(
                text="Gaming Mode: ⭕ DISABLED (new models allowed)",
                fg="#51c878"
            )
            self.gaming_mode_button.config(
                text="Enable Gaming Mode",
                bg="#4a9eff",
                activebackground="#5aaeff"
            )
        
        # Update safe to game status
        safe_to_game = status.get("safe_to_game", False)
        if safe_to_game:
            self.safe_label.config(
                text="Safe to Game: ✅ YES",
                fg="#51c878"
            )
        else:
            self.safe_label.config(
                text="Safe to Game: ❌ NO",
                fg="#ff6b6b"
            )
            # Show reason
            running_count = len(status.get("running_models", []))
            if running_count > 0:
                self.safe_label.config(
                    text=f"Safe to Game: ❌ NO ({running_count} model(s) running)",
                    fg="#ff6b6b"
                )
        
        # Update running models list
        self.models_listbox.delete(0, tk.END)
        running_models = status.get("running_models", [])
        if running_models:
            for model in running_models:
                name = model.get("name", "unknown")
                model_type = model.get("type", "text")
                idle_seconds = model.get("idle_seconds")
                
                if idle_seconds is not None:
                    idle_min = idle_seconds // 60
                    idle_sec = idle_seconds % 60
                    idle_str = f"{idle_min}m {idle_sec}s idle"
                else:
                    idle_str = "active"
                
                self.models_listbox.insert(
                    tk.END,
                    f"{name} ({model_type}) - {idle_str}"
                )
        else:
            self.models_listbox.insert(0, "(no models running)")
        
        # Enable buttons
        self.gaming_mode_button.config(state=tk.NORMAL)
        self.stop_all_button.config(state=tk.NORMAL)
    
    def toggle_gaming_mode(self):
        """Toggle gaming mode on/off."""
        if self.status_data is None:
            messagebox.showerror("Error", "Cannot connect to manager")
            return
        
        current_mode = self.status_data.get("gaming_mode", False)
        new_mode = not current_mode
        
        def toggle():
            try:
                response = requests.post(
                    f"{MANAGER_URL}/gaming-mode",
                    json={"enable": new_mode},
                    timeout=5
                )
                response.raise_for_status()
                self.root.after(0, lambda: self.refresh_status())
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror(
                    "Error",
                    f"Failed to toggle gaming mode:\n{str(e)}"
                ))
        
        thread = threading.Thread(target=toggle, daemon=True)
        thread.start()
    
    def stop_all_models(self):
        """Stop all running models."""
        if self.status_data is None:
            messagebox.showerror("Error", "Cannot connect to manager")
            return
        
        # Confirm action
        if not messagebox.askyesno(
            "Confirm",
            "Stop all running models? This will free up GPU memory."
        ):
            return
        
        def stop():
            try:
                response = requests.post(
                    f"{MANAGER_URL}/stop-all",
                    timeout=10
                )
                response.raise_for_status()
                result = response.json()
                self.root.after(0, lambda: self.on_stop_complete(result))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror(
                    "Error",
                    f"Failed to stop models:\n{str(e)}"
                ))
        
        thread = threading.Thread(target=stop, daemon=True)
        thread.start()
    
    def on_stop_complete(self, result: Dict[str, Any]):
        """Handle stop-all completion."""
        stopped = result.get("stopped", [])
        failed = result.get("failed", [])
        
        if failed:
            messagebox.showwarning(
                "Partial Success",
                f"Stopped {len(stopped)} model(s).\n"
                f"Failed to stop {len(failed)} model(s)."
            )
        else:
            messagebox.showinfo(
                "Success",
                f"Stopped {len(stopped)} model(s) successfully."
            )
        
        self.refresh_status()
    
    def schedule_refresh(self):
        """Schedule next auto-refresh."""
        self.root.after(REFRESH_INTERVAL * 1000, self.schedule_refresh)
        self.refresh_status()
    
    def on_closing(self):
        """Handle window close."""
        self.root.destroy()


def main():
    root = tk.Tk()
    
    # Configure dark theme colors
    root.configure(bg="#1e1e1e")
    
    app = GamingModeGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

