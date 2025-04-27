import os
import discord
import requests
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import json
from typing import Dict, List, Optional
import time
from database import Database

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not TOKEN or not OPENROUTER_API_KEY:
    raise ValueError("DISCORD_TOKEN e OPENROUTER_API_KEY são necessários no arquivo .env")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# Inicializa o banco de dados
db = Database()

DEFAULT_MODEL = "deepseek/deepseek-chat-v3-0324:free"
MAX_HISTORY_LENGTH = 15
MAX_MESSAGE_LENGTH = 2000  # Limite do Discord

# Configurações de rate limiting
RATE_LIMIT = {
    "window": 60,  # segundos
    "max_requests": 10  # máximo de requisições por janela
}
user_requests = {}  # {user_id: [(timestamp, command), ...]}

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
    await db._init_db()  # Inicializa o banco de dados
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
        settings = await db.get_channel_settings(canal)
        modelo_atual = settings["model"] or DEFAULT_MODEL
        await interaction.response.send_message(f"🧠 Modelo atual deste canal: `{modelo_atual}`")
        return

    model_key = model_name.lower()
    if model_key in modelos_validos:
        await db.save_channel_settings(canal, modelos_validos[model_key]["id"], False)
        await interaction.response.send_message(f"✅ Modelo deste canal alterado para `{modelos_validos[model_key]['id']}`")
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
    settings = await db.get_channel_settings(canal)
    
    if modo == "on":
        await db.save_channel_settings(canal, settings["model"] or DEFAULT_MODEL, True)
        await interaction.response.send_message("🧠 Modo contínuo **ativado** para este canal.")
    elif modo == "off":
        await db.save_channel_settings(canal, settings["model"] or DEFAULT_MODEL, False)
        await interaction.response.send_message("🔁 Modo contínuo **desativado** para este canal.")
    else:
        estado = settings["continuous_mode"]
        await interaction.response.send_message(f"🔎 Modo contínuo está: {'ativado ✅' if estado else 'desativado ❌'}")

@tree.command(name="resetmemoria", description="Apaga a memória de conversas deste canal")
async def resetmemoria(interaction: discord.Interaction):
    canal = interaction.channel.id
    await db.save_message_history(canal, [])
    await interaction.response.send_message("🧽 Memória deste canal apagada com sucesso!")

@tree.command(name="ajuda", description="Lista os comandos disponíveis")
async def ajuda(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 Comandos disponíveis",
        description="Aqui estão os comandos que você pode usar com o bot:",
        color=discord.Color.orange()
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

def get_ai_response(messages: List[Dict[str, str]], canal_id: int) -> str:
    try:
        modelo = modelo_por_canal.get(canal_id, DEFAULT_MODEL)
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }

        system_message = {
            "role": "system",
            "content": (
                "Você é Kurama, a Raposa de Nove Caudas do anime Naruto. "
                "Você é poderoso, sábio e sarcástico. Fala com autoridade e confiança, "
                "usando frases como 'criaturas tolas', 'insolentes' ou 'patéticos humanos'. "
                "Apesar da aparência hostil, você protege quem merece. Responda sempre como Kurama, "
                "com tom firme, arrogante, mas com toques de sabedoria ancestral."
            )
        }

        json_data = {
            "model": modelo,
            "messages": [system_message] + messages
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=json_data,
            timeout=30  # Timeout de 30 segundos
        )
        response.raise_for_status()  # Levanta exceção para códigos de erro HTTP
        
        return response.json()['choices'][0]['message']['content']
    
    except requests.exceptions.RequestException as e:
        print(f"Erro na API: {str(e)}")
        return "Desculpe, estou tendo problemas para processar sua solicitação. Tente novamente mais tarde."
    except (KeyError, json.JSONDecodeError) as e:
        print(f"Erro ao processar resposta: {str(e)}")
        return "Ocorreu um erro ao processar a resposta. Por favor, tente novamente."

def check_rate_limit(user_id: int, command: str) -> bool:
    """Verifica se o usuário excedeu o limite de requisições"""
    current_time = time.time()
    
    # Limpa requisições antigas
    if user_id in user_requests:
        user_requests[user_id] = [
            (ts, cmd) for ts, cmd in user_requests[user_id]
            if current_time - ts < RATE_LIMIT["window"]
        ]
    
    # Adiciona nova requisição
    if user_id not in user_requests:
        user_requests[user_id] = []
    user_requests[user_id].append((current_time, command))
    
    # Verifica limite
    return len(user_requests[user_id]) <= RATE_LIMIT["max_requests"]

