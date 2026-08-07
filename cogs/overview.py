import discord
from discord.ext import commands
from discord import app_commands
from database import load_data
import asyncio

class OverviewCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="paineloverview", description="Envia o painel fixo de moderação (Overview)")
    async def paineloverview(self, interaction: discord.Interaction):
        # Apenas administradores podem disparar e fixar o painel
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Apenas administradores podem fixar este painel.", ephemeral=True)
            return

        data = load_data()
        channel_id = data.get("overview_channel_id")
        
        # Decide onde vai enviar: no canal configurado ou no canal atual
        target_channel = interaction.channel
        if channel_id:
            config_channel = interaction.guild.get_channel(channel_id)
            if config_channel:
                target_channel = config_channel

        embed = discord.Embed(
            title="🛡️ Overview · Painel de Moderação",
            description=(
                "### 🔨 1 · Escolha a Ação\n"
                "Selecione no menu abaixo a punição que deseja aplicar.\n\n"
                "### 👤 2 · Selecione o Usuário\n"
                "Você poderá procurar o usuário pelo nome, sem precisar de IDs!\n\n"
                "### 📝 3 · Relatório Automático\n"
                "Após preencher o motivo, o bot enviará uma mensagem privada ao membro e um log no canal de relatórios."
            ),
            color=0x2b2d31
        )
        
        # Adiciona a imagem se houver
        img_url = data.get("overview_image")
        if img_url:
            embed.set_image(url=img_url)
        
        await target_channel.send(embed=embed, view=OverviewMainView(self.bot))
        await interaction.response.send_message(f"✅ Painel fixado com sucesso em {target_channel.mention}!", ephemeral=True)

# ---------------- VIEWS ---------------- #

class OverviewMainView(discord.ui.View):
    # timeout=None transforma o painel em persistente (nunca expira)
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.select(
        custom_id="overview_action_select",
        placeholder="Qual ação você deseja realizar?",
        options=[
            discord.SelectOption(label="Banir Membro", value="ban", emoji="🔨", description="Bane permanentemente o usuário."),
            discord.SelectOption(label="Expulsar Membro", value="kick", emoji="👢", description="Expulsa o usuário do servidor."),
            discord.SelectOption(label="Aplicar Castigo", value="castigo", emoji="⏳", description="Aplica cargo de castigo temporário."),
            discord.SelectOption(label="Mutar Membro", value="mute", emoji="🔇", description="Aplica cargo de mute temporário.")
        ]
    )
    async def select_action(self, interaction: discord.Interaction, select: discord.ui.Select):
        # 1. VERIFICAÇÃO DE SEGURANÇA NO CLIQUE
        data = load_data()
        overview_role_id = data.get("overview_role_id")
        
        tem_permissao = interaction.user.guild_permissions.administrator
        if overview_role_id and not tem_permissao:
            role = interaction.guild.get_role(overview_role_id)
            if role and role in interaction.user.roles:
                tem_permissao = True

        if not tem_permissao:
            await interaction.response.send_message("❌ Você não tem permissão para usar o painel de moderação.", ephemeral=True)
            return

        action = select.values[0]
        acao_nome = {"ban": "Banir", "kick": "Expulsar", "castigo": "Colocar de Castigo", "mute": "Mutar"}[action]
        
        # 2. Reseta o menu visualmente no painel fixo
        select.placeholder = "Qual ação você deseja realizar?"
        await interaction.message.edit(view=self)
        
        # 3. Abre o menu efêmero (escondido) para a staff continuar o processo
        await interaction.response.send_message(
            content=f"Você escolheu: **{acao_nome}**.\nAgora, procure e selecione o usuário abaixo:",
            view=UserSelectView(self.bot, action),
            ephemeral=True
        )

