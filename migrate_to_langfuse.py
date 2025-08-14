#!/usr/bin/env python3
"""
Migration script to replace Langfuse with Langfuse
Automatically updates all imports and function calls
"""

import sys
from pathlib import Path
import re

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def update_imports_in_file(file_path: Path) -> bool:
    """Update Langfuse imports to Langfuse in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Replace import statements
        content = re.sub(
            r'from \.\.core\.langfuse_integration import',
            'from ..core.langfuse_integration import',
            content
        )
        
        content = re.sub(
            r'from src\.core\.langfuse_integration import',
            'from src.core.langfuse_integration import',
            content
        )
        
        # Replace function calls
        content = re.sub(r'initialize_langfuse', 'initialize_langfuse', content)
        content = re.sub(r'get_langfuse_client', 'get_langfuse_client', content)
        
        # Update function names in comments and strings
        content = re.sub(r'Langfuse', 'Langfuse', content)
        content = re.sub(r'langfuse', 'langfuse', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[OK] Updated {file_path}")
            return True
        else:
            print(f"[SKIP] No changes needed in {file_path}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Failed to update {file_path}: {e}")
        return False

def update_enhanced_chat_engine():
    """Add Langfuse tracing to enhanced chat engine"""
    file_path = project_root / "src" / "core" / "enhanced_chat_engine.py"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already updated
        if "langfuse_integration" in content:
            print("[INFO] Enhanced chat engine already has Langfuse integration")
            return True
        
        # Add import
        if "from ..core.langfuse_integration import" not in content:
            # Find the right place to insert import
            lines = content.split('\n')
            insert_index = 0
            
            for i, line in enumerate(lines):
                if line.startswith('from') or line.startswith('import'):
                    insert_index = i + 1
                elif line.strip() == "" and insert_index > 0:
                    break
            
            import_line = "from ..core.langfuse_integration import trace_rag_flow_if_enabled, flush_langfuse"
            lines.insert(insert_index, import_line)
            content = '\n'.join(lines)
        
        # Add RAG flow tracing to the chat method
        if "trace_rag_flow_if_enabled" not in content:
            # Add timing at the beginning of chat method
            content = re.sub(
                r'(\s+def chat\(self[^)]+\) -> Dict\[str, Any\]:\s*"""[^"]*"""\s*)(try:)',
                r'\1start_time = time.time()\n        \2',
                content,
                flags=re.DOTALL
            )
            
            # Add comprehensive tracing before the return statement
            old_return_pattern = r'return \{\s*"answer": response_content,\s*"source_documents": source_documents,\s*"error": None[^}]*\}'
            
            new_return = '''# Trace the complete RAG flow
            total_time = time.time() - start_time
            
            # Prepare search results for tracing
            search_results_for_trace = []
            if use_rag and 'relevant_docs' in locals() and relevant_docs:
                for doc in relevant_docs[:3]:  # First 3 for brevity
                    search_results_for_trace.append({
                        "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                        "filename": doc.metadata.get("filename", "Unknown"),
                        "page": doc.metadata.get("page", "Unknown")
                    })
            
            # Trace the complete flow
            trace_rag_flow_if_enabled(
                user_input=message,
                search_query=message,
                search_results=search_results_for_trace,
                llm_response=response_content,
                provider=type(self.chat_provider).__name__,
                model=getattr(self.chat_provider, 'model', 'unknown'),
                total_time=total_time,
                metadata={
                    "use_rag": use_rag,
                    "user_filter": user_filter,
                    "user_id": self.user_id,
                    "session_id": getattr(self, 'session_id', None)
                }
            )
            
            # Flush traces to ensure they're sent
            flush_langfuse()
            
            return {
                "answer": response_content,
                "source_documents": source_documents,
                "error": None,
                "metadata": {
                    "chat_time": total_time,
                    "search_results": len(search_results_for_trace),
                    "trace_id": "logged_to_langfuse"
                }
            }'''
            
            content = re.sub(old_return_pattern, new_return, content, flags=re.DOTALL)
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("[OK] Added comprehensive Langfuse tracing to enhanced_chat_engine.py")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to update enhanced chat engine: {e}")
        return False

def update_streamlit_app():
    """Update Streamlit app to use Langfuse"""
    file_path = project_root / "src" / "ui" / "enhanced_streamlit_app.py"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already updated
        if "langfuse_integration" in content:
            print("[INFO] Streamlit app already has Langfuse integration")
            return True
        
        # Replace import
        content = re.sub(
            r'from \.\.core\.langfuse_integration import initialize_langfuse',
            'from ..core.langfuse_integration import initialize_langfuse',
            content
        )
        
        # Replace initialization call
        content = re.sub(r'initialize_langfuse\(', 'initialize_langfuse(', content)
        
        # Update method name
        content = re.sub(r'def initialize_langfuse\(', 'def initialize_langfuse(', content)
        
        # Update comments and docstrings
        content = re.sub(r'Initialize Langfuse', 'Initialize Langfuse', content)
        content = re.sub(r'Langfuse', 'Langfuse', content)
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("[OK] Updated Streamlit app to use Langfuse")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to update Streamlit app: {e}")
        return False

