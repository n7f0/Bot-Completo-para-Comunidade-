import discord
from discord.ext import commands
from database import load_data

class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        data = load_data()
        
        # 1. Dá o Cargo Automático (Autorole)
        autorole_id = data.get("autorole_id")
        if autorole_id:
            role = member.guild.get_role(autorole_id)
            if role:
                try:
                    await member.add_roles(role, reason="Entrou no servidor (Autorole)")
                except Exception as e:
                    print(f"Erro ao dar autorole: {e}")
        
        # 2. Envia a Mensagem de Boas-Vindas Detalhada
        welcome_channel_id = data.get("welcome_channel_id")
        if welcome_channel_id:
            channel = member.guild.get_channel(welcome_channel_id)
            if channel:
                # Substitui {user} pela menção
                text = data.get("welcome_text", "Bem-vindo {user}!").replace("{user}", member.mention)
                image_url = data.get("welcome_image", "")
                
                # Monta um perfil bonito
                embed = discord.Embed(
                    title=f"👋 Bem-vindo(a) ao {member.guild.name}!",
                    description=text,
                    color=0x2b2d31
                )
                embed.set_author(name=member.name, icon_url=member.display_avatar.url)
                embed.set_thumbnail(url=member.display_avatar.url)
                
                # Format_dt cria o formato nativo do Discord: "há 3 anos" ou a data exata
                conta_criada = discord.utils.format_dt(member.created_at, "R")
                
                embed.add_field(name="📅 Conta Criada:", value=conta_criada, inline=True)
                embed.add_field(name="👥 Membro Nº:", value=f"#{member.guild.member_count}", inline=True)
                
                if image_url:
                    embed.set_image(url=image_url)
                    
                await channel.send(content=member.mention, embed=embed)

async def setup(bot):
    await bot.add_cog(EventsCog(bot))
