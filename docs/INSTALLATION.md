# M.A.R.K Evolution - Installation Guide

This guide provides step-by-step instructions for installing M.A.R.K Evolution on Windows and Linux systems.

## 📋 Prerequisites

### System Requirements
- **Operating System**: Windows 10+ or Linux (Ubuntu 20.04+, Debian 11+, Fedora 35+)
- **Python**: 3.11 or higher (3.11, 3.12, 3.13 supported)
- **RAM**: 4GB minimum, 8GB+ recommended
- **Storage**: 2GB free space
- **GPU**: Optional but recommended for LLM performance

### Required Software
- **Python 3.11+** with pip
- **Git** for cloning the repository
- **Visual C++ Build Tools** (Windows only)
- **FFmpeg** (for audio processing)

---

## 🪟 Windows Installation

### Step 1: Install Python

1. Download Python 3.11+ from [python.org](https://www.python.org/downloads/)
2. Run the installer with **"Add Python to PATH"** checked
3. Verify installation:
```powershell
python --version
pip --version
```

### Step 2: Install Visual C++ Build Tools

Required for compiling some Python packages:

1. Download [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. Install "C++ build tools" workload
3. Restart your computer

### Step 3: Install Git

1. Download Git from [git-scm.com](https://git-scm.com/download/win)
2. Install with default settings
3. Verify installation:
```powershell
git --version
```

### Step 4: Install FFmpeg

1. Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to your PATH environment variable
4. Verify installation:
```powershell
ffmpeg -version
```

### Step 5: Clone and Install MARK XLVI

```powershell
# Clone the repository
git clone https://github.com/your-repo/mark-xlvi.git
cd mark-xlvi

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip

# Install MARK XLVI with all dependencies
pip install -e .

# Install optional dependencies for dashboard
pip install -e .[dashboard]

# Install optional dependencies for browser control
pip install -e .[browser]

# Install optional dependencies for audio processing
pip install -e .[audio]

# Install optional dependencies for vision
pip install -e .[vision]
```

### Step 6: Verify Installation

```powershell
# Test basic import
python -c "import jarvis; print('MARK XLVI imported successfully')"

# Test LLM connection
python test_litellm_mock.py

# Test main entry point
python -m jarvis.main --help
```

---

## 🐧 Linux Installation

### Ubuntu/Debian

#### Step 1: Install System Dependencies

```bash
# Update package list
sudo apt update

# Install Python and build tools
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install Git
sudo apt install -y git

# Install FFmpeg
sudo apt install -y ffmpeg

# Install system libraries for GUI
sudo apt install -y libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1

# Install build essentials
sudo apt install -y build-essential cmake pkg-config
```

#### Step 2: Clone and Install MARK XLVI

```bash
# Clone the repository
git clone https://github.com/your-repo/mark-xlvi.git
cd mark-xlvi

# Create virtual environment
python3.11 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install MARK XLVI with all dependencies
pip install -e .

# Install optional dependencies
pip install -e .[dashboard]
pip install -e .[browser]
pip install -e .[audio]
pip install -e .[vision]
```

### Fedora

#### Step 1: Install System Dependencies

```bash
# Update package list
sudo dnf update

# Install Python and build tools
sudo dnf install -y python3.11 python3.11-devel python3-pip

# Install Git
sudo dnf install -y git

# Install FFmpeg
sudo dnf install -y ffmpeg

# Install system libraries
sudo dnf install -y mesa-libGL glib2 libSM libXext libXrender libgomp

# Install build tools
sudo dnf groupinstall -y "Development Tools"
sudo dnf install -y cmake pkg-config
```

#### Step 2: Clone and Install MARK XLVI

```bash
# Same as Ubuntu/Debian
git clone https://github.com/your-repo/mark-xlvi.git
cd mark-xlvi
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
pip install -e .[dashboard,browser,audio,vision]
```

### Arch Linux

#### Step 1: Install System Dependencies

```bash
# Update package list
sudo pacman -Syu

# Install Python and build tools
sudo pacman -S python python-pip git

# Install FFmpeg
sudo pacman -S ffmpeg

# Install system libraries
sudo pacman -S mesa libgl libsm libxext libxrender

# Install build tools
sudo pacman -S base-devel cmake pkgconf
```

#### Step 2: Clone and Install MARK XLVI

```bash
# Same as other distributions
git clone https://github.com/your-repo/mark-xlvi.git
cd mark-xlvi
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
pip install -e .[dashboard,browser,audio,vision]
```

---

## 🔧 Post-Installation Configuration

### Step 1: Create Configuration File

Create a `.env` file in the project root:

```bash
# Copy the example configuration
cp .env.example .env

# Or use the LiteLLM template
cp .env.litellm .env
```

Edit the `.env` file with your configuration:

```env
# LLM Configuration
JARVIS_LLM_PROVIDER=litellm
JARVIS_LITELLM_BASE_URL=http://192.168.1.198:4000
JARVIS_LITELLM_API_KEY=dummy
JARVIS_DEFAULT_MODEL=qwen-fast

# Memory Configuration
JARVIS_MEMORY_BACKEND=json

# Logging
JARVIS_LOG_LEVEL=INFO
JARVIS_DEBUG=false

# Dashboard (optional)
JARVIS_DASHBOARD_HOST=127.0.0.1
JARVIS_DASHBOARD_PORT=8000
```

### Step 2: Initialize Browser Control (Optional)

If you plan to use browser control features:

```bash
# Install Playwright browsers
python -m playwright install

# Install browser dependencies (Linux only)
# Ubuntu/Debian:
sudo apt install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2

# Fedora:
sudo dnf install -y nss atk-bridge libdrm libxkbcommon libXcomposite libXdamage libXrandr libgbm libXss alsa-lib
```

### Step 3: Verify Installation

```bash
# Test basic functionality
python -c "
from jarvis.config.settings import get_settings
from jarvis.llm.litellm_provider import get_litellm_provider
print('✅ Configuration loaded')
print('✅ LiteLLM provider initialized')
print(f'Default model: {get_settings().default_model}')
"

# Test LLM connection
python test_litellm_mock.py

# Test CLI interface
python -m jarvis.main --help
```

---

## 🚀 First Run

### CLI Interface

```bash
# Activate virtual environment first
# Windows:
.venv\Scripts\activate
# Linux:
source .venv/bin/activate

# Run MARK XLVI
python -m jarvis.main
```

### GUI Application

```bash
# Run with GUI
python -m jarvis.main --gui
```

### Web Dashboard

```bash
# Start with dashboard (default)
python -m jarvis.main

# Access at: http://127.0.0.1:8000
```

---

## 🔍 Troubleshooting Installation

### Common Issues

#### Python Version Issues
```bash
# Check Python version
python --version

# If wrong version, install Python 3.11+
# Or use python3.11 explicitly:
python3.11 -m venv .venv
```

#### Permission Denied (Linux)
```bash
# Use user install for system packages
pip install --user -e .

# Or fix permissions
sudo chown -R $USER:$USER .venv
```

#### Missing Visual C++ (Windows)
- Install Visual Studio Build Tools 2019 or later
- Restart computer after installation

#### FFmpeg Not Found
- Add FFmpeg to PATH environment variable
- Or install via package manager (Linux)

#### GUI Issues on Linux
```bash
# Install additional GUI libraries
# Ubuntu/Debian:
sudo apt install -y libxcb-cursor0 libxcb-xinerama0

# Fedora:
sudo dnf install -y libxcb-cursor0 libxcb-xinerama0
```

#### Browser Control Issues
```bash
# Reinstall Playwright
pip uninstall playwright
pip install playwright
python -m playwright install

# Install system dependencies
playwright install-deps
```

---

## 📦 Optional Components

### Audio Processing
```bash
# Install additional audio dependencies
pip install -e .[audio]

# Test audio
python -c "import sounddevice; print('Audio processing available')"
```

### Computer Vision
```bash
# Install vision dependencies
pip install -e .[vision]

# Test camera
python -c "import cv2; print('Computer vision available')"
```

### PostgreSQL Memory
```bash
# Install PostgreSQL adapter
pip install psycopg[binary]

# Update .env
JARVIS_MEMORY_BACKEND=postgres
JARVIS_POSTGRES_URL=postgresql://user:password@localhost/jarvis
```

---

## ✅ Installation Verification

Run this comprehensive test to verify your installation:

```bash
# Create test script
cat > test_installation.py << 'EOF'
#!/usr/bin/env python3
"""Test MARK XLVI installation"""

import sys
from pathlib import Path

def test_imports():
    """Test all major imports"""
    try:
        from jarvis.config.settings import get_settings
        from jarvis.llm.litellm_provider import get_litellm_provider
        from jarvis.core.orchestrator import AgentOrchestrator
        from jarvis.memory.json_store import JsonMemoryStore
        print("✅ Core imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_settings():
    """Test configuration loading"""
    try:
        settings = get_settings()
        print(f"✅ Settings loaded - Provider: {settings.llm_provider}")
        return True
    except Exception as e:
        print(f"❌ Settings error: {e}")
        return False

def test_litellm():
    """Test LiteLLM provider"""
    try:
        provider = get_litellm_provider()
        stats = provider.get_stats()
        print(f"✅ LiteLLM provider ready - Base URL: {stats['base_url']}")
        return True
    except Exception as e:
        print(f"❌ LiteLLM error: {e}")
        return False

def main():
    print("🧪 MARK XLVI Installation Test")
    print("=" * 40)
    
    tests = [
        ("Core Imports", test_imports),
        ("Settings", test_settings),
        ("LiteLLM", test_litellm),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test in tests:
        print(f"\n📋 Testing {name}...")
        if test():
            passed += 1
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Installation successful!")
        return True
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
EOF

# Run the test
python test_installation.py
```

If all tests pass, your MARK XLVI installation is ready to use!

---

## 🆘 Getting Help

If you encounter issues during installation:

1. **Check the logs**: Run with `JARVIS_LOG_LEVEL=DEBUG` for detailed output
2. **Verify dependencies**: Ensure all system requirements are met
3. **Check permissions**: Make sure you have write access to the project directory
4. **Update packages**: Run `pip install --upgrade pip setuptools wheel`
5. **Consult documentation**: Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common solutions

For additional support:
- 📖 [Documentation](../README.md)
- 🐛 [GitHub Issues](https://github.com/your-repo/mark-xlvi/issues)
- 💬 [GitHub Discussions](https://github.com/your-repo/mark-xlvi/discussions)
