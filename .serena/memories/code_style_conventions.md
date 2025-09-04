# Zenith PDF Chatbot - Code Style and Conventions

## Code Style Guidelines

### General Formatting
- **Code Formatter**: Black (standardized Python formatting)
- **Linter**: Flake8 for code quality checks
- **Line Length**: 88 characters (Black default)
- **Indentation**: 4 spaces, no tabs

### Naming Conventions
- **Functions/Variables**: `snake_case`
  - Example: `process_pdf_document()`, `user_session_id`
- **Classes**: `PascalCase`
  - Example: `ChatEngine`, `VectorStore`, `SettingsManager`
- **Constants**: `UPPER_SNAKE_CASE`
  - Example: `MAX_FILE_SIZE_MB`, `DEFAULT_CHUNK_SIZE`
- **Private Methods**: Prefix with underscore `_method_name`
- **Files/Modules**: `snake_case.py`

### Type Hints
- **Required**: All function parameters and return types must have type hints
- **Style**: Use `typing` module imports
  ```python
  from typing import List, Dict, Any, Optional, Union
  
  def process_documents(files: List[str]) -> Dict[str, Any]:
      return {}
  ```

### Docstring Style
- **Format**: Google-style docstrings
- **Required**: All public functions, classes, and modules must have docstrings
- **Example**:
  ```python
  def get_file_hash(file_path: Union[str, Path]) -> str:
      """
      Get MD5 hash of a file
      
      Args:
          file_path: Path to the file to hash
          
      Returns:
          MD5 hash string
          
      Raises:
          FileNotFoundError: If file doesn't exist
      """
  ```

### Import Organization
1. **Standard library imports** (os, sys, pathlib)
2. **Third-party imports** (pandas, numpy, openai)
3. **Local imports** (src.core.config, src.utils.logger)
- Use relative imports for local modules: `from ..core.config import config`

### Error Handling
- **Logging**: Use the centralized logger from `src.utils.logger`
- **Exception Handling**: Specific exceptions preferred over bare `except:`
- **Logging Pattern**:
  ```python
  from src.utils.logger import get_logger
  logger = get_logger(__name__)
  
  try:
      # operation
      logger.info("Operation successful")
  except SpecificError as e:
      logger.error(f"Operation failed: {e}")
  ```

### Configuration Management
- **Centralized**: All config in `src/core/config.py`
- **Environment Variables**: Use Pydantic Settings with `.env` file
- **Access Pattern**: Import and use `config` object
  ```python
  from src.core.config import config
  port = config.app_port
  ```

### File Structure Patterns
- **Core Logic**: `src/core/` - Main business logic
- **Utilities**: `src/utils/` - Helper functions
- **API**: `src/api/` - REST API endpoints
- **UI**: `src/ui/` - Streamlit interface
- **Auth**: `src/auth/` - Authentication logic

### Async/Await Usage
- **Async Functions**: Use for I/O operations (file processing, API calls)
- **Naming**: Prefix async functions with `async_` if ambiguous
- **Error Handling**: Always handle async exceptions properly

### Security Considerations
- **Sensitive Data**: Never log API keys or passwords
- **Input Validation**: Validate all user inputs
- **Path Security**: Use `pathlib.Path` for file operations
- **SQL Injection**: Use parameterized queries (though project uses Qdrant)

### Performance Guidelines
- **Large Files**: Process in chunks
- **Memory Management**: Clean up temporary files
- **Caching**: Use appropriate caching for expensive operations
- **Logging**: Use appropriate log levels (DEBUG for verbose, INFO for important events)
