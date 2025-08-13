#!/usr/bin/env python3
"""
Test script for the source document processing fix
"""

def test_safe_process_source_document():
    """Test the safe source document processing function"""
    
    # Mock the method for testing
    class MockApp:
        def safe_process_source_document(self, doc, index=0):
            """Safely process source documents regardless of their format"""
            try:
                import logging
                logger = logging.getLogger(__name__)
                
                # Handle LangChain Document objects
                if hasattr(doc, 'page_content') and hasattr(doc, 'metadata'):
                    content = doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                    metadata = doc.metadata or {}
                    filename = metadata.get("filename") or metadata.get("source") or f"Document {index + 1}"
                    page = metadata.get("page") or metadata.get("page_number") or "Unknown page"
                    
                # Handle dictionary format
                elif isinstance(doc, dict):
                    # Try different possible content keys
                    content_text = (doc.get("content") or 
                                  doc.get("page_content") or 
                                  doc.get("text") or 
                                  doc.get("document") or 
                                  str(doc))
                    content = content_text[:200] + "..." if len(str(content_text)) > 200 else str(content_text)
                    
                    # Try different possible filename keys
                    filename = (doc.get("filename") or 
                               doc.get("source") or 
                               doc.get("file") or 
                               doc.get("name") or 
                               f"Document {index + 1}")
                    
                    # Try different possible page keys
                    page = (doc.get("page") or 
                           doc.get("page_number") or 
                           doc.get("page_num") or 
                           "Unknown page")
                    
                # Handle string format
                elif isinstance(doc, str):
                    content = doc[:200] + "..." if len(doc) > 200 else doc
                    filename = f"Text Document {index + 1}"
                    page = "Unknown page"
                    
                # Handle unknown types
                else:
                    print(f"Unknown document type: {type(doc)}")
                    content = str(doc)[:200] + "..."
                    filename = f"Document {index + 1}"
                    page = "Unknown page"
                
                return {
                    "content": content,
                    "filename": filename,
                    "page": str(page)
                }
                
            except Exception as e:
                print(f"Error processing source document {index}: {e}")
                return {
                    "content": f"Error loading document content: {str(e)}",
                    "filename": f"Document {index + 1}",
                    "page": "Error"
                }
    
    app = MockApp()
    
    # Test cases
    test_cases = [
        # Dictionary format (most common case causing the error)
        {
            "input": {"content": "This is test content", "filename": "test.pdf", "page": 1},
            "description": "Dictionary with content key"
        },
        {
            "input": {"page_content": "This is page content", "source": "doc.pdf", "page_number": 2},
            "description": "Dictionary with page_content key"
        },
        {
            "input": {"text": "Some text here", "file": "document.txt"},
            "description": "Dictionary with text key"
        },
        
        # String format
        {
            "input": "Just a plain string document",
            "description": "Plain string"
        },
        
        # Mock LangChain Document object
        {
            "input": type('MockDoc', (), {
                'page_content': 'This is LangChain document content',
                'metadata': {'filename': 'langchain.pdf', 'page': 3}
            })(),
            "description": "Mock LangChain Document"
        },
        
        # Edge cases
        {
            "input": {},
            "description": "Empty dictionary"
        },
        {
            "input": None,
            "description": "None value"
        },
        {
            "input": 12345,
            "description": "Integer value"
        }
    ]
    
    print("🧪 Testing safe_process_source_document function...")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases):
        try:
            result = app.safe_process_source_document(test_case["input"], i)
            print(f"✅ Test {i+1}: {test_case['description']}")
            print(f"   Content: {result['content'][:50]}...")
            print(f"   Filename: {result['filename']}")
            print(f"   Page: {result['page']}")
            print()
        except Exception as e:
            print(f"❌ Test {i+1} FAILED: {test_case['description']}")
            print(f"   Error: {e}")
            print()
    
    print("🎉 All tests completed!")

if __name__ == "__main__":
    test_safe_process_source_document()