class UserSelectView(discord.ui.View):
    def __init__(self, bot, action):
        super().__init__(timeout=300)
        self.bot = bot
        self.action = action

    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="Procure o usuário pelo nome...")
    async def select_user(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        user = select.values[0]
        
        if self.action in ["ban", "kick"]:
            await interaction.response.send_modal(MotivoModal(self.bot, self.action, user))
        else:
            await interaction.response.edit_message(
                content=f"Usuário selecionado: {user.mention}\nPor quanto tempo ele deve receber a punição?",
                view=TimeSelectView(self.bot, self.action, user)
            )

class TimeSelectView(discord.ui.View):
    def __init__(self, bot, action, user):
        super().__init__(timeout=300)
        self.bot = bot
        self.action = action
        self.user = user

    @discord.ui.select(
        placeholder="Selecione a duração da punição...",
        options=[
            discord.SelectOption(label="1 Minuto", value="60"),
            discord.SelectOption(label="5 Minutos", value="300"),
            discord.SelectOption(label="1 Hora", value="3600"),
            discord.SelectOption(label="1 Dia", value="86400"),
            discord.SelectOption(label="1 Mês", value="2592000"),
            discord.SelectOption(label="1 Ano", value="31536000")
        ]
    )
    async def select_time(self, interaction: discord.Interaction, select: discord.ui.Select):
        seconds = int(select.values[0])
        label = [opt.label for opt in select.options if opt.value == select.values[0]][0]
        
        await interaction.response.send_modal(MotivoModal(self.bot, self.action, self.user, label, seconds))

# ---------------- MODAL E LÓGICA ---------------- #

class MotivoModal(discord.ui.Modal):
    def __init__(self, bot, action, user: discord.Member, time_label=None, time_seconds=None):
        acoes = {"ban": "Banir", "kick": "Expulsar", "castigo": "Castigo", "mute": "Mute"}
        super().__init__(title=f"Relatório de {acoes[action]}")
        self.bot = bot
        self.action = action
        self.user = user
        self.time_label = time_label
        self.time_seconds = time_seconds

        self.motivo = discord.ui.TextInput(
            label="Motivo detalhado da punição",
            style=discord.TextStyle.paragraph,
            placeholder="Escreva aqui o que o usuário fez de errado...",
            required=True,
            max_length=1000
        )
        self.add_item(self.motivo)

    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()
        motivo = self.motivo.value
        guild = interaction.guild

        if self.user.id == interaction.user.id:
            await interaction.response.edit_message(content="❌ Você não pode punir a si mesmo!", view=None)
            return
        if self.user.top_role >= interaction.user.top_role and interaction.user.id != guild.owner_id:
            await interaction.response.edit_message(content="❌ Você não pode punir alguém com um cargo maior ou igual ao seu.", view=None)
            return

        dm_embed = discord.Embed(title="Oii! Temos um recadinho importante 💌", color=0xff69b4)
        if self.action == "ban":
            dm_embed.description = f"Puxa vida, {self.user.name}... 🥺\nInfelizmente você precisou ser **banido(a)** do nosso servidor.\n\n### 📝 Motivo\n{motivo}\n\nEsperamos que você fique bem e se cuide! 💕"
        elif self.action == "kick":
            dm_embed.description = f"Oie {self.user.name}! 😕\nVocê foi **expulso(a)** do servidor.\n\n### 📝 Motivo\n{motivo}\n\nMas não fique triste, se as coisas melhorarem, você pode voltar no futuro! ✨"
        elif self.action == "castigo":
            dm_embed.description = f"Oie {self.user.name}! 🛑\nVocê recebeu um **castiguinho** por **{self.time_label}**.\n\n### 📝 Motivo\n{motivo}\n\nAproveite esse tempinho para refletir e volte com tudo! 💕"
        elif self.action == "mute":
            dm_embed.description = f"Oie {self.user.name}! 🔇\nVocê foi **mutado(a)** por **{self.time_label}**.\n\n### 📝 Motivo\n{motivo}\n\nUse esse momento para esfriar a cabeça. Até logo! 🌸"

        try:
            await self.user.send(embed=dm_embed)
        except:
            pass 

        try:
            if self.action == "ban":
                await self.user.ban(reason=f"Banido por {interaction.user.name} - {motivo}")
                acao_feita = "banido permanentemente"
                
            elif self.action == "kick":
                await self.user.kick(reason=f"Expulso por {interaction.user.name} - {motivo}")
                acao_feita = "expulso"
                
            elif self.action in ["castigo", "mute"]:
                role_key = "castigo_role_id" if self.action == "castigo" else "mute_role_id"
                role_id = data.get(role_key)
                
                if not role_id:
                    await interaction.response.edit_message(content=f"❌ O cargo de {self.action} não foi configurado no /paineladmin!", view=None)
                    return
                
                role = guild.get_role(role_id)
                if not role:
                    await interaction.response.edit_message(content=f"❌ O cargo configurado para {self.action} não existe mais.", view=None)
                    return
                
                await self.user.add_roles(role, reason=f"Punido por {interaction.user.name} - {motivo}")
                acao_feita = f"punido ({self.action}) por {self.time_label}"

                self.bot.loop.create_task(self.remover_punicao(self.user, role, self.time_seconds))

        except discord.Forbidden:
            await interaction.response.edit_message(content="❌ O bot não tem permissão para realizar esta ação (verifique a hierarquia de cargos).", view=None)
            return

        report_channel_id = data.get("report_channel_id")
        if report_channel_id:
            channel = guild.get_channel(report_channel_id)
            if channel:
                report_embed = discord.Embed(title="🛡️ Novo Relatório de Moderação", color=0xff0000)
                report_embed.add_field(name="👮 Responsável", value=interaction.user.mention, inline=True)
                report_embed.add_field(name="👤 Infrator", value=self.user.mention, inline=True)
                report_embed.add_field(name="🔨 Ação", value=acao_feita.title(), inline=True)
                report_embed.add_field(name="📝 Motivo (Log)", value=f"```\n{motivo}\n```", inline=False)
                
                await channel.send(embed=report_embed)

        await interaction.response.edit_message(content="✅ Ação realizada com sucesso, DM fofa enviada e relatório gerado!", view=None, embed=None)

    async def remover_punicao(self, member, role, wait_time):
        await asyncio.sleep(wait_time)
        try:
            await member.remove_roles(role, reason="Fim automático do tempo de punição.")
        except:
            pass


async def setup(bot):
    # Registra a view como persistente no bot
    bot.add_view(OverviewMainView(bot))
    await bot.add_cog(OverviewCog(bot))
