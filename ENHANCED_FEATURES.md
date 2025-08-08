# Zenith PDF Chatbot - Enhanced Features

This document describes the new enhanced features added to Zenith PDF Chatbot, including authentication, role-based access, multi-provider AI support, and improved user experience.

## 🚀 New Features

### 1. User Authentication & Role-Based Access
- **User Registration & Login**: Secure user authentication system
- **Two User Roles**:
  - **Administrator**: Full system access, configuration management, user management
  - **Chat User**: Document upload and chat interface access only
- **Session Management**: JWT-based sessions with configurable duration
- **Password Security**: bcrypt hashing with strong password requirements

### 2. User-Isolated Document Processing
- **Personal Document Spaces**: Each user's documents are isolated and private
- **User-Specific Vector Storage**: Documents stored with user ID filtering
- **Individual Chat History**: Separate conversation history per user
- **Document Management**: Users can view and delete their own documents

### 3. Multi-Provider AI Support
- **OpenAI Integration**: Traditional cloud-based AI (GPT models + embeddings)
- **Ollama Support**: Local AI models for privacy and cost savings
- **Provider Selection**: Administrators can choose preferred providers
- **Model Configuration**: Flexible model selection for chat and embeddings

### 4. Enhanced Vector Database Support
- **Local Qdrant**: Run Qdrant locally for complete data privacy
- **Cloud Qdrant**: Use Qdrant Cloud for managed hosting
- **Flexible Configuration**: Easy switching between local and cloud modes
- **User Filtering**: Advanced filtering for multi-user environments

### 5. Improved User Interface
- **Drag & Drop Upload**: Intuitive file upload with drag-and-drop support
- **Role-Based UI**: Different interfaces for administrators and chat users
- **Chat Without Documents**: Users can chat even without uploading PDFs
- **Enhanced File Management**: Better file organization and status tracking

### 6. Administrator Features
- **System Settings**: Configure processing parameters, user management, AI models
- **User Management**: View, activate/deactivate, reset passwords, delete users
- **AI Model Configuration**: Switch between providers, configure API keys
- **System Monitoring**: Health checks, statistics, and status monitoring

## 📋 Prerequisites

### Required Dependencies
```bash
# Core dependencies (existing)
langchain>=0.0.350
qdrant-client>=1.7.0
streamlit>=1.28.0
openai>=1.3.0

# New authentication dependencies
bcrypt>=4.0.0
PyJWT>=2.8.0
cryptography>=41.0.0

# HTTP client for Ollama
requests>=2.31.0

# Enhanced configuration
pydantic-settings>=2.0.0
```

### System Requirements
- **Python 3.8+**
- **Qdrant**: Either local installation or cloud account
- **OpenAI API Key**: For OpenAI models (optional if using Ollama)
- **Ollama**: For local AI models (optional)

## 🛠️ Installation & Setup

### 1. Install Enhanced Features
```bash
# Run the enhanced setup script
python setup_enhanced.py
```

### 2. Configure Environment
Update your `.env` file with new settings:

```env
# Authentication Configuration
ENABLE_AUTH=True
JWT_SECRET_KEY=your-secure-jwt-secret-key-here
SESSION_DURATION_HOURS=24

# Model Provider Selection
CHAT_PROVIDER=openai          # or 'ollama'
EMBEDDING_PROVIDER=openai     # or 'ollama'

# Ollama Configuration (if using local models)
OLLAMA_ENABLED=False
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=llama2
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Qdrant Configuration
QDRANT_MODE=cloud            # or 'local'
QDRANT_URL=your-qdrant-url
QDRANT_API_KEY=your-api-key  # for cloud mode
```

### 3. Start the Application
```bash
python main.py ui
```

## 👥 User Roles & Permissions

### Administrator Role
- ✅ Access to all system settings
- ✅ User management (create, edit, delete users)
- ✅ AI model configuration
- ✅ System monitoring and health checks
- ✅ Document upload and chat functionality
- ✅ View system statistics and logs

### Chat User Role
- ✅ Upload PDF documents via drag & drop
- ✅ Chat with uploaded documents
- ✅ Chat without documents (general AI assistant)
- ✅ View personal document statistics
- ✅ Manage personal chat history
- ❌ No access to system settings
- ❌ Cannot manage other users

## 🔧 Configuration Options

### AI Provider Configuration

#### OpenAI Setup
```env
OPENAI_API_KEY=sk-your-api-key
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
CHAT_PROVIDER=openai
EMBEDDING_PROVIDER=openai
```

