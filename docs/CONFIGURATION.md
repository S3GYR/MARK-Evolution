# M.A.R.K Evolution - Configuration Guide

This guide covers all configuration options available in M.A.R.K Evolution, including environment variables, settings files, and runtime configuration.

## 📋 Configuration Overview

M.A.R.K Evolution uses a hierarchical configuration system:

1. **Environment Variables** (`.env` file)
2. **Settings Files** (`settings.py`)
3. **Runtime Arguments** (command line)
4. **Default Values** (built-in defaults)

Configuration is loaded from `.env` files in the following order:
1. `.env.local` (highest priority)
2. `.env` 
3. `.env.example` (lowest priority, for reference)

---

## 🔧 Core Configuration

### General Settings

| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `JARVIS_APP_NAME` | `JARVIS` | Application name | `JARVIS_APP_NAME="MyAssistant"` |
| `JARVIS_DEBUG` | `false` | Enable debug mode | `JARVIS_DEBUG=true` |
| `JARVIS_LOG_LEVEL` | `INFO` | Logging level | `JARVIS_LOG_LEVEL=DEBUG` |

**Example:**
```env
JARVIS_APP_NAME=MARK_XLVI
JARVIS_DEBUG=false
JARVIS_LOG_LEVEL=INFO
```

---

## 🤖 LLM Configuration

### LiteLLM Provider Settings

| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `JARVIS_LLM_PROVIDER` | `litellm` | LLM provider to use | `JARVIS_LLM_PROVIDER=litellm` |
| `JARVIS_LLM_MODEL` | `auto` | Default model name | `JARVIS_LLM_MODEL=qwen-fast` |
| `JARVIS_LLM_TEMPERATURE` | `0.7` | Response randomness (0.0-2.0) | `JARVIS_LLM_TEMPERATURE=0.5` |
| `JARVIS_LLM_MAX_TOKENS` | `null` | Maximum response tokens | `JARVIS_LLM_MAX_TOKENS=2048` |

### LiteLLM Gateway Settings

| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `JARVIS_LITELLM_BASE_URL` | `http://192.168.1.198:4000` | LiteLLM gateway URL | `JARVIS_LITELLM_BASE_URL=http://localhost:4000` |
| `JARVIS_LITELLM_API_KEY` | `dummy` | LiteLLM API key | `JARVIS_LITELLM_API_KEY=sk-123456` |
| `JARVIS_DEFAULT_MODEL` | `qwen-fast` | Default model for requests | `JARVIS_DEFAULT_MODEL=deepseek-chat` |

**Complete LLM Configuration:**
```env
# Provider Configuration
JARVIS_LLM_PROVIDER=litellm
JARVIS_LLM_MODEL=auto
JARVIS_LLM_TEMPERATURE=0.7
JARVIS_LLM_MAX_TOKENS=4096

# LiteLLM Gateway
JARVIS_LITELLM_BASE_URL=http://192.168.1.198:4000
JARVIS_LITELLM_API_KEY=dummy
JARVIS_DEFAULT_MODEL=qwen-fast
```

---

## 💾 Memory Configuration

### Memory Backend Settings

| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `JARVIS_MEMORY_BACKEND` | `postgres` | Memory storage backend | `JARVIS_MEMORY_BACKEND=json` |
| `JARVIS_POSTGRES_URL` | `null` | PostgreSQL connection string | `JARVIS_POSTGRES_URL=postgresql://user:pass@localhost/jarvis` |
| `JARVIS_MEMORY_MAX_CHARS` | `4000` | Max characters per memory entry | `JARVIS_MEMORY_MAX_CHARS=8000` |

### Vector Settings

| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `JARVIS_VECTOR_DIM` | `768` | Vector dimension for embeddings | `JARVIS_VECTOR_DIM=1536` |

**Memory Configuration Examples:**

**JSON Backend (Simple):**
```env
JARVIS_MEMORY_BACKEND=json
JARVIS_MEMORY_MAX_CHARS=4000
```

**PostgreSQL Backend (Advanced):**
```env
JARVIS_MEMORY_BACKEND=postgres
JARVIS_POSTGRES_URL=postgresql://jarvis:password@localhost:5432/jarvis
JARVIS_VECTOR_DIM=768
JARVIS_MEMORY_MAX_CHARS=8000
```

---

## 🌐 Dashboard Configuration

