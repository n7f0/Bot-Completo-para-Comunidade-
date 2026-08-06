import discord
from discord.ext import commands, tasks
from database import load_data
import asyncio

# === GERADOR DE ÁUDIO SILENCIOSO ===
# Impede que o Discord desconecte o bot por inatividade (idle timeout)
class SilenceAudio(discord.AudioSource):
    def read(self):
        # 20ms de silêncio PCM (stereo, 16-bit, 48000Hz) = 3840 bytes
        return b'\x00' * 3840

    def is_opus(self):
        return False


class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_stats.start()
        self.keep_alive_voice.start()
        self._lock = asyncio.Lock()          # Garante apenas 1 operação de voz por vez
        self._last_reconnect = 0             # Timestamp da última reconexão (cooldown)
        self._cooldown_seconds = 20          # Cooldown mínimo entre reconexões

    def cog_unload(self):
        self.update_stats.cancel()
        self.keep_alive_voice.cancel()

    # === TASK 1: Atualiza nomes das categorias a cada 6 minutos ===
    @tasks.loop(minutes=6)
    async def update_stats(self):
        await self.bot.wait_until_ready()
        if not self.bot.guilds:
            return

        guild = self.bot.guilds[0]
        data = load_data()

        # Categoria de Membros Totais
        cat_members_id = data.get("stats_cat_members")
        if cat_members_id:
            cat_members = guild.get_channel(cat_members_id)
            if cat_members and isinstance(cat_members, discord.CategoryChannel):
                novo_nome = f"📊 Membros: {guild.member_count}"
                if cat_members.name != novo_nome:
                    try: 
                        await cat_members.edit(name=novo_nome)
                    except Exception as e: 
                        print(f"[Stats] Erro categoria membros: {e}", flush=True)

        # Categoria de Pessoas em Call
        cat_voice_id = data.get("stats_cat_voice")
        if cat_voice_id:
            cat_voice = guild.get_channel(cat_voice_id)
            if cat_voice and isinstance(cat_voice, discord.CategoryChannel):
                in_voice = sum(1 for m in guild.members if m.voice and m.voice.channel)
                novo_nome = f"🔊 Em Call: {in_voice}"
                if cat_voice.name != novo_nome:
                    try: 
                        await cat_voice.edit(name=novo_nome)
                    except Exception as e: 
                        print(f"[Stats] Erro categoria voz: {e}", flush=True)

    # === FUNÇÃO AUXILIAR: Conectar com retry interno ===
    async def _connect_voice(self, guild, vc):
        """Conecta na call com retry interno do discord.py."""
        try:
            # Se já existe voice_client em qualquer estado, limpa primeiro
            if guild.voice_client is not None:
                try:
                    await guild.voice_client.disconnect(force=True)
                except Exception:
                    pass
                # Aguarda o discord.py limpar o estado interno
                await asyncio.sleep(3)

            # Conecta — o discord.py 2.3.2 já faz retry automático internamente
            print(f"[Keep-Alive] Conectando em {vc.name}...", flush=True)
            voice_client = await vc.connect(timeout=30.0, reconnect=True)

            # Aguarda o handshake estabilizar
            await asyncio.sleep(5)

            if voice_client and voice_client.is_connected():
                # Muta e toca áudio silencioso
                await guild.me.edit(mute=True, deafen=True)
                await asyncio.sleep(1)
                if not voice_client.is_playing():
                    voice_client.play(SilenceAudio())
                print(f"[Keep-Alive] ✅ Conectado e com áudio silencioso em {vc.name}", flush=True)
                return True
            else:
                print(f"[Keep-Alive] ⚠️ Handshake não estabilizou.", flush=True)
                return False

        except Exception as e:
            print(f"[Keep-Alive] ❌ Erro ao conectar: {e}", flush=True)
            return False

    # === TASK 2: Keep-Alive — verifica a cada 60 segundos ===
    @tasks.loop(seconds=60)
    async def keep_alive_voice(self):
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

        # Lock garante que apenas uma operação de voz rode por vez
        if self._lock.locked():
            return

        async with self._lock:
            bot_voice = guild.voice_client

            # === CASO 1: Bot NÃO está em nenhuma call ===
            if bot_voice is None:
                # Verifica cooldown para não spamar reconexões
                now = asyncio.get_event_loop().time()
                if now - self._last_reconnect < self._cooldown_seconds:
                    return
                self._last_reconnect = now

                await self._connect_voice(guild, vc)
                return

            # === CASO 2: Bot está em OUTRA call ===
            if bot_voice.channel.id != vc.id:
                now = asyncio.get_event_loop().time()
                if now - self._last_reconnect < self._cooldown_seconds:
                    return
                self._last_reconnect = now

                try:
                    print(f"[Keep-Alive] Movendo de {bot_voice.channel.name} para {vc.name}...", flush=True)
                    await bot_voice.move_to(vc)
                    await asyncio.sleep(5)

                    if guild.voice_client and guild.voice_client.is_connected():
                        await guild.me.edit(mute=True, deafen=True)
                        await asyncio.sleep(1)
                        if not guild.voice_client.is_playing():
                            guild.voice_client.play(SilenceAudio())
                        print(f"[Keep-Alive] ✅ Movido com sucesso.", flush=True)
                except Exception as e:
                    print(f"[Keep-Alive] ❌ Erro ao mover: {e}", flush=True)
                return

            # === CASO 3: Bot está na call CORRETA ===
            # Apenas garante que o áudio silencioso está ativo
            if bot_voice.is_connected() and not bot_voice.is_playing():
                try:
                    bot_voice.play(SilenceAudio())
                    print("[Keep-Alive] 🔊 Áudio silencioso reiniciado.", flush=True)
                except Exception as e:
                    print(f"[Keep-Alive] ❌ Erro ao reiniciar áudio: {e}", flush=True)


async def setup(bot):
    await bot.add_cog(StatsCog(bot))