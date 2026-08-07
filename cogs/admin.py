import discord
from discord.ext import commands
from discord import app_commands
from database import load_data, save_data
import asyncio
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
            title="⚙️ Administração · Painel Central", 
            description=(
                "### 📋 1 · Menu de Configuração\n"
                "Selecione no menu abaixo a categoria que deseja configurar.\n\n"
                "### 🔒 2 · Segurança\n"
                "O painel de botões abrirá apenas para você de forma organizada e segura."
            ),
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
            discord.SelectOption(label="Configurações Gerais", value="geral", emoji="⚙️"),
            discord.SelectOption(label="Imagens (URLs)", value="imagens", emoji="🖼️"),
            discord.SelectOption(label="Registro e Idades", value="registro", emoji="📋"),
            discord.SelectOption(label="Central de Tickets", value="tickets", emoji="🎫"),
            discord.SelectOption(label="Estatísticas e Calls", value="stats", emoji="📊"),
            discord.SelectOption(label="Regras do Servidor", value="regras", emoji="📜"),
            discord.SelectOption(label="Booster", value="booster", emoji="🚀"),
            discord.SelectOption(label="Comandos", value="comandos", emoji="📋"),
            discord.SelectOption(label="Overview & Moderação", value="overview", emoji="🛡️"),
            discord.SelectOption(label="Recrutamento Staff", value="staff", emoji="🎓"),
            discord.SelectOption(label="Tellonym (Anônimo)", value="tellonym", emoji="👻"),
            discord.SelectOption(label="Instagram", value="instagram", emoji="📸"),
            discord.SelectOption(label="Verificação", value="verify", emoji="✅", description="Configurar painel Verifique-se")
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        if not interaction.response.is_done():
            data = load_data()
            admin_id = data.get("admin_role_id")
            tem_permissao = interaction.user.guild_permissions.administrator
            if admin_id and not tem_permissao:
                role = interaction.guild.get_role(admin_id)
                if role and role in interaction.user.roles:
                    tem_permissao = True

            if not tem_permissao:
                await interaction.response.send_message("❌ Você não tem permissão.", ephemeral=True)
                return

            val = select.values[0]
            if val == "geral": await interaction.response.send_message("⚙️ **Configurações Gerais**", view=GeralConfigView(), ephemeral=True)
            elif val == "imagens": await interaction.response.send_modal(ImagensModal())
            elif val == "registro": await interaction.response.send_message("📋 **Configurações de Registro**", view=RegistroConfigView(), ephemeral=True)
            elif val == "tickets": await interaction.response.send_message("🎫 **Configurações de Tickets**", view=TicketConfigView(), ephemeral=True)
            elif val == "stats": await interaction.response.send_message("📊 **Configurações de Estatísticas**", view=StatsConfigView(), ephemeral=True)
            elif val == "regras": await interaction.response.send_modal(RegrasTextModal())
            elif val == "booster": await interaction.response.send_modal(BoosterConfigModal())
            elif val == "comandos": await interaction.response.send_modal(ComandosConfigModal())
            elif val == "overview": await interaction.response.send_message("🛡️ **Overview**", view=OverviewConfigView(), ephemeral=True)
            elif val == "staff": await interaction.response.send_message("🎓 **Recrutamento Staff**", view=StaffConfigView(), ephemeral=True)
            elif val == "tellonym": await interaction.response.send_message("👻 **Tellonym**", view=TellonymConfigView(), ephemeral=True)
            elif val == "instagram": await interaction.response.send_message("📸 **Instagram**", view=InstagramConfigView(), ephemeral=True)
            elif val == "verify": await interaction.response.send_message("✅ **Verificação (Verifique-se)**", view=VerifyConfigView(), ephemeral=True)
        else:
            await interaction.followup.send("⏰ A interação expirou.", ephemeral=True)

