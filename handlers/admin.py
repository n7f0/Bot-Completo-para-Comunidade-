import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler

from database import load_data, save_data
from config import ADMIN_CHAT_ID

# Estados da conversa do admin
ADMIN_SELECT_ACTION, ADMIN_SET_ROLE, ADMIN_ADD_ROLE, ADMIN_REMOVE_ROLE = range(4)

logger = logging.getLogger(__name__)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entrada do painel admin - verifica chat e cargo."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Verifica se é o chat fixo
    if chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("Este comando só pode ser usado no chat administrativo.")
        return ConversationHandler.END

    # Verifica se o usuário tem o cargo de admin
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        user_role = member.custom_title or ""  # cargo atribuído ao usuário
        data = load_data()
        admin_role = data.get("admin_role", "Admin")
        if user_role != admin_role:
            await update.message.reply_text("Você não tem permissão para acessar este painel.")
            return ConversationHandler.END
    except Exception as e:
        logger.error(f"Erro ao verificar cargo: {e}")
        await update.message.reply_text("Erro ao verificar permissões. Tente novamente.")
        return ConversationHandler.END

    # Mostra menu principal
    keyboard = [
        [InlineKeyboardButton("👥 Definir Cargo Admin", callback_data="admin_set_role")],
        [InlineKeyboardButton("➕ Adicionar Cargo para Registro", callback_data="admin_add_role")],
        [InlineKeyboardButton("➖ Remover Cargo para Registro", callback_data="admin_remove_role")],
        [InlineKeyboardButton("📋 Ver Configurações", callback_data="admin_view")],
        [InlineKeyboardButton("❌ Fechar", callback_data="admin_close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔧 **Painel de Administração**\nEscolha uma opção:", reply_markup=reply_markup)
    return ADMIN_SELECT_ACTION

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa os callbacks do painel admin."""
    query = update.callback_query
    await query.answer()
    data = load_data()

    if query.data == "admin_close":
        await query.edit_message_text("Painel fechado.")
        return ConversationHandler.END

    elif query.data == "admin_set_role":
        await query.edit_message_text(
            "Digite o **nome exato** do cargo (custom title) que terá acesso ao painel admin.\n"
            "Exemplo: `SuperAdmin`\n\nDigite /cancel para cancelar."
        )
        return ADMIN_SET_ROLE

    elif query.data == "admin_add_role":
        await query.edit_message_text(
            "Digite o nome do **novo cargo** que ficará disponível para registro.\n"
            "Exemplo: `Especialista`\n\nDigite /cancel para cancelar."
        )
        return ADMIN_ADD_ROLE

    elif query.data == "admin_remove_role":
        # Mostra lista de cargos para remover
        roles = data.get("available_roles", [])
        if not roles:
            await query.edit_message_text("Nenhum cargo disponível para remover.")
            return ADMIN_SELECT_ACTION
        keyboard = []
        for role in roles:
            keyboard.append([InlineKeyboardButton(f"❌ {role}", callback_data=f"remover_{role}")])
        keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="admin_back")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Selecione o cargo que deseja remover:", reply_markup=reply_markup)
        return ADMIN_REMOVE_ROLE

    elif query.data == "admin_view":
        admin_role = data.get("admin_role", "Admin")
        roles = data.get("available_roles", [])
        msg = f"**Configurações Atuais**\n"
        msg += f"👑 Cargo Admin: `{admin_role}`\n"
        msg += f"📋 Cargos disponíveis: {', '.join(roles) if roles else 'Nenhum'}"
        await query.edit_message_text(msg)
        return ADMIN_SELECT_ACTION

    elif query.data == "admin_back":
        # Volta ao menu principal
        keyboard = [
            [InlineKeyboardButton("👥 Definir Cargo Admin", callback_data="admin_set_role")],
            [InlineKeyboardButton("➕ Adicionar Cargo para Registro", callback_data="admin_add_role")],
            [InlineKeyboardButton("➖ Remover Cargo para Registro", callback_data="admin_remove_role")],
            [InlineKeyboardButton("📋 Ver Configurações", callback_data="admin_view")],
            [InlineKeyboardButton("❌ Fechar", callback_data="admin_close")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🔧 **Painel de Administração**\nEscolha uma opção:", reply_markup=reply_markup)
        return ADMIN_SELECT_ACTION

    elif query.data.startswith("remover_"):
        role_to_remove = query.data.replace("remover_", "")
        if role_to_remove in data.get("available_roles", []):
            data["available_roles"].remove(role_to_remove)
            save_data(data)
            await query.edit_message_text(f"Cargo `{role_to_remove}` removido com sucesso!")
        else:
            await query.edit_message_text("Cargo não encontrado.")
        return ADMIN_SELECT_ACTION

    return ADMIN_SELECT_ACTION

async def admin_set_role_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe o texto para definir o cargo admin."""
    text = update.message.text.strip()
    data = load_data()
    data["admin_role"] = text
    save_data(data)
    await update.message.reply_text(f"Cargo admin atualizado para: `{text}`")
    return ConversationHandler.END

async def admin_add_role_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe o texto para adicionar novo cargo."""
    text = update.message.text.strip()
    data = load_data()
    if text not in data.get("available_roles", []):
        data["available_roles"].append(text)
        save_data(data)
        await update.message.reply_text(f"Cargo `{text}` adicionado com sucesso!")
    else:
        await update.message.reply_text("Este cargo já existe.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operação cancelada.")
    return ConversationHandler.END

def admin_conversation_handler():
    """Retorna o ConversationHandler para o painel admin."""
    return ConversationHandler(
        entry_points=[CommandHandler("paineladmin", admin_panel)],
        states={
            ADMIN_SELECT_ACTION: [CallbackQueryHandler(admin_callback)],
            ADMIN_SET_ROLE: [CommandHandler("cancel", cancel),
                             CommandHandler("paineladmin", admin_panel),  # reinicia se digitar /paineladmin
                             admin_set_role_text],
            ADMIN_ADD_ROLE: [CommandHandler("cancel", cancel),
                             CommandHandler("paineladmin", admin_panel),
                             admin_add_role_text],
            ADMIN_REMOVE_ROLE: [CallbackQueryHandler(admin_callback)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
    )
