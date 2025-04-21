import os
import discord
import requests
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Modelo padrão
DEFAULT_MODEL = "deepseek/deepseek-chat-v3-0324:free"
current_model = DEFAULT_MODEL

# Dicionário de modelos disponíveis com descrição
modelos_validos = {
    "deepseek-chat": {
        "id": "deepseek-ai/deepseek-chat",
        "desc": "DeepSeek Chat (geral, gratuito)"
    },
    "deepseek-chat-v3": {
        "id": "deepseek/deepseek-chat-v3-0324:free",
        "desc": "DeepSeek Chat v3-0324 (Sucessor do DeepSeek V3, mais rápido)"
    },
    "deepseek-coder": {
        "id": "deepseek-ai/deepseek-coder:7b-instruct",
        "desc": "DeepSeek Coder (focado em programação, gratuito)"
    },
    "mistral": {
        "id": "mistral/mistral-7b-instruct",
        "desc": "Mistral 7B (rápido, gratuito)"
    },
    "gpt-3.5": {
        "id": "openai/gpt-3.5-turbo",
        "desc": "GPT-3.5 Turbo (chat geral, OpenAI)"
    },
    "claude": {
        "id": "anthropic/claude-3-haiku",
        "desc": "Claude 3 Haiku (ótimo para texto longo, gratuito)"
    },
    "llama3": {
        "id": "meta-llama/llama-3-8b-instruct",
        "desc": "LLaMA 3 (Meta, modelo novo, gratuito)"
    }
}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def ask(ctx, *, question):
    await ctx.send("Pensando... 🤔")
    response = get_ai_response(question)
    await ctx.send(response)

@bot.command()
async def model(ctx, *, model_name=None):
    global current_model
    if not model_name:
        await ctx.send(f"🧠 Modelo atual: `{current_model}`")
        return

    model_key = model_name.lower()
    if model_key in modelos_validos:
        current_model = modelos_validos[model_key]["id"]
        await ctx.send(f"✅ Modelo alterado para `{current_model}`")
    else:
        await ctx.send("❌ Modelo inválido. Use `!modelos` para ver a lista disponível.")

@bot.command()
async def modelos(ctx):
    mensagem = "**📋 Modelos disponíveis:**\n\n"
    for nome, info in modelos_validos.items():
        mensagem += f"🔹 `{nome}` → {info['desc']}\n"
    await ctx.send(mensagem)

@bot.command()
async def reset(ctx):
    global current_model
    current_model = DEFAULT_MODEL
    await ctx.send(f"🔄 Modelo resetado para o padrão: `{DEFAULT_MODEL}`")

def get_ai_response(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    json = {
        "model": current_model,
        "messages": [{"role": "user", "content": prompt}]
    }
    r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=json)
    return r.json()['choices'][0]['message']['content']

bot.run(TOKEN)
