# Project Structure Overview

```
Zenith/
├── src/                          # Source code
│   ├── core/                     # Core business logic
│   │   ├── __init__.py
│   │   ├── config.py             # Configuration management
│   │   ├── pdf_processor.py      # PDF processing logic  
│   │   ├── vector_store.py       # Qdrant vector database
│   │   └── chat_engine.py        # Conversational AI
│   ├── api/                      # REST API
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI application
│   │   └── routes.py             # API endpoints
│   ├── ui/                       # User interfaces
│   │   ├── __init__.py
│   │   └── streamlit_app.py      # Streamlit web UI
│   └── utils/                    # Utilities
│       ├── __init__.py
│       ├── logger.py             # Logging utilities
│       └── helpers.py            # Helper functions
├── config/                       # Configuration files
│   └── logging.yaml              # Logging configuration
├── data/                         # Data storage
│   └── pdfs/                     # PDF files directory
├── temp_pdfs/                    # Temporary file storage
├── logs/                         # Application logs
├── tests/                        # Unit tests
│   ├── __init__.py
│   ├── test_pdf_processor.py
│   ├── test_vector_store.py
│   └── test_chat_engine.py
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules
├── README.md                     # Documentation
├── LICENSE                       # MIT license
├── main.py                       # Main entry point
├── setup.py                      # Setup script
├── run.bat                       # Windows launcher
├── run.sh                        # Linux/Mac launcher
├── docker-compose.yml            # Docker setup
├── docker-compose.prod.yml       # Production Docker
├── Dockerfile                    # API container
└── Dockerfile.streamlit          # UI container
```

## Quick Start

1. **Setup Environment:**
   ```bash
   python setup.py
   ```

2. **Configure:**
   - Copy `.env.example` to `.env`
   - Add your OpenAI API key

3. **Start Qdrant:**
   ```bash
   docker-compose up -d
   ```

4. **Run Application:**
   ```bash
   # Web Interface
   python main.py ui

   # API Server  
   python main.py api

   # Or use launchers
   ./run.bat    # Windows
   ./run.sh     # Linux/Mac
   ```

## Features

### PDF Processing
- Multi-file batch processing
- Intelligent text chunking
- Memory-efficient processing
- Support for large documents

### Vector Database
- Qdrant integration
- OpenAI embeddings
- Semantic search
- Persistent storage

### Chat Interface
- Conversational AI
- Source attribution
- Context-aware responses
- Chat history

### Web Interface
- Streamlit-based UI
- File upload/directory selection
- Real-time processing
- Interactive chat

### REST API
- FastAPI backend
- Complete CRUD operations
- Batch processing
- Health monitoring

### Production Ready
- Docker containers
- Logging system
- Error handling
- Testing suite
- Configuration management

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │    FastAPI       │    │   PDF Files     │
│   (Port 8501)   │◄──►│   (Port 8000)    │◄──►│   (Local/Upload)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
              ┌─────────────────────────────────────┐
              │           Core Engine               │
              │  ┌─────────────────────────────────┐│
              │  │        PDF Processor            ││
              │  │   - PyPDFLoader                 ││
              │  │   - Text Splitting              ││
              │  │   - Metadata Extraction         ││
              │  └─────────────────────────────────┘│
              │  ┌─────────────────────────────────┐│
              │  │       Vector Store              ││
              │  │   - Qdrant Client               ││
              │  │   - OpenAI Embeddings           ││
              │  │   - Similarity Search           ││
              │  └─────────────────────────────────┘│
              │  ┌─────────────────────────────────┐│
              │  │       Chat Engine               ││
              │  │   - LangChain Integration       ││
              │  │   - Conversation Memory         ││
              │  │   - Source Attribution          ││
              │  └─────────────────────────────────┘│
              └─────────────────────────────────────┘
                                 │
                                 ▼
              ┌─────────────────────────────────────┐
              │         Qdrant Database             │
              │         (Port 6333)                 │
              │   - Vector Storage                  │
              │   - Semantic Search                 │
              │   - Persistent Data                 │
              └─────────────────────────────────────┘
```

## Development

### Running Tests
```bash
python main.py test
```

### Development Mode
```bash
python main.py ui --debug
python main.py api --debug
```

### System Information
```bash
python main.py info
```

## Configuration

Key settings in `.env`:
- `OPENAI_API_KEY`: Your OpenAI API key
- `QDRANT_URL`: Qdrant server address
- `CHUNK_SIZE`: Text chunk size (default: 1000)
- `CHUNK_OVERLAP`: Overlap between chunks (default: 200)
- `MAX_CHUNKS_PER_QUERY`: Retrieved chunks per query (default: 5)

## Troubleshooting

### Common Issues

1. **Qdrant Connection**
   - Check Docker is running: `docker ps`
   - Verify port 6333 is available
   - Check logs: `docker logs zenith-qdrant`

2. **OpenAI API Errors** 
   - Verify API key in `.env`
   - Check quota limits
   - Monitor rate limits

3. **Memory Issues**
   - Reduce `CHUNK_SIZE` 
   - Process fewer files at once
   - Increase system RAM

4. **PDF Processing**
   - Ensure PDFs are readable
   - Check file permissions
   - Verify file format

### Getting Help

1. Check logs in `logs/` directory
2. Run system health check: `python main.py info`
3. Review error messages
4. Check configuration settings
