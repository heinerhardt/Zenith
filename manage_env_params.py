#!/usr/bin/env python3
"""
Enterprise Environment Parameter Management System
Allows dynamic addition/editing of environment parameters
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

class EnterpriseEnvManager:
    """Manage enterprise environment parameters dynamically"""
    
    def __init__(self, env_file_path: str = ".env"):
        self.env_file = Path(env_file_path)
        self.sections = {}
        self.load_env_file()
    
    def load_env_file(self):
        """Load and parse the .env file by sections"""
        if not self.env_file.exists():
            print(f"❌ .env file not found at: {self.env_file.resolve()}")
            return
        
        current_section = "GENERAL"
        self.sections[current_section] = []
        
        with open(self.env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.rstrip()
                
                if line.startswith("# ============="):
                    # New section header
                    continue
                elif line.startswith("# ") and not line.startswith("# "):
                    # Section title
                    section_name = line[2:].strip()
                    if section_name and "CONFIGURATION" in section_name.upper():
                        current_section = section_name
                        self.sections[current_section] = []
                else:
                    self.sections[current_section].append(line)
    
    def list_parameters(self):
        """List all current environment parameters by section"""
        print("🔧 Current Environment Parameters by Section:")
        print("=" * 60)
        
        for section, lines in self.sections.items():
            if not lines or all(not line.strip() or line.startswith('#') for line in lines):
                continue
                
            print(f"\n📋 {section}")
            print("-" * 40)
            
            for line in lines:
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Mask sensitive values
                    if any(sensitive in key.upper() for sensitive in ['KEY', 'SECRET', 'PASSWORD', 'TOKEN']):
                        if value and value != 'your-' in value:
                            value = value[:8] + "***" + value[-4:]
                    
                    print(f"  ✅ {key}: {value}")
    
    def add_parameter(self, section: str, key: str, value: str, comment: str = ""):
        """Add a new parameter to a specific section"""
        print(f"➕ Adding parameter: {key} = {value}")
        
        if section not in self.sections:
            print(f"❌ Section '{section}' not found. Available sections:")
            for s in self.sections.keys():
                print(f"   - {s}")
            return False
        
        # Format new parameter
        new_param = f"{key}={value}"
        if comment:
            new_param = f"# {comment}\n{new_param}"
        
        self.sections[section].append(new_param)
        print(f"✅ Added {key} to {section} section")
        return True
    
    def update_parameter(self, key: str, new_value: str) -> bool:
        """Update an existing parameter value"""
        print(f"🔄 Updating parameter: {key} = {new_value}")
        
        for section, lines in self.sections.items():
            for i, line in enumerate(lines):
                if '=' in line and not line.startswith('#'):
                    param_key = line.split('=', 1)[0].strip()
                    if param_key == key:
                        self.sections[section][i] = f"{key}={new_value}"
                        print(f"✅ Updated {key} in {section} section")
                        return True
        
        print(f"❌ Parameter {key} not found")
        return False
    
    def save_env_file(self):
        """Save the updated environment file"""
        print(f"💾 Saving changes to {self.env_file.resolve()}")
        
        try:
            with open(self.env_file, 'w', encoding='utf-8') as f:
                for section, lines in self.sections.items():
                    if section != "GENERAL":
                        f.write(f"\n# =================================================================")\n                        f.write(f"# {section}\n")
                        f.write(f"# =================================================================\n")
                    
                    for line in lines:
                        f.write(f"{line}\n")
            
            print("✅ Environment file updated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error saving file: {e}")
            return False
    
    def create_parameter_template(self, config_class_path: str):
        """Generate parameter template from config class"""
        print(f"📋 Generating parameter template from: {config_class_path}")
        
        try:
            # Import the config module dynamically
            import importlib.util
            spec = importlib.util.spec_from_file_location("config", config_class_path)
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)
            
            # Get the Settings class
            settings_class = getattr(config_module, 'Settings')
            
            # Get field information
            if hasattr(settings_class, '__fields__'):
                print("📋 Missing parameters that could be added:")
                
                for field_name, field_info in settings_class.__fields__.items():
                    env_name = field_name.upper()
                    default_value = field_info.default
                    
                    # Check if parameter exists
                    exists = False
                    for section, lines in self.sections.items():
                        for line in lines:
                            if '=' in line and not line.startswith('#'):
                                if line.split('=', 1)[0].strip() == env_name:
                                    exists = True
                                    break
                        if exists:
                            break
                    
                    if not exists:
                        print(f"  ➕ {env_name}: {default_value} (from {field_name})")
            
        except Exception as e:
            print(f"❌ Error analyzing config class: {e}")

def main():
    """Main CLI interface for parameter management"""
    print("🚀 Enterprise Environment Parameter Manager")
    
    manager = EnterpriseEnvManager()
    
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python manage_env_params.py list                     # List all parameters")
        print("  python manage_env_params.py add SECTION KEY VALUE    # Add new parameter")
        print("  python manage_env_params.py update KEY VALUE         # Update existing parameter")
        print("  python manage_env_params.py template                 # Generate missing parameter template")
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        manager.list_parameters()
        
    elif command == "add" and len(sys.argv) >= 5:
        section = sys.argv[2]
        key = sys.argv[3]
        value = sys.argv[4]
        comment = " ".join(sys.argv[5:]) if len(sys.argv) > 5 else ""
        
        if manager.add_parameter(section, key, value, comment):
            manager.save_env_file()
            
    elif command == "update" and len(sys.argv) >= 4:
        key = sys.argv[2]
        value = sys.argv[3]
        
        if manager.update_parameter(key, value):
            manager.save_env_file()
            
    elif command == "template":
        config_path = "src/core/config.py"
        if len(sys.argv) > 2:
            config_path = sys.argv[2]
        manager.create_parameter_template(config_path)
        
    else:
        print("❌ Invalid command or missing arguments")
        print("Use: python manage_env_params.py list")

if __name__ == "__main__":
    main()