# === SUB-MENUS ===
class GeralConfigView(discord.ui.View):
    def __init__(self): super().__init__(timeout=300)
    @discord.ui.button(label="Cargo Admin", style=discord.ButtonStyle.secondary)
    async def b1(self, interaction, button): await interaction.response.send_message("Cargo Admin:", view=SingleRoleSelectView("admin_role_id"), ephemeral=True)
    @discord.ui.button(label="Cargo Automático", style=discord.ButtonStyle.secondary)
    async def b2(self, interaction, button): await interaction.response.send_message("Cargo Auto:", view=SingleRoleSelectView("autorole_id"), ephemeral=True)
    @discord.ui.button(label="Canal Boas-Vindas", style=discord.ButtonStyle.secondary)
    async def b3(self, interaction, button): await interaction.response.send_message("Canal Boas-Vindas:", view=ChannelSelectView("welcome_channel_id"), ephemeral=True)
    @discord.ui.button(label="Texto Boas-Vindas", style=discord.ButtonStyle.primary)
    async def b4(self, interaction, button): await interaction.response.send_modal(TextoBoasVindasModal())

class InstagramConfigView(discord.ui.View):
    def __init__(self): super().__init__(timeout=300)
    @discord.ui.button(label="Canal do Painel", style=discord.ButtonStyle.primary)
    async def b1(self, interaction, button): await interaction.response.send_message("Onde fica o painel?", view=ChannelSelectView("instagram_channel_id"), ephemeral=True)
    @discord.ui.button(label="Feed Masculino", style=discord.ButtonStyle.secondary)
    async def b2(self, interaction, button): await interaction.response.send_message("Canal Feed Masc:", view=ChannelSelectView("instagram_post_channel_masc"), ephemeral=True)
    @discord.ui.button(label="Feed Feminino", style=discord.ButtonStyle.secondary)
    async def b3(self, interaction, button): await interaction.response.send_message("Canal Feed Fem:", view=ChannelSelectView("instagram_post_channel_fem"), ephemeral=True)
    @discord.ui.button(label="Cargo Postador (Homem)", style=discord.ButtonStyle.primary)
    async def b4(self, interaction, button): await interaction.response.send_message("Cargo para postar no feed masc:", view=SingleRoleSelectView("instagram_role_masc"), ephemeral=True)
    @discord.ui.button(label="Cargo Postador (Mulher)", style=discord.ButtonStyle.primary)
    async def b5(self, interaction, button): await interaction.response.send_message("Cargo para postar no feed fem:", view=SingleRoleSelectView("instagram_role_fem"), ephemeral=True)
    @discord.ui.button(label="Imagem do Painel", style=discord.ButtonStyle.success)
    async def b6(self, interaction, button): await interaction.response.send_modal(InstagramImageModal())

class VerifyConfigView(discord.ui.View):
    def __init__(self): super().__init__(timeout=300)
    @discord.ui.button(label="Canal do Painel", style=discord.ButtonStyle.primary)
    async def b1(self, interaction, button): await interaction.response.send_message("Onde o painel 'Verifique-se' ficará?", view=ChannelSelectView("verify_channel_id"), ephemeral=True)
    @discord.ui.button(label="Categoria dos Chats", style=discord.ButtonStyle.secondary)
    async def b2(self, interaction, button): await interaction.response.send_message("Categoria dos chats temporários:", view=ChannelSelectView("verify_category_id", discord.ChannelType.category), ephemeral=True)
    @discord.ui.button(label="Cargo Verificador", style=discord.ButtonStyle.primary)
    async def b3(self, interaction, button): await interaction.response.send_message("Cargo da staff que verifica:", view=SingleRoleSelectView("verify_staff_role_id"), ephemeral=True)
    @discord.ui.button(label="Cargo de Verificado", style=discord.ButtonStyle.success)
    async def b4(self, interaction, button): await interaction.response.send_message("Cargo ganho após verificação:", view=SingleRoleSelectView("verify_reward_role_id"), ephemeral=True)
    @discord.ui.button(label="Imagem do Painel", style=discord.ButtonStyle.success)
    async def b5(self, interaction, button): await interaction.response.send_modal(VerifyImageModal())