### Web Server Settings

| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `JARVIS_DASHBOARD_HOST` | `127.0.0.1` | Dashboard bind address | `JARVIS_DASHBOARD_HOST=0.0.0.0` |
| `JARVIS_DASHBOARD_PORT` | `8000` | Dashboard port | `JARVIS_DASHBOARD_PORT=8080` |
| `JARVIS_DASHBOARD_MAX_UPLOAD_MB` | `500` | Max upload size in MB | `JARVIS_DASHBOARD_MAX_UPLOAD_MB=100` |

### Authentication Settings

| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `JARVIS_DASHBOARD_AUTH_TOKEN_TTL` | `3600` | Auth token TTL (seconds) | `JARVIS_DASHBOARD_AUTH_TOKEN_TTL=7200` |
| `JARVIS_DASHBOARD_AUTO_FIREWALL` | `false` | Enable automatic firewall | `JARVIS_DASHBOARD_AUTO_FIREWALL=true` |

**Dashboard Configuration:**
```env
# Server Settings
JARVIS_DASHBOARD_HOST=127.0.0.1
JARVIS_DASHBOARD_PORT=8000
JARVIS_DASHBOARD_MAX_UPLOAD_MB=500

# Security
JARVIS_DASHBOARD_AUTH_TOKEN_TTL=3600
JARVIS_DASHBOARD_AUTO_FIREWALL=false
```

---

## 🔒 Security Configuration

### General Security

| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `JARVIS_REQUIRE_CONFIRMATION` | `true` | Require confirmation for actions | `JARVIS_REQUIRE_CONFIRMATION=false` |
| `JARVIS_SANDBOX_ENABLED` | `true` | Enable execution sandbox | `JARVIS_SANDBOX_ENABLED=true` |

**Security Configuration:**
```env
JARVIS_REQUIRE_CONFIRMATION=true
JARVIS_SANDBOX_ENABLED=true
```

---

## 🎵 Audio Configuration

### Audio Settings

| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `JARVIS_AUDIO_CHANNELS` | `1` | Number of audio channels | `JARVIS_AUDIO_CHANNELS=2` |
| `JARVIS_AUDIO_SEND_SAMPLE_RATE` | `16000` | Input sample rate (Hz) | `JARVIS_AUDIO_SEND_SAMPLE_RATE=44100` |
| `JARVIS_AUDIO_RECEIVE_SAMPLE_RATE` | `24000` | Output sample rate (Hz) | `JARVIS_AUDIO_RECEIVE_SAMPLE_RATE=48000` |
| `JARVIS_AUDIO_CHUNK_SIZE` | `1024` | Audio chunk size | `JARVIS_AUDIO_CHUNK_SIZE=2048` |
| `JARVIS_AUDIO_DEVICE_INDEX` | `null` | Specific audio device index | `JARVIS_AUDIO_DEVICE_INDEX=0` |

**Audio Configuration:**
```env
JARVIS_AUDIO_CHANNELS=1
JARVIS_AUDIO_SEND_SAMPLE_RATE=16000
JARVIS_AUDIO_RECEIVE_SAMPLE_RATE=24000
JARVIS_AUDIO_CHUNK_SIZE=1024
```

---

## 🧠 Embeddings Configuration

### Embedding Provider Settings

| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `JARVIS_EMBEDDING_PROVIDER` | `sentence-transformers` | Embedding provider | `JARVIS_EMBEDDING_PROVIDER=litellm` |
| `JARVIS_EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Embedding model | `JARVIS_EMBEDDING_MODEL=text-embedding-ada-002` |
| `JARVIS_EMBEDDING_DEVICE` | `cpu` | Computation device | `JARVIS_EMBEDDING_DEVICE=cuda` |
| `JARVIS_EMBEDDING_FALLBACK_TO_MOCK` | `true` | Use mock on failure | `JARVIS_EMBEDDING_FALLBACK_TO_MOCK=false` |

**Embeddings Configuration:**
```env
JARVIS_EMBEDDING_PROVIDER=sentence-transformers
JARVIS_EMBEDDING_MODEL=all-MiniLM-L6-v2
JARVIS_EMBEDDING_DEVICE=cpu
JARVIS_EMBEDDING_FALLBACK_TO_MOCK=true
```

---

## 📁 Path Configuration

### Directory Paths

| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `JARVIS_DATA_DIR` | `~/.local/share/jarvis` | Data directory | `JARVIS_DATA_DIR=/opt/jarvis/data` |
| `JARVIS_CONFIG_DIR` | `~/.config/jarvis` | Configuration directory | `JARVIS_CONFIG_DIR=/etc/jarvis` |
| `JARVIS_CACHE_DIR` | `~/.cache/jarvis` | Cache directory | `JARVIS_CACHE_DIR=/tmp/jarvis-cache` |

---

## 🔍 Advanced Configuration

### Performance Tuning

| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `JARVIS_WORKER_THREADS` | `4` | Number of worker threads | `JARVIS_WORKER_THREADS=8` |
| `JARVIS_MAX_CONCURRENT_REQUESTS` | `10` | Max concurrent LLM requests | `JARVIS_MAX_CONCURRENT_REQUESTS=20` |

### Development Settings

| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `JARVIS_RELOAD_ON_CHANGE` | `false` | Auto-reload on code changes | `JARVIS_RELOAD_ON_CHANGE=true` |
| `JARVIS_PROFILING_ENABLED` | `false` | Enable performance profiling | `JARVIS_PROFILING_ENABLED=true` |

---

## 📝 Configuration Files

### .env File Structure

Create a `.env` file in your project root:

```env
# ========================================
# MARK XLVI Configuration
# ========================================

# General Settings
JARVIS_APP_NAME=MARK_XLVI
JARVIS_DEBUG=false
JARVIS_LOG_LEVEL=INFO

# LLM Configuration
JARVIS_LLM_PROVIDER=litellm
JARVIS_LITELLM_BASE_URL=http://192.168.1.198:4000
JARVIS_LITELLM_API_KEY=dummy
JARVIS_DEFAULT_MODEL=qwen-fast
JARVIS_LLM_TEMPERATURE=0.7
JARVIS_LLM_MAX_TOKENS=4096

# Memory Configuration
JARVIS_MEMORY_BACKEND=json
JARVIS_MEMORY_MAX_CHARS=4000
JARVIS_VECTOR_DIM=768

# Dashboard Configuration
JARVIS_DASHBOARD_HOST=127.0.0.1
JARVIS_DASHBOARD_PORT=8000
JARVIS_DASHBOARD_MAX_UPLOAD_MB=500

# Security Configuration
JARVIS_REQUIRE_CONFIRMATION=true
JARVIS_SANDBOX_ENABLED=true

# Audio Configuration
JARVIS_AUDIO_CHANNELS=1
JARVIS_AUDIO_SEND_SAMPLE_RATE=16000
JARVIS_AUDIO_RECEIVE_SAMPLE_RATE=24000

# Embeddings Configuration
JARVIS_EMBEDDING_PROVIDER=sentence-transformers
JARVIS_EMBEDDING_MODEL=all-MiniLM-L6-v2
JARVIS_EMBEDDING_DEVICE=cpu
```

### Environment-Specific Configuration

**Development (.env.development):**
```env
JARVIS_DEBUG=true
JARVIS_LOG_LEVEL=DEBUG
JARVIS_RELOAD_ON_CHANGE=true
```

**Production (.env.production):**
```env
JARVIS_DEBUG=false
JARVIS_LOG_LEVEL=INFO
JARVIS_DASHBOARD_HOST=0.0.0.0
JARVIS_REQUIRE_CONFIRMATION=true
```

**Testing (.env.test):**
```env
JARVIS_MEMORY_BACKEND=json
JARVIS_LLM_PROVIDER=mock
JARVIS_LOG_LEVEL=ERROR
```

---

## 🧪 Configuration Validation

### Test Configuration Script

Create a script to validate your configuration:

```python
#!/usr/bin/env python3
"""Validate MARK XLVI configuration"""

import os
from jarvis.config.settings import get_settings

