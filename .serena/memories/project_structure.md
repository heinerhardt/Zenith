# Zenith PDF Chatbot - Project Structure

## Directory Layout
```
Zenith/
├── src/                    # Main application source code
│   ├── api/               # FastAPI REST API endpoints
│   │   ├── main.py        # API server entry point
│   │   ├── routes.py      # API route definitions
│   │   └── __init__.py
│   ├── auth/              # Authentication and user management
│   │   ├── auth_manager.py    # JWT and session management
│   │   ├── models.py          # User data models
│   │   └── __init__.py
│   ├── core/              # Core business logic
│   │   ├── batch_processor.py     # Bulk document processing
│   │   ├── chat_engine.py         # Main chat functionality
│   │   ├── chat_history.py        # Session management
│   │   ├── config.py              # Configuration management
│   │   ├── enhanced_chat_engine.py    # Advanced chat features
│   │   ├── enhanced_settings_manager.py  # Settings UI
│   │   ├── enhanced_vector_store.py      # Vector operations
│   │   ├── init_enhanced.py             # System initialization
│   │   ├── langfuse_integration.py      # Observability
│   │   ├── minio_client.py              # Object storage
│   │   ├── ollama_integration.py        # Local LLM support
│   │   ├── pdf_processor.py             # Document processing
│   │   ├── provider_manager.py          # AI provider management
│   │   ├── qdrant_manager.py            # Vector database
│   │   ├── settings_manager.py          # Configuration UI
│   │   ├── vector_store.py              # Vector operations
│   │   └── __init__.py
│   ├── ui/                # User interfaces
│   │   ├── auth/          # Authentication UI components
│   │   ├── enhanced_streamlit_app.py  # Main web interface
│   │   └── __init__.py
│   ├── utils/             # Utility functions
│   │   ├── async_helpers.py    # Async operation helpers
│   │   ├── helpers.py          # General utilities
│   │   ├── logger.py           # Logging configuration
│   │   ├── minio_helpers.py    # MinIO utilities
│   │   ├── security.py         # Security functions
│   │   └── __init__.py
│   └── __init__.py
├── config/                # Configuration files
│   └── logging.yaml       # Logging configuration
├── data/                  # Data storage
│   └── pdfs/             # PDF document storage
├── docs/                  # Documentation
├── logs/                  # Application logs
├── qdrant_storage/        # Qdrant vector database files
├── temp_pdfs/            # Temporary file processing
├── .env                   # Environment configuration
├── .env.example           # Environment template
├── .env.minio.example     # MinIO configuration template
├── .gitignore            # Git ignore rules
├── docker-compose.yml     # Basic Docker setup
├── docker-compose.langfuse-v4.yml  # With Langfuse monitoring
├── docker-compose.prod.yml         # Production setup
├── Dockerfile            # Application container
├── Dockerfile.streamlit  # Streamlit-specific container
├── LICENSE               # MIT License
├── main.py              # Application entry point
├── README.md            # Project documentation
├── requirements.txt     # Python dependencies
├── reset_database.py    # Database reset utility
├── run.bat             # Windows launcher
├── run.sh              # Linux/macOS launcher
├── setup.py            # Project setup script
└── (various debug/test scripts)
```

## Key Modules and Their Responsibilities

### Core Modules (`src/core/`)
- **config.py**: Centralized configuration using Pydantic Settings
- **chat_engine.py**: Main chat logic and LLM integration
- **vector_store.py**: Vector database operations with Qdrant
- **pdf_processor.py**: Document ingestion and chunking
- **auth_manager.py**: User authentication and session management
- **provider_manager.py**: AI model provider abstraction (OpenAI/Ollama)

### User Interface (`src/ui/`)
- **enhanced_streamlit_app.py**: Main web application interface
- Provides chat interface, document upload, admin panel
- Handles user sessions and authentication

### API Layer (`src/api/`)
- **main.py**: FastAPI application setup
- **routes.py**: REST API endpoints for external integration
- Optional component for programmatic access

### Utilities (`src/utils/`)
- **logger.py**: Centralized logging with Loguru
- **helpers.py**: Common utility functions
- **security.py**: Security-related functions
- **async_helpers.py**: Async operation utilities

## Data Flow Architecture
1. **Document Upload** → PDF Processor → Text Chunks → Vector Store
2. **User Query** → Chat Engine → Vector Search → LLM → Response
3. **Authentication** → JWT Tokens → Session Management
4. **Monitoring** → Langfuse Integration → Observability Dashboard

## Configuration Architecture
- **Environment Variables**: `.env` file with Pydantic validation
- **Runtime Config**: `src/core/config.py` with type-safe settings
- **Logging Config**: `config/logging.yaml` for structured logging

## Storage Architecture
- **Vector Database**: Qdrant for document embeddings and search
- **File Storage**: Local filesystem or optional MinIO integration
- **User Data**: Qdrant collections for user management
- **Temporary Files**: Automatic cleanup in `temp_pdfs/`

## Deployment Architecture
- **Development**: Local Python with virtual environment
- **Containerized**: Docker Compose with separate services
- **Production**: Multi-container setup with persistent volumes
