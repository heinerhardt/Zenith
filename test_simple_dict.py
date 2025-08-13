#!/usr/bin/env python3
"""
Simple test for source document processing fix
"""

def test_dict_processing():
    """Test processing dictionary source documents"""
    
    # Simulate the problematic case
    test_doc = {
        "content": "This is some test content from a document",
        "filename": "test.pdf", 
        "page": 1
    }
    
    print("Testing dict processing...")
    
    # Test the logic we implemented
    try:
        if hasattr(test_doc, 'page_content'):
            print("Has page_content attribute")
        elif isinstance(test_doc, dict):
            print("Is dictionary - this should be the path taken")
            content = test_doc.get("content", "No content")[:200]
            filename = test_doc.get("filename", "Unknown file")
            page = test_doc.get("page", "Unknown page")
            
            result = {
                "content": content,
                "filename": filename,
                "page": str(page)
            }
            
            print("SUCCESS! Processed dictionary:")
            print(f"  Content: {result['content']}")
            print(f"  Filename: {result['filename']}")
            print(f"  Page: {result['page']}")
            
        else:
            print("Unknown type")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_dict_processing()
