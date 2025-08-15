# Zenith PDF Chatbot

A comprehensive AI-powered document chat system that enables intelligent conversations with your PDF documents using RAG (Retrieval Augmented Generation) technology.

## Features

- 🤖 **AI-Powered Chat**: Intelligent conversations with your PDF documents
- 📚 **PDF Processing**: Advanced document ingestion and chunking
- 🔍 **Vector Search**: High-performance semantic search using Qdrant
- 🌐 **Web Interface**: User-friendly Streamlit-based UI
- 🔒 **Authentication**: Secure user management with JWT tokens
- 📊 **Monitoring**: Built-in observability with Langfuse integration
- 🐳 **Containerized**: Full Docker support for easy deployment
- 🔧 **Configurable**: Flexible configuration management
- 🚀 **Multiple Providers**: Support for Ollama and OpenAI models

## Quick Start

### Prerequisites

- **Python**: 3.9 or higher
- **Memory**: Minimum 4GB RAM (8GB+ recommended)
- **Storage**: 2GB free space
- **OS**: Windows, macOS, or Linux

### Required Services
- **Qdrant**: Vector database (local or cloud)
- **Ollama**: Local LLM provider (recommended)
- **Docker**: For containerized deployment (optional)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd Zenith

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Services

#### Option A: Docker (Recommended)

```bash
# Start all services with Langfuse monitoring
docker-compose -f docker-compose.langfuse-v4.yml up -d

# Start basic services only
docker-compose up -d
```

#### Option B: Manual Setup

1. **Install Qdrant**:
```bash
# Using Docker
docker run -p 6333:6333 qdrant/qdrant

# Or download from https://qdrant.tech
```

2. **Install Ollama**:
```bash
# Download from https://ollama.ai
# Pull required models
ollama pull llama2  # or your preferred model
ollama pull nomic-embed-text  # for embeddings
```

### 3. Configuration

Create environment configuration:

```bash
# Copy example config
cp .env.example .env

# Edit configuration
nano .env
```

Key configuration variables:
```env
# Qdrant Configuration
QDRANT_URL=http://localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=zenith_docs

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=llama2
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Application Configuration
APP_PORT=8501
DEBUG_MODE=false
LOG_LEVEL=INFO

# Langfuse Monitoring (Optional)
LANGFUSE_PUBLIC_KEY=your-public-key
LANGFUSE_SECRET_KEY=your-secret-key
LANGFUSE_HOST=http://localhost:3000
```

### 4. Initialize Environment

```bash
# Setup directories and validate configuration
python main.py setup

# Check system status
python main.py info
```

### 5. Run the Application

```bash
# Start web interface
python main.py ui

# Or start API server
python main.py api
```

Access the application at `http://localhost:8501`

## 🗄️ Local Qdrant Setup (Recommended)

For complete data privacy, run Qdrant locally using Docker:

### Option 1: Automated Setup
```bash
python setup_local_qdrant.py
```

### Option 2: Manual Docker Setup
```bash
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v qdrant_storage:/qdrant/storage \
  qdrant/qdrant
```

Then update `.env`:
```env
QDRANT_MODE=local
QDRANT_URL=localhost
QDRANT_PORT=6333
```

## 🐳 Docker Deployment

### Development
```bash
docker-compose up -d
```

### Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 🛠️ Configuration

### AI Models

Configure in Admin Panel → AI Models or via environment:

**OpenAI Models:**
- Chat: `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `gpt-3.5-turbo`
- Embeddings: `text-embedding-3-large`, `text-embedding-3-small`, `text-embedding-ada-002`

**Ollama Setup:**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull models
ollama pull llama2
ollama pull nomic-embed-text

# Update .env
OLLAMA_ENABLED=true
OLLAMA_BASE_URL=http://localhost:11434
PREFERRED_CHAT_MODEL=llama2
PREFERRED_EMBEDDING_MODEL=nomic-embed-text
```

### Document Processing

Default settings (configurable in Admin Panel):
- **Chunk Size**: 1000 characters
- **Chunk Overlap**: 200 characters
- **Max File Size**: 50MB
- **Supported Formats**: PDF

### User Management

