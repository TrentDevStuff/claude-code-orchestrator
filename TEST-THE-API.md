# Test Your New API Service!

## 1. Install Dependencies

\`\`\`bash
cd ~/claude-code-api-service
pip install -r requirements.txt
pip install redis  # If not already installed
\`\`\`

## 2. Start Redis (Required)

\`\`\`bash
# macOS with Homebrew
brew services start redis

# Or run in foreground
redis-server
\`\`\`

## 3. Start the API Server

\`\`\`bash
python main.py
\`\`\`

Server starts at http://localhost:8080

## 4. Test It!

### Health Check
\`\`\`bash
curl http://localhost:8080/health
\`\`\`

### Chat Completion (Uses Your Claude Code!)
\`\`\`bash
curl -X POST http://localhost:8080/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "haiku",
    "messages": [{"role": "user", "content": "Hello!"}],
    "project_id": "test"
  }'
\`\`\`

### Use the Python Client
\`\`\`python
from client.claude_client import ClaudeClient

client = ClaudeClient(
    base_url="http://localhost:8080",
    project_id="my-app"
)

response = client.complete("Explain async/await", model="haiku")
print(response)
\`\`\`

## 5. What You Built

- ✅ REST API with 4 endpoints
- ✅ WebSocket streaming
- ✅ Model auto-routing
- ✅ Budget tracking
- ✅ Token usage analytics
- ✅ Worker pool (5 parallel Claude sessions)
- ✅ Python client library
- ✅ Complete documentation

**You now have a reusable LLM API using your Claude Code subscription!**
