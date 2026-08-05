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
            description="Selecione abaixo o departamento com o qual deseja falar.", 
            color=0xff0000
        )
        if data.get("ticket_image"):
            embed.set_image(url=data.get("ticket_image"))

        view = TicketMainView()
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Painel de Ticket fixado!", ephemeral=True)


class TicketMainView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        data = load_data()
        # Atualiza os nomes dos botões com base no que você configurar no Admin
        self.btn_denuncia.label = data.get("ticket_name_denuncia", "🚨 Denúncias")
        self.btn_parceria.label = data.get("ticket_name_parceria", "🤝 Parcerias")
        self.btn_compra.label = data.get("ticket_name_compra", "🛒 Compras")
        self.btn_duvida.label = data.get("ticket_name_duvida", "❓ Dúvidas")

    async def criar_canal(self, interaction: discord.Interaction, ticket_type: str, label: str):
        guild = interaction.guild
        user = interaction.user
        
        # Cria o nome do canal (ex: ticket-denuncia-joao)
        channel_name = f"ticket-{ticket_type}-{user.name.lower()}"
        existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message(f"❌ Você já possui um ticket deste departamento aberto: {existing_channel.mention}", ephemeral=True)
            return

        data = load_data()
        cat_id = data.get(f"ticket_cat_{ticket_type}")
        category = guild.get_channel(cat_id) if cat_id else None
        
        # Permissões: Ninguém vê, apenas o usuário e a equipe (cargos com adm)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True)
        }
        
        channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)

        embed = discord.Embed(
            title=label, 
            description=f"Olá {user.mention}!\n\nVocê abriu um ticket para **{label}**.\nDescreva seu assunto e nossa equipe responderá em breve.\n\nPara encerrar, clique em **Fechar Ticket**.", 
            color=0xff0000
        )
        view = TicketCloseView()
        await channel.send(content=f"{user.mention}", embed=embed, view=view)
        await interaction.response.send_message(f"✅ Seu ticket foi criado com sucesso: {channel.mention}", ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.danger, custom_id="btn_tkt_denuncia")
    async def btn_denuncia(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.criar_canal(interaction, "denuncia", button.label)

    @discord.ui.button(style=discord.ButtonStyle.success, custom_id="btn_tkt_parceria")
    async def btn_parceria(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.criar_canal(interaction, "parceria", button.label)

    @discord.ui.button(style=discord.ButtonStyle.primary, custom_id="btn_tkt_compra")
    async def btn_compra(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.criar_canal(interaction, "compra", button.label)

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="btn_tkt_duvida")
    async def btn_duvida(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.criar_canal(interaction, "duvida", button.label)


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
