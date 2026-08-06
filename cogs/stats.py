import discord
from discord.ext import commands, tasks
from database import load_data
import asyncio
import socket

# === GERADOR DE ÁUDIO SILENCIOSO ===
class SilenceAudio(discord.AudioSource):
    def read(self):
        return b'\x00' * 3840

    def is_opus(self):
        return False


class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_stats.start()
        self.keep_alive_voice.start()
        self._lock = asyncio.Lock()
        self._last_reconnect = 0
        self._cooldown_seconds = 60
        self._consecutive_failures = 0
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
                        print(f"[Stats] Erro categoria membros: {e}", flush=True)

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

    async def _test_udp_connectivity(self, hostname, port=443):
        """Testa se consegue resolver hostname e conectar via UDP."""
        try:
            # Tenta resolver o hostname
            ip = socket.getaddrinfo(hostname, None, socket.AF_INET)[0][4][0]
            print(f"[Keep-Alive] 🌐 DNS OK: {hostname} -> {ip}", flush=True)

            # Tenta criar um socket UDP e enviar um pacote vazio (não envia nada, só testa)
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)
            sock.connect((ip, port))
            sock.close()
            print(f"[Keep-Alive] 🌐 UDP OK: conexão de saída funciona", flush=True)
            return True
        except Exception as e:
            print(f"[Keep-Alive] 🌐 Teste de rede falhou: {e}", flush=True)
            return False

    async def _connect_voice(self, guild, vc):
        """Conecta na call com retry interno do discord.py."""
        try:
            # Verifica permissão
            permissions = vc.permissions_for(guild.me)
            if not permissions.connect:
                print(f"[Keep-Alive] ❌ Sem permissão 'Conectar' em {vc.name}", flush=True)
                return False

            # Testa conectividade de rede antes de tentar
            test_host = "discord.com"
            network_ok = await self._test_udp_connectivity(test_host)
            if not network_ok:
                print(f"[Keep-Alive] ⚠️ Problema de rede detectado. Pulando tentativa.", flush=True)
                self._consecutive_failures += 1
                return False

            # Limpa conexão anterior
            if guild.voice_client is not None:
                try:
                    await guild.voice_client.disconnect(force=True)
                except Exception:
                    pass
                await asyncio.sleep(5)

            print(f"[Keep-Alive] Conectando em {vc.name}...", flush=True)
            voice_client = await vc.connect(timeout=30.0, reconnect=True, self_deaf=True)

            # Aguarda handshake estabilizar
            await asyncio.sleep(10)

            if voice_client and voice_client.is_connected():
                try:
                    await guild.me.edit(mute=True)
                except Exception:
                    pass
                await asyncio.sleep(1)
                if not voice_client.is_playing():
                    voice_client.play(SilenceAudio())
                print(f"[Keep-Alive] ✅ Conectado e com áudio silencioso em {vc.name}", flush=True)
                self._consecutive_failures = 0
                return True
            else:
                print(f"[Keep-Alive] ⚠️ Handshake não estabilizou.", flush=True)
                self._consecutive_failures += 1
                return False

        except Exception as e:
            print(f"[Keep-Alive] ❌ Erro ao conectar: {e}", flush=True)
            self._consecutive_failures += 1
            return False

    @tasks.loop(seconds=60)
    async def keep_alive_voice(self):
        await self.bot.wait_until_ready()

        # Delay inicial na primeira execução
        if self._first_run:
            self._first_run = False
            print("[Keep-Alive] ⏳ Aguardando 60 segundos antes da primeira verificação...", flush=True)
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

            # CASO 1: Bot NÃO está em nenhuma call
            if bot_voice is None:
                now = asyncio.get_event_loop().time()
                if now - self._last_reconnect < self._cooldown_seconds:
                    return
                self._last_reconnect = now

                success = await self._connect_voice(guild, vc)

                if not success and self._consecutive_failures >= 3:
                    extra_delay = min(600, 60 * (2 ** (self._consecutive_failures - 3)))
                    print(f"[Keep-Alive] ⏸️ Muitas falhas. Aguardando {extra_delay}s extras...", flush=True)
                    self._last_reconnect = now + extra_delay
                return

            # CASO 2: Bot está em OUTRA call
            if bot_voice.channel.id != vc.id:
                now = asyncio.get_event_loop().time()
                if now - self._last_reconnect < self._cooldown_seconds:
                    return
                self._last_reconnect = now

                try:
                    print(f"[Keep-Alive] Movendo de {bot_voice.channel.name} para {vc.name}...", flush=True)
                    await bot_voice.move_to(vc)
                    await asyncio.sleep(10)

                    if guild.voice_client and guild.voice_client.is_connected():
                        try:
                            await guild.me.edit(mute=True)
                        except Exception:
                            pass
                        await asyncio.sleep(1)
                        if not guild.voice_client.is_playing():
                            guild.voice_client.play(SilenceAudio())
                        print(f"[Keep-Alive] ✅ Movido com sucesso.", flush=True)
                        self._consecutive_failures = 0
                except Exception as e:
                    print(f"[Keep-Alive] ❌ Erro ao mover: {e}", flush=True)
                    self._consecutive_failures += 1
                return

            # CASO 3: Bot está na call CORRETA
            if bot_voice.is_connected() and not bot_voice.is_playing():
                try:
                    bot_voice.play(SilenceAudio())
                    print("[Keep-Alive] 🔊 Áudio silencioso reiniciado.", flush=True)
                except Exception as e:
                    print(f"[Keep-Alive] ❌ Erro ao reiniciar áudio: {e}", flush=True)


async def setup(bot):
    await bot.add_cog(StatsCog(bot))