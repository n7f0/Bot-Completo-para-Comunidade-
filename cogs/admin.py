import discord
from discord.ext import commands
from discord import app_commands
from database import load_data, save_data

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="paineladmin", description="Abre o painel de administração")
    async def paineladmin(self, interaction: discord.Interaction):
        data = load_data()
        admin_role_id = data.get("admin_role_id")

        # Verifica permissões: quem tem o cargo admin ou é Administrador do servidor
        if admin_role_id:
            role = interaction.guild.get_role(admin_role_id)
            if not role or role not in interaction.user.roles:
                if not interaction.user.guild_permissions.administrator:
                    await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
                    return
        else:
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
                return

        # Mostra o menu principal
        view = AdminView(interaction.user)
        embed = discord.Embed(title="🔧 Painel de Administração", description="Selecione uma opção abaixo:", color=0x00ff00)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class AdminView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=120)
        self.user = user

    @discord.ui.select(
        placeholder="Escolha uma ação...",
        options=[
            discord.SelectOption(label="👥 Definir Cargo Admin", value="set_admin"),
            discord.SelectOption(label="➕ Adicionar Cargo para Registro", value="add_role"),
            discord.SelectOption(label="➖ Remover Cargo para Registro", value="remove_role"),
            discord.SelectOption(label="📋 Ver Configurações", value="view"),
            discord.SelectOption(label="❌ Fechar", value="close")
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ Você não pode interagir com este painel.", ephemeral=True)
            return

        value = select.values[0]
        data = load_data()

        if value == "close":
            await interaction.response.edit_message(content="✅ Painel fechado.", embed=None, view=None)
            return

        elif value == "set_admin":
            # Abre o menu nativo de seleção de cargos do Discord
            view = SetAdminRoleView(self.user)
            await interaction.response.edit_message(content="Selecione abaixo o cargo que terá permissão para usar o `/paineladmin`:", embed=None, view=view)

        elif value == "add_role":
            # Abre o menu nativo de seleção de cargos do Discord para adicionar ao registro
            view = AddRoleSelectView(self.user)
            await interaction.response.edit_message(content="Selecione abaixo o cargo que os membros poderão escolher no registro:", embed=None, view=view)

        elif value == "remove_role":
            available = data.get("available_roles", [])
            if not available:
                await interaction.response.send_message("❌ Nenhum cargo registrado no sistema para remover.", ephemeral=True)
                return

            options = []
            for role_id in available:
                role = interaction.guild.get_role(role_id)
                if role:
                    options.append(discord.SelectOption(label=role.name, value=str(role_id)))

            if not options:
                await interaction.response.send_message("❌ Nenhum cargo válido para remover.", ephemeral=True)
                return

            view = RemoveRoleView(self.user, options)
            await interaction.response.edit_message(content="Selecione o cargo que deseja REMOVER do registro:", embed=None, view=view)

        elif value == "view":
            admin_role_id = data.get("admin_role_id")
            admin_role = interaction.guild.get_role(admin_role_id) if admin_role_id else None
            
            available = data.get("available_roles", [])
            roles_names = []
            for rid in available:
                r = interaction.guild.get_role(rid)
                roles_names.append(r.name if r else f"ID {rid} (não encontrado)")

            embed = discord.Embed(title="📋 Configurações Atuais", color=0x00aaff)
            embed.add_field(name="Cargo Administrador do Painel", value=admin_role.mention if admin_role else "Nenhum definido (Somente Admins do servidor)", inline=False)
            embed.add_field(name="Cargos disponíveis no Registro", value=", ".join(roles_names) if roles_names else "Nenhum cargo adicionado", inline=False)
            
            await interaction.response.edit_message(content=None, embed=embed, view=self)

# --- VIEWS SECUNDÁRIAS ---

class SetAdminRoleView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=120)
        self.user = user

    # Menu Select Nativo de Cargos (RoleSelect)
    @discord.ui.select(cls=discord.ui.RoleSelect, placeholder="Selecione o cargo admin aqui...")
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.RoleSelect):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ Apenas quem abriu o menu pode interagir.", ephemeral=True)
            return

        role = select.values[0]
        data = load_data()
        data["admin_role_id"] = role.id
        save_data(data)
        await interaction.response.edit_message(content=f"✅ O cargo {role.mention} foi definido como Admin do Bot com sucesso!", embed=None, view=None)


class AddRoleSelectView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=120)
        self.user = user

    # Menu Select Nativo de Cargos (RoleSelect)
    @discord.ui.select(cls=discord.ui.RoleSelect, placeholder="Selecione o cargo para adicionar ao registro...")
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.RoleSelect):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ Apenas quem abriu o menu pode interagir.", ephemeral=True)
            return

        role = select.values[0]
        
        # Bloqueia adicionar cargos de bot ou everyone por segurança
        if role.is_default() or role.is_integration() or role.is_bot_managed():
            await interaction.response.edit_message(content="❌ Você não pode adicionar cargos de bot, integração ou @everyone no registro.", embed=None, view=None)
            return

        data = load_data()
        if role.id in data.get("available_roles", []):
            await interaction.response.edit_message(content=f"⚠️ O cargo {role.mention} já está na lista de registro.", embed=None, view=None)
            return

        # Adiciona o ID do cargo escolhido e salva
        data.setdefault("available_roles", []).append(role.id)
        save_data(data)
        await interaction.response.edit_message(content=f"✅ O cargo {role.mention} foi **adicionado** à lista de registros para os usuários!", embed=None, view=None)


class RemoveRoleView(discord.ui.View):
    def __init__(self, user, options):
        super().__init__(timeout=120)
        self.user = user
        
        # Cria o select de remoção construindo com as opções passadas
        select = discord.ui.Select(placeholder="Selecione qual cargo remover...", options=options)
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ Apenas quem abriu o menu pode interagir.", ephemeral=True)
            return

        # Pega o valor do menu (ID em formato string)
        role_id = int(interaction.data["values"][0])
        data = load_data()
        
        if role_id in data["available_roles"]:
            data["available_roles"].remove(role_id)
            save_data(data)
            await interaction.response.edit_message(content="✅ Cargo **removido** da lista de registro com sucesso.", embed=None, view=None)
        else:
            await interaction.response.edit_message(content="❌ Este cargo não foi encontrado na lista.", embed=None, view=None)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
