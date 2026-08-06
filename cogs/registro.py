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
            title="📋 Sistema de Registro | Servidor Dex",
            description=(
                "Bem-vindo(a) à central de registro do **Dex**!\n\n"
                "Para ter acesso completo às categorias do servidor e interagir com nossa comunidade, "
                "é necessário informar a sua faixa etária e escolher os cargos que combinam com seu perfil.\n\n"
                "**Como se registrar:**\n"
                "**1.** Clique no botão **🚀 Iniciar Registro** abaixo.\n"
                "**2.** Selecione a sua idade (+16, +18 ou +25).\n"
                "**3.** Opcionalmente, escolha cargos adicionais como jogos que você joga ou preferências.\n\n"
                "*(Seus cargos serão atribuídos automaticamente assim que concluir!)*"
            ),
            color=0xff0000
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
        embed = discord.Embed(title="**Passo 1: Escolha sua idade**", color=0xff0000)
        view = IdadeView(interaction.user)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class IdadeView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=300)
        self.user = user

    @discord.ui.select(placeholder="Selecione sua idade...", options=[
        discord.SelectOption(label="+16", value="role_16"),
        discord.SelectOption(label="+18", value="role_18"),
        discord.SelectOption(label="+25", value="role_25")
    ])
    async def select_age(self, interaction: discord.Interaction, select: discord.ui.Select):
        data = load_data()
        age_key = select.values[0]
        age_role_id = data.get(age_key)
        age_label = [o.label for o in select.options if o.value == age_key][0]
        
        available_ids = data.get("available_roles", [])
        options = []
        for role_id in available_ids:
            role = interaction.guild.get_role(role_id)
            if role: options.append(discord.SelectOption(label=role.name, value=str(role_id)))

        if not options:
            await self.finalizar_so_idade(interaction, age_role_id, age_label)
            return

        embed = discord.Embed(
            title="**Passo 2: Escolha seus cargos extras**", 
            description=f"Sua idade será registrada como: **{age_label}**\n\n*(Marque no menu abaixo os cargos extras que deseja, ou clique no botão para pular e ficar só com a idade)*", 
            color=0xff0000
        )
        
        view = CargosView(age_role_id, age_label)
        select_menu = discord.ui.Select(placeholder="Cargos extras (opcional)...", options=options, min_values=1, max_values=min(10, len(options)))
        select_menu.callback = view.select_callback
        view.add_item(select_menu)
        await interaction.response.edit_message(embed=embed, view=view)

    async def finalizar_so_idade(self, interaction, age_role_id, age_label):
        member = interaction.user
        if age_role_id:
            role = interaction.guild.get_role(age_role_id)
            if role:
                try: await member.add_roles(role, reason="Registro de Idade")
                except: pass
        embed = discord.Embed(title="✅ Registro Concluído no Dex!", description=f"Sua idade ({age_label}) foi registrada. Bem-vindo(a)!", color=0xff0000)
        await interaction.response.edit_message(embed=embed, view=None)

class CargosView(discord.ui.View):
    def __init__(self, age_role_id, age_label):
        super().__init__(timeout=300)
        self.age_role_id = age_role_id
        self.age_label = age_label

    async def select_callback(self, interaction: discord.Interaction):
        select = [child for child in self.children if isinstance(child, discord.ui.Select)][0]
        selected_roles = [int(v) for v in select.values]

        member = interaction.user
        roles_to_add = []
        if self.age_role_id: roles_to_add.append(self.age_role_id)
        roles_to_add.extend(selected_roles)

        for role_id in roles_to_add:
            role = interaction.guild.get_role(role_id)
            if role:
                try: await member.add_roles(role)
                except: pass

        embed = discord.Embed(title="✅ Registro Concluído no Dex!", description=f"Idade: **{self.age_label}**\nTodos os cargos selecionados foram entregues com sucesso.", color=0xff0000)
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="Apenas Idade (Finalizar)", style=discord.ButtonStyle.secondary, row=1)
    async def btn_pular(self, interaction, button):
        if self.age_role_id:
            role = interaction.guild.get_role(self.age_role_id)
            if role:
                try: await interaction.user.add_roles(role)
                except: pass
        embed = discord.Embed(title="✅ Registro Concluído!", description=f"Idade: **{self.age_label}** registrada com sucesso.", color=0xff0000)
        await interaction.response.edit_message(embed=embed, view=None)

async def setup(bot):
    bot.add_view(BotaoRegistroPersistente())
    await bot.add_cog(RegistroCog(bot))