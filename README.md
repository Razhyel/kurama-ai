# 🦊 Kurama Bot

Um bot de IA para Discord usando `discord.py`, comandos slash e integração com modelos da OpenRouter (GPT, DeepSeek, Claude, LLaMA, etc).

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Discord.py](https://img.shields.io/badge/discord.py-2.5.2-blueviolet?logo=discord)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)

---

## ✨ Funcionalidades

- 🎙️ Comandos Slash;
- 🧠 Vários modelos de IA disponíveis (DeepSeek, GPT, Claude, etc.);
- 💬 Modo contínuo de conversa por canal;
- 📚 Histórico de conversas;
- 🔧 Suporte a múltiplos canais com modelos diferentes;
- 💻 Respostas formatadas como código (modo `code`).

---

## 🚀 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/seunome/kurama-ai.git
cd kurama-ai
```

### 2. Crie e ative um ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # no Windows: venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto e adicione:

```env
DISCORD_TOKEN=seu_token_aqui
OPENROUTER_API_KEY=sua_api_key_openrouter_aqui
```

---

## ▶️ Executando o bot

```bash
python main.py
```

---

## 📜 Comandos disponíveis

Todos os comandos são acessíveis via `/` no Discord:

- `/ask` – Pergunta algo para a IA
- `/code` – Pergunta com resposta formatada como código
- `/modelos` – Lista de modelos disponíveis
- `/model` – Altera o modelo de IA do canal
- `/reset` – Restaura o modelo padrão
- `/ia` – Ver ou alternar o modo contínuo de conversa
- `/resetmemoria` – Apaga o histórico do canal
- `/ajuda` – Mostra ajuda com todos os comandos

---

## 🧠 Modelos Suportados

- DeepSeek Chat
- DeepSeek Coder
- Claude 3 Haiku
- GPT-3.5 Turbo
- LLaMA 3
- Mistral

Você pode configurar o modelo por canal, com persistência durante a sessão.

---

## 🛠️ Tecnologias

- Python 3.10+
- `discord.py` 2.5+
- OpenRouter API
- `.env` com `python-dotenv`
- `requests` para chamadas HTTP

---

## 📄 Licença

- Este projeto está licenciado sob os termos da [Licença MIT](LICENSE).
---

