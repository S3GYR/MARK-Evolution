# M.A.R.K Evolution - Troubleshooting Guide

This guide covers common issues, error messages, and solutions for M.A.R.K Evolution.

## 🚨 Quick Diagnosis

### Health Check Script

Run this script to quickly diagnose common issues:

```bash
# Create health check
cat > health_check.py << 'EOF'
#!/usr/bin/env python3
"""M.A.R.K Evolution Health Check"""

import sys
import asyncio
import os
from pathlib import Path

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} (need 3.11+)")
        return False

def check_dependencies():
    """Check core dependencies"""
    try:
        import jarvis
        print("✅ MARK XLVI package")
    except ImportError as e:
        print(f"❌ MARK XLVI package: {e}")
        return False
    
    try:
        import litellm
        print("✅ LiteLLM")
    except ImportError:
        print("❌ LiteLLM not installed")
        return False
    
    try:
        import pydantic
        print("✅ Pydantic")
    except ImportError:
        print("❌ Pydantic not installed")
        return False
    
    return True

def check_configuration():
    """Check configuration files"""
    env_files = [".env", ".env.example", ".env.litellm"]
    
    for env_file in env_files:
        if Path(env_file).exists():
            print(f"✅ {env_file} exists")
        else:
            print(f"⚠️  {env_file} missing")
    
    try:
        from jarvis.config.settings import get_settings
        settings = get_settings()
        print(f"✅ Configuration loaded")
        print(f"   Provider: {settings.llm_provider}")
        print(f"   Model: {settings.default_model}")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

async def check_litellm_connection():
    """Check LiteLLM gateway"""
    try:
        from jarvis.llm.litellm_provider import get_litellm_provider
        provider = get_litellm_provider()
        
        # Test connection
        result = await provider.test_connection()
        if result["success"]:
            print(f"✅ LiteLLM Gateway: {result['response_time']:.2f}s")
            return True
        else:
            print(f"❌ LiteLLM Gateway: {result['error']}")
            return False
    except Exception as e:
        print(f"❌ LiteLLM connection error: {e}")
        return False

def check_memory_backend():
    """Check memory backend"""
    try:
        from jarvis.config.settings import get_settings
        settings = get_settings()
        
        if settings.memory_backend == "json":
            print("✅ JSON memory backend")
            return True
        elif settings.memory_backend == "postgres":
            try:
                from jarvis.memory.postgres_store import PostgresMemoryStore
                print("✅ PostgreSQL memory backend")
                return True
            except ImportError:
                print("❌ PostgreSQL dependencies missing")
                return False
        else:
            print(f"⚠️  Unknown memory backend: {settings.memory_backend}")
            return False
    except Exception as e:
        print(f"❌ Memory backend error: {e}")
        return False

async def main():
    """Run all health checks"""
    print("🏥 M.A.R.K Evolution Health Check")
    print("=" * 40)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Configuration", check_configuration),
        ("Memory Backend", check_memory_backend),
        ("LiteLLM Connection", check_litellm_connection),
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check in checks:
        print(f"\n🔍 {name}...")
        if asyncio.iscoroutinefunction(check):
            if await check():
                passed += 1
        else:
            if check():
                passed += 1
    
    print(f"\n📊 Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 M.A.R.K Evolution is healthy!")
    else:
        print("⚠️  Some issues detected. See solutions below.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
EOF

# Run health check
python health_check.py
```

---

## 🔧 Common Issues

### 1. Installation Issues

#### Python Version Incompatible
**Symptoms**: `SyntaxError`, `ImportError`, or version-specific errors

**Diagnosis**:
```bash
python --version
```

**Solutions**:
```bash
# Install Python 3.11+
# Windows: Download from python.org
# Ubuntu/Debian:
sudo apt install python3.11 python3.11-venv python3.11-dev

# Create new venv with correct Python
python3.11 -m venv .venv
source .venv/bin/activate  # Linux
.venv\Scripts\activate     # Windows
```

