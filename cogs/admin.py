import discord
from discord.ext import commands
from discord import app_commands
from database import load_data, save_data

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="paineladmin", description="Envia o painel de administração fixo no chat")
    async def paineladmin(self, interaction: discord.Interaction):
        # Verifica se é admin do servidor
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
            color=0x2b2d31
        )
        
        # Se já tiver uma imagem configurada, ele mostra no painel
        if data.get("admin_image"):
            embed.set_image(url=data.get("admin_image"))

        view = AdminMainView()
        
        # Envia a mensagem fixa no canal
        await interaction.channel.send(embed=embed, view=view)
        
        # Responde à interação para o Discord não dar "Falha"
        await interaction.response.send_message("✅ Painel fixado no chat com sucesso! Você pode apagar esta mensagem temporária.", ephemeral=True)


class AdminMainView(discord.ui.View):
    def __init__(self):
        # timeout=None é o que garante que os botões funcionem para sempre, mesmo se o bot reiniciar
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
            # ABRE A JANELA PARA COLAR AS URLs DIRETO NO DISCORD
            await interaction.response.send_modal(TextImageModal())

    @discord.ui.button(label="Cargos Registro", style=discord.ButtonStyle.success, emoji="➕", custom_id="btn_add_reg")
    async def btn_add_reg(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.verificar_permissao(interaction):
            await interaction.response.send_message("Selecione o cargo para ADICIONAR ao painel de registro:", view=AddRegRoleView(), ephemeral=True)

    @discord.ui.button(label="Configurar Ticket", style=discord.ButtonStyle.primary, emoji="🎫", custom_id="btn_ticket")
    async def btn_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.verificar_permissao(interaction):
            await interaction.response.send_message("Selecione a Categoria para criar os Tickets:", view=ChannelSelectView("ticket_category_id", channel_type=discord.ChannelType.category), ephemeral=True)


# --- Views Secundárias Invisíveis (Só quem clica vê) ---

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


# --- Janela (Modal) onde você cola as URLs dentro do próprio Discord ---
class TextImageModal(discord.ui.Modal, title="Colar URLs das Imagens"):
    def __init__(self):
        super().__init__()
        data = load_data()
        
        # Campo 1: Texto
        self.welcome_txt = discord.ui.TextInput(
            label="Texto de Boas-Vindas (use {user})", 
            style=discord.TextStyle.paragraph, 
            default=data.get("welcome_text"), 
            required=False
        )
        # Campo 2: Imagem Boas Vindas
        self.welcome_img = discord.ui.TextInput(
            label="Link da Imagem de Boas-Vindas (URL)", 
            placeholder="https://exemplo.com/imagem.png",
            default=data.get("welcome_image"), 
            required=False
        )
        # Campo 3: Imagem Admin
        self.admin_img = discord.ui.TextInput(
            label="Link da Imagem do Painel Admin (URL)", 
            placeholder="https://exemplo.com/imagem.png",
            default=data.get("admin_image"), 
            required=False
        )
        # Campo 4: Imagem Registro
        self.reg_img = discord.ui.TextInput(
            label="Link da Imagem do Painel Registro (URL)", 
            placeholder="https://exemplo.com/imagem.png",
            default=data.get("reg_image"), 
            required=False
        )
        # Campo 5: Imagem Ticket
        self.ticket_img = discord.ui.TextInput(
            label="Link da Imagem do Painel Ticket (URL)", 
            placeholder="https://exemplo.com/imagem.png",
            default=data.get("ticket_image"), 
            required=False
        )
        
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
        
        await interaction.response.send_message(
            "✅ Textos e Imagens salvos no banco de dados com sucesso!\n"
            "*(Obs: Se você alterou a imagem de um painel, apague o painel antigo no chat e digite o comando novamente para ele aparecer com a imagem nova)*", 
            ephemeral=True
        )

# O setup registra a View para os botões não pararem de funcionar quando o bot reiniciar
async def setup(bot):
    bot.add_view(AdminMainView()) 
    await bot.add_cog(AdminCog(bot))
