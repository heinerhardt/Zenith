# Zenith PDF Chatbot - Development Guidelines and Patterns

## Design Patterns Used

### 1. Configuration Pattern
- **Centralized Configuration**: All settings in `src/core/config.py`
- **Environment-based**: Uses Pydantic Settings with `.env` file
- **Type Safety**: Full type hints and validation
- **Pattern**: Singleton-like config object imported across modules

### 2. Provider Pattern
- **AI Provider Abstraction**: `provider_manager.py` handles OpenAI/Ollama switching
- **Interface Segregation**: Separate chat and embedding providers
- **Extensibility**: Easy to add new AI providers

### 3. Factory Pattern
- **Component Initialization**: `init_enhanced.py` creates and configures components
- **Dependency Injection**: Components receive their dependencies at creation
- **Error Handling**: Graceful failure if components can't be initialized

### 4. Repository Pattern
- **Vector Store**: Abstracts Qdrant operations behind clean interface
- **Data Access**: Consistent interface for document and user data
- **Testing**: Easy to mock for unit tests

### 5. Observer Pattern
- **Langfuse Integration**: Observability through event tracking
- **Logging**: Centralized logging with structured events
- **Monitoring**: Health checks and metrics collection

## Architectural Principles

### 1. Separation of Concerns
- **UI Layer**: Streamlit components (src/ui/)
- **Business Logic**: Core functionality (src/core/)
- **Data Layer**: Vector store and file operations
- **API Layer**: REST endpoints (src/api/)

### 2. Dependency Inversion
- **Abstractions**: Core logic depends on interfaces, not implementations
- **Configuration**: External configuration drives behavior
- **Providers**: AI providers are pluggable

### 3. Single Responsibility
- **Each module has one primary purpose**
- **Functions are focused and atomic**
- **Classes represent single concepts**

### 4. Open/Closed Principle
- **Extensions**: New AI providers can be added without modifying existing code
- **Configuration**: New settings can be added without breaking existing functionality

## Error Handling Strategy

### 1. Graceful Degradation
```python
try:
    # Primary operation
    result = perform_operation()
except SpecificError as e:
    logger.warning(f"Primary operation failed: {e}")
    # Fallback operation
    result = fallback_operation()
except Exception as e:
    logger.error(f"Critical error: {e}")
    # Return safe default or raise
    raise
```

### 2. Logging Standards
- **Structured Logging**: Use consistent format with context
- **Log Levels**: INFO for normal operations, WARNING for issues, ERROR for failures
- **No Sensitive Data**: Never log API keys, passwords, or personal data

### 3. User-Friendly Errors
- **Streamlit Interface**: Show user-friendly error messages
- **Technical Details**: Log technical details for debugging
- **Recovery Guidance**: Provide actionable error messages

## Performance Guidelines

### 1. Async Operations
- **File Processing**: Use async for I/O operations
- **API Calls**: Async for external service calls
- **Concurrent Processing**: Process multiple documents in parallel

### 2. Memory Management
- **Large Files**: Process in chunks
- **Temporary Files**: Automatic cleanup
- **Streaming**: Use generators for large datasets

### 3. Caching Strategy
- **Vector Embeddings**: Cache expensive computations
- **Configuration**: Cache config objects
- **User Sessions**: Efficient session management

## Security Best Practices

### 1. Input Validation
```python
from pathlib import Path

def validate_file_path(file_path: str) -> Path:
    """Validate and sanitize file paths"""
    path = Path(file_path).resolve()
    # Additional validation logic
    return path
```

### 2. Authentication
- **JWT Tokens**: Secure session management
- **Password Hashing**: bcrypt for password storage
- **Session Expiry**: Automatic session timeout
- **Role-Based Access**: User/Admin role separation

### 3. File Security
- **Upload Restrictions**: PDF files only, size limits
- **Path Traversal**: Prevent directory traversal attacks
- **Temporary Files**: Secure cleanup of sensitive data

