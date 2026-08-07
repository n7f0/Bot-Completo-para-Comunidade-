import discord
from discord.ext import commands
from discord import app_commands
from database import load_data
import asyncio
import io

class InstagramCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="painelinstagram", description="Envia o painel fixo do Instagram")
    async def painelinstagram(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Apenas administradores podem fixar este painel.", ephemeral=True)
            return

        data = load_data()
        channel_id = data.get("instagram_channel_id")
        
        target_channel = interaction.channel
        if channel_id:
            config_channel = interaction.guild.get_channel(channel_id)
            if config_channel:
                target_channel = config_channel

        embed = discord.Embed(
            title="📸 Instagram · Poste suas fotos!",
            description=(
                "### 📷 1 · Compartilhe Momentos\n"
                "Escolha o seu feed no botão abaixo para postar uma nova foto.\n\n"
                "### ❤️ 2 · Interaja\n"
                "Curta as fotos e deixe comentários bacanas nas publicações da galera!"
            ),
            color=0x2b2d31
        )
        
        img_url = data.get("instagram_image")
        if img_url:
            embed.set_image(url=img_url)
        
        await target_channel.send(embed=embed, view=InstagramMainView(self.bot))
        await interaction.response.send_message(f"✅ Painel do Instagram fixado com sucesso em {target_channel.mention}!", ephemeral=True)

class InstagramMainView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Postar (Homem)", style=discord.ButtonStyle.primary, emoji="👨", custom_id="btn_insta_masc")
    async def post_masc(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_data()
        role_id = data.get("instagram_role_masc")
        if role_id and not interaction.user.guild_permissions.administrator:
            role = interaction.guild.get_role(role_id)
            if not role or role not in interaction.user.roles:
                await interaction.response.send_message("❌ Você não possui o cargo necessário para postar no feed masculino.", ephemeral=True)
                return
        await interaction.response.send_modal(InstaCaptionModal(self.bot, "masc"))
        
    @discord.ui.button(label="Postar (Mulher)", style=discord.ButtonStyle.danger, emoji="👩", custom_id="btn_insta_fem")
    async def post_fem(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_data()
        role_id = data.get("instagram_role_fem")
        if role_id and not interaction.user.guild_permissions.administrator:
            role = interaction.guild.get_role(role_id)
            if not role or role not in interaction.user.roles:
                await interaction.response.send_message("❌ Você não possui o cargo necessário para postar no feed feminino.", ephemeral=True)
                return
        await interaction.response.send_modal(InstaCaptionModal(self.bot, "fem"))

    @discord.ui.button(label="Postar (Pet)", style=discord.ButtonStyle.success, emoji="🐾", custom_id="btn_insta_pet")
    async def post_pet(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Pet não exige cargo nenhum
        await interaction.response.send_modal(InstaCaptionModal(self.bot, "pet"))

class InstaCaptionModal(discord.ui.Modal, title="Legenda da Postagem"):
    def __init__(self, bot, genero):
        super().__init__()
        self.bot = bot
        self.genero = genero
        
        self.legenda = discord.ui.TextInput(
            label="Legenda",
            style=discord.TextStyle.paragraph,
            placeholder="Escreva algo sobre a foto (ou deixe em branco)...",
            required=False,
            max_length=1000
        )
        self.add_item(self.legenda)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "📸 **Quase lá!**\nAgora, **envie a sua foto aqui neste chat**.\n*(Você tem 2 minutos para enviar a imagem. Eu vou apagá-la logo em seguida!)*", 
            ephemeral=True
        )

        def check_msg(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id and len(m.attachments) > 0

        try:
            msg = await self.bot.wait_for('message', check=check_msg, timeout=120.0)
        except asyncio.TimeoutError:
            await interaction.followup.send("⏳ Tempo esgotado! Você não enviou a foto a tempo.", ephemeral=True)
            return

        attachment = msg.attachments[0]
        if not attachment.content_type or not attachment.content_type.startswith('image/'):
            await interaction.followup.send("❌ O arquivo que você enviou não é uma imagem válida!", ephemeral=True)
            return

        try:
            image_bytes = await attachment.read()
            arquivo_foto = discord.File(io.BytesIO(image_bytes), filename=attachment.filename)
        except Exception as e:
            await interaction.followup.send("❌ Erro ao processar a imagem.", ephemeral=True)
            return

        data = load_data()
        if self.genero == "masc":
            post_channel_id = data.get("instagram_post_channel_masc")
            nome_feed = "Masculino"
        elif self.genero == "fem":
            post_channel_id = data.get("instagram_post_channel_fem")
            nome_feed = "Feminino"
        else:
            post_channel_id = data.get("instagram_post_channel_pet")
            nome_feed = "de Pets"
        
        if not post_channel_id:
            await interaction.followup.send(f"❌ O canal do feed {nome_feed} não foi configurado.", ephemeral=True)
            return
            
        post_channel = interaction.guild.get_channel(post_channel_id)
        if not post_channel:
            await interaction.followup.send(f"❌ O canal do feed {nome_feed} não foi encontrado.", ephemeral=True)
            return

        embed = discord.Embed(
            description=f"{interaction.user.mention} {self.legenda.value}",
            color=0x2b2d31
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.set_image(url=f"attachment://{attachment.filename}")
        embed.set_footer(text=f"AuthorID: {interaction.user.id}")

        await post_channel.send(embed=embed, file=arquivo_foto, view=InstaPostView())
        
        try:
            await msg.delete()
        except:
            pass

        await interaction.followup.send(f"✅ Sua foto foi postada com sucesso no feed {nome_feed}!", ephemeral=True)


class InstaPostView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="0", emoji="❤️", style=discord.ButtonStyle.secondary, custom_id="insta_btn_like")
    async def like_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        current_likes = int(button.label) if button.label.isdigit() else 0
        button.label = str(current_likes + 1)
        await interaction.message.edit(view=self)
        await interaction.response.send_message("❤️ Você curtiu esta postagem!", ephemeral=True)

    @discord.ui.button(label="0", emoji="💬", style=discord.ButtonStyle.secondary, custom_id="insta_btn_comment")
    async def comment_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(InstaCommentModal(button, self, interaction.message))

    @discord.ui.button(emoji="🗑️", style=discord.ButtonStyle.danger, custom_id="insta_btn_delete")
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        footer_text = embed.footer.text if embed.footer else ""
        author_id_str = footer_text.replace("AuthorID: ", "")
        
        is_author = str(interaction.user.id) == author_id_str
        is_admin = interaction.user.guild_permissions.administrator
        
        if is_author or is_admin:
            await interaction.message.delete()
            await interaction.response.send_message("🗑️ Postagem apagada com sucesso!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Apenas o autor ou um Administrador podem apagá-la.", ephemeral=True)

class InstaCommentModal(discord.ui.Modal, title="Adicionar Comentário"):
    def __init__(self, button, view, message):
        super().__init__()
        self.button = button
        self.view_instance = view
        self.message = message
        self.comentario = discord.ui.TextInput(
            label="Seu comentário",
            style=discord.TextStyle.paragraph,
            max_length=500
        )
        self.add_item(self.comentario)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.channel.send(
            f"💬 {interaction.user.mention} comentou na foto de **{self.message.embeds[0].author.name}**:\n> {self.comentario.value}"
        )
        current_comments = int(self.button.label) if self.button.label.isdigit() else 0
        self.button.label = str(current_comments + 1)
        await self.message.edit(view=self.view_instance)
        await interaction.response.send_message("✅ Comentário enviado!", ephemeral=True)

async def setup(bot):
    bot.add_view(InstagramMainView(bot))
    bot.add_view(InstaPostView())
    await bot.add_cog(InstagramCog(bot))
