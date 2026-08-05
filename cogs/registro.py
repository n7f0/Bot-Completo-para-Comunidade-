import discord
from discord.ext import commands
from discord import app_commands
from database import load_data

class RegistroCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="painelreg", description="Abre o painel de registro")
    async def painelreg(self, interaction: discord.Interaction):
        data = load_data()
        available = data.get("available_roles", [])
        if not available:
            await interaction.response.send_message("❌ Nenhum cargo disponível para registro. Contate um administrador.", ephemeral=True)
            return

        if not interaction.guild.me.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ Eu não tenho permissão para gerenciar cargos.", ephemeral=True)
            return

        embed = discord.Embed(
            title="📋 Painel de Registro",
            description="Clique no botão abaixo para iniciar seu registro.",
            color=0x00ff00
        )
        view = RegistroView(interaction.user)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class RegistroView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=120)
        self.user = user
        self.age = None
        self.selected_roles = []

    @discord.ui.button(label="🚀 Iniciar Registro", style=discord.ButtonStyle.primary)
    async def iniciar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ Este painel não é seu.", ephemeral=True)
            return

        # Passo 1: escolher idade
        embed = discord.Embed(title="**Passo 1: Escolha sua idade**", color=0x00aaff)
        view = IdadeView(self.user, self)
        await interaction.response.edit_message(embed=embed, view=view)

class IdadeView(discord.ui.View):
    def __init__(self, user, parent_view):
        super().__init__(timeout=120)
        self.user = user
        self.parent = parent_view

    @discord.ui.select(
        placeholder="Selecione sua idade...",
        options=[
            discord.SelectOption(label="+16", value="+16"),
            discord.SelectOption(label="+18", value="+18"),
            discord.SelectOption(label="+25", value="+25")
        ]
    )
    async def select_age(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ Este painel não é seu.", ephemeral=True)
            return

        self.parent.age = select.values[0]

        # Passo 2: selecionar cargos
        data = load_data()
        available_ids = data.get("available_roles", [])
        options = []
        for role_id in available_ids:
            role = interaction.guild.get_role(role_id)
            if role:
                options.append(discord.SelectOption(label=role.name, value=str(role_id)))

        if not options:
            await interaction.response.send_message("❌ Nenhum cargo disponível para seleção.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"**Passo 2: Escolha seus cargos**",
            description=f"Idade selecionada: **{self.parent.age}**\nSelecione um ou mais cargos.",
            color=0x00aaff
        )
        view = CargosView(self.user, self.parent)
        select_menu = discord.ui.Select(placeholder="Selecione os cargos...", options=options, max_values=min(10, len(options)))
        view.add_item(select_menu)
        await interaction.response.edit_message(embed=embed, view=view)

class CargosView(discord.ui.View):
    def __init__(self, user, parent_view):
        super().__init__(timeout=120)
        self.user = user
        self.parent = parent_view

    @discord.ui.select(placeholder="Selecione os cargos...", max_values=10)
    async def select_roles(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ Este painel não é seu.", ephemeral=True)
            return

        self.parent.selected_roles = [int(v) for v in select.values]

        embed = discord.Embed(
            title="✔️ Finalizar Registro",
            description=f"Idade: **{self.parent.age}**\nCargos selecionados: {len(self.parent.selected_roles)}",
            color=0x00ff00
        )
        view = FinalizarView(self.user, self.parent)
        await interaction.response.edit_message(embed=embed, view=view)

class FinalizarView(discord.ui.View):
    def __init__(self, user, parent_view):
        super().__init__(timeout=120)
        self.user = user
        self.parent = parent_view

    @discord.ui.button(label="✔️ Finalizar Registro", style=discord.ButtonStyle.success)
    async def finalizar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ Este painel não é seu.", ephemeral=True)
            return

        if not self.parent.selected_roles:
            await interaction.response.send_message("❌ Você precisa selecionar pelo menos um cargo.", ephemeral=True)
            return

        # Atribui os cargos
        member = interaction.user
        guild = interaction.guild
        added = []
        failed = []

        for role_id in self.parent.selected_roles:
            role = guild.get_role(role_id)
            if role:
                try:
                    await member.add_roles(role, reason="Registro via bot")
                    added.append(role.name)
                except:
                    failed.append(role.name)
            else:
                failed.append(f"ID {role_id} (não encontrado)")

        embed = discord.Embed(title="✅ Registro Concluído!", color=0x00ff00)
        if added:
            embed.add_field(name="Cargos atribuídos", value=", ".join(added), inline=False)
        if failed:
            embed.add_field(name="⚠️ Falhas", value=", ".join(failed), inline=False)
        embed.set_footer(text=f"Idade: {self.parent.age}")

        await interaction.response.edit_message(embed=embed, view=None)

async def setup(bot):
    await bot.add_cog(RegistroCog(bot))