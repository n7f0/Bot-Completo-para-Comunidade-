import discord
from discord.ext import commands
from discord import app_commands
from database import load_data, save_data

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="paineladmin", description="Envia o painel de administração fixo no chat")
    async def paineladmin(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Apenas administradores do servidor podem fixar este painel.", ephemeral=True)
            return

        data = load_data()
        embed = discord.Embed(
            title="⚙️ Painel Central de Administração", 
            description=(
                "Bem-vindo ao painel de controle do Bot!\n\n"
                "**Como usar:**\n"
                "Clique nos botões abaixo para configurar o servidor. "
                "Para colocar as imagens nos painéis, clique em **📝 Textos e Imagens** e cole as URLs."
            ), 
            color=0xff0000
        )
        
        if data.get("admin_image"):
            embed.set_image(url=data.get("admin_image"))

        view = AdminMainView()
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Painel fixado no chat com sucesso! Você pode apagar esta mensagem temporária.", ephemeral=True)


class AdminMainView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) 

    async def verificar_permissao(self, interaction: discord.Interaction):
        data = load_data()
        admin_id = data.get("admin_role_id")
        tem_permissao = interaction.user.guild_permissions.administrator
        
        if admin_id and not tem_permissao:
            role = interaction.guild.get_role(admin_id)
            if role and role in interaction.user.roles:
                tem_permissao = True
                
        if not tem_permissao:
            await interaction.response.send_message("❌ Você não tem permissão para usar estes botões.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Cargo Admin", style=discord.ButtonStyle.secondary, emoji="👥", custom_id="btn_admin_role")
    async def btn_admin(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.verificar_permissao(interaction):
            await interaction.response.send_message("Selecione o Cargo de Administrador do Bot:", view=SingleRoleSelectView("admin_role_id"), ephemeral=True)

    @discord.ui.button(label="Cargo Automático", style=discord.ButtonStyle.secondary, emoji="📥", custom_id="btn_autorole")
    async def btn_autorole(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.verificar_permissao(interaction):
            await interaction.response.send_message("Selecione o Cargo Automático (Autorole):", view=SingleRoleSelectView("autorole_id"), ephemeral=True)

    @discord.ui.button(label="Canal Boas-Vindas", style=discord.ButtonStyle.secondary, emoji="👋", custom_id="btn_welcome")
    async def btn_welcome(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.verificar_permissao(interaction):
            await interaction.response.send_message("Selecione o Canal de Boas-Vindas:", view=ChannelSelectView("welcome_channel_id"), ephemeral=True)

    @discord.ui.button(label="Textos e Imagens", style=discord.ButtonStyle.primary, emoji="📝", custom_id="btn_text_img")
    async def btn_text_img(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.verificar_permissao(interaction):
            await interaction.response.send_modal(TextImageModal())

    @discord.ui.button(label="Cargos Idade", style=discord.ButtonStyle.success, emoji="🎂", custom_id="btn_age_roles")
    async def btn_age_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.verificar_permissao(interaction):
            # NOVO MENU DE IDADES
            await interaction.response.send_message("⚙️ **Configuração de Idades**\nEscolha qual cargo deseja definir:", view=AgesConfigView(), ephemeral=True)

    @discord.ui.button(label="Cargos Registro", style=discord.ButtonStyle.success, emoji="➕", custom_id="btn_add_reg")
    async def btn_add_reg(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.verificar_permissao(interaction):
            await interaction.response.send_message("Selecione o cargo para ADICIONAR ao painel de registro:", view=AddRegRoleView(), ephemeral=True)

    @discord.ui.button(label="Configurar Ticket", style=discord.ButtonStyle.primary, emoji="🎫", custom_id="btn_ticket")
    async def btn_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.verificar_permissao(interaction):
            await interaction.response.send_message("⚙️ **Configuração de Tickets**\nEscolha o que deseja configurar abaixo:", view=TicketConfigView(), ephemeral=True)


# === NOVO MENU DE CONFIGURAÇÃO DE IDADES ===
class AgesConfigView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="Definir Cargo +16", style=discord.ButtonStyle.primary)
    async def btn_16(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Selecione o cargo para +16:", view=SingleRoleSelectView("role_16"), ephemeral=True)

    @discord.ui.button(label="Definir Cargo +18", style=discord.ButtonStyle.primary)
    async def btn_18(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Selecione o cargo para +18:", view=SingleRoleSelectView("role_18"), ephemeral=True)

    @discord.ui.button(label="Definir Cargo +25", style=discord.ButtonStyle.primary)
    async def btn_25(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Selecione o cargo para +25:", view=SingleRoleSelectView("role_25"), ephemeral=True)


# === MENUS DE TICKETS ===
class TicketConfigView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="Editar Nomes dos Botões", style=discord.ButtonStyle.primary, emoji="📝")
    async def btn_names(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketNamesModal())

    @discord.ui.button(label="Categoria: Denúncias", style=discord.ButtonStyle.secondary)
    async def btn_cat_denuncia(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Selecione a categoria para Denúncias:", view=ChannelSelectView("ticket_cat_denuncia", discord.ChannelType.category), ephemeral=True)

    @discord.ui.button(label="Categoria: Parcerias", style=discord.ButtonStyle.secondary)
    async def btn_cat_parceria(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Selecione a categoria para Parcerias:", view=ChannelSelectView("ticket_cat_parceria", discord.ChannelType.category), ephemeral=True)

    @discord.ui.button(label="Categoria: Compras", style=discord.ButtonStyle.secondary)
    async def btn_cat_compra(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Selecione a categoria para Compras:", view=ChannelSelectView("ticket_cat_compra", discord.ChannelType.category), ephemeral=True)

    @discord.ui.button(label="Categoria: Dúvidas", style=discord.ButtonStyle.secondary)
    async def btn_cat_duvida(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Selecione a categoria para Dúvidas:", view=ChannelSelectView("ticket_cat_duvida", discord.ChannelType.category), ephemeral=True)

class TicketNamesModal(discord.ui.Modal, title="Nomes dos Botões de Ticket"):
    def __init__(self):
        super().__init__()
        data = load_data()
        
        self.denuncia = discord.ui.TextInput(label="Botão 1 (Denúncias)", default=data.get("ticket_name_denuncia"))
        self.parceria = discord.ui.TextInput(label="Botão 2 (Parcerias)", default=data.get("ticket_name_parceria"))
        self.compra = discord.ui.TextInput(label="Botão 3 (Compras)", default=data.get("ticket_name_compra"))
        self.duvida = discord.ui.TextInput(label="Botão 4 (Dúvidas)", default=data.get("ticket_name_duvida"))
        
        self.add_item(self.denuncia)
        self.add_item(self.parceria)
        self.add_item(self.compra)
        self.add_item(self.duvida)

    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()
        data["ticket_name_denuncia"] = self.denuncia.value
        data["ticket_name_parceria"] = self.parceria.value
        data["ticket_name_compra"] = self.compra.value
        data["ticket_name_duvida"] = self.duvida.value
        save_data(data)
        await interaction.response.send_message("✅ Nomes dos botões salvos! (Apague o painel de ticket antigo e envie /painelticket novamente para atualizar os nomes)", ephemeral=True)


# === VIEWS SECUNDÁRIAS GERAIS ===
class SingleRoleSelectView(discord.ui.View):
    def __init__(self, config_key):
        super().__init__(timeout=120)
        self.config_key = config_key

    @discord.ui.select(cls=discord.ui.RoleSelect, placeholder="Escolha o cargo aqui...")
    async def callback(self, interaction: discord.Interaction, select: discord.ui.RoleSelect):
        data = load_data()
        data[self.config_key] = select.values[0].id
        save_data(data)
        await interaction.response.edit_message(content=f"✅ Configuração salva: {select.values[0].mention}", view=None)

class ChannelSelectView(discord.ui.View):
    def __init__(self, config_key, channel_type=discord.ChannelType.text):
        super().__init__(timeout=120)
        self.config_key = config_key
        self.add_item(ChannelSelectComponent(config_key, channel_type))

class ChannelSelectComponent(discord.ui.ChannelSelect):
    def __init__(self, config_key, channel_type):
        super().__init__(placeholder="Escolha o canal/categoria...", channel_types=[channel_type])
        self.config_key = config_key

    async def callback(self, interaction: discord.Interaction):
        data = load_data()
        data[self.config_key] = self.values[0].id
        save_data(data)
        await interaction.response.edit_message(content=f"✅ Configuração salva: {self.values[0].mention}", view=None)

class AddRegRoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.select(cls=discord.ui.RoleSelect, placeholder="Selecione o cargo...")
    async def callback(self, interaction: discord.Interaction, select: discord.ui.RoleSelect):
        role = select.values[0]
        data = load_data()
        if role.id not in data.get("available_roles", []):
            data.setdefault("available_roles", []).append(role.id)
            save_data(data)
            await interaction.response.edit_message(content=f"✅ Cargo {role.mention} adicionado ao /painelreg!", view=None)
        else:
            await interaction.response.edit_message(content="⚠️ O cargo já está na lista de registro.", view=None)

class TextImageModal(discord.ui.Modal, title="Colar URLs das Imagens"):
    def __init__(self):
        super().__init__()
        data = load_data()
        
        self.welcome_txt = discord.ui.TextInput(label="Texto de Boas-Vindas (use {user})", style=discord.TextStyle.paragraph, default=data.get("welcome_text"), required=False)
        self.welcome_img = discord.ui.TextInput(label="Link da Imagem de Boas-Vindas", placeholder="https://exemplo.com/img.png", default=data.get("welcome_image"), required=False)
        self.admin_img = discord.ui.TextInput(label="Link da Imagem do Painel Admin", placeholder="https://exemplo.com/img.png", default=data.get("admin_image"), required=False)
        self.reg_img = discord.ui.TextInput(label="Link da Imagem do Painel Registro", placeholder="https://exemplo.com/img.png", default=data.get("reg_image"), required=False)
        self.ticket_img = discord.ui.TextInput(label="Link da Imagem do Painel Ticket", placeholder="https://exemplo.com/img.png", default=data.get("ticket_image"), required=False)
        
        self.add_item(self.welcome_txt)
        self.add_item(self.welcome_img)
        self.add_item(self.admin_img)
        self.add_item(self.reg_img)
        self.add_item(self.ticket_img)

    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()
        data["welcome_text"] = self.welcome_txt.value
        data["welcome_image"] = self.welcome_img.value
        data["admin_image"] = self.admin_img.value
        data["reg_image"] = self.reg_img.value
        data["ticket_image"] = self.ticket_img.value
        save_data(data)
        await interaction.response.send_message("✅ Textos e Imagens salvos com sucesso!", ephemeral=True)

async def setup(bot):
    bot.add_view(AdminMainView()) 
    await bot.add_cog(AdminCog(bot))
