# 📚 Zenith PDF Chatbot

A modern, secure PDF document processing and chat application with AI-powered question answering, user authentication, and chat history management.

## ✨ Features

- **PDF Document Processing** - Upload and process multiple PDF files
- **AI-Powered Chat** - Ask questions about your documents using OpenAI or Ollama
- **User Authentication** - Secure login system with role-based access
- **Chat History** - Persistent conversation history (last 5 sessions per user)
- **Admin Panel** - Administrative controls and MinIO integration
- **Vector Database** - Efficient document storage using Qdrant (local or cloud)
- **Multi-Provider AI** - Support for OpenAI and Ollama models

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Git
- OpenAI API key (or local Ollama installation)
- Qdrant database (local or cloud)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd Zenith
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Environment Configuration

Copy and configure environment file:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# AI Configuration
OPENAI_API_KEY=your-openai-api-key
PREFERRED_CHAT_MODEL=gpt-4o-mini
PREFERRED_EMBEDDING_MODEL=text-embedding-3-small

# Qdrant Configuration (Cloud)
QDRANT_MODE=cloud
QDRANT_CLOUD_URL=your-qdrant-url
QDRANT_CLOUD_API_KEY=your-qdrant-api-key

# Or Qdrant Local (see Local Setup section)
# QDRANT_MODE=local
# QDRANT_URL=localhost
# QDRANT_PORT=6333

# Application Settings
APP_PORT=8505
DEBUG_MODE=false
ENABLE_AUTH=true
JWT_SECRET_KEY=your-secure-jwt-secret
```

### 3. Initialize Database

```bash
python setup.py
```

This creates:
- Database collections and indexes
- Default admin user (username: `admin`, password: `Admin123!`)
- Initial configuration

### 4. Run Application

```bash
python main.py ui --port 8505
```

Or use provided scripts:
```bash
# Windows
run.bat

# Linux/Mac
./run.sh
```

### 5. Access Application

- **URL**: http://127.0.0.1:8505
- **Admin Login**: `admin` / `Admin123!`
- **Register**: Create new user accounts via registration form

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