class OverviewConfigView(discord.ui.View):
    def __init__(self): super().__init__(timeout=300)
    @discord.ui.button(label="Cargo Staff", style=discord.ButtonStyle.primary)
    async def b1(self, interaction, button): await interaction.response.send_message("Acesso:", view=SingleRoleSelectView("overview_role_id"), ephemeral=True)
    @discord.ui.button(label="Relatórios", style=discord.ButtonStyle.primary)
    async def b2(self, interaction, button): await interaction.response.send_message("Logs:", view=ChannelSelectView("report_channel_id"), ephemeral=True)
    @discord.ui.button(label="Painel Fixo", style=discord.ButtonStyle.primary)
    async def b3(self, interaction, button): await interaction.response.send_message("Painel:", view=ChannelSelectView("overview_channel_id"), ephemeral=True)
    @discord.ui.button(label="Mutado", style=discord.ButtonStyle.danger)
    async def b4(self, interaction, button): await interaction.response.send_message("Cargo:", view=SingleRoleSelectView("mute_role_id"), ephemeral=True)
    @discord.ui.button(label="Castigo", style=discord.ButtonStyle.danger)
    async def b5(self, interaction, button): await interaction.response.send_message("Cargo:", view=SingleRoleSelectView("castigo_role_id"), ephemeral=True)
    @discord.ui.button(label="Imagem", style=discord.ButtonStyle.secondary)
    async def b6(self, interaction, button): await interaction.response.send_modal(OverviewImageModal())

class StaffConfigView(discord.ui.View):
    def __init__(self): super().__init__(timeout=300)
    @discord.ui.button(label="Recrutador", style=discord.ButtonStyle.primary)
    async def b1(self, interaction, button): await interaction.response.send_message("Cargo:", view=SingleRoleSelectView("staff_recruiter_role_id"), ephemeral=True)
    @discord.ui.button(label="Categoria", style=discord.ButtonStyle.secondary)
    async def b2(self, interaction, button): await interaction.response.send_message("Categoria:", view=ChannelSelectView("staff_category_id", discord.ChannelType.category), ephemeral=True)
    @discord.ui.button(label="Painel", style=discord.ButtonStyle.secondary)
    async def b3(self, interaction, button): await interaction.response.send_message("Painel:", view=ChannelSelectView("staff_channel_id"), ephemeral=True)
    @discord.ui.button(label="Imagem", style=discord.ButtonStyle.success)
    async def b4(self, interaction, button): await interaction.response.send_modal(StaffImageModal())

class TellonymConfigView(discord.ui.View):
    def __init__(self): super().__init__(timeout=300)
    @discord.ui.button(label="Canal do Painel", style=discord.ButtonStyle.primary)
    async def b1(self, interaction, button): await interaction.response.send_message("Onde ficará o botão?", view=ChannelSelectView("tellonym_channel_id"), ephemeral=True)
    @discord.ui.button(label="Canal de Envio", style=discord.ButtonStyle.secondary)
    async def b2(self, interaction, button): await interaction.response.send_message("Onde as mensagens vão?", view=ChannelSelectView("tellonym_send_channel_id"), ephemeral=True)
    @discord.ui.button(label="Imagem", style=discord.ButtonStyle.success)
    async def b3(self, interaction, button): await interaction.response.send_modal(TellonymImageModal())

class RegistroConfigView(discord.ui.View):
    def __init__(self): super().__init__(timeout=300)
    @discord.ui.button(label="Cargo +16", style=discord.ButtonStyle.primary)
    async def b1(self, interaction, button): await interaction.response.send_message("Cargo +16:", view=SingleRoleSelectView("role_16"), ephemeral=True)
    @discord.ui.button(label="Cargo +18", style=discord.ButtonStyle.primary)
    async def b2(self, interaction, button): await interaction.response.send_message("Cargo +18:", view=SingleRoleSelectView("role_18"), ephemeral=True)
    @discord.ui.button(label="Cargo +25", style=discord.ButtonStyle.primary)
    async def b3(self, interaction, button): await interaction.response.send_message("Cargo +25:", view=SingleRoleSelectView("role_25"), ephemeral=True)
    @discord.ui.button(label="Adicionar Extras", style=discord.ButtonStyle.success)
    async def b4(self, interaction, button): await interaction.response.send_message("Cargo extra:", view=AddRegRoleView(), ephemeral=True)
    @discord.ui.button(label="Remover Extras", style=discord.ButtonStyle.danger)
    async def b5(self, interaction, button): 
        data = load_data()
        available = data.get("available_roles", [])
        if not available:
            await interaction.response.send_message("❌ Nenhum cargo extra registrado.", ephemeral=True)
            return
        options = [discord.SelectOption(label=interaction.guild.get_role(r).name, value=str(r)) for r in available if interaction.guild.get_role(r)]
        if not options: return
        await interaction.response.send_message("Selecione para **REMOVER**:", view=RemoveRegRoleView(options), ephemeral=True)

