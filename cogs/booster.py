import discord
from discord.ext import commands
from discord import app_commands
from database import load_data

class BoosterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="painelbooster", description="Envia o painel de impulso (booster) do servidor")
    async def painelbooster(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Apenas administradores podem enviar este painel.", ephemeral=True)
            return

        data = load_data()
        guild = interaction.guild

        embed = discord.Embed(
            title=data.get("booster_title", "🚀 Impulsione o Servidor!"),
            description=data.get("booster_description", ""),
            color=0xff0000
        )
        if data.get("booster_image"):
            embed.set_image(url=data.get("booster_image"))

        boost_url = f"https://discord.com/servers/{guild.id}"
        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label=data.get("booster_button_label", "⭐ Impulsionar Servidor"),
                style=discord.ButtonStyle.link,
                url=boost_url,
                emoji="⭐"
            )
        )

                await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Painel de Booster enviado com sucesso!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(BoosterCog(bot))
