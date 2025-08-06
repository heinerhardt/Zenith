"""
Unit tests for PDF Processor
"""

import pytest
import tempfile
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.pdf_processor import PDFProcessor
from src.core.config import config


class TestPDFProcessor:
    """Test cases for PDF Processor"""
    
    @pytest.fixture
    def pdf_processor(self):
        """Create PDF processor instance for testing"""
        return PDFProcessor(chunk_size=500, chunk_overlap=50)
    
    def test_pdf_processor_initialization(self, pdf_processor):
        """Test PDF processor initialization"""
        assert pdf_processor.chunk_size == 500
        assert pdf_processor.chunk_overlap == 50
        assert pdf_processor.text_splitter is not None
    
    def test_validate_pdf_invalid_extension(self, pdf_processor):
        """Test PDF validation with invalid extension"""
        # Create temporary text file
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(b"test content")
        
        try:
            result = pdf_processor.validate_pdf(temp_path)
            assert result is False
        finally:
            temp_path.unlink()
    
    def test_validate_pdf_nonexistent_file(self, pdf_processor):
        """Test PDF validation with nonexistent file"""
        fake_path = Path("nonexistent_file.pdf")
        result = pdf_processor.validate_pdf(fake_path)
        assert result is False
    
    def test_get_pdf_info_nonexistent_file(self, pdf_processor):
        """Test getting PDF info for nonexistent file"""
        fake_path = Path("nonexistent_file.pdf")
        info = pdf_processor.get_pdf_info(fake_path)
        
        assert info['filename'] == 'nonexistent_file.pdf'
        assert info['file_size'] == 0
        assert info['num_pages'] == 0
        assert info['is_valid'] is False
    
    def test_split_documents_empty_list(self, pdf_processor):
        """Test splitting empty document list"""
        documents = []
        result = pdf_processor.split_documents(documents)
        assert result == []
    
    def test_cleanup_temp_files(self, pdf_processor):
        """Test cleanup of temporary files"""
        # Create temp directory and file
        temp_dir = Path(config.temp_dir)
        temp_dir.mkdir(exist_ok=True)
        
        temp_file = temp_dir / "test.pdf"
        temp_file.write_text("test content")
        
        # Run cleanup
        pdf_processor._cleanup_temp_files()
        
        # File should be removed
        assert not temp_file.exists()


if __name__ == "__main__":
    pytest.main([__file__])
