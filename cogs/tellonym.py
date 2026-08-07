import discord
from discord.ext import commands
from discord import app_commands
from database import load_data

class TellonymCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="paineltellonym", description="Envia o painel fixo de Tellonyms (Mensagens Anônimas)")
    async def paineltellonym(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Apenas administradores podem fixar este painel.", ephemeral=True)
            return

        data = load_data()
        channel_id = data.get("tellonym_channel_id")
        
        target_channel = interaction.channel
        if channel_id:
            config_channel = interaction.guild.get_channel(channel_id)
            if config_channel:
                target_channel = config_channel

        embed = discord.Embed(
            title="👻 Tellonym · Mensagens Anônimas",
            description=(
                "### 🤫 1 · Totalmente Anônimo\n"
                "Envie uma mensagem secreta, uma confissão ou um elogio. Ninguém saberá quem foi!\n\n"
                "### ✍️ 2 · Como Enviar\n"
                "Clique no botão abaixo e digite sua mensagem. Ela será postada automaticamente."
            ),
            color=0x2b2d31
        )
        
        img_url = data.get("tellonym_image")
        if img_url:
            embed.set_image(url=img_url)
        
        await target_channel.send(embed=embed, view=TellonymMainView())
        await interaction.response.send_message(f"✅ Painel fixado com sucesso em {target_channel.mention}!", ephemeral=True)

class TellonymMainView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Enviar Tellonym", style=discord.ButtonStyle.primary, emoji="💌", custom_id="btn_send_tellonym")
    async def send_tellonym(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TellonymModal())

class TellonymModal(discord.ui.Modal, title="Escreva seu Tellonym"):
    def __init__(self):
        super().__init__()
        self.mensagem = discord.ui.TextInput(
            label="Sua mensagem (100% anônima)",
            style=discord.TextStyle.paragraph,
            placeholder="Escreva seu segredo, confissão ou elogio aqui...",
            required=True,
            max_length=2000
        )
        self.add_item(self.mensagem)

    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()
        send_channel_id = data.get("tellonym_send_channel_id")
        
        if not send_channel_id:
            await interaction.response.send_message("❌ O canal de envio de Tellonyms não foi configurado pelos administradores no /paineladmin.", ephemeral=True)
            return
        
        send_channel = interaction.guild.get_channel(send_channel_id)
        if not send_channel:
            await interaction.response.send_message("❌ O canal configurado para receber os Tellonyms não foi encontrado.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="💌 Novo Tellonym Recebido!",
            description=f"```\n{self.mensagem.value}\n```",
            color=0x2b2d31
        )
        embed.set_footer(text="Enviado anonimamente 👻")
        
        await send_channel.send(embed=embed)
        await interaction.response.send_message("✅ Seu Tellonym foi enviado anonimamente com sucesso!", ephemeral=True)

async def setup(bot):
    bot.add_view(TellonymMainView())
    await bot.add_cog(TellonymCog(bot))
