import discord
from discord.ext import commands
from discord import app_commands
from database import load_data

class RegistroCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="painelreg", description="Envia o painel de registro")
    async def painelreg(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Apenas admins podem enviar este painel.", ephemeral=True)
            return

        data = load_data()
        embed = discord.Embed(
            title="📋 Painel de Registro",
            description="Clique no botão abaixo para iniciar seu registro em nosso servidor.",
            color=0x00ff00
        )
        if data.get("reg_image"):
            embed.set_image(url=data.get("reg_image"))

        view = BotaoRegistroPersistente()
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Painel de registro enviado!", ephemeral=True)

class BotaoRegistroPersistente(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🚀 Iniciar Registro", style=discord.ButtonStyle.primary, custom_id="btn_start_registro")
    async def iniciar(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Abre o processo de registro invisível só para o usuário
        embed = discord.Embed(title="**Passo 1: Escolha sua idade**", color=0x00aaff)
        view = IdadeView(interaction.user)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class IdadeView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=120)
        self.user = user

    @discord.ui.select(placeholder="Selecione sua idade...", options=[
        discord.SelectOption(label="+16", value="+16"),
        discord.SelectOption(label="+18", value="+18"),
        discord.SelectOption(label="+25", value="+25")
    ])
    async def select_age(self, interaction: discord.Interaction, select: discord.ui.Select):
        age = select.values[0]
        data = load_data()
        available_ids = data.get("available_roles", [])
        
        options = []
        for role_id in available_ids:
            role = interaction.guild.get_role(role_id)
            if role:
                options.append(discord.SelectOption(label=role.name, value=str(role_id)))

        if not options:
            await interaction.response.edit_message(content="❌ Nenhum cargo disponível para seleção no momento.", embed=None, view=None)
            return

        embed = discord.Embed(title="**Passo 2: Escolha seus cargos**", description=f"Idade: **{age}**", color=0x00aaff)
        view = CargosView(age)
        select_menu = discord.ui.Select(placeholder="Selecione os cargos...", options=options, max_values=min(10, len(options)))
        select_menu.callback = view.select_callback
        view.add_item(select_menu)
        await interaction.response.edit_message(embed=embed, view=view)

class CargosView(discord.ui.View):
    def __init__(self, age):
        super().__init__(timeout=120)
        self.age = age

    async def select_callback(self, interaction: discord.Interaction):
        select = self.children[0]
        selected_roles = [int(v) for v in select.values]

        member = interaction.user
        guild = interaction.guild
        for role_id in selected_roles:
            role = guild.get_role(role_id)
            if role:
                try: await member.add_roles(role, reason="Registro via bot")
                except: pass

        embed = discord.Embed(title="✅ Registro Concluído!", description="Cargos entregues com sucesso.", color=0x00ff00)
        await interaction.response.edit_message(embed=embed, view=None)

async def setup(bot):
    bot.add_view(BotaoRegistroPersistente())
    await bot.add_cog(RegistroCog(bot))