class TicketConfigView(discord.ui.View):
    def __init__(self): super().__init__(timeout=300)
    @discord.ui.button(label="Nomes Botões", style=discord.ButtonStyle.primary)
    async def b_names(self, interaction, button): await interaction.response.send_modal(TicketNamesModal())
    @discord.ui.button(label="Denúncias", style=discord.ButtonStyle.secondary)
    async def b1(self, interaction, button): await interaction.response.send_message("Categoria:", view=ChannelSelectView("ticket_cat_denuncia", discord.ChannelType.category), ephemeral=True)
    @discord.ui.button(label="Parcerias", style=discord.ButtonStyle.secondary)
    async def b2(self, interaction, button): await interaction.response.send_message("Categoria:", view=ChannelSelectView("ticket_cat_parceria", discord.ChannelType.category), ephemeral=True)
    @discord.ui.button(label="Compras", style=discord.ButtonStyle.secondary)
    async def b3(self, interaction, button): await interaction.response.send_message("Categoria:", view=ChannelSelectView("ticket_cat_compra", discord.ChannelType.category), ephemeral=True)
    @discord.ui.button(label="Dúvidas", style=discord.ButtonStyle.secondary)
    async def b4(self, interaction, button): await interaction.response.send_message("Categoria:", view=ChannelSelectView("ticket_cat_duvida", discord.ChannelType.category), ephemeral=True)

class StatsConfigView(discord.ui.View):
    def __init__(self): super().__init__(timeout=300)
    @discord.ui.button(label="Total Membros", style=discord.ButtonStyle.primary)
    async def b1(self, interaction, button): await interaction.response.send_message("Local:", view=ChannelSelectView("stats_cat_members", discord.ChannelType.category), ephemeral=True)
    @discord.ui.button(label="Em Call", style=discord.ButtonStyle.primary)
    async def b2(self, interaction, button): await interaction.response.send_message("Local:", view=ChannelSelectView("stats_cat_voice", discord.ChannelType.category), ephemeral=True)
    @discord.ui.button(label="Canal Bot", style=discord.ButtonStyle.secondary)
    async def b3(self, interaction, button): await interaction.response.send_message("Canal:", view=ChannelSelectView("stats_voice_channel", discord.ChannelType.voice), ephemeral=True)

# === MODAIS ===
class VerifyImageModal(discord.ui.Modal, title="Imagem da Verificação"):
    def __init__(self):
        super().__init__()
        data = load_data()
        self.img = discord.ui.TextInput(label="URL da Imagem do Painel", default=data.get("verify_image"), required=False)
        self.add_item(self.img)
    async def on_submit(self, interaction: discord.Interaction):
        data = load_data(); data["verify_image"] = self.img.value; save_data(data)
        await interaction.response.send_message("✅ Imagem da verificação salva!", ephemeral=True)

class InstagramImageModal(discord.ui.Modal, title="Imagem do Instagram"):
    def __init__(self):
        super().__init__()
        data = load_data()
        self.img = discord.ui.TextInput(label="URL da Imagem do Painel", default=data.get("instagram_image"), required=False)
        self.add_item(self.img)
    async def on_submit(self, interaction: discord.Interaction):
        data = load_data(); data["instagram_image"] = self.img.value; save_data(data)
        await interaction.response.send_message("✅ Imagem do Instagram salva!", ephemeral=True)

class OverviewImageModal(discord.ui.Modal, title="Imagem do Overview"):
    def __init__(self):
        super().__init__()
        data = load_data()
        self.img = discord.ui.TextInput(label="URL da Imagem do Painel", default=data.get("overview_image"), required=False)
        self.add_item(self.img)
    async def on_submit(self, interaction):
        data = load_data(); data["overview_image"] = self.img.value; save_data(data)
        await interaction.response.send_message("✅ Imagem salva!", ephemeral=True)

class StaffImageModal(discord.ui.Modal, title="Imagem de Recrutamento"):
    def __init__(self):
        super().__init__()
        data = load_data()
        self.img = discord.ui.TextInput(label="URL da Imagem", default=data.get("staff_image"), required=False)
        self.add_item(self.img)
    async def on_submit(self, interaction):
        data = load_data(); data["staff_image"] = self.img.value; save_data(data)
        await interaction.response.send_message("✅ Imagem salva!", ephemeral=True)

