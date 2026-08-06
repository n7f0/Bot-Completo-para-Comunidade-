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
        self.keep_alive_voice.start()  # Mantém o bot na call 24/7
        self._reconnecting = False  # Flag para evitar múltiplas reconexões simultâneas

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

    # === FUNÇÃO AUXILIAR: Conectar com retry e delay ===
    async def _safe_connect_voice(self, guild, vc, max_retries=3):
        """Conecta na call com retry, delay e verificação de estado."""
        for attempt in range(1, max_retries + 1):
            try:
                # Desconecta primeiro se houver conexão pendente/travada
                if guild.voice_client:
                    try:
                        await guild.voice_client.disconnect(force=True)
                    except:
                        pass
                    await asyncio.sleep(2)

                # Conecta e aguarda o handshake completar
                print(f"🔊 [Keep-Alive] Tentativa {attempt}/{max_retries} de conectar em {vc.name}...", flush=True)
                voice_client = await vc.connect(timeout=30.0, reconnect=True)

                # Aguarda o handshake de voz completar (pode levar 2-5 segundos)
                await asyncio.sleep(4)

                # Verifica se realmente conectou
                if not voice_client or not voice_client.is_connected():
                    print(f"⚠️ [Keep-Alive] Handshake não completou na tentativa {attempt}. Retrying...", flush=True)
                    await asyncio.sleep(3)
                    continue

                # Muta o bot
                await guild.me.edit(mute=True, deafen=True)
                await asyncio.sleep(1)

                # Inicia áudio silencioso
                if not voice_client.is_playing():
                    voice_client.play(SilenceAudio())

                print(f"✅ [Keep-Alive] Conectado com sucesso em {vc.name}!", flush=True)
                return True

            except Exception as e:
                print(f"❌ [Keep-Alive] Tentativa {attempt} falhou: {e}", flush=True)
                if attempt < max_retries:
                    await asyncio.sleep(5 * attempt)  # Backoff crescente
                else:
                    print(f"❌ [Keep-Alive] Todas as tentativas falharam.", flush=True)
                    return False
        return False

    # === TASK 2: KEEP-ALIVE 24/7 - Reconecta automaticamente ===
    @tasks.loop(seconds=45)
    async def keep_alive_voice(self):
        """Verifica a cada 45 segundos se o bot está na call configurada.
        Se não estiver, reconecta. Se estiver, garante que o áudio silencioso está tocando."""

        # Evita múltiplas reconexões simultâneas
        if self._reconnecting:
            return

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
            # CASO 1: Bot não está em nenhuma call → Conecta
            if bot_voice is None:
                self._reconnecting = True
                success = await self._safe_connect_voice(guild, vc)
                self._reconnecting = False
                return

            # CASO 2: Bot está em outra call → Move para a correta
            if bot_voice.channel.id != vc.id:
                self._reconnecting = True
                print(f"🔊 [Keep-Alive] Bot em outra call. Movendo para {vc.name}...", flush=True)
                try:
                    await bot_voice.move_to(vc)
                    await asyncio.sleep(4)  # Aguarda handshake após mover

                    if guild.voice_client and guild.voice_client.is_connected():
                        await guild.me.edit(mute=True, deafen=True)
                        await asyncio.sleep(1)
                        if not guild.voice_client.is_playing():
                            guild.voice_client.play(SilenceAudio())
                        print(f"✅ [Keep-Alive] Bot movido com sucesso!", flush=True)
                except Exception as e:
                    print(f"❌ [Keep-Alive] Erro ao mover: {e}. Tentando reconectar do zero...", flush=True)
                    # Se falhou ao mover, tenta conectar do zero
                    await self._safe_connect_voice(guild, vc)
                finally:
                    self._reconnecting = False
                return

            # CASO 3: Bot está na call correta → Garante que o áudio silencioso está ativo
            if bot_voice.is_connected():
                if not bot_voice.is_playing():
                    bot_voice.play(SilenceAudio())
                    print("🔊 [Keep-Alive] Áudio silencioso reiniciado.", flush=True)

        except Exception as e:
            print(f"❌ [Keep-Alive] Erro inesperado: {e}", flush=True)
            self._reconnecting = False

    # === EVENTO: Quando o bot for desconectado manualmente/kickado da call ===
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Se o bot for desconectado da call (kick/mute server), reconecta em 10 segundos."""
        if member.id != self.bot.user.id:
            return

        # Se o bot saiu de um canal (before tem canal, after não tem)
        if before.channel is not None and after.channel is None:
            print("⚠️ [VoiceState] Bot foi desconectado da call! Reconectando em 10s...", flush=True)
            await asyncio.sleep(10)

            # Evita reconectar se já reconectou por outro meio
            if member.guild.voice_client and member.guild.voice_client.is_connected():
                return

            data = load_data()
            voice_id = data.get("stats_voice_channel")
            if voice_id:
                vc = member.guild.get_channel(voice_id)
                if vc and isinstance(vc, discord.VoiceChannel):
                    await self._safe_connect_voice(member.guild, vc)


async def setup(bot):
    await bot.add_cog(StatsCog(bot))