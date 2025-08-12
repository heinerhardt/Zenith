"""
Fix for Qdrant index creation and user filtering issues
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.qdrant_manager import get_qdrant_client
from src.core.config import config
from src.utils.logger import get_logger
from qdrant_client.http import models

logger = get_logger(__name__)


def fix_qdrant_indexes():
    """
    Fix Qdrant collection indexes to resolve user_id filtering issues
    """
    logger.info("🔧 Starting Qdrant index fix...")
    
    try:
        # Get Qdrant manager
        qdrant_manager = get_qdrant_client()
        collection_name = config.qdrant_collection_name
        
        # Check if collection exists
        if not qdrant_manager.collection_exists(collection_name):
            logger.info(f"📁 Collection {collection_name} doesn't exist, creating it...")
            
            # Create collection with default embedding size
            success = qdrant_manager.create_collection(
                collection_name=collection_name,
                vector_size=1536,  # Default OpenAI embedding size
                distance=models.Distance.COSINE
            )
            
            if not success:
                raise Exception(f"Failed to create collection {collection_name}")
            
            logger.info(f"✅ Created collection {collection_name}")
        
        # Create/recreate necessary indexes
        logger.info("🔨 Creating/updating indexes...")
        
        # Create user_id index
        success_user = qdrant_manager.create_index(
            collection_name=collection_name,
            field_name="user_id",
            field_type="keyword"
        )
        
        # Create document_id index
        success_doc = qdrant_manager.create_index(
            collection_name=collection_name,
            field_name="document_id", 
            field_type="keyword"
        )
        
        # Create chunk_index index for sorting
        success_chunk = qdrant_manager.create_index(
            collection_name=collection_name,
            field_name="chunk_index",
            field_type="integer"
        )
        
        if success_user:
            logger.info("✅ Created user_id index")
        else:
            logger.warning("⚠️ Failed to create user_id index (may already exist)")
        
        if success_doc:
            logger.info("✅ Created document_id index")
        else:
            logger.warning("⚠️ Failed to create document_id index (may already exist)")
            
        if success_chunk:
            logger.info("✅ Created chunk_index index")
        else:
            logger.warning("⚠️ Failed to create chunk_index index (may already exist)")
        
        # Verify collection info
        info = qdrant_manager.get_collection_info(collection_name)
        if info:
            logger.info(f"📊 Collection info:")
            logger.info(f"   Points: {info.get('points_count', 0)}")
            logger.info(f"   Vectors: {info.get('vectors_count', 0)}")
            logger.info(f"   Status: {info.get('status', 'Unknown')}")
        
        # Test filtering capability
        logger.info("🧪 Testing user filtering...")
        test_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="user_id",
                    match=models.MatchValue(value="test_user")
                )
            ]
        )
        
        try:
            count = qdrant_manager.count_points(collection_name, test_filter)
            logger.info(f"✅ User filtering test successful (found {count} test documents)")
        except Exception as e:
            logger.error(f"❌ User filtering test failed: {e}")
            return False
        
        logger.info("🎉 Qdrant index fix completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Qdrant index fix failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def clean_and_rebuild_collection():
    """
    Nuclear option: Delete and recreate the collection with proper indexes
    """
    logger.warning("💥 NUCLEAR OPTION: Rebuilding collection from scratch...")
    logger.warning("🚨 This will DELETE ALL existing documents!")
    
    try:
        qdrant_manager = get_qdrant_client()
        collection_name = config.qdrant_collection_name
        
        # Delete existing collection
        if qdrant_manager.collection_exists(collection_name):
            logger.info(f"🗑️ Deleting existing collection {collection_name}...")
            qdrant_manager.delete_collection(collection_name)
        
        # Create new collection
        logger.info("🏗️ Creating new collection...")
        success = qdrant_manager.create_collection(
            collection_name=collection_name,
            vector_size=1536,  # Default for OpenAI
            distance=models.Distance.COSINE
        )
        
        if not success:
            raise Exception("Failed to create new collection")
        
        # Create all necessary indexes
        indexes = [
            ("user_id", "keyword"),
            ("document_id", "keyword"), 
            ("chunk_index", "integer"),
            ("filename", "keyword"),
            ("embedding_provider", "keyword")
        ]
        
        for field_name, field_type in indexes:
            qdrant_manager.create_index(
                collection_name=collection_name,
                field_name=field_name,
                field_type=field_type
            )
            logger.info(f"✅ Created {field_name} ({field_type}) index")
        
        logger.info("🎉 Collection rebuilt successfully!")
        logger.warning("📝 Note: You'll need to re-upload your documents")
        return True
        
    except Exception as e:
        logger.error(f"❌ Collection rebuild failed: {e}")
        return False


def diagnose_qdrant_issues():
    """
    Diagnose Qdrant configuration and index issues
    """
    logger.info("🔍 Diagnosing Qdrant issues...")
    
    try:
        qdrant_manager = get_qdrant_client()
        collection_name = config.qdrant_collection_name
        
        # Check connection
        logger.info("🔌 Testing Qdrant connection...")
        if qdrant_manager.health_check():
            logger.info("✅ Qdrant connection is healthy")
        else:
            logger.error("❌ Qdrant connection failed")
            return
        
        # Check collections
        logger.info("📁 Checking collections...")
        try:
            collections = qdrant_manager.client.get_collections()
            logger.info(f"📊 Found {len(collections.collections)} collections:")
            for col in collections.collections:
                logger.info(f"   - {col.name}")
        except Exception as e:
            logger.error(f"❌ Failed to list collections: {e}")
            return
        
        # Check target collection
        if not qdrant_manager.collection_exists(collection_name):
            logger.warning(f"⚠️ Target collection '{collection_name}' doesn't exist")
            return
        
        # Get collection details
        info = qdrant_manager.get_collection_info(collection_name)
        if info:
            logger.info(f"📊 Collection '{collection_name}' details:")
            for key, value in info.items():
                logger.info(f"   {key}: {value}")
        
        # Test point counting
        logger.info("🧮 Testing point counting...")
        try:
            total_points = qdrant_manager.count_points(collection_name)
            logger.info(f"📊 Total points in collection: {total_points}")
        except Exception as e:
            logger.error(f"❌ Failed to count points: {e}")
        
        # Test user filtering
        logger.info("👤 Testing user filtering...")
        test_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="user_id",
                    match=models.MatchValue(value="test_user_123")
                )
            ]
        )
        
        try:
            filtered_count = qdrant_manager.count_points(collection_name, test_filter)
            logger.info(f"✅ User filtering works (found {filtered_count} test user docs)")
        except Exception as e:
            logger.error(f"❌ User filtering failed: {e}")
            logger.info("💡 This suggests missing user_id index")
        
        logger.info("🎯 Diagnosis complete!")
        
    except Exception as e:
        logger.error(f"❌ Diagnosis failed: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix Qdrant index issues")
    parser.add_argument("--diagnose", action="store_true", help="Diagnose issues only")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild collection (DELETES ALL DATA)")
    
    args = parser.parse_args()
    
    if args.diagnose:
        diagnose_qdrant_issues()
    elif args.rebuild:
        print("🚨 WARNING: This will DELETE ALL documents in the collection!")
        response = input("Type 'YES' to continue: ")
        if response == "YES":
            clean_and_rebuild_collection()
        else:
            print("❌ Operation cancelled")
    else:
        fix_qdrant_indexes()