- **Registration**: Enabled by default
- **Admin Approval**: Optional
- **Session Duration**: 24 hours
- **Roles**: `chat_user`, `administrator`

## 📖 Usage Guide

### For Users

1. **Login/Register** - Create account or login
2. **Upload Documents** - Use "Upload Documents" tab
3. **Chat** - Ask questions in "Chat" tab (default)
4. **History** - Access previous conversations in sidebar
5. **New Sessions** - Click "🆕 New Chat" to start fresh

### For Administrators

1. **Access Admin Panel** - Click "⚙️ Admin" button
2. **System Settings** - Configure processing parameters
3. **AI Models** - Setup OpenAI/Ollama connections
4. **User Management** - Manage user accounts
5. **MinIO Integration** - Process documents from MinIO buckets
6. **System Status** - Monitor application health

### Chat Features

- **Document-Aware**: Answers based on uploaded PDFs
- **General Chat**: Works without documents
- **Source References**: Shows document sources for answers
- **History Management**: Automatic session save/load
- **Session Cleanup**: Keeps 5 most recent sessions

## 🔧 Administrative Tasks

### Reset Admin Password
```bash
python reset_admin_password.py
```

### Get Admin Credentials
```bash
python get_admin_credentials.py
```

### Create Database Indexes
```bash
python create_user_indexes.py
```

### MinIO Integration

Configure in Admin Panel for bulk PDF processing:

```env
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=documents
```

## 📁 Project Structure

```
Zenith/
├── src/
│   ├── auth/           # Authentication system
│   ├── core/           # Core functionality
│   │   ├── chat_history.py     # Session management
│   │   ├── enhanced_chat_engine.py
│   │   ├── enhanced_vector_store.py
│   │   ├── pdf_processor.py
│   │   ├── qdrant_manager.py
│   │   └── settings_manager.py
│   ├── ui/             # Web interface
│   │   └── enhanced_streamlit_app.py
│   └── utils/          # Utilities
├── config/             # Configuration files
├── data/               # Data storage
├── logs/               # Application logs
├── main.py             # Application entry point
├── requirements.txt    # Dependencies
└── setup.py           # Database initialization
```

## 🔒 Security Features

- **JWT Authentication** - Secure session management
- **Password Hashing** - bcrypt encryption
- **Role-Based Access** - User/Admin separation
- **Data Isolation** - User-specific document access
- **Input Validation** - Secure file upload
- **Session Management** - Automatic cleanup

## 🚨 Troubleshooting

### Common Issues

**Connection Errors:**
```bash
# Test Qdrant connection
curl http://localhost:6333/health

# Check Docker containers
docker ps
```

**Permission Issues:**
```bash
# Reset file permissions
chmod +x run.sh
```

**Module Not Found:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Database Issues:**
```bash
# Reinitialize database
python setup.py --reset
```

### Debug Mode

Enable detailed logging:
```env
DEBUG_MODE=true
LOG_LEVEL=DEBUG
```

View logs:
```bash
tail -f logs/zenith.log
```

## 📊 Performance Optimization

### Recommended Settings

**Production Environment:**
- Use local Qdrant instance
- Enable persistent storage
- Configure proper resource limits
- Use production-grade secret keys

**Vector Database:**
- Optimize chunk size based on document types
- Configure appropriate overlap for context
- Use efficient embedding models

**Caching:**
- Enable Redis for session storage (optional)
- Configure file system caching
- Use CDN for static assets

## 🔄 Updates and Maintenance

### Backup
```bash
# Export Qdrant data
docker exec qdrant ./qdrant --dump /qdrant/storage/backup.tar

# Backup user data
cp -r data/ backup/
```

### Update Dependencies
```bash
pip install -r requirements.txt --upgrade
```

### Health Checks
```bash
# Application health
curl http://localhost:8505/health

# Database health
curl http://localhost:6333/health
```

## 📄 License

[MIT License](LICENSE)

## 🤝 Support

For issues and questions:
1. Check troubleshooting section
2. Review application logs
3. Verify configuration settings
4. Test individual components

---

**Built with ❤️ using Streamlit, Qdrant, and OpenAI**
