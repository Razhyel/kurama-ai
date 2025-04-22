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

# @bot.command()
# async def ask(ctx, *, question):
#     await ctx.send("Pensando... 🤔")
#     response = get_ai_response(question)
#     await ctx.send(response)

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

# [continuação do código anterior]

# Histórico por canal
historico_por_canal = {}
modo_continuo_por_canal = {}

@bot.command()
async def ia(ctx, modo=None):
    canal = ctx.channel.id
    if modo == "on":
        modo_continuo_por_canal[canal] = True
        await ctx.send("🧠 Modo contínuo **ativado** para este canal.")
    elif modo == "off":
        modo_continuo_por_canal[canal] = False
        await ctx.send("🔁 Modo contínuo **desativado** para este canal.")
    else:
        estado = modo_continuo_por_canal.get(canal, False)
        await ctx.send(f"🔎 Modo contínuo está: {'ativado ✅' if estado else 'desativado ❌'}")

@bot.command()
async def resetmemoria(ctx):
    canal = ctx.channel.id
    historico_por_canal[canal] = []
    await ctx.send("🧽 Memória deste canal apagada com sucesso!")

@bot.command()
async def code(ctx, *, pergunta):
    canal = ctx.channel.id
    await ctx.send("💻 Gerando código...")

    if canal not in historico_por_canal:
        historico_por_canal[canal] = []

    historico = historico_por_canal[canal] if modo_continuo_por_canal.get(canal, False) else []
    historico.append({"role": "user", "content": pergunta})

    response = get_ai_response(historico)

    historico.append({"role": "assistant", "content": response})

    if modo_continuo_por_canal.get(canal, False):
        historico_por_canal[canal] = historico[-15:]

    # Envia como bloco de código (```)
    await ctx.send(f"```markdown\n{response}\n```")


@bot.command()
async def ask(ctx, *, question):
    canal = ctx.channel.id
    await ctx.send("Pensando... 🤔")
    
    # Inicializa histórico se necessário
    if canal not in historico_por_canal:
        historico_por_canal[canal] = []

    historico = historico_por_canal[canal] if modo_continuo_por_canal.get(canal, False) else []
    historico.append({"role": "user", "content": question})

    response = get_ai_response(historico)
    
    historico.append({"role": "assistant", "content": response})
    
    if modo_continuo_por_canal.get(canal, False):
        historico_por_canal[canal] = historico[-15:]  # mantém últimos 15 turnos

    await ctx.send(response)

def get_ai_response(messages):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    json = {
        "model": current_model,
        "messages": messages
    }
    r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=json)
    return r.json()['choices'][0]['message']['content']


bot.run(TOKEN)
