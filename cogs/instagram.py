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
        await interaction.response.send_modal(InstaCaptionModal(self.bot, "masc"))
        
    @discord.ui.button(label="Postar (Mulher)", style=discord.ButtonStyle.danger, emoji="👩", custom_id="btn_insta_fem")
    async def post_fem(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(InstaCaptionModal(self.bot, "fem"))

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
        # 1. Manda a instrução para a pessoa enviar a imagem no chat
        await interaction.response.send_message(
            "📸 **Quase lá!**\nAgora, **envie a sua foto aqui neste chat**.\n*(Você tem 2 minutos para enviar a imagem. Eu vou apagá-la logo em seguida!)*", 
            ephemeral=True
        )

        # 2. Fica aguardando a mensagem do usuário no mesmo canal contendo um anexo (foto)
        def check_msg(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id and len(m.attachments) > 0

        try:
            msg = await self.bot.wait_for('message', check=check_msg, timeout=120.0)
        except asyncio.TimeoutError:
            await interaction.followup.send("⏳ Tempo esgotado! Você não enviou a foto a tempo. Clique no botão de postar novamente.", ephemeral=True)
            return

        # 3. Verifica se o anexo é realmente uma imagem
        attachment = msg.attachments[0]
        if not attachment.content_type or not attachment.content_type.startswith('image/'):
            await interaction.followup.send("❌ O arquivo que você enviou não é uma imagem válida! Tente novamente.", ephemeral=True)
            return

        # 4. Lê os bytes da imagem para que o Discord não expire o link depois de 24h
        try:
            image_bytes = await attachment.read()
            arquivo_foto = discord.File(io.BytesIO(image_bytes), filename=attachment.filename)
        except Exception as e:
            await interaction.followup.send("❌ Houve um erro ao processar sua imagem.", ephemeral=True)
            return

        # 5. Descobre para qual canal a foto vai
        data = load_data()
        if self.genero == "masc":
            post_channel_id = data.get("instagram_post_channel_masc")
            nome_feed = "Masculino"
        else:
            post_channel_id = data.get("instagram_post_channel_fem")
            nome_feed = "Feminino"
        
        if not post_channel_id:
            await interaction.followup.send(f"❌ O canal do feed {nome_feed} não foi configurado no /paineladmin.", ephemeral=True)
            return
            
        post_channel = interaction.guild.get_channel(post_channel_id)
        if not post_channel:
            await interaction.followup.send(f"❌ O canal do feed {nome_feed} configurado não foi encontrado.", ephemeral=True)
            return

        # 6. Monta o Embed do Instagram
        embed = discord.Embed(
            description=f"{interaction.user.mention} {self.legenda.value}",
            color=0x2b2d31
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.set_image(url=f"attachment://{attachment.filename}")
        embed.set_footer(text=f"AuthorID: {interaction.user.id}")

        # 7. Posta a foto no feed e tenta apagar a mensagem original enviada no painel
        await post_channel.send(embed=embed, file=arquivo_foto, view=InstaPostView())
        
        try:
            await msg.delete()
        except discord.Forbidden:
            # Caso o bot não tenha permissão de gerenciar mensagens no chat do painel
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
            await interaction.response.send_message("❌ Apenas a pessoa que postou a foto ou um Administrador podem apagá-la.", ephemeral=True)

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