@tree.command(name="ask", description="Faz uma pergunta à IA")
@app_commands.describe(question="Sua pergunta para a IA")
async def ask(interaction: discord.Interaction, question: str):
    # Sanitiza a entrada
    question = db.sanitize_input(question)

    # Verifica rate limit
    if not check_rate_limit(interaction.user.id, "ask"):
        await interaction.response.send_message(
            "⚠️ Você atingiu o limite de requisições. Por favor, aguarde um momento."
        )
        return

    if len(question) > MAX_MESSAGE_LENGTH:
        await interaction.response.send_message(
            f"❌ Sua pergunta é muito longa. O limite é de {MAX_MESSAGE_LENGTH} caracteres."
        )
        return

    canal = interaction.channel.id
    await interaction.response.defer()

    try:
        # Registra uso
        await db.log_usage(canal, interaction.user.id, "ask")
        
        # Recupera configurações do canal
        settings = await db.get_channel_settings(canal)
        historico = await db.get_message_history(canal) if settings["continuous_mode"] else []
        
        historico.append({"role": "user", "content": question})
        response = get_ai_response(historico, canal)
        historico.append({"role": "assistant", "content": response})
        
        # Salva histórico se modo contínuo estiver ativo
        if settings["continuous_mode"]:
            await db.save_message_history(canal, historico)
        
        await interaction.followup.send(response)
    except Exception as e:
        print(f"Erro ao processar pergunta: {str(e)}")
        await interaction.followup.send(
            "Desculpe, ocorreu um erro ao processar sua pergunta. Tente novamente mais tarde."
        )

@tree.command(name="code", description="Faz uma pergunta e recebe a resposta como código")
@app_commands.describe(pergunta="Pergunta para a IA")
async def code(interaction: discord.Interaction, pergunta: str):
    # Sanitiza a entrada
    pergunta = db.sanitize_input(pergunta)

    # Verifica rate limit
    if not check_rate_limit(interaction.user.id, "code"):
        await interaction.response.send_message(
            "⚠️ Você atingiu o limite de requisições. Por favor, aguarde um momento."
        )
        return

    if len(pergunta) > MAX_MESSAGE_LENGTH:
        await interaction.response.send_message(
            f"❌ Sua pergunta é muito longa. O limite é de {MAX_MESSAGE_LENGTH} caracteres."
        )
        return

    canal = interaction.channel.id
    await interaction.response.defer()

    try:
        # Registra uso
        await db.log_usage(canal, interaction.user.id, "code")
        
        # Recupera configurações do canal
        settings = await db.get_channel_settings(canal)
        historico = await db.get_message_history(canal) if settings["continuous_mode"] else []
        
        historico.append({"role": "user", "content": pergunta})
        response = get_ai_response(historico, canal)
        historico.append({"role": "assistant", "content": response})
        
        # Salva histórico se modo contínuo estiver ativo
        if settings["continuous_mode"]:
            await db.save_message_history(canal, historico)
        
        await interaction.followup.send(f"```markdown\n{response}\n```")
    except Exception as e:
        print(f"Erro ao processar código: {str(e)}")
        await interaction.followup.send(
            "Desculpe, ocorreu um erro ao processar sua solicitação de código. Tente novamente mais tarde."
        )

@tree.command(name="stats", description="Mostra estatísticas de uso do canal")
async def stats(interaction: discord.Interaction):
    canal = interaction.channel.id
    stats = await db.get_usage_stats(canal)
    
    if not stats:
        await interaction.response.send_message("📊 Ainda não há estatísticas de uso para este canal.")
        return
    
    embed = discord.Embed(
        title="📊 Estatísticas de Uso",
        description="Estatísticas dos últimos 7 dias:",
        color=discord.Color.blue()
    )
    
    for command, count in stats.items():
        embed.add_field(name=f"`{command}`", value=f"{count} usos", inline=True)
    
    await interaction.response.send_message(embed=embed)

bot.run(TOKEN)
