import discord
from discord.ext import commands
from discord import app_commands
from database import load_data, save_data


class ComandosCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="painelcomandos", description="Envia o painel com todos os comandos do servidor")
    async def painelcomandos(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Apenas administradores podem enviar este painel.", ephemeral=True)
            return

        data = load_data()
        data["comandos_channel_id"] = interaction.channel_id
        save_data(data)

        view = ComandosPaginacaoView()
        embed = view.get_embed(interaction.guild)
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Painel de Comandos enviado com sucesso!", ephemeral=True)


class ComandosPaginacaoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.current_page = 0
        self.total_pages = 4

    def get_embed(self, guild):
        data = load_data()
        
        comandos_por_pagina = [
            {
                "titulo": "⚙️ Administração",
                "comandos": [
                    ("🔧 /paineladmin", "Envia o painel central de administração para configuração do servidor."),
                    ("📜 /painelregras", "Envia o painel com as regras do servidor."),
                    ("📋 /painelreg", "Envia o painel de registro para novos membros."),
                    ("🎫 /painelticket", "Envia o painel de abertura de tickets."),
                    ("🚀 /painelbooster", "Envia o painel para impulsionar o servidor."),
                    ("📋 /painelcomandos", "Envia este painel com todos os comandos disponíveis.")
                ]
            },
            {
                "titulo": "📋 Registro",
                "comandos": [
                    ("🚀 Iniciar Registro", "Botão no painel de registro - Escolha sua idade (+16, +18, +25) e cargos extras."),
                    ("✅ Registro Concluído", "Confirmação automática após o registro ser finalizado com sucesso."),
                    ("📋 Painel de Registro", "Comando para administradores enviarem o painel de registro.")
                ]
            },
            {
                "titulo": "🎫 Tickets",
                "comandos": [
                    ("🚨 Denúncias", "Abre um ticket para reportar violações das regras ou membros."),
                    ("🤝 Parcerias", "Abre um ticket para solicitar parceria com o servidor."),
                    ("🛒 Compras", "Abre um ticket para compras de benefícios VIP."),
                    ("❓ Dúvidas", "Abre um ticket para dúvidas gerais sobre o servidor."),
                    ("🔒 Fechar Ticket", "Botão disponível para staff fechar o ticket após o atendimento.")
                ]
            },
            {
                "titulo": "📊 Utilitários",
                "comandos": [
                    ("📊 Total de Membros", "Categoria que mostra o total de membros (atualizado automaticamente)."),
                    ("🔊 Pessoas em Call", "Categoria que mostra quantas pessoas estão em call (atualizado automaticamente)."),
                    ("📜 Regras do Servidor", "Painel fixo com todas as regras do servidor."),
                    ("🚀 Impulsionar Servidor", "Painel para usuários impulsionarem o servidor e ganharem benefícios."),
                    ("🔊 Bot na Call", "Botão para forçar o bot a entrar em um canal de voz (keep-alive).")
                ]
            }
        ]

        if self.current_page >= len(comandos_por_pagina):
            self.current_page = 0

        pagina = comandos_por_pagina[self.current_page]

        embed = discord.Embed(color=0xff0000)
        desc_linhas = []

        if self.current_page == 0:
            embed.title = data.get("comandos_title", "📋 Comandos · Central do Servidor")
            desc_linhas.append(data.get("comandos_description", "### 🔎 1 · Navegação\nAbaixo estão todos os comandos disponíveis no servidor.\n"))
        else:
            embed.title = f"📌 {pagina['titulo']} · Página {self.current_page + 1}"

        # Formatação do Markdown igual a da imagem (### Emoji Número · Nome)
        for i, (cmd, desc) in enumerate(pagina["comandos"], 1):
            desc_linhas.append(f"### 🔹 {i} · {cmd}\n{desc}\n")

        embed.description = "\n".join(desc_linhas)

        embed.set_footer(
            text=f"Página {self.current_page + 1}/{len(comandos_por_pagina)} • Use os botões abaixo para navegar"
        )

        if data.get("comandos_image"):
            embed.set_image(url=data.get("comandos_image"))

        return embed

    @discord.ui.button(label="◀️ Anterior", style=discord.ButtonStyle.secondary, custom_id="cmd_anterior")
    async def anterior_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
        else:
            self.current_page = self.total_pages - 1

        embed = self.get_embed(interaction.guild)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="📋 Páginas", style=discord.ButtonStyle.primary, custom_id="cmd_paginas")
    async def paginas_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        options = []
        for i in range(self.total_pages):
            options.append(
                discord.SelectOption(
                    label=f"Página {i+1}",
                    value=str(i),
                    default=(i == self.current_page)
                )
            )

        select = discord.ui.Select(
            placeholder="Selecione uma página...",
            options=options,
            custom_id="cmd_select_pagina"
        )

        async def select_callback(interaction: discord.Interaction):
            self.current_page = int(select.values[0])
            embed = self.get_embed(interaction.guild)
            await interaction.response.edit_message(embed=embed, view=self)

        select.callback = select_callback
        
        view = discord.ui.View()
        view.add_item(select)
        
        cancel_button = discord.ui.Button(
            label="Cancelar",
            style=discord.ButtonStyle.danger,
            custom_id="cmd_cancelar"
        )
        
        async def cancel_callback(interaction: discord.Interaction):
            embed = self.get_embed(interaction.guild)
            await interaction.response.edit_message(embed=embed, view=self)
        
        cancel_button.callback = cancel_callback
        view.add_item(cancel_button)

        await interaction.response.edit_message(view=view)

    @discord.ui.button(label="Próxima ▶️", style=discord.ButtonStyle.secondary, custom_id="cmd_proxima")
    async def proxima_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
        else:
            self.current_page = 0

        embed = self.get_embed(interaction.guild)
        await interaction.response.edit_message(embed=embed, view=self)


async def setup(bot):
    bot.add_view(ComandosPaginacaoView())
    await bot.add_cog(ComandosCog(bot))
