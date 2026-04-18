# WinPyAI

A production-grade desktop AI chat application built with Python 3.10+, PyQt6, and Ollama. Chat with local large language models through a modern, dark-themed interface inspired by industry-leading chat applications.

> **Screenshot Placeholder**
>
> ![WinPyAI Screenshot](docs/screenshot.png)
>
> *A modern dark-themed AI chat interface with sidebar navigation, streaming message bubbles, and real-time model selection.*

---

## Features

### Phase 1 (Current)

- **Local AI Chat** -- Connect to Ollama and chat with locally-running language models (Llama 3.2, Mistral, CodeLlama, and more)
- **Modern Dark UI** -- Clean, dark-themed interface built with PyQt6 Fusion style and custom QSS styling
- **Streaming Responses** -- Real-time token streaming for a fluid chat experience
- **Multi-Chat Management** -- Create, rename, delete, and switch between multiple conversation sessions
- **Persistent History** -- All conversations stored in SQLite with full message history
- **Model Selection** -- Switch between installed Ollama models per chat session
- **System Prompts** -- Configure custom system prompts per chat to tailor AI behavior
- **High DPI Support** -- Automatic scaling for high-resolution displays
- **Cross-Platform** -- Runs on Windows, macOS, and Linux

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python      | 3.10+   | Required for modern type hints and language features |
| Ollama      | latest  | Local AI inference server -- see [ollama.ai](https://ollama.ai) |
| PyQt6       | 6.6.0+  | Installed automatically via `requirements.txt` |
| requests    | 2.31.0+ | HTTP client for Ollama API communication |

---

## Installation

### Step 1: Install Ollama

Download and install Ollama for your platform from [https://ollama.ai](https://ollama.ai).

Verify the installation:

```bash
ollama --version
```

### Step 2: Pull a Model

Download a language model to chat with. We recommend starting with Llama 3.2:

```bash
ollama pull llama3.2
```

Other popular options:

```bash
ollama pull mistral          # General purpose
ollama pull codellama        # Code assistance
ollama pull llama3.2:latest  # Latest version tag
```

### Step 3: Clone the Repository

```bash
git clone <repository-url>
cd winpyai
```

### Step 4: Create a Virtual Environment

```bash
python -m venv venv
```

### Step 5: Activate the Virtual Environment

**Windows:**

```bash
venv\Scripts\activate
```

### Step 6: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:

- `PyQt6>=6.6.0` -- GUI framework
- `requests>=2.31.0` -- HTTP client for Ollama API

### Step 7: Run the Application

```bash
python main.py
```

The application window will open. Ensure Ollama is running in the background.

---

## Quick Start

1. Start Ollama (it runs as a background service on port 11434):

   ```bash
   ollama serve
   ```

2. Launch WinPyAI:

   ```bash
   python main.py
   ```

3. Click **"New Chat"** in the sidebar
4. Type your message and press **Enter** (or click **Send**)
5. Watch the AI respond in real-time with streaming tokens

---

## Architecture Overview

WinPyAI follows a clean layered architecture with clear separation of concerns:

```
winpyai/
|-- main.py                     # Application entry point
|-- requirements.txt            # Python dependencies
|-- README.md                   # This file
|
|-- winpyai/
|   |-- __init__.py
|   |-- config.py               # Constants, colors, fonts, defaults
|   |-- app.py                  # QApplication bootstrap & wiring
|   |
|   |-- database/
|   |   |-- __init__.py
|   |   |-- db.py               # SQLite connection, schema, WAL mode
|   |   |-- repository.py       # Chat & Message CRUD operations
|   |
|   |-- services/
|   |   |-- __init__.py
|   |   |-- ollama_service.py   # Ollama HTTP API client
|   |   |-- chat_service.py     # Business logic, signal orchestration
|   |
|   |-- workers/
|   |   |-- __init__.py
|   |   |-- stream_worker.py    # QThread for streaming AI responses
|   |
|   |-- ui/
|   |   |-- __init__.py
|   |   |-- main_window.py      # Main window layout & signal wiring
|   |   |-- sidebar.py          # Chat list panel
|   |   |-- chat_area.py        # Scrollable message display
|   |   |-- message_bubble.py   # Individual message widget
|   |   |-- input_bar.py        # Text input + send/stop button
|   |   |-- styles.py           # QSS theme strings + dark palette
```

### Data Flow

```
User Input
    |
    v
+-----------+     +-------------+     +------------------+
| InputBar  | --> | MainWindow  | --> |  ChatService     |
+-----------+     +-------------+     +------------------+
                                            |
                    +-----------------------+-----------------------+
                    |                                               |
                    v                                               v
            +-------------+                                 +-------------+
            | Database    |                                 | OllamaService|
            | (SQLite)    |                                 | (HTTP API)  |
            +-------------+                                 +-------------+
                    ^                                               |
                    |                                               |
                    |                                               v
                    |                                        +-------------+
                    |                                        | StreamWorker|
                    |                                        | (QThread)   |
                    |                                        +-------------+
                    |                                               |
                    +-----------------------+-----------------------+
                                            |
                                            v
                                     +-------------+
                                     | ChatArea    |
                                     | (UI Update) |
                                     +-------------+
```

### Key Design Patterns

- **Repository Pattern** -- `ChatRepository` and `MessageRepository` encapsulate all database access
- **Service Layer** -- `ChatService` orchestrates business logic and emits Qt signals for UI updates
- **Worker Threads** -- `StreamWorker` runs AI streaming in a separate QThread to keep the UI responsive
- **Signal/Slot Architecture** -- All cross-layer communication uses PyQt6 signals for loose coupling

---

## Configuration

Configuration is managed via `winpyai/config.py`. Key settings:

| Setting             | Default                  | Description                          |
|---------------------|--------------------------|--------------------------------------|
| `APP_NAME`          | `"WinPyAI"`              | Application display name             |
| `APP_VERSION`       | `"1.0.0"`                | Version string                       |
| `OLLAMA_HOST`       | `"http://localhost:11434"` | Ollama server URL                    |
| `DEFAULT_MODEL`     | `"llama3.2:latest"`      | Default AI model for new chats       |
| `DB_PATH`           | `"winpyai.db"`           | SQLite database file path            |
| `MAX_CHAT_WIDTH`    | `800`                    | Maximum width for message bubbles    |
| `FONT_FAMILY`       | `"Segoe UI"`             | Primary UI font                      |
| `FONT_SIZE_NORMAL`  | `14`                     | Default font size (points)           |
| `ACCENT_COLOR`      | `"#10A37F"`              | Primary accent (ChatGPT green)       |

To customize, edit `winpyai/config.py` before running the application.

---

## Troubleshooting

### Ollama Not Running

**Symptom:** Status bar shows "Ollama: Disconnected" or "Cannot connect to Ollama"

**Solution:**

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve
```

On Windows, Ollama typically runs as a background service. Check the system tray or Services panel.

### Model Not Found

**Symptom:** Error message "Model not found" or empty model list

**Solution:**

```bash
# List installed models
ollama list

# Pull the required model
ollama pull llama3.2
```

### Port Already in Use

**Symptom:** "Address already in use" when starting Ollama

**Solution:** Ollama is likely already running. Check with:

```bash
curl http://localhost:11434/api/tags
```

### PyQt6 Import Error

**Symptom:** `ModuleNotFoundError: No module named 'PyQt6'`

**Solution:**

```bash
pip install --upgrade PyQt6>=6.6.0
```

### Database Permission Error

**Symptom:** `sqlite3.OperationalError: unable to open database file`

**Solution:** Ensure the application has write permissions in the working directory. The database file `winpyai.db` is created in the current working directory.

### High DPI Display Issues

**Symptom:** UI appears too small or blurry on 4K displays

**Solution:** High DPI scaling is enabled automatically in `app.py` via `setHighDpiScaleFactorRoundingPolicy(PassThrough)`. If issues persist, try setting environment variables before running:

```bash
# Windows
set QT_SCALE_FACTOR=1.5
python main.py

# Linux/macOS
export QT_SCALE_FACTOR=1.5
python main.py
```

### Streaming Stops Mid-Response

**Symptom:** AI response cuts off unexpectedly

**Solution:**
- Check Ollama logs for errors
- Ensure the model has enough system memory
- Try a smaller model (e.g., `llama3.2:3b` instead of `llama3.2:8b`)
- Check if the stop button was accidentally clicked

---

## License

MIT License

Copyright (c) 2024 WinPyAI Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
