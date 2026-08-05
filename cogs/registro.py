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
        super().__init__(timeout=120)
        self.user = user

    @discord.ui.select(placeholder="Selecione sua idade...", options=[
        discord.SelectOption(label="+16", value="role_16"),
        discord.SelectOption(label="+18", value="role_18"),
        discord.SelectOption(label="+25", value="role_25")
    ])
    async def select_age(self, interaction: discord.Interaction, select: discord.ui.Select):
        data = load_data()
        
        # Pega a key selecionada (role_16, role_18 ou role_25) e busca o ID configurado
        age_key = select.values[0]
        age_role_id = data.get(age_key)
        
        # Pega o texto da label (ex: "+18") para exibir na mensagem
        age_label = [o.label for o in select.options if o.value == age_key][0]
        
        # Carrega os cargos adicionais
        available_ids = data.get("available_roles", [])
        options = []
        for role_id in available_ids:
            role = interaction.guild.get_role(role_id)
            if role:
                options.append(discord.SelectOption(label=role.name, value=str(role_id)))

        if not options:
            # Se não houver cargos extras configurados, ele já entrega a idade e encerra
            await self.finalizar_so_idade(interaction, age_role_id, age_label)
            return

        embed = discord.Embed(
            title="**Passo 2: Escolha seus cargos extras**", 
            description=f"Sua idade será registrada como: **{age_label}**\n\n*(Selecione os cargos desejados abaixo. Você pode marcar várias opções antes de confirmar, ou clicar no botão para finalizar apenas com a idade)*", 
            color=0xff0000
        )
        
        view = CargosView(age_role_id, age_label)
        # Menu select configurado para permitir até 10 escolhas
        select_menu = discord.ui.Select(placeholder="Selecione os cargos (opcional)...", options=options, min_values=1, max_values=min(10, len(options)))
        select_menu.callback = view.select_callback
        view.add_item(select_menu)
        
        await interaction.response.edit_message(embed=embed, view=view)

    async def finalizar_so_idade(self, interaction: discord.Interaction, age_role_id, age_label):
        member = interaction.user
        guild = interaction.guild
        if age_role_id:
            role = guild.get_role(age_role_id)
            if role:
                try: await member.add_roles(role, reason="Registro de Idade")
                except: pass
                
        embed = discord.Embed(title="✅ Registro Concluído!", description=f"Sua idade ({age_label}) foi registrada com sucesso.", color=0xff0000)
        await interaction.response.edit_message(embed=embed, view=None)

class CargosView(discord.ui.View):
    def __init__(self, age_role_id, age_label):
        super().__init__(timeout=120)
        self.age_role_id = age_role_id
        self.age_label = age_label

    async def select_callback(self, interaction: discord.Interaction):
        # Acha o select dentro da view e pega todos os cargos que a pessoa marcou
        select = [child for child in self.children if isinstance(child, discord.ui.Select)][0]
        selected_roles = [int(v) for v in select.values]

        member = interaction.user
        guild = interaction.guild
        
        # Junta a idade com os cargos selecionados
        roles_to_add = []
        if self.age_role_id:
            roles_to_add.append(self.age_role_id)
        roles_to_add.extend(selected_roles)

        for role_id in roles_to_add:
            role = guild.get_role(role_id)
            if role:
                try: await member.add_roles(role, reason="Registro via bot")
                except: pass

        embed = discord.Embed(title="✅ Registro Concluído!", description=f"Idade: **{self.age_label}**\nTodos os cargos selecionados foram entregues com sucesso.", color=0xff0000)
        await interaction.response.edit_message(embed=embed, view=None)

    # Caso a pessoa não queira escolher nada no menu
    @discord.ui.button(label="Apenas Idade (Finalizar)", style=discord.ButtonStyle.secondary, row=1)
    async def btn_pular(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user
        guild = interaction.guild
        
        if self.age_role_id:
            role = guild.get_role(self.age_role_id)
            if role:
                try: await member.add_roles(role, reason="Registro de Idade")
                except: pass
                
        embed = discord.Embed(title="✅ Registro Concluído!", description=f"Idade: **{self.age_label}** registrada com sucesso.", color=0xff0000)
        await interaction.response.edit_message(embed=embed, view=None)

async def setup(bot):
    bot.add_view(BotaoRegistroPersistente())
    await bot.add_cog(RegistroCog(bot))
