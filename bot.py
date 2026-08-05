import discord
from discord.ext import commands
import os
import asyncio
import sys

# Força o Python a não bufferizar a saída
sys.stdout.reconfigure(line_buffering=True)

from config import TOKEN

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}", flush=True)
    try:
        await bot.tree.sync()
        print("✅ Comandos sincronizados com o Discord", flush=True)
    except Exception as e:
        print(f"❌ Erro ao sincronizar comandos: {e}", flush=True)

async def load_cogs():
    await bot.load_extension("cogs.admin")
    await bot.load_extension("cogs.registro")

async def main():
    print("🚀 Bot iniciando...", flush=True)
    await load_cogs()
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())