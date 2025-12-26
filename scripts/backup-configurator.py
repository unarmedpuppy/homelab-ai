#!/usr/bin/env python3
"""
Backup Configurator - Surgical Backup Selection Tool
Interactive TUI for selecting which directories to backup from jenquist-cloud
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Set
import argparse

@dataclass
class BackupConfig:
    """Configuration for backup selection"""
    name: str
    source_paths: List[str]
    exclude_patterns: List[str]
    priority: str  # high, medium, low
    enabled: bool
    rclone_remote: str = "b2-encrypted:"

class BackupConfigurator:
    def __init__(self, base_path: str = "/jenquist-cloud"):
        self.base_path = Path(base_path)
        self.selected_paths: Set[str] = set()
        self.configs: List[BackupConfig] = []
        self.config_file = Path.home() / ".backup-configs.json"
        
    def log_error(self, message: str):
        """Print error message"""
        print(f"ERROR: {message}")
    
    def log_success(self, message: str):
        """Print success message"""
        print(f"✓ {message}")
    
    def log_info(self, message: str):
        """Print info message"""
        print(f"ℹ {message}")

    def get_directory_size(self, path: Path) -> str:
        """Get human readable directory size"""
        try:
            if not path.exists():
                return "0B"
            
            # Use du command for accurate size
            result = subprocess.run(
                ['du', '-sh', str(path)], 
                capture_output=True, 
                text=True
            )
            if result.returncode == 0:
                size = result.stdout.split()[0]
                return size
            else:
                return "Unknown"
        except Exception:
            return "Unknown"

    def display_directory_structure(self, path: Path, max_depth: int = 3, current_depth: int = 0, prefix: str = ""):
        """Display directory structure in basic text"""
        if current_depth >= max_depth:
            return
            
        try:
            items = sorted([p for p in path.iterdir() if p.is_dir() and not p.name.startswith('.')])
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                size = self.get_directory_size(item)
                connector = "└── " if is_last else "├── "
                print(f"{prefix}{connector}{item.name} ({size})")
                
                if current_depth < max_depth - 1:
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    self.display_directory_structure(item, max_depth, current_depth + 1, next_prefix)
        except PermissionError:
            print(f"{prefix}└── [Permission denied]")

    def interactive_selection(self):
        """Interactive path selection"""
        print("\n" + "="*60)
        print("INTERACTIVE BACKUP SELECTION")
        print("="*60)
        
        self._selection_menu()

    def _selection_menu(self):
        """Main selection menu"""
        while True:
            print("\nOPTIONS:")
            print("1. Add path manually")
            print("2. View selected paths") 
            print("3. Remove selected path")
            print("4. Configure exclude patterns")
            print("5. Save configuration")
            print("6. Generate rclone command")
            print("7. Exit")
            
            choice = input("Select option [1-7]: ").strip()
            
            if choice == "1":
                self._manual_path_add()
            elif choice == "2":
                self._show_selections()
            elif choice == "3":
                self._remove_selection()
            elif choice == "4":
                self._configure_excludes()
            elif choice == "5":
                self._save_config()
            elif choice == "6":
                self._generate_rclone_command()
            elif choice == "7":
                break
            else:
                print("Invalid option")

    def _manual_path_add(self):
        """Add path manually"""
        path_str = input("Enter path to backup (relative to /jenquist-cloud): ")
        
        if not path_str:
            return
            
        full_path = self.base_path / path_str
        if full_path.exists() and full_path.is_dir():
            self.selected_paths.add(str(full_path))
            size = self.get_directory_size(full_path)
            self.log_success(f"Added: {full_path} ({size})")
        else:
            self.log_error(f"Path does not exist: {full_path}")

    def _browse_selection(self):
        """Browse and select directories"""
        self.log_info("Available directories:")
        
        try:
            for item in sorted(self.base_path.iterdir()):
                if item.is_dir() and not item.name.startswith('.'):
                    size = self.get_directory_size(item)
                    select = input(f"Select {item.name}? ({size}) [y/N]: ").lower() == 'y'
                    if select:
                        self.selected_paths.add(str(item))
                        self.log_success(f"Selected: {item}")
        except PermissionError:
            self.log_error("Permission denied scanning base directory")

    def _show_selections(self):
        """Show currently selected paths"""
        if not self.selected_paths:
            self.log_info("No paths selected")
            return
            
        print("\nSELECTED PATHS:")
        print("-" * 60)
        total_size = 0
        for path in sorted(self.selected_paths):
            size = self.get_directory_size(Path(path))
            print(f"{path} ({size})")
        
        print(f"\nTotal selected: {len(self.selected_paths)} paths")

    def _remove_selection(self):
        """Remove a selected path"""
        if not self.selected_paths:
            self.log_info("No paths selected")
            return
            
        paths_list = sorted(self.selected_paths)
        print("\nSelect path to remove:")
        for i, path in enumerate(paths_list):
            print(f"{i+1}. {path}")
        
        try:
            idx = int(input("Enter number: ")) - 1
            if 0 <= idx < len(paths_list):
                removed = paths_list[idx]
                self.selected_paths.remove(removed)
                self.log_success(f"Removed: {removed}")
            else:
                print("Invalid selection")
        except (ValueError, IndexError):
            print("Invalid selection")

    def _configure_excludes(self):
        """Configure exclude patterns"""
        default_excludes = [
            "*.tmp", "*.temp", ".DS_Store", "Thumbs.db",
            ".cache/", "tmp/", "temp/", ".Trash/"
        ]
        
        self.log_info("Current exclude patterns:")
        for pattern in default_excludes:
            print(f"  - {pattern}")
        
        add = input("Add custom exclude pattern? [y/N]: ").lower() == 'y'
        if add:
            pattern = input("Enter pattern: ")
            if pattern:
                default_excludes.append(pattern)
                self.log_success(f"Added pattern: {pattern}")

    def _save_config(self):
        """Save current configuration"""
        if not self.selected_paths:
            self.log_error("No paths selected to save")
            return
            
        config_name = input("Enter configuration name: ")
        if not config_name:
            config_name = "backup-config"
        
        config = BackupConfig(
            name=config_name,
            source_paths=list(self.selected_paths),
            exclude_patterns=["*.tmp", "*.temp", ".DS_Store"],
            priority="medium",
            enabled=True
        )
        
        self.configs.append(config)
        self._save_configs_to_file()
        self.log_success(f"Configuration '{config_name}' saved")

    def _save_configs_to_file(self):
        """Save configurations to JSON file"""
        configs_data = [asdict(config) for config in self.configs]
        try:
            with open(self.config_file, 'w') as f:
                json.dump(configs_data, f, indent=2)
        except Exception as e:
            self.log_error(f"Failed to save configs: {e}")

    def _generate_rclone_command(self):
        """Generate rclone command for selected paths"""
        if not self.selected_paths:
            self.log_error("No paths selected")
            return
            
        print("\n" + "="*60)
        print("GENERATED RCLONE COMMAND")
        print("="*60)
        
        # Create include file for selected paths
        config_name = self.configs[0].name if self.configs else 'backup'
        include_file = Path.home() / f".rclone-include-{config_name}.txt"
        
        with open(include_file, 'w') as f:
            for path in sorted(self.selected_paths):
                # Convert absolute path to relative for rclone
                rel_path = str(Path(path).relative_to(self.base_path))
                f.write(f"+ {rel_path}/**\n")
            f.write("- *")  # Exclude everything else
        
        exclude_patterns = ["*.tmp", "*.temp", ".DS_Store", ".cache/", "tmp/"]
        
        cmd_parts = [
            "rclone sync",
            str(self.base_path),
            "b2-encrypted:",
            "--include-from", str(include_file),
        ]
        
        for pattern in exclude_patterns:
            cmd_parts.extend(["--exclude", pattern])
        
        cmd_parts.extend([
            "--transfers", "4",
            "--checkers", "8", 
            "--progress",
            "--stats", "1m",
            "--stats-one-line"
        ])
        
        print("Generated command:")
        print(" ".join(cmd_parts))
        print(f"\nInclude file: {include_file}")
        print("\nTo test (dry run):")
        print(" ".join(cmd_parts + ["--dry-run"]))
        
        # Calculate estimated total size
        print("\nEstimated backup size:")
        total_size = 0
        for path in sorted(self.selected_paths):
            size = self.get_directory_size(Path(path))
            print(f"  {path}: {size}")
        
        run_now = input("\nExecute this command now? [y/N]: ").lower() == 'y'
        if run_now:
            self._execute_rclone_command(cmd_parts)

    def _execute_rclone_command(self, cmd_parts):
        """Execute rclone command"""
        try:
            self.log_info("Executing rclone command...")
            result = subprocess.run(cmd_parts, check=True)
            self.log_success("Backup completed successfully!")
        except subprocess.CalledProcessError as e:
            self.log_error(f"Backup failed: {e}")
        except FileNotFoundError:
            self.log_error("rclone not found. Install with: sudo apt install rclone")

    def load_existing_configs(self):
        """Load existing configurations"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    configs_data = json.load(f)
                    self.configs = [BackupConfig(**config) for config in configs_data]
                self.log_info(f"Loaded {len(self.configs)} existing configurations")
            except Exception as e:
                self.log_error(f"Failed to load configs: {e}")

    def run(self):
        """Main run method"""
        print("Backup Configurator - Surgical Backup Selection Tool")
        print("=" * 60)
        print("This tool helps you create surgical backup selections for jenquist-cloud")
        print("Current setup backs up ENTIRE /jenquist-cloud to encrypted Backblaze B2")
        print("Use this tool to reduce costs by backing up only what you need")
        print("=" * 60)
        
        # Load existing configurations
        self.load_existing_configs()
        
        # Display directory structure
        print(f"\nJENQUIST-CLOUD STRUCTURE (at {self.base_path}):")
        if not self.base_path.exists():
            self.log_error(f"Base path {self.base_path} does not exist!")
            return
        
        self.display_directory_structure(self.base_path)
            
        # Interactive selection
        self.interactive_selection()

def main():
    parser = argparse.ArgumentParser(description="Interactive backup configuration tool")
    parser.add_argument("--base-path", default="/jenquist-cloud", 
                       help="Base path to scan (default: /jenquist-cloud)")
    parser.add_argument("--remote", default="b2-encrypted:",
                       help="rclone remote destination")
    
    args = parser.parse_args()
    
    configurator = BackupConfigurator(args.base_path)
    configurator.run()

if __name__ == "__main__":
    main()