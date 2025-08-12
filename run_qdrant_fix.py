"""
Quick fix for the Qdrant index error
Run this script to fix the user_id index issue
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fix_qdrant_indexes import fix_qdrant_indexes, diagnose_qdrant_issues

if __name__ == "__main__":
    print("🔧 Zenith Qdrant Index Fix")
    print("=" * 30)
    
    # First diagnose the issue
    print("\n1. Diagnosing current state...")
    diagnose_qdrant_issues()
    
    # Then fix it
    print("\n2. Applying fix...")
    success = fix_qdrant_indexes()
    
    if success:
        print("\n✅ Fix applied successfully!")
        print("\n💡 You can now use the application without the index error.")
    else:
        print("\n❌ Fix failed. You may need to rebuild the collection.")
        print("\n🚨 To rebuild (WARNING: deletes all documents):")
        print("   python fix_qdrant_indexes.py --rebuild")
