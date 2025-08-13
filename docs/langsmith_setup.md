# Langsmith Integration Setup

## Installation

To enable Langsmith observability and evaluation features, install the required package:

```bash
pip install langsmith
```

## Configuration

### Environment Variables (.env file)

Add these variables to your `.env` file:

```env
# Langsmith Configuration
LANGSMITH_ENABLED=True
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT_NAME=zenith-pdf-chatbot
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_TRACING_ENABLED=True
LANGSMITH_EVALUATION_ENABLED=False
```

### Admin Settings Override

You can also configure Langsmith through the Admin interface, which will override the .env settings.

## Features

### Automatic Tracing

When enabled, Zenith will automatically trace:

- **Chat Interactions**: User inputs, responses, model provider, and timing
- **Document Processing**: File uploads, chunking, and processing times
- **Search Queries**: RAG retrieval queries and results

### Evaluation Support

- Create evaluation datasets from chat interactions
- Run automated evaluations on response quality
- Compare different model providers
- Track performance metrics over time

## Usage

Once configured, tracing happens automatically. You can view traces and analytics in your Langsmith dashboard at https://smith.langchain.com

### Example: Manual Tracing

```python
from src.core.langsmith_integration import trace_chat_if_enabled

# This will automatically trace if Langsmith is enabled
run_id = trace_chat_if_enabled(
    user_input="What is the main topic of this document?",
    response="The document discusses AI safety and alignment.",
    provider="ollama",
    model="llama2",
    metadata={"document_count": 3, "chunk_count": 15}
)
```

## Benefits

- **Observability**: Track all interactions and performance metrics
- **Debugging**: Identify issues in RAG pipeline and model responses
- **Evaluation**: Measure response quality and accuracy
- **Optimization**: Compare different models and configurations
- **Analytics**: Monitor usage patterns and system health

## Get Your API Key

1. Sign up at https://smith.langchain.com
2. Create a project
3. Generate an API key
4. Add it to your `.env` file or Admin settings

## Notes

- Langsmith integration is optional and won't affect core functionality if not configured
- All tracing is done asynchronously to avoid impacting response times
- Data is sent to Langsmith's servers - review their privacy policy if needed
