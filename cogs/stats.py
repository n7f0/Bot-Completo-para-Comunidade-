import discord
from discord.ext import commands, tasks
from database import load_data
import asyncio
import os
import subprocess

# ============================================
# Fonte de áudio silencioso via FFmpeg (Opus)
# ============================================
class SilenceAudio(discord.FFmpegPCMAudio):
    def __init__(self):
        # Cria um arquivo de silêncio se não existir
        silence_file = "silence.mp3"
        if not os.path.exists(silence_file):
            try:
                subprocess.run(
                    ["ffmpeg", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono",
                     "-t", "3600", "-acodec", "libmp3lame", silence_file],
                    check=True, capture_output=True
                )
                print("[Audio] Arquivo de silêncio criado com sucesso.")
            except Exception as e:
                print(f"[Audio] Erro ao criar silence.mp3: {e}. Usando fallback PCM.")
                # Fallback para PCM (pode não funcionar em todos os casos)
                super().__init__(silence_file)  # vai falhar, mas tratamos
                return
        super().__init__(silence_file, before_options="-reconnect 1 -reconnect_streamed 1")


class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_stats.start()
        self.keep_alive_voice.start()
        self._lock = asyncio.Lock()
        self._last_reconnect = 0
        self._cooldown_seconds = 120          # 2 minutos entre tentativas
        self._consecutive_failures = 0
        self._max_failures = 5                # desativa após 5 falhas seguidas
        self._disabled = False                # task desativada
        self._first_run = True

    def cog_unload(self):
        self.update_stats.cancel()
        self.keep_alive_voice.cancel()

    @tasks.loop(minutes=6)
    async def update_stats(self):
        await self.bot.wait_until_ready()
        if not self.bot.guilds:
            return

        guild = self.bot.guilds[0]
        data = load_data()

        cat_members_id = data.get("stats_cat_members")
        if cat_members_id:
            cat_members = guild.get_channel(cat_members_id)
            if cat_members and isinstance(cat_members, discord.CategoryChannel):
                novo_nome = f"📊 Membros: {guild.member_count}"
                if cat_members.name != novo_nome:
                    try:
                        await cat_members.edit(name=novo_nome)
                    except Exception as e:
                        print(f"[Stats] Erro categoria membros: {e}")

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
                        print(f"[Stats] Erro categoria voz: {e}")

    async def _connect_voice(self, guild, vc):
        """Conecta na call com tratamento de erro e backoff."""
        if self._disabled:
            print("[Keep-Alive] ⛔ Task desativada devido a muitas falhas. Reinicie o bot para reativar.")
            return False

        try:
            # Verifica permissão
            permissions = vc.permissions_for(guild.me)
            if not permissions.connect:
                print(f"[Keep-Alive] ❌ Sem permissão 'Conectar' em {vc.name}")
                return False

            # Desconecta qualquer conexão anterior
            if guild.voice_client:
                try:
                    await guild.voice_client.disconnect(force=True)
                except:
                    pass
                await asyncio.sleep(5)

            print(f"[Keep-Alive] Conectando em {vc.name}...")
            voice_client = await vc.connect(timeout=30.0, reconnect=True, self_deaf=True)

            # Aguarda estabilização
            await asyncio.sleep(8)

            if voice_client and voice_client.is_connected():
                # Muta o bot (já está self_deaf, mas garantimos)
                try:
                    await guild.me.edit(mute=True)
                except:
                    pass

                # Inicia áudio silencioso
                if not voice_client.is_playing():
                    voice_client.play(SilenceAudio())
                print(f"[Keep-Alive] ✅ Conectado e com áudio silencioso em {vc.name}")
                self._consecutive_failures = 0
                return True
            else:
                print("[Keep-Alive] ⚠️ Handshake não estabilizou.")
                self._consecutive_failures += 1
                return False

        except Exception as e:
            print(f"[Keep-Alive] ❌ Erro ao conectar: {e}")
            self._consecutive_failures += 1
            if self._consecutive_failures >= self._max_failures:
                self._disabled = True
                print(f"[Keep-Alive] ⛔ Desativado permanentemente após {self._max_failures} falhas.")
            return False

    @tasks.loop(seconds=60)
    async def keep_alive_voice(self):
        await self.bot.wait_until_ready()

        if self._disabled:
            return

        if self._first_run:
            self._first_run = False
            print("[Keep-Alive] ⏳ Aguardando 60s antes da primeira verificação...")
            await asyncio.sleep(60)

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

        if self._lock.locked():
            return

        async with self._lock:
            bot_voice = guild.voice_client

            # Caso 1: Bot não está em nenhuma call
            if bot_voice is None:
                now = asyncio.get_event_loop().time()
                if now - self._last_reconnect < self._cooldown_seconds:
                    return
                self._last_reconnect = now

                success = await self._connect_voice(guild, vc)
                if not success and self._consecutive_failures >= 3:
                    # Aumenta cooldown progressivamente
                    extra = min(600, 60 * (2 ** (self._consecutive_failures - 3)))
                    print(f"[Keep-Alive] ⏸️ Falhas: {self._consecutive_failures}. Aguardando {extra}s extras.")
                    self._last_reconnect = now + extra
                return

            # Caso 2: Bot está em outra call
            if bot_voice.channel.id != vc.id:
                now = asyncio.get_event_loop().time()
                if now - self._last_reconnect < self._cooldown_seconds:
                    return
                self._last_reconnect = now

                try:
                    print(f"[Keep-Alive] Movendo de {bot_voice.channel.name} para {vc.name}...")
                    await bot_voice.move_to(vc)
                    await asyncio.sleep(8)

                    if guild.voice_client and guild.voice_client.is_connected():
                        try:
                            await guild.me.edit(mute=True)
                        except:
                            pass
                        if not guild.voice_client.is_playing():
                            guild.voice_client.play(SilenceAudio())
                        print("[Keep-Alive] ✅ Movido com sucesso.")
                        self._consecutive_failures = 0
                except Exception as e:
                    print(f"[Keep-Alive] ❌ Erro ao mover: {e}")
                    self._consecutive_failures += 1
                    if self._consecutive_failures >= self._max_failures:
                        self._disabled = True
                return

            # Caso 3: Bot está na call correta – apenas garante que o áudio está tocando
            if bot_voice.is_connected() and not bot_voice.is_playing():
                try:
                    bot_voice.play(SilenceAudio())
                    print("[Keep-Alive] 🔊 Áudio silencioso reiniciado.")
                except Exception as e:
                    print(f"[Keep-Alive] ❌ Erro ao reiniciar áudio: {e}")


async def setup(bot):
    await bot.add_cog(StatsCog(bot))