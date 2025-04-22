import os
import discord
import requests
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

DEFAULT_MODEL = "deepseek/deepseek-chat-v3-0324:free"

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

historico_por_canal = {}
modo_continuo_por_canal = {}
modelo_por_canal = {}

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logado como {bot.user}")

@tree.command(name="modelos", description="Lista os modelos de IA disponíveis")
async def modelos(interaction: discord.Interaction):
    mensagem = "**📋 Modelos disponíveis:**\n\n"
    for nome, info in modelos_validos.items():
        mensagem += f"🔹 `{nome}` → {info['desc']}\n"
    await interaction.response.send_message(mensagem)

@tree.command(name="model", description="Define ou mostra o modelo atual para o canal")
@app_commands.describe(model_name="Nome do modelo (use /modelos para ver)")
async def model(interaction: discord.Interaction, model_name: str = None):
    canal = interaction.channel.id
    if not model_name:
        modelo_atual = modelo_por_canal.get(canal, DEFAULT_MODEL)
        await interaction.response.send_message(f"🧠 Modelo atual deste canal: `{modelo_atual}`")
        return

    model_key = model_name.lower()
    if model_key in modelos_validos:
        modelo_por_canal[canal] = modelos_validos[model_key]["id"]
        await interaction.response.send_message(f"✅ Modelo deste canal alterado para `{modelo_por_canal[canal]}`")
    else:
        await interaction.response.send_message("❌ Modelo inválido. Use `/modelos` para ver a lista disponível.")

@tree.command(name="reset", description="Restaura o modelo padrão para este canal")
async def reset(interaction: discord.Interaction):
    canal = interaction.channel.id
    modelo_por_canal.pop(canal, None)
    await interaction.response.send_message(f"🔄 Modelo deste canal resetado para o padrão: `{DEFAULT_MODEL}`")

@tree.command(name="ia", description="Ativa, desativa ou consulta o modo contínuo")
@app_commands.describe(modo="Escolha on, off ou deixe em branco para ver o estado atual")
async def ia(interaction: discord.Interaction, modo: str = None):
    canal = interaction.channel.id
    if modo == "on":
        modo_continuo_por_canal[canal] = True
        await interaction.response.send_message("🧠 Modo contínuo **ativado** para este canal.")
    elif modo == "off":
        modo_continuo_por_canal[canal] = False
        await interaction.response.send_message("🔁 Modo contínuo **desativado** para este canal.")
    else:
        estado = modo_continuo_por_canal.get(canal, False)
        await interaction.response.send_message(f"🔎 Modo contínuo está: {'ativado ✅' if estado else 'desativado ❌'}")

@tree.command(name="resetmemoria", description="Apaga a memória de conversas deste canal")
async def resetmemoria(interaction: discord.Interaction):
    canal = interaction.channel.id
    historico_por_canal[canal] = []
    await interaction.response.send_message("🧽 Memória deste canal apagada com sucesso!")

@tree.command(name="ajuda", description="Lista os comandos disponíveis")
async def ajuda(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 Comandos disponíveis",
        description="Aqui estão os comandos que você pode usar com o bot:",
        color=discord.Color.blue()
    )
    embed.add_field(name="/ask", value="Pergunte algo à IA.", inline=False)
    embed.add_field(name="/code", value="Recebe a resposta formatada como código.", inline=False)
    embed.add_field(name="/modelos", value="Lista os modelos de IA disponíveis.", inline=False)
    embed.add_field(name="/model", value="Define o modelo de IA no canal.", inline=False)
    embed.add_field(name="/reset", value="Reseta o modelo para o padrão.", inline=False)
    embed.add_field(name="/ia", value="Ativa/desativa o modo contínuo.", inline=False)
    embed.add_field(name="/resetmemoria", value="Apaga a memória do canal.", inline=False)
    embed.add_field(name="/ajuda", value="Mostra esta lista de comandos.", inline=False)

    canal = interaction.channel.id
    modelo_atual = modelo_por_canal.get(canal, DEFAULT_MODEL)
    embed.set_footer(text=f"🧠 Modelo atual: {modelo_atual}")

    await interaction.response.send_message(embed=embed)

@tree.command(name="ask", description="Faz uma pergunta à IA")
@app_commands.describe(question="Sua pergunta para a IA")
async def ask(interaction: discord.Interaction, question: str):
    canal = interaction.channel.id
    await interaction.response.defer()
    
    historico = historico_por_canal.get(canal, []) if modo_continuo_por_canal.get(canal, False) else []
    historico.append({"role": "user", "content": question})

    response = get_ai_response(historico, canal)

    historico.append({"role": "assistant", "content": response})
    if modo_continuo_por_canal.get(canal, False):
        historico_por_canal[canal] = historico[-15:]

    await interaction.followup.send(response)

@tree.command(name="code", description="Faz uma pergunta e recebe a resposta como código")
@app_commands.describe(pergunta="Pergunta para a IA")
async def code(interaction: discord.Interaction, pergunta: str):
    canal = interaction.channel.id
    await interaction.response.defer()
    
    historico = historico_por_canal.get(canal, []) if modo_continuo_por_canal.get(canal, False) else []
    historico.append({"role": "user", "content": pergunta})

    response = get_ai_response(historico, canal)

    historico.append({"role": "assistant", "content": response})
    if modo_continuo_por_canal.get(canal, False):
        historico_por_canal[canal] = historico[-15:]

    await interaction.followup.send(f"```markdown\n{response}\n```")

def get_ai_response(messages, canal):
    model = modelo_por_canal.get(canal, DEFAULT_MODEL)
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    json = {
        "model": model,
        "messages": messages
    }
    r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=json)
    r.raise_for_status()
    return r.json()['choices'][0]['message']['content']

bot.run(TOKEN)
