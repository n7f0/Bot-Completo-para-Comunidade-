import discord
from discord.ext import commands, tasks
from database import load_data

class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_stats.start()

    def cog_unload(self):
        self.update_stats.cancel()

    # Atualiza apenas os nomes das categorias (Membros e Pessoas em Call) a cada 6 minutos
    @tasks.loop(minutes=6)
    async def update_stats(self):
        await self.bot.wait_until_ready()
        data = load_data()
        
        if not self.bot.guilds:
            return
        
        guild = self.bot.guilds[0]

        # 1. Atualizar Categoria de Membros Totais
        cat_members_id = data.get("stats_cat_members")
        if cat_members_id:
            cat_members = guild.get_channel(cat_members_id)
            if cat_members and isinstance(cat_members, discord.CategoryChannel):
                novo_nome = f"📊 Membros: {guild.member_count}"
                if cat_members.name != novo_nome:
                    try: 
                        await cat_members.edit(name=novo_nome)
                    except Exception as e: 
                        print(f"Erro ao editar categoria de membros: {e}")

        # 2. Atualizar Categoria de Pessoas em Call (Lê em tempo real quem está em canais de voz)
        cat_voice_id = data.get("stats_cat_voice")
        if cat_voice_id:
            cat_voice = guild.get_channel(cat_voice_id)
            if cat_voice and isinstance(cat_voice, discord.CategoryChannel):
                in_voice = sum(1 for member in guild.members if member.voice and member.voice.channel)
                novo_nome = f"🔊 Em Call: {in_voice}"
                if cat_voice.name != novo_nome:
                    try: 
                        await cat_voice.edit(name=novo_nome)
                    except Exception as e: 
                        print(f"Erro ao editar categoria de voz: {e}")

async def setup(bot):
    await bot.add_cog(StatsCog(bot))
