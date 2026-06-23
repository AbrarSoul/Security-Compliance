# GPT-Lab Local Models

This project connects to the GPT-Lab **GPU-farmi-004** server at Tampere University. The server runs Ollama models and exposes them through an **OpenAI-compatible API**, so you can list models, chat interactively, or call them from your own code.

## Prerequisites

- Python 3.8+
- `requests` (`pip install requests`)
- A valid GPT-Lab API key (`sk-ollama-gptlab-...`)

API keys are shared on **GPT-Lab Teams/OneDrive**. You can also set your own key with the `GPTLAB_API_KEY` environment variable.

## Endpoints

| Purpose | URL |
|---------|-----|
| OpenAI-compatible API | `https://gptlab.rd.tuni.fi/GPT-Lab/resources/GPU-farmi-004/v1` |
| Native Ollama API | `https://gptlab.rd.tuni.fi/GPT-Lab/resources/GPU-farmi-004/api` |
| Resource browser | [gptlab.rd.tuni.fi/GPT-Lab/resources/](https://gptlab.rd.tuni.fi/GPT-Lab/resources/) |
| Web chat UI | [chat.gptlab.rd.tuni.fi](https://chat.gptlab.rd.tuni.fi/) |

All API requests require a Bearer token:

```
Authorization: Bearer YOUR_API_KEY
```

## Quick start

### 1. Set your API key (optional)

If you do not want to edit `models.py`, set the key in your shell:

**Windows (PowerShell):**

```powershell
$env:GPTLAB_API_KEY = "sk-ollama-gptlab-YOUR_KEY_HERE"
```

**Linux / macOS:**

```bash
export GPTLAB_API_KEY="sk-ollama-gptlab-YOUR_KEY_HERE"
```

### 2. List available models

```powershell
python models.py list
```

This prints every model currently loaded on GPU-farmi-004 (for example `llama3.1:8b`, `qwen3.5:35b`, `gpt-oss:20b`).

### 3. Start an interactive chat

```powershell
python models.py
```

1. Pick a model by **number** or **exact name**.
2. Type your message and press Enter.
3. The assistant reply appears in the terminal.

#### Chat commands

| Command | Description |
|---------|-------------|
| `/quit` | Exit the chat |
| `/model` | Switch to a different model |
| `/clear` | Clear conversation history |
| `/list` | Show all available models |

## How to access models

### Option A — This script (`models.py`)

The easiest way to explore and chat:

```powershell
python models.py list    # list models only
python models.py         # interactive chat
```

### Option B — Web UI

Open [chat.gptlab.rd.tuni.fi](https://chat.gptlab.rd.tuni.fi/) in your browser, sign in if prompted, and select a model from the dropdown. TUNI VPN may be required off campus.

### Option C — HTTP API

List models:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "https://gptlab.rd.tuni.fi/GPT-Lab/resources/GPU-farmi-004/v1/models"
```

## How to use models

### From Python (this project)

```python
from models import fetch_models, chat

# List model names
models = fetch_models()
print(models)

# Send a single message
reply = chat(
    "llama3.1:8b",
    [{"role": "user", "content": "Explain recursion in one sentence."}],
)
print(reply)

# Multi-turn conversation
history = [
    {"role": "user", "content": "My name is Alex."},
    {"role": "assistant", "content": "Nice to meet you, Alex!"},
    {"role": "user", "content": "What is my name?"},
]
print(chat("llama3.1:8b", history))
```

### With the OpenAI Python SDK

```python
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_API_KEY",
    base_url="https://gptlab.rd.tuni.fi/GPT-Lab/resources/GPU-farmi-004/v1",
)

response = client.chat.completions.create(
    model="qwen3.5:9b",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)
```

### With curl (chat completions)

```bash
curl https://gptlab.rd.tuni.fi/GPT-Lab/resources/GPU-farmi-004/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### With curl (native Ollama generate)

```bash
curl https://gptlab.rd.tuni.fi/GPT-Lab/resources/GPU-farmi-004/api/generate \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "prompt": "Why is the sky blue?",
    "stream": false
  }'
```

## Tips

- Use the **exact model name** returned by `python models.py list` (for example `llama3.1:8b`, not `llama3.1`).
- Start with smaller models (`llama3.1:8b`, `qwen3.5:9b`) for faster responses. Large models like `gpt-oss:120b` or `llama3.3:70b` can be slow or time out.
- Embedding models (for example `nomic-embed-text:latest`) are for vector embeddings, not chat.
- Do not commit API keys to version control. Use `GPTLAB_API_KEY` or a local `.env` file instead.

## Other GPU farms

GPT-Lab hosts multiple resource endpoints under [resources/](https://gptlab.rd.tuni.fi/GPT-Lab/resources/), including `GPU-farmi-001` through `GPU-farmi-004`. This project is configured for **GPU-farmi-004**. To use another farm, change `API_BASE` in `models.py`.

## Troubleshooting

| Problem | What to try |
|---------|-------------|
| `401` / auth error | Check your API key on GPT-Lab Teams/OneDrive |
| `404` on model name | Run `python models.py list` and copy the exact name |
| Timeout | Try a smaller model or increase the `timeout` in `chat()` |
| Cannot reach the server | Connect to TUNI VPN if you are off campus |
