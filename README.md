# 🦊 Kurama Bot

An AI bot for Discord using `discord.py`, slash commands, and integration with models from OpenRouter (GPT, DeepSeek, Claude, LLaMA, etc).

You can also read the project in [Português](README.pt.md).


![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Discord.py](https://img.shields.io/badge/discord.py-2.5.2-blueviolet?logo=discord)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-in%20development-yellow)

---

## ✨ Features

- 🎙️ Slash commands;
- 🧠 Multiple AI models available (DeepSeek, GPT, Claude, etc.);
- 💬 Continuous conversation mode by channel;
- 📚 Conversation history;
- 🔧 Support for multiple channels with different models;
- 💻 Responses formatted as code (mode `code`).

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/kurama-ai.git
cd kurama-ai
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate
```

### 3. Install the dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file at the root of the project and add:

```env
DISCORD_TOKEN=seu_token_aqui
OPENROUTER_API_KEY=sua_api_key_openrouter_aqui
```

---

## ▶️ Running the bot

```bash
python main.py
```

## 📜 Available Commands

All commands are accessible via `/` on Discord:

- `/ask` – Ask something to the AI
- `/code` – Ask with a response formatted as code
- `/models` – List of available models
- `/model` – Change the AI model for the channel
- `/reset` – Restore the default model
- `/ai` – View or toggle continuous conversation mode
- `/resetmemory` – Clear the channel's conversation history
- `/help` – Show help with all commands

## 🧠 Supported Models

- DeepSeek Chat
- DeepSeek Coder
- Claude 3 Haiku
- GPT-3.5 Turbo
- LLaMA 3
- Mistral

You can configure the model by channel, with persistence throughout the session.

---

## 🛠️ Technologies

- Python 3.10+
- discord.py 2.5+
- OpenRouter API
- `.env` with `python-dotenv`
- `requests` for HTTP calls

## 📄 License
This project is licensed under the terms of the [MIT License](LICENSE).
