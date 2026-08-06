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
                super().__init__(silence_file)
                return
        super().__init__(silence_file, before_options="-reconnect 1 -reconnect_streamed 1")


class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_stats.start()
        # DESATIVADO TEMPORARIAMENTE PARA EVITAR ERROS DE DNS
        # self.keep_alive_voice.start()
        self._lock = asyncio.Lock()
        self._last_reconnect = 0
        self._cooldown_seconds = 120
        self._consecutive_failures = 0
        self._max_failures = 5
        self._disabled = True  # Começa desativado
        self._first_run = True

    def cog_unload(self):
        self.update_stats.cancel()
        # self.keep_alive_voice.cancel()

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
        if self._disabled:
            print("[Keep-Alive] ⛔ Task desativada. Para reativar, reinicie o bot e descomente a linha no __init__.")
            return False

        try:
            permissions = vc.permissions_for(guild.me)
            if not permissions.connect:
                print(f"[Keep-Alive] ❌ Sem permissão 'Conectar' em {vc.name}")
                return False

            if guild.voice_client:
                try:
                    await guild.voice_client.disconnect(force=True)
                except:
                    pass
                await asyncio.sleep(5)

            print(f"[Keep-Alive] Conectando em {vc.name} com self_deaf=False...")
            voice_client = await vc.connect(timeout=20.0, reconnect=True, self_deaf=False)
            await asyncio.sleep(10)

            if voice_client and voice_client.is_connected():
                try:
                    await guild.me.edit(mute=True, deafen=True)
                except Exception as e:
                    print(f"[Keep-Alive] Erro ao mutar/ensurdecer: {e}")

                if not voice_client.is_playing():
                    voice_client.play(SilenceAudio())

                print(f"[Keep-Alive] ✅ Conectado e mutado em {vc.name}")
                self._consecutive_failures = 0
                return True
            else:
                print("[Keep-Alive] ⚠️ Handshake não estabilizou após 10s.")
                self._consecutive_failures += 1
                return False

        except discord.ClientException as e:
            print(f"[Keep-Alive] ❌ ClientException: {e}")
            self._consecutive_failures += 1
            return False
        except Exception as e:
            print(f"[Keep-Alive] ❌ Erro ao conectar: {e}")
            self._consecutive_failures += 1
            if self._consecutive_failures >= self._max_failures:
                self._disabled = True
                print(f"[Keep-Alive] ⛔ Desativado permanentemente após {self._max_failures} falhas.")
            return False

    # Task de keep_alive desativada - comentada
    # @tasks.loop(seconds=60)
    # async def keep_alive_voice(self):
    #     await self.bot.wait_until_ready()
    #     if self._disabled:
    #         return
    #     # ... resto do código ...


async def setup(bot):
    await bot.add_cog(StatsCog(bot))