#### Dependencies Not Found
**Symptoms**: `ModuleNotFoundError: No module named 'jarvis'`

**Diagnosis**:
```bash
pip list | grep jarvis
```

**Solutions**:
```bash
# Reinstall in development mode
pip install -e .

# Install specific dependencies
pip install litellm pydantic pydantic-settings

# Install optional dependencies
pip install -e .[dashboard,audio,vision]
```

#### Visual C++ Build Tools Missing (Windows)
**Symptoms**: `error: Microsoft Visual C++ 14.0 is required`

**Solutions**:
1. Download [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. Install "C++ build tools" workload
3. Restart computer
4. Reinstall packages: `pip install --force-reinstall -e .`

---

### 2. Configuration Issues

#### Environment Variables Not Loading
**Symptoms**: Default values being used, configuration ignored

**Diagnosis**:
```bash
# Check if .env exists
ls -la .env*

# Check environment variables
env | grep JARVIS_
```

**Solutions**:
```bash
# Create .env file
cp .env.example .env

# Set correct permissions
chmod 600 .env

# Verify format (no spaces around =)
JARVIS_LLM_PROVIDER=litellm  # Correct
JARVIS_LLM_PROVIDER = litellm  # Incorrect
```

#### Invalid Configuration Values
**Symptoms**: `ValidationError`, `ValueError`, or startup failures

**Diagnosis**:
```bash
# Validate configuration
python -c "from jarvis.config.settings import get_settings; print(get_settings())"
```

**Solutions**:
```bash
# Check common value errors
JARVIS_LLM_TEMPERATURE=0.7  # Valid (0.0-2.0)
JARVIS_LLM_TEMPERATURE=3.0  # Invalid (>2.0)

JARVIS_DASHBOARD_PORT=8000  # Valid (1-65535)
JARVIS_DASHBOARD_PORT=70000 # Invalid (>65535)
```

---

### 3. LLM/LiteLLM Issues

#### LiteLLM Gateway Connection Failed
**Symptoms**: `Connection refused`, `Timeout`, or `Network unreachable`

**Diagnosis**:
```bash
# Test gateway connectivity
curl http://192.168.1.198:4000/health

# Check network
ping 192.168.1.198

# Verify URL in configuration
grep JARVIS_LITELLM_BASE_URL .env
```

**Solutions**:
```bash
# Update gateway URL
JARVIS_LITELLM_BASE_URL=http://localhost:4000

# Check if gateway is running
docker ps | grep litellm

# Restart gateway
docker restart litellm-container
```

#### Model Not Found
**Symptoms**: `Model 'qwen-fast' not found` or `Invalid model`

**Diagnosis**:
```bash
# List available models
curl http://192.168.1.198:4000/v1/models

# Check model mapping
python -c "from jarvis.llm.litellm_provider import get_litellm_provider; print(get_litellm_provider()._get_model('qwen-fast'))"
```

**Solutions**:
```bash
# Use correct model name
JARVIS_DEFAULT_MODEL=openai/qwen-fast

# Or add model to gateway config
# In litellm_config.yaml:
model_list:
  - model_name: qwen-fast
    litellm_params:
      model: openai/qwen-fast
```

#### API Key Authentication Error
**Symptoms**: `AuthenticationError`, `Invalid API key`, or `Unauthorized`

**Diagnosis**:
```bash
# Check API key format
echo $JARVIS_LITELLM_API_KEY

# Test with curl
curl -H "Authorization: Bearer $JARVIS_LITELLM_API_KEY" \
     http://192.168.1.198:4000/v1/models
```

**Solutions**:
```bash
# Update API key
JARVIS_LITELLM_API_KEY=sk-your-actual-key

# Or disable auth (development only)
JARVIS_LITELLM_API_KEY=dummy
```

---

### 4. Memory Issues

#### PostgreSQL Connection Failed
**Symptoms**: `Connection refused`, `authentication failed`, or `database does not exist`

**Diagnosis**:
```bash
# Test PostgreSQL connection
psql $JARVIS_POSTGRES_URL -c "SELECT 1;"

# Check if PostgreSQL is running
sudo systemctl status postgresql
```

**Solutions**:
```bash
# Use JSON backend instead
JARVIS_MEMORY_BACKEND=json

# Or fix PostgreSQL connection
JARVIS_POSTGRES_URL=postgresql://user:password@localhost:5432/jarvis

# Create database
createdb jarvis
```

#### Memory Not Persisting
**Symptoms**: Conversation history lost between sessions

**Diagnosis**:
```bash
# Check memory backend
python -c "from jarvis.config.settings import get_settings; print(get_settings().memory_backend)"

# Check data directory
ls -la ~/.local/share/jarvis/
```

**Solutions**:
```bash
# Ensure data directory exists
mkdir -p ~/.local/share/jarvis

# Check file permissions
ls -la ~/.local/share/jarvis/memory.json

# Use PostgreSQL for persistence
JARVIS_MEMORY_BACKEND=postgres
```

---

### 5. Dashboard Issues

#### Dashboard Not Accessible
**Symptoms**: `Connection refused` on http://127.0.0.1:8000

**Diagnosis**:
```bash
# Check if port is in use
netstat -tlnp | grep 8000

# Check dashboard logs
python -m jarvis.main --debug
```

**Solutions**:
```bash
# Change port
JARVIS_DASHBOARD_PORT=8080

# Allow external access
JARVIS_DASHBOARD_HOST=0.0.0.0

# Check firewall
sudo ufw allow 8000
```

#### WebSocket Connection Failed
**Symptoms**: Real-time updates not working, WebSocket errors

**Diagnosis**:
```bash
# Test WebSocket connection
wscat -c ws://127.0.0.1:8000/ws

# Check browser console for errors
```

**Solutions**:
```bash
# Check CORS settings
JARVIS_DEBUG=true  # Enable CORS in debug mode

# Use correct WebSocket URL
ws://127.0.0.1:8000/ws  # Not ws://localhost:8000/ws
```

---

### 6. GUI Issues

#### PyQt6 Not Available
**Symptoms**: `ImportError: No module named 'PyQt6'`

**Diagnosis**:
```bash
pip list | grep PyQt6
```

**Solutions**:
```bash
# Install PyQt6
pip install PyQt6

# Install system dependencies (Linux)
sudo apt install python3-pyqt6  # Ubuntu/Debian
sudo dnf install python3-qt6     # Fedora
```

#### GUI Window Not Appearing
**Symptoms**: Process starts but no window appears

**Diagnosis**:
```bash
# Run with debug output
python -m jarvis.main --gui --debug

# Check display server
echo $DISPLAY
```

**Solutions**:
```bash
# Set display (Linux)
export DISPLAY=:0

# Use virtual display (headless)
xvfb-run -a python -m jarvis.main --gui
```

---

### 7. Audio Issues

#### Audio Device Not Found
**Symptoms**: `No input device found` or audio recording errors

**Diagnosis**:
```bash
# List audio devices
python -c "import sounddevice; print(sounddevice.query_devices())"
```

**Solutions**:
```bash
# Specify audio device
JARVIS_AUDIO_DEVICE_INDEX=0

# Install audio drivers (Linux)
sudo apt install pulseaudio alsa-utils
```

#### FFmpeg Not Found
**Symptoms**: `FFmpeg not found` or audio processing errors

**Diagnosis**:
```bash
ffmpeg -version
```

**Solutions**:
```bash
# Install FFmpeg
# Ubuntu/Debian:
sudo apt install ffmpeg

# Windows: Download from ffmpeg.org
# macOS:
brew install ffmpeg
```

---

### 8. Browser Control Issues

#### Playwright Not Installed
**Symptoms**: `Playwright not found` or browser automation errors

**Diagnosis**:
```bash
python -c "import playwright; print('Playwright OK')"
```

**Solutions**:
```bash
# Install Playwright
pip install playwright

# Install browser binaries
python -m playwright install

# Install system dependencies
playwright install-deps
```

#### Browser Launch Failed
**Symptoms**: `Browser launch failed` or timeout errors

**Diagnosis**:
```bash
# Test browser launch
python -c "from playwright.sync_api import sync_playwright; sync_playwright().start().chromium.launch()"
```

**Solutions**:
```bash
# Install browser dependencies
# Ubuntu/Debian:
sudo apt install libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0

# Run headless
# In code: browser = playwright.chromium.launch(headless=True)
```

---

## 🔍 Debug Mode

Enable comprehensive debugging:

```bash
# Enable all debug features
JARVIS_DEBUG=true
JARVIS_LOG_LEVEL=DEBUG
python -m jarvis.main --debug
```

### Debug Categories

```bash
# LLM debugging
JARVIS_DEBUG=true python -c "
import litellm
litellm.set_verbose = True
from jarvis.llm.litellm_provider import get_litellm_provider
provider = get_litellm_provider()
"

# Memory debugging
JARVIS_DEBUG=true python -c "
from jarvis.memory.json_store import JsonMemoryStore
memory = JsonMemoryStore()
print(memory)
"

# Dashboard debugging
JARVIS_DEBUG=true python -m jarvis.main --debug
```

---

## 📊 Performance Issues

### Slow Response Times

**Diagnosis**:
```bash
# Test LLM response time
time curl -X POST http://192.168.1.198:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen-fast", "messages": [{"role": "user", "content": "test"}]}'
```

**Solutions**:
```bash
# Use faster model
JARVIS_DEFAULT_MODEL=qwen-fast

# Enable caching
JARVIS_CACHE_ENABLED=true

# Reduce token limit
JARVIS_LLM_MAX_TOKENS=1000
```

### High Memory Usage

**Diagnosis**:
```bash
# Check memory usage
ps aux | grep python
top -p $(pgrep -f "python.*jarvis")
```

**Solutions**:
```bash
# Limit conversation history
JARVIS_MEMORY_MAX_CHARS=2000

# Use JSON backend (lower memory)
JARVIS_MEMORY_BACKEND=json

# Clear cache periodically
JARVIS_CACHE_TTL=3600
```

---

## 🆘 Getting Help

### Log Files

Check log files for detailed error information:

```bash
# Application logs
tail -f ~/.local/share/jarvis/logs/jarvis.log

# Dashboard logs
tail -f ~/.local/share/jarvis/logs/dashboard.log

# System logs (Linux)
journalctl -u jarvis -f
```

### Support Channels

1. **Documentation**: Check [CONFIGURATION.md](CONFIGURATION.md) and [LITELLM.md](LITELLM.md)
2. **GitHub Issues**: [Create an issue](https://github.com/your-repo/mark-xlvi/issues) with:
   - Error message
   - Configuration file (remove sensitive data)
   - System information
   - Steps to reproduce

3. **Community**: [GitHub Discussions](https://github.com/your-repo/mark-xlvi/discussions)

### Bug Report Template

```markdown
## Bug Report
**MARK XLVI Version**: 46.0.0
**Operating System**: Windows 11 / Ubuntu 22.04
**Python Version**: 3.11.5

### Issue Description
[Describe the issue]

### Steps to Reproduce
1. 
2. 
3. 

### Error Message
```
[Paste error message here]
```

### Configuration
```env
[Paste .env file here, remove API keys]
```

### Logs
```
[Paste relevant log output here]
```
```

---

## 📚 Additional Resources

- [Installation Guide](INSTALLATION.md) - Setup instructions
- [Configuration Guide](CONFIGURATION.md) - All configuration options
- [LiteLLM Documentation](LITELLM.md) - LLM provider setup
- [Architecture Documentation](../ARCHITECTURE.md) - System overview

---

Remember: Most issues are related to configuration or dependencies. Always check the health check script first, then verify your configuration matches the examples in the documentation.
