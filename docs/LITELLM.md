# M.A.R.K Evolution - LiteLLM Configuration Guide

This guide covers the LiteLLM integration in M.A.R.K Evolution, including setup, configuration, and troubleshooting.

## 🏗️ Architecture Overview

M.A.R.K Evolution uses LiteLLM as a unified gateway to access multiple LLM providers:

```
M.A.R.K Evolution
    ↓
LiteLLM Provider (jarvis/llm/litellm_provider.py)
    ↓
LiteLLM Gateway (http://192.168.1.198:4000)
    ↓
Multiple LLM Providers
├── NVIDIA API
├── DeepSeek API
├── Gemini API
├── Ollama (Local)
└── Other providers
```

### Benefits of LiteLLM Integration

- **Single Entry Point** - One configuration for all providers
- **Automatic Failover** - Built-in retry and fallback logic
- **Load Balancing** - Distribute requests across providers
- **Unified API** - Consistent interface regardless of provider
- **Cost Optimization** - Route to cheapest available provider

---

## ⚙️ LiteLLM Configuration

### Basic Configuration

Create or update your `.env` file:

```env
# LiteLLM Gateway Settings
JARVIS_LLM_PROVIDER=litellm
JARVIS_LITELLM_BASE_URL=http://192.168.1.198:4000
JARVIS_LITELLM_API_KEY=dummy
JARVIS_DEFAULT_MODEL=qwen-fast
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JARVIS_LLM_PROVIDER` | Yes | `litellm` | Must be set to `litellm` |
| `JARVIS_LITELLM_BASE_URL` | Yes | `http://192.168.1.198:4000` | LiteLLM gateway URL |
| `JARVIS_LITELLM_API_KEY` | No | `dummy` | API key for the gateway |
| `JARVIS_DEFAULT_MODEL` | Yes | `qwen-fast` | Default model to use |

### LLM Parameters

| Variable | Default | Description | Range |
|----------|---------|-------------|-------|
| `JARVIS_LLM_TEMPERATURE` | `0.7` | Response randomness | 0.0-2.0 |
| `JARVIS_LLM_MAX_TOKENS` | `null` | Max response tokens | 1-8192 |

---

## 🤖 Available Models

### Default Model Mapping

MARK XLVI automatically maps model names to their proper LiteLLM format:

| Short Name | LiteLLM Format | Provider |
|------------|----------------|----------|
| `qwen-fast` | `openai/qwen-fast` | OpenAI Compatible |
| `deepseek-chat` | `deepseek/deepseek-chat` | DeepSeek |
| `nemotron` | `nvidia/nemotron` | NVIDIA |
| `llama-3.1-8b` | `ollama/llama-3.1-8b` | Ollama |
| `gemini-flash` | `gemini/gemini-flash` | Google |

### Model Selection

You can change models in several ways:

#### 1. Configuration File
```env
JARVIS_DEFAULT_MODEL=deepseek-chat
```

#### 2. Environment Override
```bash
JARVIS_DEFAULT_MODEL=nemotron python -m jarvis.main
```

#### 3. Runtime Selection
```python
from jarvis.llm.client import LLMClient

client = LLMClient()
response = await client.chat(
    messages=[{"role": "user", "content": "Hello"}],
    model="gemini-flash"  # Override default for this request
)
```

---

## 🚀 LiteLLM Gateway Setup

### Option 1: Use Existing Gateway

If you have a LiteLLM gateway running, simply update the URL:

```env
JARVIS_LITELLM_BASE_URL=http://your-gateway-host:4000
```

### Option 2: Set Up Local Gateway

Install and configure LiteLLM gateway:

```bash
# Install LiteLLM
pip install litellm

# Create configuration file
cat > litellm_config.yaml << 'EOF'
model_list:
  - model_name: qwen-fast
    litellm_params:
      model: openai/qwen-fast
      api_base: http://localhost:8000/v1
      api_key: your-key
  
  - model_name: deepseek-chat
    litellm_params:
      model: deepseek/deepseek-chat
      api_key: your-deepseek-key
  
  - model_name: nemotron
    litellm_params:
      model: nvidia/nemotron-70b
      api_key: your-nvidia-key
EOF

# Start the gateway
litellm --config litellm_config.yaml --port 4000
```

### Option 3: Docker Gateway