class TellonymImageModal(discord.ui.Modal, title="Imagem do Tellonym"):
    def __init__(self):
        super().__init__()
        data = load_data()
        self.img = discord.ui.TextInput(label="URL da Imagem", default=data.get("tellonym_image"), required=False)
        self.add_item(self.img)
    async def on_submit(self, interaction):
        data = load_data(); data["tellonym_image"] = self.img.value; save_data(data)
        await interaction.response.send_message("✅ Imagem salva!", ephemeral=True)

class ImagensModal(discord.ui.Modal, title="URLs das Imagens"):
    def __init__(self):
        super().__init__()
        data = load_data()
        self.i1 = discord.ui.TextInput(label="Painel Admin", default=data.get("admin_image"), required=False)
        self.i2 = discord.ui.TextInput(label="Painel de Regras", default=data.get("rules_image"), required=False)
        self.i3 = discord.ui.TextInput(label="Painel de Registro", default=data.get("reg_image"), required=False)
        self.i4 = discord.ui.TextInput(label="Painel de Ticket", default=data.get("ticket_image"), required=False)
        self.i5 = discord.ui.TextInput(label="Boas Vindas (Chat)", default=data.get("welcome_image"), required=False)
        self.add_item(self.i1); self.add_item(self.i2); self.add_item(self.i3); self.add_item(self.i4); self.add_item(self.i5)
    async def on_submit(self, interaction):
        data = load_data()
        data["admin_image"] = self.i1.value; data["rules_image"] = self.i2.value; data["reg_image"] = self.i3.value
        data["ticket_image"] = self.i4.value; data["welcome_image"] = self.i5.value; save_data(data)
        await interaction.response.send_message("✅ URLs salvas!", ephemeral=True)

class TextoBoasVindasModal(discord.ui.Modal, title="Texto Boas-Vindas"):
    def __init__(self):
        super().__init__()
        self.txt = discord.ui.TextInput(label="Texto", style=discord.TextStyle.paragraph, default=load_data().get("welcome_text"), required=False)
        self.add_item(self.txt)
    async def on_submit(self, interaction):
        data = load_data(); data["welcome_text"] = self.txt.value; save_data(data)
        await interaction.response.send_message("✅ Texto salvo!", ephemeral=True)

class RegrasTextModal(discord.ui.Modal, title="Escrever Regras"):
    def __init__(self):
        super().__init__()
        self.txt = discord.ui.TextInput(label="Regras", style=discord.TextStyle.paragraph, default=load_data().get("rules_text"), max_length=4000)
        self.add_item(self.txt)
    async def on_submit(self, interaction):
        data = load_data(); data["rules_text"] = self.txt.value; save_data(data)
        await interaction.response.send_message("✅ Regras salvas!", ephemeral=True)

class TicketNamesModal(discord.ui.Modal, title="Nomes Botões de Ticket"):
    def __init__(self):
        super().__init__()
        data = load_data()
        self.d1 = discord.ui.TextInput(label="Denúncias", default=data.get("ticket_name_denuncia"))
        self.d2 = discord.ui.TextInput(label="Parcerias", default=data.get("ticket_name_parceria"))
        self.d3 = discord.ui.TextInput(label="Compras", default=data.get("ticket_name_compra"))
        self.d4 = discord.ui.TextInput(label="Dúvidas", default=data.get("ticket_name_duvida"))
        self.add_item(self.d1); self.add_item(self.d2); self.add_item(self.d3); self.add_item(self.d4)
    async def on_submit(self, interaction):
        data = load_data()
        data["ticket_name_denuncia"] = self.d1.value; data["ticket_name_parceria"] = self.d2.value
        data["ticket_name_compra"] = self.d3.value; data["ticket_name_duvida"] = self.d4.value
        save_data(data); await interaction.response.send_message("✅ Nomes salvos!", ephemeral=True)

