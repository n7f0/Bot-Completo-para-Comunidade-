import discord
from discord.ext import commands
from discord import app_commands
from database import load_data, save_data
import asyncio

# Importação relativa (mesmo pacote cogs)
from .stats import SilenceAudio


class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="paineladmin", description="Envia o painel de administração")
    async def paineladmin(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Apenas administradores podem fixar este painel.", ephemeral=True)
            return

        data = load_data()
        embed = discord.Embed(
            title="⚙️ Painel Central de Administração", 
            description="Selecione no menu abaixo a categoria que deseja configurar. O painel de botões abrirá apenas para você de forma organizada.", 
            color=0xff0000
        )
        if data.get("admin_image"):
            embed.set_image(url=data.get("admin_image"))

        view = AdminMainView()
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Painel organizado fixado!", ephemeral=True)


class AdminMainView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) 

    @discord.ui.select(
        custom_id="master_admin_select",
        placeholder="Selecione o que deseja configurar...",
        options=[
            discord.SelectOption(label="Configurações Gerais", value="geral", emoji="⚙️", description="Cargo Admin, Autorole e Boas-vindas"),
            discord.SelectOption(label="Imagens (URLs)", value="imagens", emoji="🖼️", description="Colar links das imagens de todos os painéis"),
            discord.SelectOption(label="Registro e Idades", value="registro", emoji="📋", description="Configurar cargos do /painelreg"),
            discord.SelectOption(label="Central de Tickets", value="tickets", emoji="🎫", description="Editar categorias e nomes de tickets"),
            discord.SelectOption(label="Estatísticas e Calls", value="stats", emoji="📊", description="Painel de categorias em tempo real"),
            discord.SelectOption(label="Regras do Servidor", value="regras", emoji="📜", description="Escrever o texto das regras")
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        data = load_data()
        admin_id = data.get("admin_role_id")
        tem_permissao = interaction.user.guild_permissions.administrator
        if admin_id and not tem_permissao:
            role = interaction.guild.get_role(admin_id)
            if role and role in interaction.user.roles:
                tem_permissao = True

        if not tem_permissao:
            await interaction.response.send_message("❌ Você não tem permissão para usar o painel.", ephemeral=True)
            return

        val = select.values[0]
        if val == "geral":
            await interaction.response.send_message("⚙️ **Configurações Gerais**", view=GeralConfigView(), ephemeral=True)
        elif val == "imagens":
            await interaction.response.send_modal(ImagensModal())
        elif val == "registro":
            await interaction.response.send_message("📋 **Configurações de Registro**", view=RegistroConfigView(), ephemeral=True)
        elif val == "tickets":
            await interaction.response.send_message("🎫 **Configurações de Tickets**", view=TicketConfigView(), ephemeral=True)
        elif val == "stats":
            await interaction.response.send_message("📊 **Configurações de Estatísticas**", view=StatsConfigView(), ephemeral=True)
        elif val == "regras":
            await interaction.response.send_modal(RegrasTextModal())


# === SUB-MENUS ===
class GeralConfigView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
    @discord.ui.button(label="Cargo Admin", style=discord.ButtonStyle.secondary)
    async def b1(self, interaction, button): await interaction.response.send_message("Cargo Admin:", view=SingleRoleSelectView("admin_role_id"), ephemeral=True)
    @discord.ui.button(label="Cargo Automático", style=discord.ButtonStyle.secondary)
    async def b2(self, interaction, button): await interaction.response.send_message("Cargo Auto:", view=SingleRoleSelectView("autorole_id"), ephemeral=True)
    @discord.ui.button(label="Canal Boas-Vindas", style=discord.ButtonStyle.secondary)
    async def b3(self, interaction, button): await interaction.response.send_message("Canal Boas-Vindas:", view=ChannelSelectView("welcome_channel_id"), ephemeral=True)
    @discord.ui.button(label="Texto Boas-Vindas", style=discord.ButtonStyle.primary)
    async def b4(self, interaction, button): await interaction.response.send_modal(TextoBoasVindasModal())

class RegistroConfigView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
    @discord.ui.button(label="Cargo +16", style=discord.ButtonStyle.primary)
    async def b1(self, interaction, button): await interaction.response.send_message("Cargo +16:", view=SingleRoleSelectView("role_16"), ephemeral=True)
    @discord.ui.button(label="Cargo +18", style=discord.ButtonStyle.primary)
    async def b2(self, interaction, button): await interaction.response.send_message("Cargo +18:", view=SingleRoleSelectView("role_18"), ephemeral=True)
    @discord.ui.button(label="Cargo +25", style=discord.ButtonStyle.primary)
    async def b3(self, interaction, button): await interaction.response.send_message("Cargo +25:", view=SingleRoleSelectView("role_25"), ephemeral=True)

    @discord.ui.button(label="Adicionar Cargos Extras", style=discord.ButtonStyle.success)
    async def b4(self, interaction, button): await interaction.response.send_message("Selecione o cargo para ADICIONAR ao Registro:", view=AddRegRoleView(), ephemeral=True)

    @discord.ui.button(label="Remover Cargos Extras", style=discord.ButtonStyle.danger)
    async def b5(self, interaction, button): 
        data = load_data()
        available = data.get("available_roles", [])
        if not available:
            await interaction.response.send_message("❌ Nenhum cargo extra registrado no momento.", ephemeral=True)
            return

        options = []
        for role_id in available:
            role = interaction.guild.get_role(role_id)
            if role:
                options.append(discord.SelectOption(label=role.name, value=str(role_id)))

        if not options:
            await interaction.response.send_message("❌ Nenhum cargo válido para remover.", ephemeral=True)
            return

        await interaction.response.send_message("Selecione o cargo para **REMOVER** do painel de registro:", view=RemoveRegRoleView(options), ephemeral=True)

class TicketConfigView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
    @discord.ui.button(label="Nomes dos Botões", style=discord.ButtonStyle.primary)
    async def b_names(self, interaction, button): await interaction.response.send_modal(TicketNamesModal())
    @discord.ui.button(label="Cat: Denúncias", style=discord.ButtonStyle.secondary)
    async def b1(self, interaction, button): await interaction.response.send_message("Categoria Denúncias:", view=ChannelSelectView("ticket_cat_denuncia", discord.ChannelType.category), ephemeral=True)
    @discord.ui.button(label="Cat: Parcerias", style=discord.ButtonStyle.secondary)
    async def b2(self, interaction, button): await interaction.response.send_message("Categoria Parcerias:", view=ChannelSelectView("ticket_cat_parceria", discord.ChannelType.category), ephemeral=True)
    @discord.ui.button(label="Cat: Compras", style=discord.ButtonStyle.secondary)
    async def b3(self, interaction, button): await interaction.response.send_message("Categoria Compras:", view=ChannelSelectView("ticket_cat_compra", discord.ChannelType.category), ephemeral=True)
    @discord.ui.button(label="Cat: Dúvidas", style=discord.ButtonStyle.secondary)
    async def b4(self, interaction, button): await interaction.response.send_message("Categoria Dúvidas:", view=ChannelSelectView("ticket_cat_duvida", discord.ChannelType.category), ephemeral=True)


class StatsConfigView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="Categoria: Total Membros", style=discord.ButtonStyle.primary)
    async def b1(self, interaction, button): 
        await interaction.response.send_message("Onde mostrar Total de Membros:", view=ChannelSelectView("stats_cat_members", discord.ChannelType.category), ephemeral=True)

    @discord.ui.button(label="Categoria: Em Call", style=discord.ButtonStyle.primary)
    async def b2(self, interaction, button): 
        await interaction.response.send_message("Onde mostrar Pessoas em Call:", view=ChannelSelectView("stats_cat_voice", discord.ChannelType.category), ephemeral=True)

    @discord.ui.button(label="Canal de Voz pro Bot ficar", style=discord.ButtonStyle.secondary)
    async def b3(self, interaction, button): 
        await interaction.response.send_message("Canal pro bot entrar mutado:", view=ChannelSelectView("stats_voice_channel", discord.ChannelType.voice), ephemeral=True)

    # === BOTÃO: FORÇAR CONEXÃO DO BOT (CORRIGIDO) ===
    @discord.ui.button(label="Forçar Bot na Call", style=discord.ButtonStyle.success, emoji="🔊")
    async def b4(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_data()
        voice_id = data.get("stats_voice_channel")

        if not voice_id:
            await interaction.response.send_message("❌ Você precisa configurar o **Canal de Voz pro Bot ficar** primeiro!", ephemeral=True)
            return

        guild = interaction.guild
        vc = guild.get_channel(voice_id)

        if not vc or not isinstance(vc, discord.VoiceChannel):
            await interaction.response.send_message("❌ O canal configurado não foi encontrado. Configure novamente.", ephemeral=True)
            return

        # Verifica permissão do bot
        permissions = vc.permissions_for(guild.me)
        if not permissions.connect:
            await interaction.response.send_message("❌ O bot não tem permissão para **conectar** neste canal de voz!", ephemeral=True)
            return

        await interaction.response.send_message("🔊 Conectando o bot na call, aguarde...", ephemeral=True)

        try:
            bot_voice = guild.voice_client

            if bot_voice and bot_voice.channel.id == vc.id:
                # Já está na call correta
                await asyncio.sleep(2)
                if bot_voice.is_connected() and not bot_voice.is_playing():
                    bot_voice.play(SilenceAudio())
                await interaction.edit_original_response(content=f"✅ O bot já está na call {vc.mention}! (Áudio silencioso ativo)")
                return

            # Se está em outra call, desconecta primeiro
            if bot_voice:
                try:
                    await bot_voice.disconnect(force=True)
                except:
                    pass
                await asyncio.sleep(5)

            # Conecta na call correta com self_deaf
            voice_client = await vc.connect(timeout=30.0, reconnect=True, self_deaf=True)
            await asyncio.sleep(8)  # Aguarda handshake estabilizar

            if voice_client and voice_client.is_connected():
                try:
                    await guild.me.edit(mute=True)
                except:
                    pass
                await asyncio.sleep(1)
                if not voice_client.is_playing():
                    voice_client.play(SilenceAudio())
                await interaction.edit_original_response(content=f"✅ O bot entrou e foi mutado na call {vc.mention}! (Keep-alive 24/7 ativado)")
            else:
                await interaction.edit_original_response(content=f"⚠️ O handshake está em andamento. O bot tentará estabilizar automaticamente em até 60 segundos.")

        except Exception as e:
            await interaction.edit_original_response(content=f"❌ Erro: {e}. A task automática tentará reconectar em breve.")


# === MODAIS E VIEWS GENÉRICAS ===
class ImagensModal(discord.ui.Modal, title="URLs das Imagens (Limite do Discord: 5)"):
    def __init__(self):
        super().__init__()
        data = load_data()
        self.i1 = discord.ui.TextInput(label="Painel Admin", default=data.get("admin_image"), required=False)
        self.i2 = discord.ui.TextInput(label="Painel de Regras", default=data.get("rules_image"), required=False)
        self.i3 = discord.ui.TextInput(label="Painel de Registro", default=data.get("reg_image"), required=False)
        self.i4 = discord.ui.TextInput(label="Painel de Ticket", default=data.get("ticket_image"), required=False)
        self.i5 = discord.ui.TextInput(label="Boas Vindas (Chat)", default=data.get("welcome_image"), required=False)
        self.add_item(self.i1); self.add_item(self.i2); self.add_item(self.i3); self.add_item(self.i4); self.add_item(self.i5)

    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()
        data["admin_image"] = self.i1.value
        data["rules_image"] = self.i2.value
        data["reg_image"] = self.i3.value
        data["ticket_image"] = self.i4.value
        data["welcome_image"] = self.i5.value
        save_data(data)
        await interaction.response.send_message("✅ URLs salvas!", ephemeral=True)

class TextoBoasVindasModal(discord.ui.Modal, title="Texto Boas-Vindas"):
    def __init__(self):
        super().__init__()
        data = load_data()
        self.txt = discord.ui.TextInput(label="Texto (use {user} para mencionar)", style=discord.TextStyle.paragraph, default=data.get("welcome_text"), required=False)
        self.add_item(self.txt)
    async def on_submit(self, interaction):
        data = load_data(); data["welcome_text"] = self.txt.value; save_data(data)
        await interaction.response.send_message("✅ Texto salvo!", ephemeral=True)

class RegrasTextModal(discord.ui.Modal, title="Escrever Regras"):
    def __init__(self):
        super().__init__()
        data = load_data()
        self.txt = discord.ui.TextInput(label="Regras do Servidor", style=discord.TextStyle.paragraph, default=data.get("rules_text"), max_length=4000)
        self.add_item(self.txt)
    async def on_submit(self, interaction):
        data = load_data(); data["rules_text"] = self.txt.value; save_data(data)
        await interaction.response.send_message("✅ Regras salvas! Use o comando /painelregras no canal desejado para postar.", ephemeral=True)

class TicketNamesModal(discord.ui.Modal, title="Nomes dos Botões de Ticket"):
    def __init__(self):
        super().__init__()
        data = load_data()
        self.d1 = discord.ui.TextInput(label="Botão 1 (Denúncias)", default=data.get("ticket_name_denuncia"))
        self.d2 = discord.ui.TextInput(label="Botão 2 (Parcerias)", default=data.get("ticket_name_parceria"))
        self.d3 = discord.ui.TextInput(label="Botão 3 (Compras)", default=data.get("ticket_name_compra"))
        self.d4 = discord.ui.TextInput(label="Botão 4 (Dúvidas)", default=data.get("ticket_name_duvida"))
        self.add_item(self.d1); self.add_item(self.d2); self.add_item(self.d3); self.add_item(self.d4)
    async def on_submit(self, interaction):
        data = load_data()
        data["ticket_name_denuncia"] = self.d1.value; data["ticket_name_parceria"] = self.d2.value
        data["ticket_name_compra"] = self.d3.value; data["ticket_name_duvida"] = self.d4.value
        save_data(data); await interaction.response.send_message("✅ Nomes salvos!", ephemeral=True)

class SingleRoleSelectView(discord.ui.View):
    def __init__(self, config_key):
        super().__init__(timeout=120)
        self.config_key = config_key
    @discord.ui.select(cls=discord.ui.RoleSelect, placeholder="Escolha o cargo aqui...")
    async def callback(self, interaction, select):
        data = load_data(); data[self.config_key] = select.values[0].id; save_data(data)
        await interaction.response.edit_message(content=f"✅ Salvo: {select.values[0].mention}", view=None)

class ChannelSelectView(discord.ui.View):
    def __init__(self, config_key, channel_type=discord.ChannelType.text):
        super().__init__(timeout=120)
        self.config_key = config_key
        self.add_item(ChannelSelectComponent(config_key, channel_type))

class ChannelSelectComponent(discord.ui.ChannelSelect):
    def __init__(self, config_key, channel_type):
        super().__init__(placeholder="Escolha o canal/categoria...", channel_types=[channel_type])
        self.config_key = config_key
    async def callback(self, interaction):
        data = load_data(); data[self.config_key] = self.values[0].id; save_data(data)
        await interaction.response.edit_message(content=f"✅ Salvo: {self.values[0].mention}", view=None)

class AddRegRoleView(discord.ui.View):
    def __init__(self): super().__init__(timeout=120)
    @discord.ui.select(cls=discord.ui.RoleSelect, placeholder="Selecione o cargo para adicionar...")
    async def callback(self, interaction, select):
        role = select.values[0]; data = load_data()
        if role.id not in data.get("available_roles", []):
            data.setdefault("available_roles", []).append(role.id); save_data(data)
            await interaction.response.edit_message(content=f"✅ Cargo {role.mention} adicionado!", view=None)
        else: await interaction.response.edit_message(content="⚠️ O cargo já está na lista.", view=None)

class RemoveRegRoleView(discord.ui.View):
    def __init__(self, options):
        super().__init__(timeout=120)
        select = discord.ui.Select(placeholder="Selecione qual cargo remover...", options=options)
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        role_id = int(interaction.data["values"][0])
        data = load_data()

        if role_id in data.get("available_roles", []):
            data["available_roles"].remove(role_id)
            save_data(data)
            await interaction.response.edit_message(content="✅ Cargo removido da lista de registro com sucesso!", view=None)
        else:
            await interaction.response.edit_message(content="❌ Erro: Este cargo não foi encontrado na lista.", view=None)

async def setup(bot):
    bot.add_view(AdminMainView()) 
    await bot.add_cog(AdminCog(bot))