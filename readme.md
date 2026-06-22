# M.A.R.K Evolution

> **The AI Command Center - Modular Autonomous Reasoning Keeper Platform**

M.A.R.K Evolution is a Modular Autonomous Reasoning Keeper platform designed to orchestrate AI models, autonomous agents, memory systems and automation tools through a unified architecture. The platform acts as an AI Command Center capable of reasoning, planning, executing actions and coordinating multiple specialized agents using a centralized LiteLLM infrastructure.

## ✨ Features

### 🤖 AI Capabilities
- **LiteLLM Integration** - Single gateway to multiple LLM providers (NVIDIA, DeepSeek, Gemini, Ollama)
- **Smart Routing** - Automatic failover and load balancing
- **Memory System** - Persistent conversation memory with PostgreSQL/pgvector or JSON fallback
- **Tool Execution** - Secure sandboxed execution of system commands and web interactions

### 🖥️ Multiple Interfaces
- **CLI Interface** - Interactive command-line interface
- **GUI Application** - Modern PyQt6 desktop interface
- **Web Dashboard** - FastAPI-based web interface with real-time updates
- **WebSocket Support** - Real-time bidirectional communication

### 🔒 Security & Architecture
- **Sandboxed Execution** - Secure tool execution with permission framework
- **Dynamic Certificates** - Automatic SSL certificate generation
- **Secret Management** - Secure API key storage with keyring
- **Modular Design** - Clean separation of concerns with plugin architecture

### 🛠️ Advanced Features
- **Browser Control** - Automated web interactions via Playwright
- **Audio Processing** - Real-time audio capture and playback
- **File Operations** - Secure file management with trash support
- **System Integration** - Deep OS integration with monitoring capabilities

## 🏗️ Architecture

```
M.A.R.K Evolution
├── jarvis/
│   ├── core/           # Orchestrator and player logic
│   ├── llm/            # LiteLLM integration and routing
│   ├── memory/         # PostgreSQL and JSON memory stores
│   ├── web/            # FastAPI dashboard and WebSocket
│   ├── ui/             # PyQt6 desktop interface
│   ├── tools/          # Secure tool execution framework
│   ├── audio/          # Audio processing pipeline
│   ├── security/       # Certificates, secrets, permissions
│   ├── observability/  # Logging and tracing
│   └── config/         # Settings and configuration
└── dashboard/          # Static web assets
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** (tested on 3.11, 3.12, 3.13)
- **Windows 10+** or **Linux** (Ubuntu/Debian/Fedora)
- **4GB+ RAM** recommended
- **GPU** optional but recommended for LLM performance

### Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/mark-xlvi.git
cd mark-xlvi

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -e .

# Optional: Install dashboard dependencies
pip install -e .[dashboard]

# Optional: Install browser control dependencies
pip install -e .[browser]
```

### Configuration

Create a `.env` file in the project root:

```env
# LLM Configuration
JARVIS_LLM_PROVIDER=litellm
JARVIS_LITELLM_BASE_URL=http://192.168.1.198:4000
JARVIS_LITELLM_API_KEY=dummy
JARVIS_DEFAULT_MODEL=qwen-fast

# Memory Configuration
JARVIS_MEMORY_BACKEND=json

# General Settings
JARVIS_LOG_LEVEL=INFO
JARVIS_DEBUG=false
```

### Running MARK XLVI

#### CLI Interface
```bash
python -m jarvis.main
```

#### GUI Application
```bash
python -m jarvis.main --gui
```

#### Web Dashboard
```bash
# Start the application (dashboard runs automatically)
python -m jarvis.main

# Access at: http://127.0.0.1:8000
```

## � Documentation

- **[Installation Guide](docs/INSTALLATION.md)** - Detailed setup instructions
- **[Configuration](docs/CONFIGURATION.md)** - Complete configuration reference
- **[LiteLLM Setup](docs/LITELLM.md)** - LLM provider configuration
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

## 🔧 Development

### Project Structure

```
mark-xlvi/
├── jarvis/                 # Main application package
│   ├── main.py            # Modular entry point
│   ├── core/              # Core orchestration logic
│   ├── llm/               # LLM integration
│   ├── memory/            # Memory management
│   ├── web/               # Web dashboard
│   ├── ui/                # Desktop interface
│   ├── tools/             # Tool execution
│   ├── audio/             # Audio processing
│   ├── security/          # Security components
│   ├── observability/     # Logging & tracing
│   └── config/            # Configuration
├── tests/                 # Test suite
├── dashboard/             # Web assets
├── docs/                  # Documentation
└── pyproject.toml         # Project configuration
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=jarvis

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
```

### Code Quality

