# Getting Started with Zenith PDF Chatbot

Welcome to Zenith PDF Chatbot! This guide will help you get up and running quickly.

## Prerequisites

- Python 3.8 or higher
- Docker (recommended for Qdrant database)
- OpenAI API key

## Quick Setup (5 minutes)

### 1. Navigate to the Zenith directory
```bash
cd Zenith
```

### 2. Run the setup script
```bash
python setup.py
```
This will:
- Check your Python version
- Create necessary directories
- Install dependencies
- Start Qdrant database (if Docker is available)
- Create configuration files

### 3. Configure your API key
Edit the `.env` file and add your OpenAI API key:
```env
OPENAI_API_KEY=your_actual_api_key_here
```

### 4. Add PDF files
Place your PDF files in the `data/pdfs/` directory, or prepare to upload them through the web interface.

### 5. Start the application

**Option A: Web Interface (Recommended)**
```bash
python main.py ui
```
Open your browser to: http://localhost:8501

**Option B: Use the launcher scripts**
- Windows: Double-click `run.bat`
- Linux/Mac: `./run.sh`

**Option C: API Server**
```bash
python main.py api
```
API docs at: http://localhost:8000/docs

## First Time Usage

1. **Open the web interface** at http://localhost:8501

2. **Configure settings** in the sidebar:
   - Enter your OpenAI API key
   - Adjust chunk size if needed (1000 is good for most cases)

3. **Upload PDFs** either by:
   - Drag & drop files in the upload area
   - Specify a directory path containing PDFs

4. **Click "Process PDFs"** and wait for processing to complete

5. **Start chatting** with your documents!

## Example Questions to Try

- "What are the main topics covered in these documents?"
- "Can you summarize the key findings?"
- "What methodology was used?"
- "Are there any important dates or numbers?"
- "What are the conclusions?"

## Troubleshooting

### Qdrant Not Starting?
If Docker isn't available, you can install Qdrant manually:
- Visit: https://qdrant.tech/documentation/quick-start/
- Or use Qdrant Cloud: https://cloud.qdrant.io/

### OpenAI API Issues?
- Make sure your API key is correct
- Check you have available quota
- Verify the key has the right permissions

### PDF Processing Errors?
- Ensure PDFs are not password-protected
- Check file permissions
- Try with smaller files first

### Memory Issues?
- Reduce chunk size in settings (try 500-600)
- Process fewer files at once
- Close other applications

## Advanced Usage

### Multiple Collections
You can create different collections for different document sets by changing the collection name in the sidebar.

### Batch Processing
For large document sets, the system automatically processes in batches to manage memory usage.

### API Integration
Use the REST API at http://localhost:8000 for programmatic access:

```python
import requests

# Process PDFs
response = requests.post(
    "http://localhost:8000/api/v1/process-pdfs",
    json={"pdf_directory": "/path/to/pdfs"}
)

# Chat with documents
response = requests.post(
    "http://localhost:8000/api/v1/chat",
    json={"question": "What is this about?"}
)
```

### Command Line Options
```bash
python main.py ui --port 8502        # Custom port
python main.py ui --debug            # Debug mode
python main.py info                  # System information
python main.py test                  # Run tests
```

## File Organization

```
data/pdfs/
├── research_papers/
│   ├── ai_paper1.pdf
│   └── ml_paper2.pdf
├── manuals/
│   ├── user_manual.pdf
│   └── technical_spec.pdf
└── reports/
    └── annual_report.pdf
```

## Performance Tips

### For Better Speed:
- Use smaller chunk sizes (500-800) if you have limited VRAM
- Process documents in smaller batches
- Use SSD storage for better I/O performance

### For Better Results:
- Use larger chunk sizes (1200-1500) for complex documents
- Increase chunk overlap (300-400) for better context
- Ask specific questions rather than very broad ones

## Support

If you run into issues:

1. Check the logs in the `logs/` directory
2. Run `python main.py info` for system status
3. Review the troubleshooting section above
4. Check the full README.md for detailed documentation

## What's Next?

- Try different types of documents
- Experiment with different chunk sizes
- Explore the API endpoints
- Set up multiple collections for different projects
- Consider deploying with Docker for production use

Enjoy chatting with your documents! 🚀📚
