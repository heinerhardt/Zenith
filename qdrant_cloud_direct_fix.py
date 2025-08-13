#!/usr/bin/env python3
"""
Direct fix for Qdrant Cloud vector dimensions
Uses your specific Qdrant Cloud configuration
"""

import requests
import json

def main():
    print("🔧 Qdrant Cloud Vector Dimension Fix")
    print("=" * 50)
    
    # Your specific configuration
    qdrant_url = "https://ff544b2f-9868-490a-806a-f499c01c3b2b.us-east4-0.gcp.cloud.qdrant.io"
    qdrant_api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.k1rigQDkZo9G4gIkWcmIBnDt96Er6rhV7nETUvQOcm8"
    collection_name = "zenith_documents"
    
    headers = {
        "Content-Type": "application/json",
        "api-key": qdrant_api_key
    }
    
    print(f"Qdrant URL: {qdrant_url}")
    print(f"Collection: {collection_name}")
    print(f"Target dimensions: 768 (nomic-embed-text)")
    
    try:
        # Test connection
        print(f"\n🔌 Testing connection...")
        health_resp = requests.get(f"{qdrant_url}/health", headers=headers, timeout=10)
        
        if health_resp.status_code == 200:
            print("✅ Connected to Qdrant Cloud!")
        else:
            print(f"❌ Health check failed: {health_resp.status_code}")
            return 1
        
        # Check collection
        print(f"\n📊 Checking collection '{collection_name}'...")
        collection_url = f"{qdrant_url}/collections/{collection_name}"
        
        resp = requests.get(collection_url, headers=headers, timeout=10)
        
        if resp.status_code == 404:
            print("ℹ️ Collection doesn't exist yet - will be created when you upload documents")
            return 0
        elif resp.status_code != 200:
            print(f"❌ Error getting collection: {resp.status_code}")
            print(resp.text)
            return 1
        
        # Analyze collection
        data = resp.json()
        current_dim = data["result"]["config"]["params"]["vectors"]["size"]
        points_count = data["result"]["points_count"]
        
        print(f"Current dimensions: {current_dim}")
        print(f"Documents stored: {points_count}")
        print(f"Required dimensions: 768")
        
        if current_dim == 768:
            print("✅ Collection dimensions are already correct!")
            return 0
        
        print(f"\n❌ Dimension mismatch detected!")
        print(f"Collection has {current_dim} dimensions, but nomic-embed-text needs 768")
        
        if points_count > 0:
            print(f"\n⚠️  WARNING: This will delete {points_count} documents!")
        
        response = input("\nProceed with fix? (y/N): ")
        if response.lower() != 'y':
            print("❌ Operation cancelled")
            return 0
        
        # Delete collection
        print(f"\n🗑️ Deleting collection...")
        delete_resp = requests.delete(collection_url, headers=headers, timeout=30)
        
        if delete_resp.status_code in [200, 404]:
            print("✅ Collection deleted!")
        else:
            print(f"❌ Delete failed: {delete_resp.status_code}")
            print(delete_resp.text)
            return 1
        
        # Create new collection
        print(f"\n✨ Creating new collection with 768 dimensions...")
        
        create_data = {
            "vectors": {
                "size": 768,
                "distance": "Cosine"
            }
        }
        
        create_resp = requests.put(
            collection_url,
            headers=headers,
            json=create_data,
            timeout=30
        )
        
        if create_resp.status_code == 200:
            print("✅ Collection created successfully!")
            
            # Verify the fix
            print(f"\n🔍 Verifying fix...")
            verify_resp = requests.get(collection_url, headers=headers, timeout=10)
            
            if verify_resp.status_code == 200:
                verify_data = verify_resp.json()
                new_dim = verify_data["result"]["config"]["params"]["vectors"]["size"]
                
                if new_dim == 768:
                    print(f"🎉 SUCCESS! Collection now has {new_dim} dimensions")
                    print(f"\n📝 Next steps:")
                    print(f"   1. Restart your Streamlit application")
                    print(f"   2. Re-upload your PDF documents")
                    print(f"   3. Test document searches")
                    return 0
                else:
                    print(f"⚠️ Verification issue: expected 768, got {new_dim}")
                    return 1
            else:
                print(f"❌ Could not verify fix: {verify_resp.status_code}")
                return 1
        else:
            print(f"❌ Failed to create collection: {create_resp.status_code}")
            print(create_resp.text)
            return 1
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to Qdrant Cloud")
        print(f"Check your internet connection and API key")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    print(f"\n{'=' * 50}")
    if exit_code == 0:
        print("🎉 Vector dimension fix completed!")
    else:
        print("💥 Vector dimension fix failed!")
    
    input("Press Enter to exit...")
