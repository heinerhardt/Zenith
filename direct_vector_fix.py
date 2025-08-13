#!/usr/bin/env python3
"""
Direct Vector Dimension Fix - No imports needed!
This script connects directly to Qdrant and fixes the dimension mismatch
"""

import os
import requests
import json
from pathlib import Path

def load_env_file():
    """Load .env file manually"""
    env_path = Path(__file__).parent / ".env"
    env_vars = {}
    
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"\'')
                    env_vars[key] = value
                    os.environ[key] = value
    except Exception as e:
        print(f"Warning: Could not load .env file: {e}")
    
    return env_vars

def main():
    print("🔧 Zenith Vector Dimension Fix Tool")
    print("=" * 50)
    
    # Load environment variables
    env_vars = load_env_file()
    
    # Get configuration
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    collection_name = os.getenv("QDRANT_COLLECTION_NAME", "zenith_documents")
    ollama_model = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
    
    print(f"📋 Configuration:")
    print(f"   Qdrant URL: {qdrant_url}")
    print(f"   Collection: {collection_name}")
    print(f"   Ollama Model: {ollama_model}")
    
    # Set up headers
    headers = {"Content-Type": "application/json"}
    if qdrant_api_key:
        headers["api-key"] = qdrant_api_key
    
    try:
        # Test Qdrant connection
        print(f"\n🔌 Testing connection to Qdrant...")
        health_url = f"{qdrant_url.rstrip('/')}/health"
        response = requests.get(health_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ Qdrant is healthy!")
        else:
            print(f"⚠️ Qdrant health check returned: {response.status_code}")
        
        # Get collection info
        print(f"\n📊 Checking collection '{collection_name}'...")
        collection_url = f"{qdrant_url.rstrip('/')}/collections/{collection_name}"
        response = requests.get(collection_url, headers=headers)
        
        if response.status_code == 404:
            print(f"ℹ️ Collection '{collection_name}' does not exist yet.")
            print("It will be created when you upload documents.")
            return 0
        elif response.status_code != 200:
            print(f"❌ Error getting collection info: {response.status_code}")
            print(f"Response: {response.text}")
            return 1
        
        collection_info = response.json()
        current_dim = collection_info["result"]["config"]["params"]["vectors"]["size"]
        points_count = collection_info["result"]["points_count"]
        
        print(f"   Current dimensions: {current_dim}")
        print(f"   Documents stored: {points_count}")
        
        # Determine correct dimensions for Ollama
        ollama_dimensions = {
            "nomic-embed-text": 768,
            "mxbai-embed-large": 1024,
            "all-minilm": 384,
            "all-MiniLM-L6-v2": 384,
        }
        
        correct_dim = ollama_dimensions.get(ollama_model, 1024)
        print(f"   Required dimensions: {correct_dim}")
        
        if current_dim == correct_dim:
            print("✅ Collection dimensions are already correct!")
            return 0
        
        print(f"\n❌ Dimension mismatch detected!")
        print(f"   Collection has: {current_dim} dimensions")
        print(f"   Ollama needs: {correct_dim} dimensions")
        
        if points_count > 0:
            print(f"\n⚠️  WARNING: This will delete {points_count} documents!")
        
        # Ask for confirmation
        response = input("\nDo you want to recreate the collection? (y/N): ")
        if response.lower() != 'y':
            print("❌ Operation cancelled.")
            return 0
        
        print(f"\n🗑️ Deleting collection '{collection_name}'...")
        delete_response = requests.delete(collection_url, headers=headers)
        
        if delete_response.status_code in [200, 404]:
            print("✅ Collection deleted successfully!")
        else:
            print(f"❌ Error deleting collection: {delete_response.status_code}")
            return 1
        
        print(f"\n✨ Creating new collection with {correct_dim} dimensions...")
        
        create_data = {
            "vectors": {
                "size": correct_dim,
                "distance": "Cosine"
            }
        }
        
        create_response = requests.put(
            collection_url, 
            headers=headers, 
            data=json.dumps(create_data)
        )
        
        if create_response.status_code == 200:
            print("✅ Collection created successfully!")
            
            # Verify the new collection
            verify_response = requests.get(collection_url, headers=headers)
            if verify_response.status_code == 200:
                new_info = verify_response.json()
                new_dim = new_info["result"]["config"]["params"]["vectors"]["size"]
                
                if new_dim == correct_dim:
                    print(f"🎉 Verification successful! Collection now has {new_dim} dimensions.")
                else:
                    print(f"⚠️ Verification warning: Expected {correct_dim}, got {new_dim}")
            
            print(f"\n✅ Fix completed successfully!")
            print(f"\n📝 Next steps:")
            print(f"   1. Restart your Streamlit application")
            print(f"   2. Re-upload your PDF documents")
            print(f"   3. Test searches - they should work now!")
            
            return 0
        else:
            print(f"❌ Error creating collection: {create_response.status_code}")
            print(f"Response: {create_response.text}")
            return 1
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to Qdrant at {qdrant_url}")
        print("   Make sure Qdrant is running and the URL is correct.")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    print(f"\n{'=' * 50}")
    if exit_code == 0:
        print("🎉 Vector dimension fix completed!")
    else:
        print("💥 Vector dimension fix failed!")
    
    input("Press Enter to exit...")
