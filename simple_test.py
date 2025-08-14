"""
Simple test to validate the method signature and import
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.core.enhanced_vector_store import UserVectorStore
    import inspect
    
    # Check if method exists
    if hasattr(UserVectorStore, 'get_total_document_count'):
        print("[OK] get_total_document_count method exists")
        
        # Check method signature
        sig = inspect.signature(UserVectorStore.get_total_document_count)
        print(f"[OK] Method signature: {sig}")
        
        print("[SUCCESS] Method is properly defined")
    else:
        print("[ERROR] get_total_document_count method not found")
        
except Exception as e:
    print(f"[ERROR] Import or inspection failed: {e}")
    import traceback
    traceback.print_exc()