def validate_configuration():
    """Validate current configuration"""
    print("🔍 MARK XLVI Configuration Validation")
    print("=" * 50)
    
    try:
        settings = get_settings()
        
        # Core Settings
        print(f"✅ App Name: {settings.app_name}")
        print(f"✅ Debug Mode: {settings.debug}")
        print(f"✅ Log Level: {settings.log_level}")
        
        # LLM Settings
        print(f"✅ LLM Provider: {settings.llm_provider}")
        print(f"✅ Default Model: {settings.default_model}")
        print(f"✅ LiteLLM Base URL: {settings.litellm_base_url}")
        
        # Memory Settings
        print(f"✅ Memory Backend: {settings.memory_backend}")
        print(f"✅ Vector Dim: {settings.vector_dim}")
        
        # Dashboard Settings
        print(f"✅ Dashboard Host: {settings.dashboard_host}")
        print(f"✅ Dashboard Port: {settings.dashboard_port}")
        
        # Security Settings
        print(f"✅ Require Confirmation: {settings.require_confirmation}")
        print(f"✅ Sandbox Enabled: {settings.sandbox_enabled}")
        
        print("\n🎉 Configuration is valid!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

if __name__ == "__main__":
    validate_configuration()
```

Run the validation:
```bash
python validate_config.py
```

---

## 🔄 Runtime Configuration

### Command Line Arguments

MARK XLVI supports several command line arguments:

```bash
# Basic usage
python -m jarvis.main

# Enable GUI
python -m jarvis.main --gui

# Specify configuration file
python -m jarvis.main --config custom.env

# Enable debug mode
python -m jarvis.main --debug

# Override specific settings
python -m jarvis.main --set JARVIS_LOG_LEVEL=DEBUG
```

### Environment Override

You can override any configuration variable at runtime:

```bash
# Override log level
JARVIS_LOG_LEVEL=DEBUG python -m jarvis.main

# Override LLM model
JARVIS_DEFAULT_MODEL=deepseek-chat python -m jarvis.main

# Override memory backend
JARVIS_MEMORY_BACKEND=postgres python -m jarvis.main
```

---

## 📊 Configuration Examples

### Minimal Configuration
```env
JARVIS_LLM_PROVIDER=litellm
JARVIS_LITELLM_BASE_URL=http://192.168.1.198:4000
JARVIS_DEFAULT_MODEL=qwen-fast
JARVIS_MEMORY_BACKEND=json
```

### Production Configuration
```env
JARVIS_DEBUG=false
JARVIS_LOG_LEVEL=INFO
JARVIS_LLM_PROVIDER=litellm
JARVIS_LITELLM_BASE_URL=https://litellm.example.com
JARVIS_LITELLM_API_KEY=sk-your-api-key
JARVIS_DEFAULT_MODEL=gpt-4
JARVIS_MEMORY_BACKEND=postgres
JARVIS_POSTGRES_URL=postgresql://jarvis:password@db.example.com/jarvis
JARVIS_DASHBOARD_HOST=0.0.0.0
JARVIS_DASHBOARD_PORT=8000
JARVIS_REQUIRE_CONFIRMATION=true
JARVIS_SANDBOX_ENABLED=true
```

### Development Configuration
```env
JARVIS_DEBUG=true
JARVIS_LOG_LEVEL=DEBUG
JARVIS_LLM_PROVIDER=mock
JARVIS_MEMORY_BACKEND=json
JARVIS_RELOAD_ON_CHANGE=true
JARVIS_PROFILING_ENABLED=true
```

---

## 🆘 Configuration Troubleshooting

### Common Issues

#### Configuration Not Loading
```bash
# Check if .env file exists
ls -la .env*

# Verify file permissions
chmod 600 .env

# Check environment variables
env | grep JARVIS_
```

#### Invalid Values
```bash
# Validate with debug mode
JARVIS_DEBUG=true python -m jarvis.main --help

# Check specific setting
python -c "from jarvis.config.settings import get_settings; print(get_settings().llm_provider)"
```

#### Memory Backend Issues
```bash
# Test JSON backend
JARVIS_MEMORY_BACKEND=json python -c "from jarvis.memory.json_store import JsonMemoryStore; print('JSON OK')"

# Test PostgreSQL backend
JARVIS_MEMORY_BACKEND=postgres JARVIS_POSTGRES_URL=postgresql://user:pass@localhost/test python -c "from jarvis.memory.postgres_store import PostgresMemoryStore; print('PostgreSQL OK')"
```

---

## 📚 Additional Resources

- [LiteLLM Configuration](LITELLM.md) - Detailed LiteLLM setup
- [Installation Guide](INSTALLATION.md) - System setup instructions
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions

For configuration-specific questions:
- 🐛 [GitHub Issues](https://github.com/your-repo/mark-xlvi/issues)
- 💬 [GitHub Discussions](https://github.com/your-repo/mark-xlvi/discussions)
