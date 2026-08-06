import discord
from discord.ext import commands
from discord import app_commands
from database import load_data

class RegrasCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="painelregras", description="Envia o painel de regras do servidor")
    async def painelregras(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Apenas admins podem enviar este painel.", ephemeral=True)
            return

        data = load_data()
        embed = discord.Embed(
            title="📜 Regras do Servidor Dex",
            description=data.get("rules_text", "Nenhuma regra definida ainda."),
            color=0xff0000
        )
        if data.get("rules_image"):
            embed.set_image(url=data.get("rules_image"))

        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("✅ Painel de Regras enviado com sucesso!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(RegrasCog(bot))
