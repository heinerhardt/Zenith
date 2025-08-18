# Zenith PDF Chatbot - Suggested Commands

## Windows Commands (Primary Development Environment)

### Development Setup
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup project environment
python main.py setup
```

### Running the Application
```bash
# Start Streamlit web interface (primary interface)
python main.py ui
python main.py ui --host 0.0.0.0 --port 8501

# Start FastAPI server (optional API)
python main.py api
python main.py api --host 0.0.0.0 --port 8000

# Quick startup with menu (Windows)
run.bat

# Quick startup with menu (Linux/macOS)
./run.sh
```

### Docker Operations
```bash
# Start Qdrant vector database
docker-compose up -d qdrant

# Start all services with Langfuse monitoring
docker-compose -f docker-compose.langfuse-v4.yml up -d

# Start basic services
docker-compose up -d

# Production deployment
docker-compose -f docker-compose.prod.yml up -d
```

### Development Tools
```bash
# Run tests
python main.py test
pytest tests/ -v --tb=short

# Code formatting
black src/ --line-length 88
black . --check  # Check without modifying

# Linting
flake8 src/ --max-line-length=88
```

### System Information and Health Checks
```bash
# Show system status and configuration
python main.py info

# Test Qdrant connection
curl http://localhost:6333/health

# Check Docker containers
docker ps
docker logs zenith-qdrant
```

### Database and Storage Management
```bash
# Reset admin password
python reset_database.py

# Initialize database
python setup.py

# Clean temporary files
# (handled automatically by the application)
```

### Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit configuration (use your preferred text editor)
notepad .env          # Windows
nano .env            # Linux/macOS
code .env            # VS Code
```

### MinIO Integration (Optional)
```bash
# Test MinIO connection (if configured)
# Access MinIO console at http://localhost:9000

# Process documents from MinIO bucket
# (done through the web interface Admin panel)
```

### Debugging and Monitoring
```bash
# View application logs
type logs\zenith.log        # Windows
tail -f logs/zenith.log     # Linux/macOS

# Enable debug mode
# Set DEBUG_MODE=true in .env file

# View Qdrant dashboard
# Open http://localhost:6333/dashboard

# View Langfuse dashboard (if enabled)
# Open http://localhost:3000
```

### Maintenance Commands
```bash
# Update dependencies
pip install -r requirements.txt --upgrade

# Clean Docker volumes (if needed)
docker-compose down -v
docker volume prune

# Backup Qdrant data
docker exec zenith-qdrant tar -czf /tmp/qdrant-backup.tar.gz /qdrant/storage
```

### Windows-Specific Commands
```bash
# Check if Python is available
python --version

# List running processes (if needed)
tasklist | findstr python

# Kill process by PID (if needed)
taskkill /PID <process_id> /F

# Check port usage
netstat -an | findstr :8501
netstat -an | findstr :6333
```

### Performance Monitoring
```bash
# Monitor system resources
# Use Task Manager (Windows) or htop/top (Linux/macOS)

# Check disk space
dir C:\ # Windows basic
Get-WmiObject -Class Win32_LogicalDisk | Select-Object DeviceID,FreeSpace,Size # PowerShell

# Monitor application performance
# Check logs/zenith.log for performance metrics
```

### Git Operations (Development)
```bash
# Standard Git workflow
git status
git add .
git commit -m "Description of changes"
git push origin main

# Check project structure
tree /F  # Windows
tree     # Linux/macOS with tree installed
```

### Troubleshooting Commands
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Clear Python cache
py -m pip cache purge  # Windows
python -m pip cache purge  # Linux/macOS

# Reset Docker environment
docker-compose down
docker-compose up -d

# Check firewall (Windows)
# Ensure ports 8501, 6333, and 8000 are not blocked
```