## Testing Strategy

### 1. Unit Tests
```python
import pytest
from src.core.config import config

def test_config_loading():
    """Test configuration loading"""
    assert config.app_port > 0
    assert config.chunk_size > 0
```

### 2. Integration Tests
- **End-to-End**: Test complete user workflows
- **Component Integration**: Test module interactions
- **External Services**: Test Qdrant and AI provider connections

### 3. Testing Guidelines
- **Mocking**: Mock external dependencies
- **Test Data**: Use small, reproducible test files
- **Coverage**: Aim for high test coverage on core logic

## Code Organization Principles

### 1. Module Structure
```python
"""
Module docstring explaining purpose
"""

# Standard library imports
import os
import sys
from pathlib import Path

# Third-party imports
import pandas as pd
from openai import OpenAI

# Local imports
from ..core.config import config
from ..utils.logger import get_logger

logger = get_logger(__name__)
```

### 2. Class Design
```python
class DocumentProcessor:
    """
    Process PDF documents for vector storage
    
    Handles document chunking, embedding generation,
    and vector database storage operations.
    """
    
    def __init__(self, vector_store: VectorStore):
        """Initialize with vector store dependency"""
        self.vector_store = vector_store
        self.logger = get_logger(__name__)
    
    def process_document(self, file_path: Path) -> bool:
        """Process single document"""
        # Implementation
        pass
```

### 3. Function Design
```python
def extract_text_from_pdf(file_path: Union[str, Path]) -> str:
    """
    Extract text content from PDF file
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Extracted text content
        
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        PDFProcessingError: If PDF cannot be processed
    """
    # Implementation with proper error handling
    pass
```

## Development Workflow

### 1. Feature Development
1. **Branch**: Create feature branch from main
2. **Implement**: Follow coding standards and patterns
3. **Test**: Write and run tests
4. **Review**: Self-review code quality
5. **Commit**: Descriptive commit messages
6. **Deploy**: Test in staging environment

### 2. Bug Fixes
1. **Reproduce**: Create test case that reproduces bug
2. **Fix**: Implement minimal fix
3. **Verify**: Ensure fix resolves issue and doesn't break other features
4. **Test**: Run full test suite
5. **Document**: Update documentation if necessary

### 3. Code Review Checklist
- [ ] Follows established patterns and conventions
- [ ] Proper error handling and logging
- [ ] Type hints and docstrings present
- [ ] No security vulnerabilities
- [ ] Performance considerations addressed
- [ ] Tests cover new/modified functionality

## Deployment Considerations

### 1. Environment Configuration
- **Development**: Local setup with debug enabled
- **Staging**: Mirror production with test data
- **Production**: Optimized settings, monitoring enabled

### 2. Health Monitoring
```python
def health_check() -> Dict[str, Any]:
    """System health check endpoint"""
    return {
        "status": "healthy",
        "version": __version__,
        "components": {
            "vector_store": vector_store.health_check(),
            "ai_provider": provider.health_check()
        }
    }
```

### 3. Scaling Considerations
- **Horizontal**: Multiple application instances
- **Vertical**: Resource allocation optimization
- **Database**: Qdrant cluster for large datasets
- **Storage**: MinIO for distributed file storage

## Troubleshooting Patterns

### 1. Diagnostic Tools
```python
def diagnose_system():
    """Run system diagnostics"""
    checks = [
        check_qdrant_connection(),
        check_ai_provider_status(),
        check_disk_space(),
        check_memory_usage()
    ]
    return checks
```

### 2. Common Issues
- **Connection Failures**: Retry with exponential backoff
- **Memory Issues**: Process in smaller batches
- **Performance**: Profile and optimize bottlenecks
- **Configuration**: Validate settings on startup

This project emphasizes maintainable, secure, and scalable code that follows Python best practices while providing robust AI-powered document chat functionality.
