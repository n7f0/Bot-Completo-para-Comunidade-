import discord
from discord.ext import commands
from discord import app_commands
from database import load_data

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
        await interaction.response.send_modal(InstaCreateModal("masc"))
        
    @discord.ui.button(label="Postar (Mulher)", style=discord.ButtonStyle.danger, emoji="👩", custom_id="btn_insta_fem")
    async def post_fem(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(InstaCreateModal("fem"))

class InstaCreateModal(discord.ui.Modal, title="Criar Postagem"):
    def __init__(self, genero):
        super().__init__()
        self.genero = genero
        self.imagem = discord.ui.TextInput(
            label="URL da Imagem (Obrigatório)",
            placeholder="Cole o link da sua foto (ex: termina em .png, .jpg)",
            required=True
        )
        self.legenda = discord.ui.TextInput(
            label="Legenda",
            style=discord.TextStyle.paragraph,
            placeholder="Escreva algo sobre a foto...",
            required=False,
            max_length=1000
        )
        self.add_item(self.imagem)
        self.add_item(self.legenda)

    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()
        
        # Define para qual canal vai com base no botão clicado
        if self.genero == "masc":
            post_channel_id = data.get("instagram_post_channel_masc")
            nome_feed = "Masculino"
        else:
            post_channel_id = data.get("instagram_post_channel_fem")
            nome_feed = "Feminino"
        
        if not post_channel_id:
            await interaction.response.send_message(f"❌ O canal do feed {nome_feed} não foi configurado no /paineladmin.", ephemeral=True)
            return
            
        post_channel = interaction.guild.get_channel(post_channel_id)
        if not post_channel:
            await interaction.response.send_message(f"❌ O canal do feed {nome_feed} configurado não foi encontrado.", ephemeral=True)
            return

        # Monta a postagem estilo Instagram
        embed = discord.Embed(
            description=f"{interaction.user.mention} {self.legenda.value}",
            color=0x2b2d31
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.set_image(url=self.imagem.value)
        # Salva o ID do autor no rodapé para validar quem pode apagar
        embed.set_footer(text=f"AuthorID: {interaction.user.id}")

        await post_channel.send(embed=embed, view=InstaPostView())
        await interaction.response.send_message(f"✅ Sua foto foi postada com sucesso no feed {nome_feed}!", ephemeral=True)

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
        # Manda o comentário como uma mensagem normal marcando o post original
        await interaction.channel.send(
            f"💬 {interaction.user.mention} comentou na foto de **{self.message.embeds[0].author.name}**:\n> {self.comentario.value}"
        )
        
        # Atualiza o contador de comentários no botão
        current_comments = int(self.button.label) if self.button.label.isdigit() else 0
        self.button.label = str(current_comments + 1)
        await self.message.edit(view=self.view_instance)
        
        await interaction.response.send_message("✅ Comentário enviado!", ephemeral=True)

async def setup(bot):
    # Registra as Views no bot para elas não quebrarem ao reiniciar
    bot.add_view(InstagramMainView(bot))
    bot.add_view(InstaPostView())
    await bot.add_cog(InstagramCog(bot))
