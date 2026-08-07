import discord
from discord.ext import commands
from discord import app_commands
from database import load_data
import asyncio

class StaffCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="painelstaff", description="Envia o painel fixo de Recrutamento Staff")
    async def painelstaff(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Apenas administradores podem fixar este painel.", ephemeral=True)
            return

        data = load_data()
        channel_id = data.get("staff_channel_id")
        
        target_channel = interaction.channel
        if channel_id:
            config_channel = interaction.guild.get_channel(channel_id)
            if config_channel:
                target_channel = config_channel

        embed = discord.Embed(
            title="🎓 Recrutamento · Seja da nossa Equipe!",
            description=(
                "### 📝 1 · Como Funciona\n"
                "Clique no botão abaixo para abrir um chat direto com nossos recrutadores.\n\n"
                "### 🤝 2 · Entrevista\n"
                "Após abrir o canal, aguarde a equipe te chamar para a entrevista ou análise."
            ),
            color=0x2b2d31
        )
        
        img_url = data.get("staff_image")
        if img_url:
            embed.set_image(url=img_url)
        
        await target_channel.send(embed=embed, view=StaffMainView())
        await interaction.response.send_message(f"✅ Painel fixado com sucesso em {target_channel.mention}!", ephemeral=True)

class StaffMainView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Quero ser Staff", style=discord.ButtonStyle.primary, emoji="📋", custom_id="btn_apply_staff")
    async def apply_staff(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_data()
        category_id = data.get("staff_category_id")
        recruiter_role_id = data.get("staff_recruiter_role_id")
        guild = interaction.guild

        if not category_id:
            await interaction.response.send_message("❌ A categoria de recrutamento não foi configurada pelos administradores.", ephemeral=True)
            return

        category = guild.get_channel(category_id)
        if not category or not isinstance(category, discord.CategoryChannel):
            await interaction.response.send_message("❌ A categoria configurada não foi encontrada.", ephemeral=True)
            return

        # Verifica se o usuário já tem um ticket aberto
        channel_name = f"recrutamento-{interaction.user.name.lower()}"
        existing_channel = discord.utils.get(category.text_channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message(f"⚠️ Você já tem um canal de recrutamento aberto em {existing_channel.mention}!", ephemeral=True)
            return

        # Configura as permissões
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }

        # Adiciona a permissão pro cargo de recrutador
        mention_text = interaction.user.mention
        if recruiter_role_id:
            role = guild.get_role(recruiter_role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                mention_text += f" {role.mention}"

        await interaction.response.defer(ephemeral=True)
        new_channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)

        embed = discord.Embed(
            title="🎓 Central de Recrutamento",
            description=f"Olá {interaction.user.mention}! Um recrutador já vai te atender.\nPor favor, aguarde as instruções ou diga por que você quer entrar para a equipe.",
            color=0x2b2d31
        )
        
        await new_channel.send(content=mention_text, embed=embed, view=StaffTicketView())
        await interaction.followup.send(f"✅ Seu canal de recrutamento foi criado em {new_channel.mention}!")

class StaffTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fechar Canal", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="btn_close_staff_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⚠️ O canal será fechado e deletado em **5 segundos**...")
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete()
        except:
            pass

async def setup(bot):
    bot.add_view(StaffMainView())
    bot.add_view(StaffTicketView())
    await bot.add_cog(StaffCog(bot))
