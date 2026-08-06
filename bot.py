import discord
from discord.ext import commands
import os
import asyncio
import sys

sys.stdout.reconfigure(line_buffering=True)
from config import TOKEN

class MeuBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True 
        intents.voice_states = True # Necessário para contar quem está em call
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        print("🚀 Carregando extensões...", flush=True)
        await self.load_extension("cogs.admin")
        await self.load_extension("cogs.registro")
        await self.load_extension("cogs.events")
        await self.load_extension("cogs.ticket")
        await self.load_extension("cogs.regras")
        await self.load_extension("cogs.stats")
        
        try:
            await self.tree.sync()
            print("✅ Comandos de barra sincronizados!", flush=True)
        except Exception as e:
            print(f"❌ Erro ao sincronizar comandos: {e}", flush=True)

bot = MeuBot()

@bot.event
async def on_ready():
    print(f"✅ Bot totalmente conectado como {bot.user}", flush=True)

if __name__ == "__main__":
    bot.run(TOKEN)
