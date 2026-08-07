import discord
from discord.ext import commands
from discord import app_commands
from database import load_data

class VerifyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="painelverificar", description="Envia o painel fixo de verificação (Verifique-se)")
    async def painelverificar(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Apenas administradores podem fixar este painel.", ephemeral=True)
            return

        data = load_data()
        channel_id = data.get("verify_channel_id")
        
        target_channel = interaction.channel
        if channel_id:
            config_channel = interaction.guild.get_channel(channel_id)
            if config_channel:
                target_channel = config_channel

        embed = discord.Embed(
            title="✅ Verifique-se",
            description=(
                "A verificação garante a veracidade das postagens.\n"
                "Verifique-se para ter acesso aos canais de mídia.\n\n"
                "**__Como funciona?__**\n"
                "`01` Você terá que mostrar seu rosto para um admin;\n"
                "`02` Ninguém terá acesso às provas da sua verificação.\n\n"
                "-# Este canal é exclusivo para fotos do seu próprio rosto.\n"
                "-# Evite postar imagens de terceiros e conteúdo enganoso.\n"
                "-# O descumprimento pode resultar em remoção da verificação."
            ),
            color=0x2b2d31
        )
        
        img_url = data.get("verify_image")
        if img_url:
            embed.set_image(url=img_url)
        
        await target_channel.send(embed=embed, view=VerifyMainView())
        await interaction.response.send_message(f"✅ Painel 'Verifique-se' fixado com sucesso em {target_channel.mention}!", ephemeral=True)

class VerifyMainView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Iniciar Verificação", style=discord.ButtonStyle.success, emoji="📸", custom_id="btn_start_verify")
    async def start_verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_data()
        category_id = data.get("verify_category_id")
        staff_role_id = data.get("verify_staff_role_id")
        guild = interaction.guild

        if not category_id:
            await interaction.response.send_message("❌ A categoria de verificação não foi configurada no painel admin.", ephemeral=True)
            return

        category = guild.get_channel(category_id)
        if not category or not isinstance(category, discord.CategoryChannel):
            await interaction.response.send_message("❌ A categoria de verificação não foi encontrada.", ephemeral=True)
            return

        channel_name = f"verificacao-{interaction.user.name.lower()}"
        existing_channel = discord.utils.get(category.text_channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message(f"⚠️ Você já possui um canal de verificação aberto em {existing_channel.mention}!", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }

        mention_text = interaction.user.mention
        if staff_role_id:
            role = guild.get_role(staff_role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                mention_text += f" {role.mention}"

        await interaction.response.defer(ephemeral=True)
        new_channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)

        embed = discord.Embed(
            title="📸 Sala de Verificação",
            description=f"Olá {interaction.user.mention}! Envie a foto do seu rosto neste canal para comprovar sua identidade para a staff.\n\nAssim que um administrador verificar, clique no botão abaixo.",
            color=0x2b2d31
        )

        await new_channel.send(content=mention_text, embed=embed, view=VerifyActionView())
        await interaction.followup.send(f"✅ Seu canal de verificação foi aberto em {new_channel.mention}!")

class VerifyActionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verificou?", style=discord.ButtonStyle.primary, emoji="✅", custom_id="btn_verify_done")
    async def verify_done(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_data()
        staff_role_id = data.get("verify_staff_role_id")
        
        # Verifica se quem clicou é staff/administrador
        is_admin = interaction.user.guild_permissions.administrator
        is_staff = False
        if staff_role_id:
            role = interaction.guild.get_role(staff_role_id)
            if role and role in interaction.user.roles:
                is_staff = True

        if not (is_admin or is_staff):
            await interaction.response.send_message("❌ Apenas administradores ou verificadores podem usar este botão.", ephemeral=True)
            return

        # Abre o menu select para escolher o usuário sem precisar de ID
        await interaction.response.send_message("Selecione abaixo o usuário que foi verificado:", view=VerifyUserSelectView(), ephemeral=True)

class VerifyUserSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="Selecione o membro verificado...")
    async def select_user(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        member = select.values[0]
        data = load_data()
        reward_role_id = data.get("verify_reward_role_id")
        
        if not reward_role_id:
            await interaction.response.edit_message(content="❌ O cargo de recompensa de verificação não foi configurado no painel admin.", view=None)
            return

        role = interaction.guild.get_role(reward_role_id)
        if not role:
            await interaction.response.edit_message(content="❌ O cargo de verificado não foi encontrado.", view=None)
            return

        try:
            await member.add_roles(role, reason=f"Verificado por {interaction.user.name}")
            await interaction.response.edit_message(content=f"✅ O usuário {member.mention} recebeu o cargo {role.mention} com sucesso! Este canal será deletado em 5 segundos.", view=None)
            
            await asyncio.sleep(5)
            try:
                await interaction.channel.delete()
            except:
                pass
        except Exception as e:
            await interaction.response.edit_message(content=f"❌ Erro ao dar o cargo: {e}", view=None)

async def setup(bot):
    bot.add_view(VerifyMainView())
    bot.add_view(VerifyActionView())
    await bot.add_cog(VerifyCog(bot))
