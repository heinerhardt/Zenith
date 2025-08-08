# 🗄️ Qdrant Local Database Setup Guide

This guide will help you set up Qdrant as a local database for the Zenith PDF Chatbot instead of using the cloud service.

## 📋 Prerequisites

- Docker installed on your system
- Or ability to install Qdrant directly

## 🚀 Method 1: Docker Installation (Recommended)

### 1. Install Docker
If you don't have Docker installed:
- **Windows**: Download from https://docs.docker.com/desktop/windows/install/
- **macOS**: Download from https://docs.docker.com/desktop/mac/install/
- **Linux**: Follow instructions at https://docs.docker.com/engine/install/

### 2. Run Qdrant Container
```bash
# Run Qdrant with persistent storage
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v qdrant_storage:/qdrant/storage \
  qdrant/qdrant
```

Or for Windows Command Prompt:
```cmd
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 -v qdrant_storage:/qdrant/storage qdrant/qdrant
```

### 3. Verify Installation
```bash
# Check if container is running
docker ps

# Test connection
curl http://localhost:6333/health
```

You should see: `{"status":"ok"}`

## 🖥️ Method 2: Direct Installation

### For Linux/macOS:
```bash
# Download and install Qdrant
wget https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-unknown-linux-gnu.tar.gz
tar -xzf qdrant-x86_64-unknown-linux-gnu.tar.gz
./qdrant
```

### For Windows:
Download the Windows binary from: https://github.com/qdrant/qdrant/releases/latest

## ⚙️ Configure Zenith to Use Local Qdrant

### 1. Update Environment Variables
Edit your `.env` file in the Zenith directory:

```env
# Change from cloud to local
QDRANT_MODE=local
QDRANT_URL=localhost
QDRANT_PORT=6333

# Remove cloud settings (comment out or delete)
# QDRANT_API_KEY=your-cloud-api-key

# Keep your collection names
QDRANT_COLLECTION_NAME=zenith_documents
QDRANT_USERS_COLLECTION=zenith_users
```

### 2. Update Configuration via Admin Panel
1. Login to Zenith as admin: http://127.0.0.1:8505
2. Click "⚙️ Admin" button
3. Go to "AI Models" tab
4. Expand "Qdrant Settings"
5. Select "local" from Qdrant Mode dropdown
6. Set Host: `localhost`
7. Set Port: `6333`
8. Click "Test Qdrant Connection"
9. Click "💾 Save AI Model Settings"
10. Restart the application

## 🔄 Migration from Cloud to Local

### Option 1: Fresh Start (Easiest)
1. Stop Zenith application
2. Set up local Qdrant as above
3. Update configuration to local mode
4. Restart Zenith
5. Re-upload your documents

### Option 2: Export/Import Data (Advanced)
```python
# Export script (run with existing cloud config)
python -c "
from src.core.qdrant_manager import get_qdrant_client
client = get_qdrant_client()
# Export logic here - contact support for full script
"
```

## 🏃‍♂️ Quick Setup Script

Create a file called `setup_local_qdrant.py`:

```python
#!/usr/bin/env python3
import subprocess
import sys
import time
import requests

def setup_local_qdrant():
    print("Setting up local Qdrant...")
    
    # Check if Docker is available
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        print("✅ Docker is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker not found. Please install Docker first.")
        return False
    
    # Stop existing container if running
    try:
        subprocess.run(["docker", "stop", "qdrant"], check=True, capture_output=True)
        subprocess.run(["docker", "rm", "qdrant"], check=True, capture_output=True)
        print("🔄 Stopped existing Qdrant container")
    except subprocess.CalledProcessError:
        pass  # Container doesn't exist, that's ok
    
    # Start new Qdrant container
    try:
        cmd = [
            "docker", "run", "-d",
            "--name", "qdrant",
            "-p", "6333:6333",
            "-p", "6334:6334",
            "-v", "qdrant_storage:/qdrant/storage",
            "qdrant/qdrant"
        ]
        subprocess.run(cmd, check=True)
        print("🚀 Started Qdrant container")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Qdrant: {e}")
        return False
    
    # Wait for startup
    print("⏳ Waiting for Qdrant to start...")
    time.sleep(10)
    
    # Test connection
    try:
        response = requests.get("http://localhost:6333/health", timeout=5)
        if response.status_code == 200:
            print("✅ Qdrant is running and healthy")
            return True
        else:
            print("❌ Qdrant health check failed")
            return False
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to Qdrant")
        return False

if __name__ == "__main__":
    if setup_local_qdrant():
        print("\n🎉 Local Qdrant setup complete!")
        print("Next steps:")
        print("1. Update your Zenith configuration to use local mode")
        print("2. Restart Zenith application")
        print("3. Test the connection in admin panel")
    else:
        print("\n💥 Setup failed. Check Docker installation and try again.")
```

