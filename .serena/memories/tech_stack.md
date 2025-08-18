# Zenith PDF Chatbot - Tech Stack

## Programming Language
- **Python 3.9+** - Primary development language

## Core AI/ML Framework
- **LangChain** (>=0.0.350) - LLM application framework
- **LangChain Community** - Additional integrations
- **OpenAI** (>=1.3.0) - GPT models and embeddings
- **Sentence Transformers** - Local embedding models

## Vector Database
- **Qdrant** (>=1.7.0) - Vector search and storage
- **qdrant-client** - Python client for Qdrant

## Web Framework
- **Streamlit** (>=1.28.0) - Primary web interface
- **streamlit-chat** - Chat UI components
- **FastAPI** (>=0.104.0) - REST API server (optional)
- **Uvicorn** - ASGI server for FastAPI

## Authentication & Security
- **bcrypt** (>=4.0.0) - Password hashing
- **PyJWT** (>=2.8.0) - JWT token management
- **cryptography** (>=41.0.0) - Cryptographic functions

## PDF Processing
- **pypdf** (>=3.17.0) - PDF text extraction
- **pdfplumber** (>=0.9.0) - Advanced PDF processing

## Configuration & Data
- **pydantic** (>=2.0.0) - Data validation and settings
- **python-dotenv** - Environment variable management
- **pandas** - Data manipulation
- **numpy** - Numerical computing

## Monitoring & Observability
- **Langfuse** (>=2.50.0) - LLM observability and tracing
- **loguru** - Advanced logging

## Development Tools
- **pytest** - Testing framework
- **black** - Code formatting
- **flake8** - Linting

## Containerization
- **Docker** - Containerization platform
- **Docker Compose** - Multi-container orchestration

## Optional Integrations
- **MinIO** - Object storage for bulk document processing
- **Ollama** - Local LLM deployment
- **Redis** - Caching (when enabled)

## System Requirements
- **Minimum**: 4GB RAM, Python 3.9+
- **Recommended**: 8GB+ RAM for better performance
- **Storage**: 2GB free space minimum
- **OS**: Windows, macOS, or Linux
