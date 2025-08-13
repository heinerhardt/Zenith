#!/usr/bin/env python3
"""
Emergency Settings Fix - No imports needed!
This script directly modifies your .env file and optionally updates Qdrant
"""

import os
import requests
import json
from pathlib import Path

def load_env_file():
    """Load current .env file"""
    env_path = Path(__file__).parent / ".env"
    env_vars = {}
    
    try:
        with open(env_path, 'r') as f:
            content = f.read()
            
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                value = value.strip('"\'')
                env_vars[key] = value
        
        return env_vars, content
    except Exception as e:
        print(f"Warning: Could not load .env file: {e}")
        return {}, ""

def update_env_file(updates):
    """Update .env file with new values"""
    env_path = Path(__file__).parent / ".env"
    
    try:
        # Read current content
        env_vars, content = load_env_file()
        
        # Create backup
        backup_path = Path(__file__).parent / ".env.backup"
        with open(backup_path, 'w') as f:
            f.write(content)
        print(f"✅ Backup created: {backup_path}")
        
        # Update values
        lines = content.split('\n')
        updated_lines = []
        updated_keys = set()
        
        for line in lines:
            if '=' in line and not line.strip().startswith('#'):
                key = line.split('=', 1)[0].strip()
                if key in updates:
                    # Update existing line
                    value = updates[key]
                    if ' ' in str(value) or any(c in str(value) for c in ['"', "'"]):
                        updated_lines.append(f'{key}="{value}"')
                    else:
                        updated_lines.append(f'{key}={value}')
                    updated_keys.add(key)
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        
        # Add new keys that weren't found
        for key, value in updates.items():
            if key not in updated_keys:
                if ' ' in str(value) or any(c in str(value) for c in ['"', "'"]):
                    updated_lines.append(f'{key}="{value}"')
                else:
                    updated_lines.append(f'{key}={value}')
        
        # Write updated content
        with open(env_path, 'w') as f:
            f.write('\n'.join(updated_lines))
        
        print(f"✅ Updated .env file")
        return True
        
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
        return False

def main():
    print("🚨 Emergency Settings Fix")
    print("=" * 50)
    
    # Load current .env
    env_vars, _ = load_env_file()
    
    print("📋 Current .env settings:")
    relevant_keys = [
        'OLLAMA_ENABLED', 'CHAT_PROVIDER', 'EMBEDDING_PROVIDER',
        'OLLAMA_BASE_URL', 'OLLAMA_CHAT_MODEL', 'OLLAMA_EMBEDDING_MODEL',
        'OPENAI_API_KEY'
    ]
    
    for key in relevant_keys:
        value = env_vars.get(key, 'Not set')
        if 'API_KEY' in key and value != 'Not set':
            value = value[:10] + '...' if len(value) > 10 else value
        print(f"  {key}: {value}")
    
    print(f"\n🎯 Quick Fix Options:")
    print(f"1. Enable Ollama as default")
    print(f"2. Set OpenAI as default") 
    print(f"3. Custom configuration")
    print(f"4. Just fix hanging issue (keep current providers)")
    print(f"5. Exit")
    
    try:
        choice = input(f"\nSelect option (1-5): ").strip()
        
        updates = {}
        
        if choice == '1':
            print(f"\n🦙 Configuring Ollama as default...")
            updates = {
                'OLLAMA_ENABLED': 'True',
                'CHAT_PROVIDER': 'ollama',
                'EMBEDDING_PROVIDER': 'ollama'
            }
            
        elif choice == '2':
            print(f"\n🤖 Configuring OpenAI as default...")
            updates = {
                'OLLAMA_ENABLED': 'False',
                'CHAT_PROVIDER': 'openai',
                'EMBEDDING_PROVIDER': 'openai'
            }
            
        elif choice == '3':
            print(f"\n🛠️ Custom configuration...")
            
            ollama_enabled = input("Enable Ollama? (y/n): ").lower().startswith('y')
            chat_provider = input("Chat provider (openai/ollama): ").strip()
            embedding_provider = input("Embedding provider (openai/ollama): ").strip()
            
            updates = {
                'OLLAMA_ENABLED': 'True' if ollama_enabled else 'False',
                'CHAT_PROVIDER': chat_provider if chat_provider in ['openai', 'ollama'] else 'openai',
                'EMBEDDING_PROVIDER': embedding_provider if embedding_provider in ['openai', 'ollama'] else 'openai'
            }
            
        elif choice == '4':
            print(f"\n🔧 Just fixing hanging issue...")
            # No changes to providers, just ensure clean state
            updates = {}
            
        elif choice == '5':
            print(f"👋 Exiting...")
            return 0
            
        else:
            print(f"❌ Invalid choice")
            return 1
        
        # Apply updates
        if updates:
            success = update_env_file(updates)
            if not success:
                return 1
            
            print(f"\n✅ Updated .env file with:")
            for key, value in updates.items():
                print(f"  {key} = {value}")
        
        print(f"\n📝 Next steps:")
        print(f"1. 🔄 Restart your Streamlit application")
        print(f"2. 🧪 Test that settings save without hanging")
        print(f"3. 🔍 Use 'Force Reinitialize' to test providers")
        print(f"4. 📄 Re-upload documents if you switched embedding providers")
        
        # Offer to test Qdrant connection
        test_qdrant = input(f"\nTest Qdrant connection? (y/n): ").lower().startswith('y')
        
        if test_qdrant:
            print(f"\n🔌 Testing Qdrant connection...")
            
            qdrant_url = env_vars.get('QDRANT_URL')
            qdrant_api_key = env_vars.get('QDRANT_API_KEY')
            
            if qdrant_url and qdrant_api_key:
                try:
                    headers = {"api-key": qdrant_api_key}
                    response = requests.get(f"{qdrant_url.rstrip('/')}/health", headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        print(f"✅ Qdrant connection successful!")
                    else:
                        print(f"⚠️ Qdrant responded with status: {response.status_code}")
                        
                except Exception as e:
                    print(f"❌ Qdrant connection failed: {e}")
            else:
                print(f"ℹ️ Qdrant configuration not found in .env")
        
        return 0
        
    except KeyboardInterrupt:
        print(f"\n\n👋 Cancelled by user")
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    print(f"\n{'=' * 50}")
    if exit_code == 0:
        print("🎉 Emergency fix completed!")
    else:
        print("💥 Emergency fix failed!")
    
    input("Press Enter to exit...")
