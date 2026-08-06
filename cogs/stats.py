import discord
from discord.ext import commands, tasks
from database import load_data

class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_stats.start()

    def cog_unload(self):
        self.update_stats.cancel()

    @tasks.loop(minutes=6)
    async def update_stats(self):
        # Espera o bot estar totalmente pronto
        await self.bot.wait_until_ready()
        data = load_data()

        # Precisamos pegar uma guilda (servidor)
        # Assumindo que o bot está em 1 servidor principal
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
                    try: await cat_members.edit(name=novo_nome)
                    except Exception as e: print(f"Erro ao editar categoria de membros: {e}")

        # 2. Atualizar Categoria de Pessoas em Call
        cat_voice_id = data.get("stats_cat_voice")
        if cat_voice_id:
            cat_voice = guild.get_channel(cat_voice_id)
            if cat_voice and isinstance(cat_voice, discord.CategoryChannel):
                # Conta quantas pessoas únicas estão conectadas em canais de voz
                in_voice = sum(1 for member in guild.members if member.voice)
                novo_nome = f"🔊 Em Call: {in_voice}"
                if cat_voice.name != novo_nome:
                    try: await cat_voice.edit(name=novo_nome)
                    except Exception as e: print(f"Erro ao editar categoria de voz: {e}")

        # 3. Entrar e ficar mutado no Canal de Voz escolhido
        voice_channel_id = data.get("stats_voice_channel")
        if voice_channel_id:
            vc = guild.get_channel(voice_channel_id)
            if vc and isinstance(vc, discord.VoiceChannel):
                # Se o bot não estiver no canal
                bot_voice_client = discord.utils.get(self.bot.voice_clients, guild=guild)
                if bot_voice_client is None:
                    try:
                        await vc.connect()
                        # Muta o bot no servidor (self_mute e self_deaf não têm api direta simples para o objeto bot, mas podemos mutar o bot como membro se necessário, geralmente o connect já serve)
                        # Entrar mutado no servidor
                        me = guild.me
                        await me.edit(mute=True, deafen=True)
                    except Exception as e:
                        print(f"Erro ao conectar na call: {e}")
                elif bot_voice_client.channel != vc:
                    # Move de canal se mudaram
                    await bot_voice_client.move_to(vc)

async def setup(bot):
    await bot.add_cog(StatsCog(bot))
