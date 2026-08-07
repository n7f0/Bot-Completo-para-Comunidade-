import discord
from discord.ext import commands
from discord import app_commands
from database import load_data
import asyncio

class ConselhoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="painelconselho", description="Envia o painel fixo de conselhos e ajuda")
    async def painelconselho(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Apenas administradores podem fixar este painel.", ephemeral=True)
            return

        data = load_data()
        channel_id = data.get("conselho_channel_id")
        
        target_channel = interaction.channel
        if channel_id:
            config_channel = interaction.guild.get_channel(channel_id)
            if config_channel:
                target_channel = config_channel

        embed = discord.Embed(
            title="💡 Sala de Conselho & Ajuda",
            description=(
                "Precisa de um conselho, desabafo ou ajuda com alguma situação?\n\n"
                "### 🤝 Como funciona?\n"
                "Clique no botão abaixo para abrir um chat privado e sigiloso com nossa equipe de apoio."
            ),
            color=0x2b2d31
        )
        
        img_url = data.get("conselho_image")
        if img_url:
            embed.set_image(url=img_url)
        
        await target_channel.send(embed=embed, view=ConselhoMainView())
        await interaction.response.send_message(f"✅ Painel de Conselho fixado com sucesso em {target_channel.mention}!", ephemeral=True)

class ConselhoMainView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Pedir Conselho", style=discord.ButtonStyle.primary, emoji="💡", custom_id="btn_start_conselho")
    async def start_conselho(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_data()
        category_id = data.get("conselho_category_id")
        role_id = data.get("conselho_role_id")
        guild = interaction.guild

        if not category_id:
            await interaction.response.send_message("❌ A categoria para os canais de conselho não foi configurada no painel admin.", ephemeral=True)
            return

        category = guild.get_channel(category_id)
        if not category or not isinstance(category, discord.CategoryChannel):
            await interaction.response.send_message("❌ A categoria configurada não foi encontrada.", ephemeral=True)
            return

        channel_name = f"conselho-{interaction.user.name.lower()}"
        existing_channel = discord.utils.get(category.text_channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message(f"⚠️ Você já tem um canal de conselho aberto em {existing_channel.mention}!", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }

        mention_text = interaction.user.mention
        if role_id:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                mention_text += f" {role.mention}"

        await interaction.response.defer(ephemeral=True)
        new_channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)

        embed = discord.Embed(
            title="💡 Canal de Apoio e Conselhos",
            description=f"Olá {interaction.user.mention}! Um responsável já vai te atender.\nFique à vontade para relatar o que está acontecendo.",
            color=0x2b2d31
        )

        # Salvamos o ID do autor no canal para permitir que ele feche
        await new_channel.send(content=mention_text, embed=embed, view=ConselhoCloseView(interaction.user.id))
        await interaction.followup.send(f"✅ Seu canal de atendimento foi aberto em {new_channel.mention}!")

class ConselhoCloseView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=None)
        self.author_id = author_id

    @discord.ui.button(label="Fechar Canal", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="btn_close_conselho")
    async def close_conselho(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_data()
        role_id = data.get("conselho_role_id")
        
        is_author = interaction.user.id == self.author_id
        is_admin = interaction.user.guild_permissions.administrator
        is_responsible = False
        
        if role_id:
            role = interaction.guild.get_role(role_id)
            if role and role in interaction.user.roles:
                is_responsible = True

        if is_author or is_admin or is_responsible:
            await interaction.response.send_message("⚠️ O canal será fechado e deletado em **5 segundos**...")
            await asyncio.sleep(5)
            try:
                await interaction.channel.delete()
            except:
                pass
        else:
            await interaction.response.send_message("❌ Apenas quem abriu o atendimento, os responsáveis ou um Administrador podem fechar este canal.", ephemeral=True)

async def setup(bot):
    bot.add_view(ConselhoMainView())
    # Como o ConselhoCloseView recebe argumento dinâmico (author_id), registramos sem ID fixo se necessário ou adicionamos a view padrão
    await bot.add_cog(ConselhoCog(bot))