class BoosterConfigModal(discord.ui.Modal, title="Configuração Booster"):
    def __init__(self):
        super().__init__()
        data = load_data()
        self.titulo = discord.ui.TextInput(label="Título", default=data.get("booster_title"), max_length=100)
        self.descricao = discord.ui.TextInput(label="Descrição", style=discord.TextStyle.paragraph, default=data.get("booster_description"), required=False)
        self.imagem = discord.ui.TextInput(label="URL da Imagem", default=data.get("booster_image"), required=False)
        self.label_botao = discord.ui.TextInput(label="Texto do Botão", default=data.get("booster_button_label"))
        self.add_item(self.titulo); self.add_item(self.descricao); self.add_item(self.imagem); self.add_item(self.label_botao)
    async def on_submit(self, interaction):
        data = load_data()
        data["booster_title"] = self.titulo.value; data["booster_description"] = self.descricao.value
        data["booster_image"] = self.imagem.value; data["booster_button_label"] = self.label_botao.value
        save_data(data); await interaction.response.send_message("✅ Salvo!", ephemeral=True)

class ComandosConfigModal(discord.ui.Modal, title="Configuração Comandos"):
    def __init__(self):
        super().__init__()
        data = load_data()
        self.titulo = discord.ui.TextInput(label="Título", default=data.get("comandos_title"), max_length=100)
        self.descricao = discord.ui.TextInput(label="Descrição", style=discord.TextStyle.paragraph, default=data.get("comandos_description"), required=False)
        self.imagem = discord.ui.TextInput(label="URL da Imagem", default=data.get("comandos_image"), required=False)
        self.add_item(self.titulo); self.add_item(self.descricao); self.add_item(self.imagem)
    async def on_submit(self, interaction):
        data = load_data()
        data["comandos_title"] = self.titulo.value; data["comandos_description"] = self.descricao.value
        data["comandos_image"] = self.imagem.value
        save_data(data); await interaction.response.send_message("✅ Salvo!", ephemeral=True)


# === VIEWS GENÉRICAS ===
class SingleRoleSelectView(discord.ui.View):
    def __init__(self, config_key):
        super().__init__(timeout=300)
        self.config_key = config_key
    @discord.ui.select(cls=discord.ui.RoleSelect, placeholder="Escolha o cargo...")
    async def callback(self, interaction, select):
        data = load_data(); data[self.config_key] = select.values[0].id; save_data(data)
        await interaction.response.edit_message(content=f"✅ Salvo: {select.values[0].mention}", view=None)

class ChannelSelectView(discord.ui.View):
    def __init__(self, config_key, channel_type=discord.ChannelType.text):
        super().__init__(timeout=300)
        self.config_key = config_key
        self.add_item(ChannelSelectComponent(config_key, channel_type))

class ChannelSelectComponent(discord.ui.ChannelSelect):
    def __init__(self, config_key, channel_type):
        super().__init__(placeholder="Escolha o canal...", channel_types=[channel_type])
        self.config_key = config_key
    async def callback(self, interaction):
        data = load_data(); data[self.config_key] = self.values[0].id; save_data(data)
        await interaction.response.edit_message(content=f"✅ Salvo: {self.values[0].mention}", view=None)

class AddRegRoleView(discord.ui.View):
    def __init__(self): super().__init__(timeout=300)
    @discord.ui.select(cls=discord.ui.RoleSelect, placeholder="Selecione o cargo...")
    async def callback(self, interaction, select):
        role = select.values[0]; data = load_data()
        if role.id not in data.get("available_roles", []):
            data.setdefault("available_roles", []).append(role.id); save_data(data)
            await interaction.response.edit_message(content=f"✅ Cargo {role.mention} adicionado!", view=None)
        else: await interaction.response.edit_message(content="⚠️ Já está na lista.", view=None)

class RemoveRegRoleView(discord.ui.View):
    def __init__(self, options):
        super().__init__(timeout=300)
        select = discord.ui.Select(placeholder="Remover cargo...", options=options)
        select.callback = self.select_callback
        self.add_item(select)
    async def select_callback(self, interaction):
        role_id = int(interaction.data["values"][0]); data = load_data()
        if role_id in data.get("available_roles", []):
            data["available_roles"].remove(role_id); save_data(data)
            await interaction.response.edit_message(content="✅ Cargo removido!", view=None)
        else: await interaction.response.edit_message(content="❌ Erro.", view=None)

async def setup(bot):
    bot.add_view(AdminMainView()) 
    await bot.add_cog(AdminCog(bot))
