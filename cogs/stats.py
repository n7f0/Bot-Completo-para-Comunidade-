import discord
from discord.ext import commands, tasks
from database import load_data

class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_stats.start()
        self.maintain_voice.start()

    def cog_unload(self):
        self.update_stats.cancel()
        self.maintain_voice.cancel()

    # TAREFA 1: Atualiza os nomes das categorias (Roda a cada 6 minutos pelo Rate Limit do Discord)
    @tasks.loop(minutes=6)
    async def update_stats(self):
        await self.bot.wait_until_ready()
        data = load_data()
        
        if not self.bot.guilds:
            return
        
        guild = self.bot.guilds[0]

        # Atualizar Categoria de Membros Totais
        cat_members_id = data.get("stats_cat_members")
        if cat_members_id:
            cat_members = guild.get_channel(cat_members_id)
            if cat_members and isinstance(cat_members, discord.CategoryChannel):
                novo_nome = f"📊 Membros: {guild.member_count}"
                if cat_members.name != novo_nome:
                    try: await cat_members.edit(name=novo_nome)
                    except Exception as e: print(f"Erro ao editar categoria de membros: {e}")

        # Atualizar Categoria de Pessoas em Call
        cat_voice_id = data.get("stats_cat_voice")
        if cat_voice_id:
            cat_voice = guild.get_channel(cat_voice_id)
            if cat_voice and isinstance(cat_voice, discord.CategoryChannel):
                in_voice = sum(1 for member in guild.members if member.voice)
                novo_nome = f"🔊 Em Call: {in_voice}"
                if cat_voice.name != novo_nome:
                    try: await cat_voice.edit(name=novo_nome)
                    except Exception as e: print(f"Erro ao editar categoria de voz: {e}")

    # TAREFA 2: Mantém o bot na call automaticamente e previne o erro 4006 (Roda a cada 15 segundos)
    @tasks.loop(seconds=15)
    async def maintain_voice(self):
        await self.bot.wait_until_ready()
        data = load_data()
        
        if not self.bot.guilds:
            return
            
        guild = self.bot.guilds[0]
        voice_channel_id = data.get("stats_voice_channel")
        
        if voice_channel_id:
            vc = guild.get_channel(voice_channel_id)
            if vc and isinstance(vc, discord.VoiceChannel):
                bot_voice_client = guild.voice_client
                
                try:
                    # Se o bot cair em um estado corrompido ou erro de socket, desconecta limpo primeiro
                    if bot_voice_client and not bot_voice_client.is_connected():
                        await bot_voice_client.disconnect(force=True)
                        bot_voice_client = None

                    if bot_voice_client is None:
                        await vc.connect()
                        await guild.me.edit(mute=True, deafen=True)
                    elif bot_voice_client.channel.id != vc.id:
                        await bot_voice_client.move_to(vc)
                        await guild.me.edit(mute=True, deafen=True)
                except Exception as e:
                    if guild.voice_client:
                        try: await guild.voice_client.disconnect(force=True)
                        except: pass

async def setup(bot):
    await bot.add_cog(StatsCog(bot))
