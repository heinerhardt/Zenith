#!/usr/bin/env python3
"""
Quick fix for vector dimension mismatch in Zenith
This will recreate the collection with the correct dimensions for Ollama embeddings
"""

import sys
import os
from pathlib import Path

def main():
    try:
        print("🔧 Zenith Vector Dimension Fix")
        print("=" * 50)
        
        # Set up path
        zenith_root = Path(__file__).parent
        os.chdir(zenith_root)
        src_path = zenith_root / "src"
        sys.path.insert(0, str(src_path))
        
        # Import after path setup
        from core.enhanced_vector_store import EnhancedVectorStore
        from core.enhanced_settings_manager import get_enhanced_settings_manager
        
        # Get current settings
        settings_manager = get_enhanced_settings_manager()
        current_settings = settings_manager.get_current_settings()
        
        print(f"Current embedding provider: {settings_manager.get_effective_embedding_provider()}")
        print(f"Ollama embedding model: {current_settings.ollama_embedding_model}")
        
        # Create vector store instance
        vector_store = EnhancedVectorStore()
        
        # Check dimension compatibility
        print("\n🔍 Checking dimension compatibility...")
        compatible, message, collection_dim, provider_dim = vector_store.check_dimension_compatibility()
        
        print(f"Status: {message}")
        if not compatible:
            print(f"Collection expects: {collection_dim} dimensions")
            print(f"Provider produces: {provider_dim} dimensions")
            
            print("\n🔄 Fixing dimension mismatch...")
            success, fix_message = vector_store.fix_dimension_mismatch()
            
            if success:
                print(f"✅ {fix_message}")
                print("\n📝 Next steps:")
                print("1. Restart your Streamlit application")
                print("2. Re-upload your PDF documents")
                print("3. Your searches should now work correctly")
            else:
                print(f"❌ {fix_message}")
                return 1
        else:
            print("✅ No dimension mismatch found!")
            
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    print(f"\n{'=' * 50}")
    if exit_code == 0:
        print("🎉 Vector dimension fix completed successfully!")
    else:
        print("💥 Vector dimension fix failed!")
    
    input("Press Enter to continue...")
    sys.exit(exit_code)
