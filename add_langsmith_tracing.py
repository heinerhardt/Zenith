#!/usr/bin/env python3
"""
Patch script to add LangSmith tracing to Enhanced Chat Engine
Run this script to automatically add LangSmith observability to your chat engine.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def add_langsmith_imports():
    """Add LangSmith imports to the chat engine"""
    chat_engine_path = project_root / "src" / "core" / "enhanced_chat_engine.py"
    
    # Read the current file
    with open(chat_engine_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if imports already exist
    if "langsmith_integration" in content:
        print("[INFO] LangSmith imports already present")
        return True
    
    # Add imports after existing imports
    import_line = "from ..core.langsmith_integration import trace_chat_if_enabled, trace_search_if_enabled\nimport time"
    
    # Find the right place to insert (after existing imports)
    lines = content.split('\n')
    insert_index = 0
    
    for i, line in enumerate(lines):
        if line.startswith('from') or line.startswith('import'):
            insert_index = i + 1
        elif line.strip() == "" and insert_index > 0:
            break
    
    # Insert the import
    lines.insert(insert_index, import_line)
    
    # Write back to file
    with open(chat_engine_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print("[OK] Added LangSmith imports to enhanced_chat_engine.py")
    return True

def add_search_tracing():
    """Add search tracing to the similarity_search call"""
    chat_engine_path = project_root / "src" / "core" / "enhanced_chat_engine.py"
    
    # Read the current file
    with open(chat_engine_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if tracing already exists
    if "trace_search_if_enabled" in content:
        print("[INFO] Search tracing already present")
        return True
    
    # Find the similarity_search call and add tracing around it
    old_search_block = '''# Search for relevant documents with user filter preference
                relevant_docs = self.vector_store.similarity_search(
                    query=message,
                    k=config.max_chunks_per_query,
                    user_filter=user_filter  # Use provided filter setting
                )'''
    
    new_search_block = '''# Search for relevant documents with user filter preference
                search_start = time.time()
                relevant_docs = self.vector_store.similarity_search(
                    query=message,
                    k=config.max_chunks_per_query,
                    user_filter=user_filter  # Use provided filter setting
                )
                search_time = time.time() - search_start
                
                # Trace the search operation
                trace_search_if_enabled(
                    query=message,
                    results_count=len(relevant_docs),
                    retrieval_time=search_time,
                    metadata={
                        "user_filter": user_filter,
                        "max_chunks": config.max_chunks_per_query,
                        "user_id": self.user_id
                    }
                )'''
    
    # Replace the search block
    content = content.replace(old_search_block, new_search_block)
    
    # Write back to file
    with open(chat_engine_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("[OK] Added search tracing to enhanced_chat_engine.py")
    return True

def add_chat_tracing():
    """Add chat tracing to the chat method"""
    chat_engine_path = project_root / "src" / "core" / "enhanced_chat_engine.py"
    
    # Read the current file
    with open(chat_engine_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if chat tracing already exists
    if "trace_chat_if_enabled" in content:
        print("[INFO] Chat tracing already present")
        return True
    
    # Add timing at the beginning of the chat method
    old_method_start = '''        try:
            # Create user message'''
    
    new_method_start = '''        start_time = time.time()
        
        try:
            # Create user message'''
    
    content = content.replace(old_method_start, new_method_start)
    
    # Add tracing before the return statement
    old_return = '''            return {
                "answer": response_content,
                "source_documents": source_documents,
                "error": None
            }'''
    
    new_return = '''            # Trace the complete chat interaction
            chat_time = time.time() - start_time
            trace_chat_if_enabled(
                user_input=message,
                response=response_content,
                provider=type(self.chat_provider).__name__,
                model=getattr(self.chat_provider, 'model', 'unknown'),
                metadata={
                    "use_rag": use_rag,
                    "user_filter": user_filter,
                    "source_documents_count": len(source_documents),
                    "chat_time_seconds": chat_time,
                    "user_id": self.user_id
                }
            )
            
            return {
                "answer": response_content,
                "source_documents": source_documents,
                "error": None,
                "metadata": {
                    "chat_time": chat_time,
                    "search_results": len(relevant_docs) if use_rag and relevant_docs else 0
                }
            }'''
    
    content = content.replace(old_return, new_return)
    
    # Write back to file
    with open(chat_engine_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("[OK] Added chat tracing to enhanced_chat_engine.py")
    return True

def add_streamlit_initialization():
    """Add LangSmith initialization to Streamlit app"""
    streamlit_path = project_root / "src" / "ui" / "enhanced_streamlit_app.py"
    
    # Read the current file
    with open(streamlit_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if initialization already exists
    if "initialize_langsmith" in content:
        print("[INFO] LangSmith initialization already present in Streamlit app")
        return True
    
    # Add import
    if "from ..core.langsmith_integration import" not in content:
        # Find import section
        lines = content.split('\n')
        import_index = 0
        for i, line in enumerate(lines):
            if line.startswith('from src.') or line.startswith('from ..'):
                import_index = i + 1
        
        lines.insert(import_index, "from ..core.langsmith_integration import initialize_langsmith")
        content = '\n'.join(lines)
    
    # Add initialization to __init__ method
    old_init = '''        self.initialize_session_state()
        self.initialize_auth()'''
    
    new_init = '''        self.initialize_session_state()
        self.initialize_auth()
        self.initialize_langsmith()'''
    
    content = content.replace(old_init, new_init)
    
    # Add the initialization method
    init_method = '''    
    def initialize_langsmith(self):
        """Initialize LangSmith if enabled"""
        try:
            settings_manager = get_enhanced_settings_manager()
            settings = settings_manager.get_settings()
            initialize_langsmith(settings)
            logger.info("LangSmith initialization attempted")
        except Exception as e:
            logger.warning(f"Could not initialize LangSmith: {e}")'''
    
    # Find a good place to insert the method (after other initialization methods)
    init_auth_end = content.find("def initialize_auth(self):")
    if init_auth_end > -1:
        # Find the end of the initialize_auth method
        lines = content[init_auth_end:].split('\n')
        method_end = 0
        indent_level = None
        
        for i, line in enumerate(lines[1:], 1):  # Skip the def line
            if line.strip() == "":
                continue
            current_indent = len(line) - len(line.lstrip())
            if indent_level is None and line.strip():
                indent_level = current_indent
            elif line.strip() and current_indent <= 4:  # Found next method or class
                method_end = init_auth_end + len('\n'.join(lines[:i]))
                break
        
        if method_end > 0:
            content = content[:method_end] + init_method + content[method_end:]
    
    # Write back to file
    with open(streamlit_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("[OK] Added LangSmith initialization to Streamlit app")
    return True

def main():
    """Main function to apply all LangSmith patches"""
    print("=" * 60)
    print("ADDING LANGSMITH OBSERVABILITY TO ZENITH")
    print("=" * 60)
    
    success = True
    
    try:
        # Add all the tracing components
        success &= add_langsmith_imports()
        success &= add_search_tracing()
        success &= add_chat_tracing()
        success &= add_streamlit_initialization()
        
        print("\n" + "=" * 60)
        if success:
            print("[SUCCESS] LangSmith tracing has been added to your application!")
            print("\nNext steps:")
            print("1. Update your .env file with LangSmith API key:")
            print("   LANGSMITH_ENABLED=True")
            print("   LANGSMITH_API_KEY=ls__your_api_key_here")
            print("2. Install langsmith: pip install langsmith")
            print("3. Restart your Streamlit app")
            print("4. Check the LangSmith dashboard for traces")
        else:
            print("[ERROR] Some patches failed. Check the messages above.")
            return 1
        
    except Exception as e:
        print(f"[ERROR] Patch failed: {e}")
        return 1
    
    print("=" * 60)
    return 0

if __name__ == "__main__":
    exit(main())
