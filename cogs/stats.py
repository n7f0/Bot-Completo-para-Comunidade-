import discord
from discord.ext import commands, tasks
from database import load_data
import asyncio

# === GERADOR DE ÁUDIO SILENCIOSO ===
# Isso impede que o Discord desconecte o bot por inatividade
class SilenceAudio(discord.AudioSource):
    def read(self):
        # 20ms de silêncio (stereo, 16-bit, 48000Hz) = 3840 bytes
        return b'\x00' * 3840

    def is_opus(self):
        return False


class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_stats.start()
        self.keep_alive_voice.start()  # NOVO: Mantém o bot na call 24/7

    def cog_unload(self):
        self.update_stats.cancel()
        self.keep_alive_voice.cancel()

    # === TASK 1: Atualiza nomes das categorias a cada 6 minutos ===
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

        # 2. Atualizar Categoria de Pessoas em Call
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

    # === TASK 2: KEEP-ALIVE 24/7 - Reconecta automaticamente ===
    @tasks.loop(seconds=30)
    async def keep_alive_voice(self):
        """Verifica a cada 30 segundos se o bot está na call configurada.
        Se não estiver, reconecta. Se estiver, garante que o áudio silencioso está tocando."""
        await self.bot.wait_until_ready()

        if not self.bot.guilds:
            return

        guild = self.bot.guilds[0]
        data = load_data()
        voice_id = data.get("stats_voice_channel")

        if not voice_id:
            return

        vc = guild.get_channel(voice_id)
        if not vc or not isinstance(vc, discord.VoiceChannel):
            return

        bot_voice = guild.voice_client

        try:
            if bot_voice is None:
                # Bot não está em nenhuma call → Conecta
                print("🔊 [Keep-Alive] Bot desconectado. Reconectando na call...", flush=True)
                await vc.connect()
                await asyncio.sleep(1)

                # Começa a tocar áudio silencioso
                if guild.voice_client and not guild.voice_client.is_playing():
                    guild.voice_client.play(SilenceAudio())

                # Garante que fique mutado
                await guild.me.edit(mute=True, deafen=True)
                print("✅ [Keep-Alive] Bot reconectado e mutado com sucesso!", flush=True)

            elif bot_voice.channel.id != vc.id:
                # Bot está em outra call → Move para a correta
                print(f"🔊 [Keep-Alive] Bot em outra call. Movendo para {vc.name}...", flush=True)
                await bot_voice.move_to(vc)
                await asyncio.sleep(1)

                if guild.voice_client and not guild.voice_client.is_playing():
                    guild.voice_client.play(SilenceAudio())

                await guild.me.edit(mute=True, deafen=True)
                print("✅ [Keep-Alive] Bot movido com sucesso!", flush=True)

            else:
                # Bot está na call correta → Garante que o áudio silencioso está ativo
                if not bot_voice.is_playing():
                    bot_voice.play(SilenceAudio())
                    print("🔊 [Keep-Alive] Áudio silencioso reiniciado.", flush=True)

        except Exception as e:
            print(f"❌ [Keep-Alive] Erro: {e}", flush=True)

    # === EVENTO: Quando o bot for desconectado manualmente/kickado da call ===
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Se o bot for desconectado da call (kick/mute server), reconecta em 5 segundos."""
        if member.id != self.bot.user.id:
            return

        # Se o bot saiu de um canal (before tem canal, after não tem)
        if before.channel is not None and after.channel is None:
            print("⚠️ [VoiceState] Bot foi desconectado da call! Reconectando em 5s...", flush=True)
            await asyncio.sleep(5)
            # A task keep_alive_voice vai reconectar em no máximo 30s, 
            # mas aqui aceleramos um pouco
            data = load_data()
            voice_id = data.get("stats_voice_channel")
            if voice_id:
                vc = member.guild.get_channel(voice_id)
                if vc and isinstance(vc, discord.VoiceChannel):
                    try:
                        await vc.connect()
                        await asyncio.sleep(1)
                        if member.guild.voice_client and not member.guild.voice_client.is_playing():
                            member.guild.voice_client.play(SilenceAudio())
                        await member.guild.me.edit(mute=True, deafen=True)
                        print("✅ [VoiceState] Reconexão rápida realizada!", flush=True)
                    except Exception as e:
                        print(f"❌ [VoiceState] Erro na reconexão rápida: {e}", flush=True)


async def setup(bot):
    await bot.add_cog(StatsCog(bot))