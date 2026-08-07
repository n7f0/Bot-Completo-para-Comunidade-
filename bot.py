import discord
from discord.ext import commands
import os
import asyncio
import sys
import logging

# Configura logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord_bot')

sys.stdout.reconfigure(line_buffering=True)
from config import TOKEN

class MeuBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True 
        intents.voice_states = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        print("🚀 Carregando extensões...", flush=True)
        try:
            await self.load_extension("cogs.admin")
            await self.load_extension("cogs.registro")
            await self.load_extension("cogs.events")
            await self.load_extension("cogs.ticket")
            await self.load_extension("cogs.regras")
            await self.load_extension("cogs.stats")
            await self.load_extension("cogs.booster")
            await self.load_extension("cogs.comandos")
            await self.load_extension("cogs.overview")
            await self.load_extension("cogs.staff")
            await self.load_extension("cogs.tellonym")
            print("✅ Todas as extensões carregadas!", flush=True)
        except Exception as e:
            print(f"❌ Erro ao carregar extensões: {e}", flush=True)
            logger.error(f"Erro ao carregar extensões: {e}")
        
        try:
            await self.tree.sync()
            print("✅ Comandos de barra sincronizados!", flush=True)
        except Exception as e:
            print(f"❌ Erro ao sincronizar comandos: {e}", flush=True)
            logger.error(f"Erro ao sincronizar comandos: {e}")

bot = MeuBot()

@bot.event
async def on_ready():
    print(f"✅ Bot totalmente conectado como {bot.user}", flush=True)
    logger.info(f"Bot conectado como {bot.user}")

@bot.event
async def on_error(event, *args, **kwargs):
    print(f"❌ Erro no evento {event}: {args}", flush=True)
    logger.error(f"Erro no evento {event}: {args}")

if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"❌ Erro fatal: {e}", flush=True)
        logger.critical(f"Erro fatal: {e}")
