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

        # Verifica permissões
        if admin_role_id:
            role = interaction.guild.get_role(admin_role_id)
            if not role or role not in interaction.user.roles:
                await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
                return
        else:
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
                return

        # Mostra o menu
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
        # Verifica se é o mesmo usuário
        if interaction.user != self.user:
            await interaction.response.send_message("❌ Você não pode interagir com este painel.", ephemeral=True)
            return

        value = select.values[0]
        data = load_data()

        if value == "close":
            await interaction.response.edit_message(content="Painel fechado.", embed=None, view=None)
            return

        elif value == "set_admin":
            # Mostra lista de cargos para escolher
            roles = [r for r in interaction.guild.roles if r.name != "@everyone"]
            if not roles:
                await interaction.response.send_message("❌ Nenhum cargo disponível no servidor.", ephemeral=True)
                return

            # Cria um novo view com select
            view = SetAdminView(self.user)
            options = []
            for r in roles[:25]:  # Limite de 25 opções
                options.append(discord.SelectOption(label=r.name, value=str(r.id)))
            
            select_menu = discord.ui.Select(placeholder="Selecione o cargo admin...", options=options)
            view.add_item(select_menu)
            await interaction.response.edit_message(content="Escolha o cargo que terá acesso ao /paineladmin:", embed=None, view=view)

        elif value == "add_role":
            # Usa modal para entrada de texto
            modal = AddRoleModal()
            await interaction.response.send_modal(modal)

        elif value == "remove_role":
            available = data.get("available_roles", [])
            if not available:
                await interaction.response.send_message("❌ Nenhum cargo disponível para remover.", ephemeral=True)
                return

            options = []
            for role_id in available:
                role = interaction.guild.get_role(role_id)
                if role:
                    options.append(discord.SelectOption(label=role.name, value=str(role_id)))

            if not options:
                await interaction.response.send_message("❌ Nenhum cargo válido para remover.", ephemeral=True)
                return

            view = RemoveRoleView(self.user)
            select_menu = discord.ui.Select(placeholder="Selecione o cargo para remover...", options=options)
            view.add_item(select_menu)
            await interaction.response.edit_message(content="Selecione o cargo a ser removido:", embed=None, view=view)

        elif value == "view":
            admin_role_id = data.get("admin_role_id")
            admin_role = interaction.guild.get_role(admin_role_id) if admin_role_id else None
            available = data.get("available_roles", [])
            roles_names = []
            for rid in available:
                r = interaction.guild.get_role(rid)
                roles_names.append(r.name if r else f"ID {rid} (não encontrado)")

            embed = discord.Embed(title="📋 Configurações Atuais", color=0x00aaff)
            embed.add_field(name="Cargo Admin", value=admin_role.mention if admin_role else "Nenhum definido", inline=False)
            embed.add_field(name="Cargos para Registro", value=", ".join(roles_names) if roles_names else "Nenhum", inline=False)
            await interaction.response.edit_message(embed=embed, view=self)

class SetAdminView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=120)
        self.user = user

    @discord.ui.select(placeholder="Selecione o cargo admin...")
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ Você não pode interagir com este painel.", ephemeral=True)
            return

        role_id = int(select.values[0])
        data = load_data()
        data["admin_role_id"] = role_id
        save_data(data)
        role = interaction.guild.get_role(role_id)
        await interaction.response.edit_message(content=f"✅ Cargo admin definido como {role.mention}", embed=None, view=None)

class RemoveRoleView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=120)
        self.user = user

    @discord.ui.select(placeholder="Selecione o cargo para remover...")
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ Você não pode interagir com este painel.", ephemeral=True)
            return

        role_id = int(select.values[0])
        data = load_data()
        if role_id in data["available_roles"]:
            data["available_roles"].remove(role_id)
            save_data(data)
            await interaction.response.edit_message(content="✅ Cargo removido da lista de registro.", embed=None, view=None)
        else:
            await interaction.response.edit_message(content="❌ Cargo não encontrado na lista.", embed=None, view=None)

class AddRoleModal(discord.ui.Modal, title="Adicionar Cargo para Registro"):
    role_id_input = discord.ui.TextInput(
        label="ID do Cargo",
        placeholder="Cole o ID numérico do cargo aqui...",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            role_id = int(self.role_id_input.value)
        except ValueError:
            await interaction.response.send_message("❌ ID inválido. Insira apenas números.", ephemeral=True)
            return

        role = interaction.guild.get_role(role_id)
        if not role:
            await interaction.response.send_message("❌ Cargo não encontrado no servidor.", ephemeral=True)
            return

        data = load_data()
        if role_id in data.get("available_roles", []):
            await interaction.response.send_message("⚠️ Este cargo já está na lista.", ephemeral=True)
            return

        data["available_roles"].append(role_id)
        save_data(data)
        await interaction.response.send_message(f"✅ Cargo {role.mention} adicionado à lista de registro.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
