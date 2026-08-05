import discord
from discord.ext import commands
from discord import app_commands
from database import load_data

class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="painelticket", description="Envia o painel de atendimento")
    async def painelticket(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)
            return
        
        data = load_data()
        embed = discord.Embed(
            title="📩 Central de Atendimento", 
            description="Precisa de ajuda? Clique no botão abaixo para abrir um ticket privado com a nossa equipe.", 
            color=0x2b2d31
        )
        if data.get("ticket_image"):
            embed.set_image(url=data.get("ticket_image"))

        view = TicketMainView()
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Painel de Ticket fixado!", ephemeral=True)

class TicketMainView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Abrir Ticket", style=discord.ButtonStyle.primary, emoji="🎫", custom_id="btn_open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        
        # Evita spam de tickets (um por pessoa)
        channel_name = f"ticket-{interaction.user.name.lower()}"
        existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message(f"❌ Você já possui um ticket aberto: {existing_channel.mention}", ephemeral=True)
            return

        data = load_data()
        category = guild.get_channel(data.get("ticket_category_id")) if data.get("ticket_category_id") else None
        
        # Configura as permissões do canal de ticket
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True)
        }
        
        channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)

        embed = discord.Embed(
            title="🎫 Ticket de Suporte", 
            description=f"Olá {interaction.user.mention}!\n\nDescreva seu problema ou dúvida. Nossa equipe responderá em breve.\nPara encerrar o atendimento, clique em **Fechar Ticket**.", 
            color=0xffa500
        )
        view = TicketCloseView()
        await channel.send(content=f"{interaction.user.mention}", embed=embed, view=view)
        await interaction.response.send_message(f"✅ Seu ticket foi criado com sucesso: {channel.mention}", ephemeral=True)

class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Fechar Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="btn_close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("⚠️ Apenas a equipe (com permissão de gerenciar canais) pode fechar tickets.", ephemeral=True)
            return
            
        await interaction.response.send_message("🔒 O ticket será apagado em 5 segundos...", ephemeral=False)
        import asyncio
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete()
        except:
            pass

async def setup(bot):
    bot.add_view(TicketMainView())
    bot.add_view(TicketCloseView())
    await bot.add_cog(TicketCog(bot))