def update_requirements():
    """Update requirements.txt to include Langfuse instead of Langfuse"""
    file_path = project_root / "requirements.txt"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove langfuse
        content = re.sub(r'langfuse[>=<\d\.\w]*\n?', '', content)
        
        # Add langfuse if not present
        if 'langfuse' not in content:
            content += '\nlangfuse>=2.0.0\n'
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("[OK] Updated requirements.txt")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to update requirements.txt: {e}")
        return False

def update_settings_manager():
    """Update settings manager to handle Langfuse settings"""
    file_path = project_root / "src" / "core" / "enhanced_settings_manager.py"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already updated
        if "langfuse" in content.lower():
            print("[INFO] Settings manager already has Langfuse settings")
            return True
        
        # Add Langfuse settings methods
        langfuse_methods = '''
    def is_langfuse_enabled(self) -> bool:
        """Check if Langfuse is enabled"""
        try:
            settings = self.get_settings()
            return getattr(settings, 'langfuse_enabled', False)
        except Exception:
            return False
    
    @property
    def langfuse_host(self) -> Optional[str]:
        """Get Langfuse host"""
        try:
            settings = self.get_settings()
            return getattr(settings, 'langfuse_host', None)
        except Exception:
            return None
    
    @property
    def langfuse_public_key(self) -> Optional[str]:
        """Get Langfuse public key"""
        try:
            settings = self.get_settings()
            return getattr(settings, 'langfuse_public_key', None)
        except Exception:
            return None
    
    @property
    def langfuse_secret_key(self) -> Optional[str]:
        """Get Langfuse secret key"""
        try:
            settings = self.get_settings()
            return getattr(settings, 'langfuse_secret_key', None)
        except Exception:
            return None
    
    @property
    def langfuse_project_name(self) -> Optional[str]:
        """Get Langfuse project name"""
        try:
            settings = self.get_settings()
            return getattr(settings, 'langfuse_project_name', None)
        except Exception:
            return None
'''
        
        # Find a good place to insert (before the last class method or at the end)
        if 'def get_settings(' in content:
            # Insert before the last method
            lines = content.split('\n')
            insert_index = len(lines) - 1
            
            # Find the last method
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip().startswith('def ') and not lines[i].strip().startswith('def __'):
                    insert_index = i - 1
                    break
            
            lines.insert(insert_index, langfuse_methods)
            content = '\n'.join(lines)
        else:
            content += langfuse_methods
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("[OK] Updated settings manager with Langfuse methods")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to update settings manager: {e}")
        return False

def main():
    """Main migration function"""
    print("=" * 60)
    print("MIGRATING FROM LANGSMITH TO LANGFUSE")
    print("=" * 60)
    
    success = True
    
    try:
        # Update core files
        print("\n1. Updating core files...")
        success &= update_enhanced_chat_engine()
        success &= update_streamlit_app()
        success &= update_requirements()
        success &= update_settings_manager()
        
        # Update any other Python files that might import langfuse
        print("\n2. Scanning for other files with Langfuse imports...")
        python_files = list(project_root.rglob("*.py"))
        
        for file_path in python_files:
            if "langfuse" in file_path.name or ".bak" in file_path.name:
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if "langfuse_integration" in content:
                    update_imports_in_file(file_path)
            except Exception as e:
                print(f"[WARNING] Could not check {file_path}: {e}")
        
        print("\n" + "=" * 60)
        if success:
            print("[SUCCESS] Migration from Langfuse to Langfuse completed!")
            print("\nNext steps:")
            print("1. Start Langfuse with Docker:")
            print("   docker-compose -f docker-compose.langfuse.yml up -d")
            print("2. Access Langfuse at http://localhost:3000")
            print("3. Create a project and get API keys")
            print("4. Update your .env file:")
            print("   LANGFUSE_ENABLED=True")
            print("   LANGFUSE_PUBLIC_KEY=pk-...")
            print("   LANGFUSE_SECRET_KEY=sk-...")
            print("5. Install Langfuse: pip install langfuse")
            print("6. Restart your Streamlit app")
        else:
            print("[ERROR] Some migration steps failed. Check the messages above.")
            return 1
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        return 1
    
    print("=" * 60)
    return 0

if __name__ == "__main__":
    exit(main())