```bash
# Pull LiteLLM image
docker pull ghcr.io/berriai/litellm:main

# Run with configuration
docker run -p 4000:4000 \
  -v $(pwd)/litellm_config.yaml:/app/config.yaml \
  ghcr.io/berriai/litellm:main \
  --config /app/config.yaml --port 4000
```

---

## 🔧 Provider Configuration

### NVIDIA API

1. **Get API Key**: Register at [NVIDIA NGC](https://ngc.nvidia.com/)
2. **Configure Gateway**:
```yaml
model_list:
  - model_name: nemotron
    litellm_params:
      model: nvidia/nemotron-70b
      api_key: nvapi-your-key
```

### DeepSeek API

1. **Get API Key**: Register at [DeepSeek](https://platform.deepseek.com/)
2. **Configure Gateway**:
```yaml
model_list:
  - model_name: deepseek-chat
    litellm_params:
      model: deepseek/deepseek-chat
      api_key: sk-your-key
```

### Google Gemini API

1. **Get API Key**: Register at [Google AI Studio](https://aistudio.google.com/)
2. **Configure Gateway**:
```yaml
model_list:
  - model_name: gemini-flash
    litellm_params:
      model: gemini/gemini-1.5-flash
      api_key: your-gemini-key
```

### Ollama (Local)

1. **Install Ollama**:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

2. **Pull Models**:
```bash
ollama pull llama3.1:8b
ollama pull codellama:7b
```

3. **Configure Gateway**:
```yaml
model_list:
  - model_name: llama-3.1-8b
    litellm_params:
      model: ollama/llama3.1:8b
      api_base: http://localhost:11434
```

---

## 🧪 Testing LiteLLM Integration

### 1. Basic Connection Test

```bash
# Test with mock (no real API calls)
python test_litellm_mock.py
```

### 2. Real API Test

```bash
# Test with actual LiteLLM gateway
python test_litellm_migration.py
```

### 3. Manual Test Script

Create a test script:

```python
#!/usr/bin/env python3
"""Test LiteLLM integration"""

import asyncio
from jarvis.llm.client import LLMClient

async def test_models():
    """Test different models"""
    client = LLMClient()
    
    models = ["qwen-fast", "deepseek-chat", "nemotron"]
    
    for model in models:
        try:
            print(f"Testing {model}...")
            response = await client.chat(
                messages=[{"role": "user", "content": "Say 'Hello from {model}'"}],
                model=model
            )
            print(f"✅ {model}: {response.content}")
        except Exception as e:
            print(f"❌ {model}: {e}")

if __name__ == "__main__":
    asyncio.run(test_models())
```

Run the test:
```bash
python test_litellm_models.py
```

---

## 📊 Monitoring and Statistics

### Provider Statistics

MARK XLVI tracks LiteLLM usage statistics:

```python
from jarvis.llm.litellm_provider import get_litellm_provider

provider = get_litellm_provider()
stats = provider.get_stats()

print(f"Total requests: {stats['total_requests']}")
print(f"Success rate: {stats['success_rate']:.1f}%")
print(f"Average response time: {stats['avg_response_time']:.2f}s")
print(f"Last error: {stats['last_error']}")
```

### Real-time Monitoring

The dashboard displays LiteLLM statistics:
- Active provider
- Response times
- Success/failure rates
- Model usage

---

## 🔧 Advanced Configuration

### Custom Model Mapping

Add custom models in `jarvis/llm/litellm_provider.py`:

```python
def _get_model(self, model: str | None = None) -> str:
    if model and model != "auto":
        if "/" not in model:
            model_mapping = {
                "qwen-fast": "openai/qwen-fast",
                "deepseek-chat": "deepseek/deepseek-chat",
                "nemotron": "nvidia/nemotron-70b",
                "custom-model": "your-provider/custom-model",  # Add this
            }
            return model_mapping.get(model, f"openai/{model}")
    return model
```

### Request Timeout Configuration

```python
# In litellm_provider.py
async def chat(self, **kwargs):
    # Add timeout to request
    kwargs["timeout"] = 30  # 30 seconds timeout
    response = await acompletion(**kwargs)
```

### Retry Configuration

```python
# Configure retry logic
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def chat_with_retry(self, **kwargs):
    return await self.chat(**kwargs)
```

---

## 🚨 Troubleshooting

### Common Issues

#### 1. Connection Refused
**Error**: `Connection refused: http://192.168.1.198:4000`

**Solutions**:
- Check if LiteLLM gateway is running
- Verify the URL in `JARVIS_LITELLM_BASE_URL`
- Check network connectivity

```bash
# Test gateway connectivity
curl http://192.168.1.198:4000/v1/models

# Check if gateway is running
docker ps | grep litellm
```

#### 2. Authentication Error
**Error**: `AuthenticationError: API key required`

**Solutions**:
- Update `JARVIS_LITELLM_API_KEY`
- Check gateway configuration
- Verify API key format

```bash
# Test with correct API key
JARVIS_LITELLM_API_KEY=sk-your-key python -m jarvis.main
```

#### 3. Model Not Found
**Error**: `Model 'qwen-fast' not found`

**Solutions**:
- Check if model is configured in gateway
- Verify model name spelling
- Use full model name with provider prefix

```yaml
# In litellm_config.yaml
model_list:
  - model_name: qwen-fast
    litellm_params:
      model: openai/qwen-fast  # Ensure this matches
```

#### 4. Slow Response Times
**Symptoms**: Responses taking >10 seconds

**Solutions**:
- Check gateway performance
- Use faster models
- Enable caching
- Check network latency

```bash
# Test response time
time curl -X POST http://192.168.1.198:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen-fast", "messages": [{"role": "user", "content": "test"}]}'
```

### Debug Mode

Enable detailed logging:

```env
JARVIS_DEBUG=true
JARVIS_LOG_LEVEL=DEBUG
```

Or use LiteLLM debug:

```python
import litellm
litellm.set_verbose = True
```

### Health Check Script

Create a health check script:

```python
#!/usr/bin/env python3
"""LiteLLM health check"""

import asyncio
import aiohttp
from jarvis.config.settings import get_settings

async def health_check():
    """Check LiteLLM gateway health"""
    settings = get_settings()
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test basic connectivity
            async with session.get(f"{settings.litellm_base_url}/health") as resp:
                if resp.status == 200:
                    print("✅ Gateway is healthy")
                else:
                    print(f"⚠️ Gateway returned status {resp.status}")
            
            # Test model availability
            async with session.get(f"{settings.litellm_base_url}/v1/models") as resp:
                if resp.status == 200:
                    models = await resp.json()
                    print(f"✅ Available models: {len(models.get('data', []))}")
                else:
                    print("⚠️ Could not fetch models")
                    
    except Exception as e:
        print(f"❌ Health check failed: {e}")

if __name__ == "__main__":
    asyncio.run(health_check())
```

---

## 📚 Additional Resources

### Documentation
- [LiteLLM Official Docs](https://docs.litellm.ai/)
- [LiteLLM GitHub](https://github.com/BerriAI/litellm)
- [Provider Configuration](https://docs.litellm.ai/docs/providers)

### Configuration Examples
- [Docker Compose Setup](https://docs.litellm.ai/docs/simple_proxy)
- [Multi-Provider Config](https://docs.litellm.ai/docs/completion_proxy)
- [Load Balancing](https://docs.litellm.ai/docs/load_balancing)

### Community
- [LiteLLM Discord](https://discord.gg/vuVdZz9dNQ)
- [GitHub Discussions](https://github.com/BerriAI/litellm/discussions)

---

## 🎯 Best Practices

### 1. Model Selection
- Use fast models (`qwen-fast`) for quick responses
- Use capable models (`deepseek-chat`) for complex tasks
- Use local models (`ollama`) for privacy

### 2. Performance Optimization
- Enable request caching
- Use appropriate timeout values
- Monitor response times
- Set up alerts for failures

### 3. Cost Management
- Configure cost tracking
- Use cheaper models when possible
- Set usage limits
- Monitor token consumption

### 4. Reliability
- Set up multiple providers
- Configure proper failover
- Monitor gateway health
- Have backup models ready

---

For LiteLLM-specific issues:
- 📖 [LiteLLM Documentation](https://docs.litellm.ai/)
- 🐛 [LiteLLM GitHub Issues](https://github.com/BerriAI/litellm/issues)
- 💬 [MARK XLVI Discussions](https://github.com/your-repo/mark-xlvi/discussions)
