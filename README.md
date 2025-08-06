# Zenith PDF Chatbot with LangChain & Qdrant

A comprehensive PDF processing and chatbot system built with LangChain, Qdrant vector database, and OpenAI embeddings. Upload PDF documents, process them into searchable embeddings, and interact with your documents through an intelligent chatbot interface.

## 🚀 Features

- **Multi-PDF Processing**: Batch process multiple PDF files from directories
- **Intelligent Text Chunking**: Smart text splitting with context preservation
- **Vector Search**: Semantic search using Qdrant vector database and OpenAI embeddings
- **Conversational AI**: Context-aware chatbot with conversation memory
- **Web Interface**: User-friendly Streamlit interface
- **REST API**: FastAPI backend for programmatic access
- **VRAM Optimization**: Efficient memory management for large document collections
- **Source Attribution**: View source documents for all AI responses

## 📁 Project Structure

```
Zenith/
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── pdf_processor.py      # PDF processing logic
│   │   ├── vector_store.py       # Qdrant vector database operations
│   │   ├── chat_engine.py        # Conversational AI engine
│   │   └── config.py             # Configuration management
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI application
│   │   └── routes.py             # API endpoints
│   ├── ui/
│   │   ├── __init__.py
│   │   └── streamlit_app.py      # Streamlit web interface
│   └── utils/
│       ├── __init__.py
│       ├── logger.py             # Logging utilities
│       └── helpers.py            # Helper functions
├── config/
│   └── logging.yaml              # Logging configuration
├── data/
│   └── pdfs/                     # Place your PDF files here
├── temp_pdfs/                    # Temporary file storage
├── logs/                         # Application logs
├── tests/                        # Unit tests
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
├── docker-compose.yml            # Docker setup for Qdrant
├── Dockerfile                    # Application container
└── README.md                     # This file
```

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- Docker (for Qdrant)
- OpenAI API Key

### 1. Clone and Setup

```bash
cd Zenith
cp .env.example .env
# Edit .env with your API keys
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start Qdrant Database

```bash
docker-compose up -d
```

### 4. Run the Application

#### Streamlit Web Interface
```bash
streamlit run src/ui/streamlit_app.py
```

#### FastAPI Server
```bash
uvicorn src.api.main:app --reload --port 8000
```

## 🎯 Usage

### Web Interface

1. Open your browser to `http://localhost:8501`
2. Configure your OpenAI API key in the sidebar
3. Upload PDF files or specify a directory path
4. Click "Process PDFs" to extract and embed the content
5. Start chatting with your documents!

### API Usage

```python
import requests

# Process PDFs
response = requests.post(
    "http://localhost:8000/process-pdfs",
    json={"pdf_directory": "/path/to/pdfs"}
)

# Chat with documents
response = requests.post(
    "http://localhost:8000/chat",
    json={"question": "What are the main topics in these documents?"}
)
```

### Python SDK

```python
from src.core.pdf_processor import PDFProcessor
from src.core.vector_store import VectorStore
from src.core.chat_engine import ChatEngine

# Initialize components
processor = PDFProcessor()
vector_store = VectorStore()
chat_engine = ChatEngine(vector_store)

# Process PDFs
documents = processor.load_and_split_pdfs("/path/to/pdfs")
vector_store.add_documents(documents)

# Chat
response = chat_engine.chat("What is this document about?")
print(response["answer"])
```

## ⚙️ Configuration

### Environment Variables

Key configuration options in `.env`:

- `OPENAI_API_KEY`: Your OpenAI API key
- `QDRANT_URL`: Qdrant server URL (default: localhost)
- `CHUNK_SIZE`: Text chunk size for processing (default: 1000)
- `CHUNK_OVERLAP`: Overlap between chunks (default: 200)
- `MAX_CHUNKS_PER_QUERY`: Number of chunks to retrieve (default: 5)

### Performance Tuning

For limited VRAM or large document collections:

```env
CHUNK_SIZE=500          # Smaller chunks for limited memory
CHUNK_OVERLAP=100       # Reduced overlap
BATCH_SIZE=25           # Smaller batch sizes
MEMORY_LIMIT_GB=4       # Memory limit
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_pdf_processor.py

# Run with coverage
pytest --cov=src tests/
```

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose -f docker-compose.prod.yml up --build
```

## 📊 Monitoring

- **Logs**: Check `logs/` directory for application logs
- **Metrics**: Access metrics at `http://localhost:8502` (if enabled)
- **Health Check**: `http://localhost:8000/health`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

1. **Qdrant Connection Error**
   - Ensure Docker is running: `docker-compose ps`
   - Check port 6333 is available

2. **OpenAI API Errors**
   - Verify API key in `.env`
   - Check API quota and rate limits

3. **Memory Issues**
   - Reduce `CHUNK_SIZE` in `.env`
   - Process fewer documents at once
   - Increase system RAM/VRAM

4. **PDF Processing Errors**
   - Ensure PDFs are not password-protected
   - Check file permissions
   - Verify PDF format compatibility

### Performance Optimization

- Use smaller chunk sizes for limited VRAM
- Enable batch processing for large document sets
- Consider using local embeddings to reduce API costs
- Monitor memory usage and adjust batch sizes accordingly

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review logs in the `logs/` directory

---

**Happy chatting with your documents! 🚀📚**