#### Ollama Setup (Local AI)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull models
ollama pull llama2
ollama pull nomic-embed-text

# Configure environment
OLLAMA_ENABLED=True
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=llama2
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
CHAT_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
```

### Qdrant Configuration

#### Local Qdrant
```bash
# Install Qdrant locally
docker run -p 6333:6333 qdrant/qdrant

# Configure environment
QDRANT_MODE=local
QDRANT_URL=localhost
QDRANT_PORT=6333
```

#### Cloud Qdrant
```env
QDRANT_MODE=cloud
QDRANT_URL=https://your-cluster.qdrant.tech
QDRANT_API_KEY=your-api-key
```

## 🎯 Usage Examples

### For Chat Users

1. **Login**: Use your username/email and password
2. **Upload Documents**: Drag and drop PDF files in the upload area
3. **Chat**: Ask questions about your documents or general topics
4. **Manage Files**: View your uploaded documents and delete if needed

### For Administrators

1. **Login**: Use admin credentials (displayed on first run)
2. **Access Admin Panel**: Click "⚙️ Admin" button
3. **Configure System**: Set up AI providers, processing settings
4. **Manage Users**: View, create, edit, or delete user accounts
5. **Monitor System**: Check health status and statistics

## 🔒 Security Features

### Authentication Security
- **Password Hashing**: bcrypt with salt for secure password storage
- **JWT Tokens**: Secure session management with configurable expiration
- **Rate Limiting**: Protection against brute force attacks
- **Session Validation**: Automatic session cleanup and validation

### Data Privacy
- **User Isolation**: Complete separation of user data and documents
- **Local Processing**: Option to run everything locally with Ollama + local Qdrant
- **Secure Storage**: Encrypted API keys and secure configuration management

## 🚨 Migration from Previous Version

### For Existing Users

1. **Backup Data**: Export your existing documents and settings
2. **Run Setup**: Execute `python setup_enhanced.py`
3. **Create Admin User**: Default admin account will be created
4. **Migrate Documents**: Re-upload documents (they'll be assigned to your user account)
5. **Configure Settings**: Review and update system settings in admin panel

### Configuration Changes

The enhanced version includes new configuration options. Update your `.env` file:

```env
# Add these new settings
ENABLE_AUTH=True
JWT_SECRET_KEY=generate-a-secure-key
CHAT_PROVIDER=openai
EMBEDDING_PROVIDER=openai
QDRANT_MODE=cloud
```

## 🐛 Troubleshooting

### Common Issues

#### Authentication Problems
```bash
# Reset admin password
python -c "
from src.auth.auth_manager import AuthenticationManager
from src.core.qdrant_manager import get_qdrant_client
auth = AuthenticationManager(get_qdrant_client().get_client())
# Check console for new admin password
"
```

#### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt
python setup_enhanced.py
```

#### Qdrant Connection Issues
```bash
# Test connection
python -c "
from src.core.qdrant_manager import get_qdrant_client
client = get_qdrant_client()
print('Health:', client.health_check())
"
```

#### Ollama Issues
```bash
# Check Ollama status
ollama list
ollama serve

# Test connection
curl http://localhost:11434/api/tags
```

## 📈 Performance Considerations

### Resource Usage
- **Memory**: ~200MB base + ~100MB per active user session
- **Storage**: Documents stored as vector embeddings (efficient)
- **CPU**: Depends on AI provider (local Ollama vs cloud OpenAI)

### Scaling
- **Users**: Supports 100+ concurrent users with proper Qdrant setup
- **Documents**: No hard limit, scales with vector database capacity
- **Performance**: Local Ollama provides faster response times but requires more CPU

## 🤝 Contributing

### Development Setup
```bash
# Clone and setup development environment
git clone <repository>
cd zenith
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python setup_enhanced.py
```

### Code Structure
- `src/auth/`: Authentication and user management
- `src/core/enhanced_*`: Enhanced AI and vector store modules
- `src/core/settings_manager.py`: System configuration management
- `src/ui/enhanced_streamlit_app.py`: New user interface
- `src/utils/security.py`: Security utilities

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
1. Check the troubleshooting section above
2. Review the application logs in the `logs/` directory
3. Ensure all prerequisites are properly installed
4. Verify your configuration settings

## 🗺️ Roadmap

### Upcoming Features
- [ ] Advanced user permissions and groups
- [ ] Document sharing between users
- [ ] API key management for users
- [ ] Advanced analytics and reporting
- [ ] Integration with more AI providers
- [ ] Mobile-responsive interface improvements