## 🌐 Web Interface

Qdrant provides a web interface at: http://localhost:6333/dashboard

Use this to:
- Monitor collections
- View stored data
- Check system health
- Browse vector spaces

## 🔧 Advanced Configuration

### Custom Configuration File
Create `qdrant-config.yaml`:

```yaml
service:
  http_port: 6333
  grpc_port: 6334

storage:
  storage_path: ./storage
  snapshots_path: ./snapshots

log_level: INFO

cluster:
  enabled: false

telemetry_disabled: true
```

Run with custom config:
```bash
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v $(pwd)/qdrant-config.yaml:/qdrant/config/production.yaml \
  -v qdrant_storage:/qdrant/storage \
  qdrant/qdrant
```

### Performance Tuning
For production use:

```yaml
# In qdrant-config.yaml
service:
  max_request_size_mb: 32
  max_workers: 0  # Auto-detect CPU cores

storage:
  performance:
    max_search_threads: 0  # Auto-detect
    search_hnsw_ef: 128
```

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**:
   ```bash
   docker stop qdrant
   docker rm qdrant
   # Then restart
   ```

2. **Cannot connect**:
   - Check if Docker is running
   - Verify ports 6333 and 6334 are not blocked
   - Check firewall settings

3. **Data persistence issues**:
   - Ensure volume mount is correct
   - Check Docker volume: `docker volume ls`

4. **Performance issues**:
   - Increase Docker memory allocation
   - Use SSD storage for volumes
   - Adjust Qdrant configuration

### Health Check Commands
```bash
# Check container status
docker logs qdrant

# Check API health
curl http://localhost:6333/health

# List collections
curl http://localhost:6333/collections

# Check telemetry (should show metrics)
curl http://localhost:6333/telemetry
```

## 📊 Monitoring

### Basic Monitoring
```bash
# Container resources
docker stats qdrant

# Disk usage
docker system df
```

### Advanced Monitoring
Use Qdrant's built-in metrics:
- CPU usage: `/metrics`
- Memory usage: `/telemetry`
- Request statistics: `/collections/{collection}/cluster`

## 🔒 Security Considerations

### For Production:
1. **Enable authentication**:
   ```yaml
   service:
     api_key: "your-secure-api-key"
   ```

2. **Network security**:
   - Use Docker networks
   - Restrict port access
   - Use reverse proxy

3. **Data encryption**:
   - Enable TLS
   - Encrypt volumes
   - Use secure connections

## 🆘 Getting Help

If you encounter issues:

1. **Check logs**: `docker logs qdrant`
2. **Verify configuration**: Compare with working examples
3. **Test connectivity**: Use curl commands above
4. **Restart services**: Stop and start containers
5. **Reset data**: Remove volumes and recreate

## 📝 Quick Reference

### Essential Commands
```bash
# Start Qdrant
docker run -d --name qdrant -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant

# Stop Qdrant
docker stop qdrant

# Remove container
docker rm qdrant

# Check health
curl http://localhost:6333/health

# View dashboard
# Open http://localhost:6333/dashboard in browser
```

### Configuration Summary
- **Host**: localhost
- **Port**: 6333 (HTTP), 6334 (gRPC)
- **Dashboard**: http://localhost:6333/dashboard
- **Health**: http://localhost:6333/health
- **Storage**: Docker volume `qdrant_storage`

This local setup provides complete data privacy and eliminates dependency on external services!
