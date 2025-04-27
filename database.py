import os
import json
from typing import Dict, List, Optional
import logging
import asyncpg
from datetime import datetime, timedelta

# Configuração do sistema de logging
# Usa apenas StreamHandler pois o sistema de arquivos é efêmero no Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

class Database:
    """Classe responsável por gerenciar todas as operações do banco de dados"""
    
    def __init__(self):
        """Inicializa a classe Database"""
        self.pool = None  # Pool de conexões com o banco de dados
        self._init_db()

    async def _init_db(self):
        """Inicializa o banco de dados e cria as tabelas necessárias"""
        try:
            # Obtém a URL do banco de dados da variável de ambiente ou usa valor padrão para desenvolvimento
            DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/bot')
            
            # Cria um pool de conexões com o banco de dados
            self.pool = await asyncpg.create_pool(DATABASE_URL)
            
            # Cria as tabelas necessárias
            async with self.pool.acquire() as conn:
                # Tabela para armazenar o histórico de mensagens
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS message_history (
                        channel_id BIGINT,  -- ID do canal do Discord
                        message_data JSONB, -- Dados da mensagem em formato JSON
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Data e hora da mensagem
                    )
                ''')
                
                # Tabela para armazenar as configurações de cada canal
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS channel_settings (
                        channel_id BIGINT PRIMARY KEY,  -- ID do canal do Discord
                        model TEXT,  -- Modelo de IA configurado
                        continuous_mode BOOLEAN DEFAULT FALSE  -- Modo contínuo ativado/desativado
                    )
                ''')
                
                # Tabela para armazenar métricas de uso
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS usage_metrics (
                        channel_id BIGINT,  -- ID do canal do Discord
                        user_id BIGINT,  -- ID do usuário
                        command TEXT,  -- Comando utilizado
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Data e hora do uso
                    )
                ''')

                # Tabela para rate limiting
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS rate_limits (
                        user_id BIGINT,
                        command TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (user_id, command, timestamp)
                    )
                ''')
                
                logging.info("Banco de dados inicializado com sucesso")
        except Exception as e:
            logging.error(f"Erro ao inicializar banco de dados: {str(e)}")
            raise

    async def save_message_history(self, channel_id: int, messages: List[Dict[str, str]]):
        """Salva o histórico de mensagens de um canal
        
        Args:
            channel_id: ID do canal do Discord
            messages: Lista de mensagens no formato [{"role": str, "content": str}, ...]
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO message_history (channel_id, message_data) VALUES ($1, $2)",
                    channel_id, json.dumps(messages)
                )
        except Exception as e:
            logging.error(f"Erro ao salvar histórico: {str(e)}")

    async def get_message_history(self, channel_id: int, limit: int = 15) -> List[Dict[str, str]]:
        """Recupera o histórico de mensagens de um canal
        
        Args:
            channel_id: ID do canal do Discord
            limit: Número máximo de mensagens a retornar
            
        Returns:
            Lista de mensagens no formato [{"role": str, "content": str}, ...]
        """
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow(
                    "SELECT message_data FROM message_history WHERE channel_id = $1 ORDER BY timestamp DESC LIMIT 1",
                    channel_id
                )
                if result:
                    return json.loads(result['message_data'])[-limit:]
                return []
        except Exception as e:
            logging.error(f"Erro ao recuperar histórico: {str(e)}")
            return []

    async def save_channel_settings(self, channel_id: int, model: str, continuous_mode: bool):
        """Salva as configurações de um canal
        
        Args:
            channel_id: ID do canal do Discord
            model: Nome do modelo de IA
            continuous_mode: Se o modo contínuo está ativado
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO channel_settings (channel_id, model, continuous_mode) VALUES ($1, $2, $3) ON CONFLICT (channel_id) DO UPDATE SET model = $2, continuous_mode = $3",
                    channel_id, model, continuous_mode
                )
        except Exception as e:
            logging.error(f"Erro ao salvar configurações: {str(e)}")

    async def get_channel_settings(self, channel_id: int) -> Dict:
        """Recupera as configurações de um canal
        
        Args:
            channel_id: ID do canal do Discord
            
        Returns:
            Dicionário com as configurações do canal
        """
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow(
                    "SELECT model, continuous_mode FROM channel_settings WHERE channel_id = $1",
                    channel_id
                )
                if result:
                    return {
                        "model": result['model'],
                        "continuous_mode": result['continuous_mode']
                    }
                return {"model": None, "continuous_mode": False}
        except Exception as e:
            logging.error(f"Erro ao recuperar configurações: {str(e)}")
            return {"model": None, "continuous_mode": False}

    async def log_usage(self, channel_id: int, user_id: int, command: str):
        """Registra o uso de um comando
        
        Args:
            channel_id: ID do canal do Discord
            user_id: ID do usuário
            command: Nome do comando utilizado
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO usage_metrics (channel_id, user_id, command) VALUES ($1, $2, $3)",
                    channel_id, user_id, command
                )
        except Exception as e:
            logging.error(f"Erro ao registrar uso: {str(e)}")

    async def get_usage_stats(self, channel_id: int, days: int = 7) -> Dict:
        """Recupera estatísticas de uso de um canal
        
        Args:
            channel_id: ID do canal do Discord
            days: Número de dias para considerar nas estatísticas
            
        Returns:
            Dicionário com o número de usos por comando
        """
        try:
            async with self.pool.acquire() as conn:
                results = await conn.fetch(
                    "SELECT command, COUNT(*) as count FROM usage_metrics WHERE channel_id = $1 AND timestamp > NOW() - INTERVAL '$2 days' GROUP BY command",
                    channel_id, days
                )
                return {row['command']: row['count'] for row in results}
        except Exception as e:
            logging.error(f"Erro ao recuperar estatísticas: {str(e)}")
            return {}

    async def check_rate_limit(self, user_id: int, command: str, window: int = 60, max_requests: int = 10) -> bool:
        """Verifica se o usuário excedeu o limite de requisições
        
        Args:
            user_id: ID do usuário
            command: Nome do comando
            window: Janela de tempo em segundos
            max_requests: Número máximo de requisições por janela
            
        Returns:
            True se o usuário pode fazer a requisição, False caso contrário
        """
        try:
            async with self.pool.acquire() as conn:
                # Limpa requisições antigas
                await conn.execute(
                    "DELETE FROM rate_limits WHERE user_id = $1 AND command = $2 AND timestamp < NOW() - INTERVAL '$3 seconds'",
                    user_id, command, window
                )
                
                # Conta requisições na janela atual
                count = await conn.fetchval(
                    "SELECT COUNT(*) FROM rate_limits WHERE user_id = $1 AND command = $2",
                    user_id, command
                )
                
                # Se não excedeu o limite, registra a nova requisição
                if count < max_requests:
                    await conn.execute(
                        "INSERT INTO rate_limits (user_id, command) VALUES ($1, $2)",
                        user_id, command
                    )
                    return True
                return False
        except Exception as e:
            logging.error(f"Erro ao verificar rate limit: {str(e)}")
            return True  # Em caso de erro, permite a requisição

    def sanitize_input(self, text: str, max_length: int = 2000) -> str:
        """Sanitiza a entrada do usuário
        
        Args:
            text: Texto a ser sanitizado
            max_length: Tamanho máximo permitido
            
        Returns:
            Texto sanitizado
        """
        # Remove caracteres de controle
        text = ''.join(char for char in text if ord(char) >= 32)
        
        # Limita o tamanho
        if len(text) > max_length:
            text = text[:max_length]
            
        return text 