```bash
# Format code
black jarvis/

# Type checking
mypy jarvis/

# Security audit
bandit -r jarvis/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the BY-NC 4.0 License - see the [LICENSE](LICENSE) file for details.

## 🔗 Dependencies

### Core Dependencies
- **litellm** - LLM provider abstraction
- **pydantic** - Data validation and settings
- **fastapi** - Web framework (dashboard)
- **PyQt6** - Desktop GUI framework
- **psycopg** - PostgreSQL adapter
- **cryptography** - Security operations

### Optional Dependencies
- **playwright** - Browser automation
- **sentence-transformers** - Text embeddings
- **opencv-python** - Computer vision
- **whisper** - Speech recognition

## 🆘 Support

- 📖 **Documentation** - Check the [docs](docs/) folder
- 🐛 **Issues** - [GitHub Issues](https://github.com/your-repo/mark-xlvi/issues)
- 💬 **Discussions** - [GitHub Discussions](https://github.com/your-repo/mark-xlvi/discussions)

## 🎯 Roadmap

- [ ] **Enhanced Memory** - Vector search and semantic memory
- [ ] **Plugin System** - Dynamic plugin loading
- [ ] **Multi-modal** - Image and audio processing
- [ ] **Cloud Deployment** - Docker and Kubernetes support
- [ ] **Mobile App** - React Native interface

---

**M.A.R.K Evolution** - *The AI Command Center*

*Reason. Remember. Act. Evolve.*

Made with ❤️ by the FatihMakes team

A real-time voice AI that can hear, see, understand, and control your computer — on any OS. Supporting Windows, macOS, and Linux. Built with Gemini integration for maximum stability and performance, delivering zero subscriptions and total digital autonomy.

---

## ✨ Overview

MARK XLVI represents a massive milestone in the Jarvis series, evolving into a fully connected, highly persistent, and remote-accessible system. It completely bridges the gap between your mobile device, desktop OS, and human intent. Through real-time Gemini reasoning, Mark 46 allows you to control your PC from your phone, share large files securely, and maintain deep contextual conversations across sessions.

It's not just an assistant — it's an extension of your digital life.

---

## 🚀 Capabilities

### Core Features
| Feature | Description |
|---|---|
| 🎙️ Real-time Voice | Ultra-low latency conversation in any language |
| 🖥️ System Control | Launch apps, manage files, execute terminal commands |
| 🧩 Autonomous Tasks | High-level planning for complex, multi-step goals |
| 👁️ Visual Awareness | Real-time screen processing and webcam vision |
| 🧠 Persistent Memory | Deeply remembers your projects, preferences, and personal context |
| ⌨️ Hybrid Input | Seamlessly switch between keyboard typing and voice commands |

---

## 🆕 What's New in XLVI

- 📱 **Full Remote Phone Control** — Take command of your entire desktop operating system directly from your smartphone, anywhere, anytime.
- 🧠 **Advanced Long-Term Memory** — Upgraded memory architecture allows Jarvis to contextually remember past interactions, preferences, and complex workflows across reboots.
- 🚀 **Powered by Gemini Integration** — Re-engineered from the ground up to utilize the full speed and precision of the Google Gemini API for ultimate reasoning and stability.
- ⚡ **Next-Gen Performance & Stability** — Comprehensive system-wide optimizations delivering faster response times and rock-solid execution on Windows, Mac, and Linux.
- 📂 **Advanced File Handling & Hybrid Input** — Fluidly switch between voice or keyboard input, and drag-and-drop code, PDFs, or images for instant analysis and automation.
- 🔒 **Secure Mobile File Sharing** — Wirelessly and securely share files or entire folders up to 500 MB from your phone directly to your computer with complete privacy.

---

## ⚡ Quick Start

```bash
git clone [https://github.com/FatihMakes/Mark-XLVI.git](https://github.com/FatihMakes/Mark-XLVI.git)
cd Mark-XLVI
pip install -r requirements.txt
playwright install
python main.py

```

> ⚠️ **Installation Note:** To keep the repository lightweight, some OS-specific dependencies are not bundled in `requirements.txt`. If you run into a `ModuleNotFoundError`, simply install the missing package via `pip install <module_name>` for your specific system.

---

## 🏗️ Modular Refactoring (In Progress)

The project is being refactored into a secure, modular architecture compatible with **LiteLLM**, **PostgreSQL/pgvector**, **Hindsight**, and **Agent Zero** patterns.

### New structure

```
jarvis/
├── config/          # Paths, settings, constants
├── security/        # Secrets, sandbox, permissions, certificates
├── core/            # Player protocol, orchestrator
├── llm/             # LiteLLM client and multi-model router
├── memory/          # PostgreSQL/pgvector + JSON fallback
├── tools/           # Secure tool wrappers
├── audio/           # Audio pipeline (pending)
├── web/             # Dashboard (pending)
├── ui/              # PyQt6 UI (pending)
└── observability/   # Logging, metrics
```

### Run the new modular CLI

```bash
uv sync --extra all
python -m jarvis.main
```

### Security improvements

- API keys stored in keyring or encrypted fallback (no plaintext `api_keys.json`).
- Dynamic SSL certificates (no committed private keys).
- `exec()` replaced by a subprocess sandbox with static analysis.
- `shell=True` replaced by argument-list execution with allowlists.
- User confirmation required for high-risk actions.

See `REFACTORING_STATUS.md` for the full roadmap and `ARCHITECTURE.md` for the new design.

### Configuration

```bash
# Required for LLM
export JARVIS_LLM_API_KEY=your-key

# Optional: embeddings
export JARVIS_EMBEDDING_PROVIDER=sentence-transformers
export JARVIS_EMBEDDING_MODEL=all-MiniLM-L6-v2

# Optional: OpenTelemetry
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

### Docker

```bash
# Start with PostgreSQL and dashboard
docker compose up

# Or build the image manually
docker build -t jarvis .
```

---

## 📋 Requirements

| Requirement | Details |
| --- | --- |
| **OS** | Windows 10/11, macOS, or Linux |
| **Python** | 3.11 or 3.12 |
| **Microphone** | Required for voice interaction |
| **API Key** | Free Gemini API key |

---

## ⚠️ License

Personal and non-commercial use only.
Licensed under **[Creative Commons BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)**.

---

## About M.A.R.K Evolution

M.A.R.K Evolution (Modular Autonomous Reasoning Keeper) is an AI orchestration platform designed to coordinate language models, memory systems, autonomous agents and automation tools through a unified architecture.

Core capabilities include:

* LiteLLM integration
* Multi-agent orchestration
* Long-term memory
* Browser automation
* Desktop automation
* Dashboard and API
* Knowledge management
* Future PostgreSQL / Hindsight memory support