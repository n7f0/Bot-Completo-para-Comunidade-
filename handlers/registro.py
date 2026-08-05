import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler

from database import load_data

# Estados da conversa de registro
REG_SELECT_AGE, REG_SELECT_ROLES, REG_FINISH = range(3)

logger = logging.getLogger(__name__)

# Dicionário para armazenar seleções temporárias (em produção, use cache ou banco)
user_selections = {}

async def registro_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia o painel de registro."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Verifica se o bot é admin no grupo (para atribuir cargos)
    try:
        bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
        if not (bot_member.status in ["administrator", "creator"]):
            await update.message.reply_text("⚠️ O bot não é administrador neste grupo. Peça a um admin para me promover.")
            return ConversationHandler.END
    except Exception as e:
        logger.error(f"Erro ao verificar permissões do bot: {e}")
        await update.message.reply_text("Erro ao verificar permissões.")
        return ConversationHandler.END

    # Inicializa seleções do usuário
    user_selections[user_id] = {"age": None, "roles": []}

    keyboard = [[InlineKeyboardButton("🚀 Iniciar Registro", callback_data="reg_begin")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📋 **Painel de Registro**\nClique no botão abaixo para começar.",
        reply_markup=reply_markup
    )
    return REG_SELECT_AGE

async def reg_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa os callbacks do registro."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = load_data()
    age_options = data.get("age_options", ["+16", "+18", "+25"])
    available_roles = data.get("available_roles", [])

    if query.data == "reg_begin":
        # Mostra opções de idade
        keyboard = []
        for age in age_options:
            keyboard.append([InlineKeyboardButton(age, callback_data=f"age_{age}")])
        keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="reg_cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "**Passo 1: Escolha sua idade**\nSelecione uma opção:",
            reply_markup=reply_markup
        )
        return REG_SELECT_AGE

    elif query.data.startswith("age_"):
        age = query.data.replace("age_", "")
        user_selections[user_id]["age"] = age

        # Passo 2: escolher cargos (seleção múltipla com checkboxes)
        if not available_roles:
            await query.edit_message_text("❌ Nenhum cargo disponível para seleção. Contate o administrador.")
            return ConversationHandler.END

        keyboard = []
        for role in available_roles:
            # Verifica se já foi selecionado
            checked = "✅ " if role in user_selections[user_id]["roles"] else ""
            keyboard.append([InlineKeyboardButton(f"{checked}{role}", callback_data=f"role_{role}")])
        keyboard.append([InlineKeyboardButton("✔️ Finalizar Registro", callback_data="reg_finish")])
        keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="reg_cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"**Passo 2: Escolha seus cargos** (clique para marcar/desmarcar)\nIdade selecionada: {age}\n",
            reply_markup=reply_markup
        )
        return REG_SELECT_ROLES

    elif query.data.startswith("role_"):
        role = query.data.replace("role_", "")
        # Alterna seleção
        if role in user_selections[user_id]["roles"]:
            user_selections[user_id]["roles"].remove(role)
        else:
            user_selections[user_id]["roles"].append(role)

        # Atualiza a mensagem com os novos checkboxes
        keyboard = []
        for r in available_roles:
            checked = "✅ " if r in user_selections[user_id]["roles"] else ""
            keyboard.append([InlineKeyboardButton(f"{checked}{r}", callback_data=f"role_{r}")])
        keyboard.append([InlineKeyboardButton("✔️ Finalizar Registro", callback_data="reg_finish")])
        keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="reg_cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"**Passo 2: Escolha seus cargos**\nIdade selecionada: {user_selections[user_id]['age']}\n",
            reply_markup=reply_markup
        )
        return REG_SELECT_ROLES

    elif query.data == "reg_finish":
        # Finaliza registro
        age = user_selections[user_id].get("age")
        roles = user_selections[user_id].get("roles", [])
        if not age:
            await query.edit_message_text("❌ Você precisa selecionar uma idade primeiro.")
            return REG_SELECT_AGE
        if not roles:
            await query.edit_message_text("❌ Você precisa selecionar pelo menos um cargo.")
            return REG_SELECT_ROLES

        # Atribui os cargos ao usuário no grupo
        chat_id = query.message.chat.id
        user_id = query.from_user.id
        try:
            # Atribui cada cargo (custom title) - requer que o bot seja admin com permissão para gerenciar títulos
            for role in roles:
                await context.bot.set_chat_administrator_custom_title(
                    chat_id=chat_id,
                    user_id=user_id,
                    custom_title=role
                )
            # Mensagem de sucesso
            await query.edit_message_text(
                f"✅ **Registro concluído!**\n"
                f"Idade: {age}\n"
                f"Cargos atribuídos: {', '.join(roles)}"
            )
        except Exception as e:
            logger.error(f"Erro ao atribuir cargos: {e}")
            await query.edit_message_text(
                "❌ Erro ao atribuir cargos. Verifique se o bot tem permissões suficientes.\n"
                "O bot precisa poder gerenciar títulos de administradores (set_chat_administrator_custom_title)."
            )

        # Limpa seleção do usuário
        if user_id in user_selections:
            del user_selections[user_id]
        return ConversationHandler.END

    elif query.data == "reg_cancel":
        if user_id in user_selections:
            del user_selections[user_id]
        await query.edit_message_text("Registro cancelado.")
        return ConversationHandler.END

    return REG_SELECT_AGE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operação cancelada.")
    return ConversationHandler.END

def registro_conversation_handler():
    """Retorna o ConversationHandler para o registro."""
    return ConversationHandler(
        entry_points=[CommandHandler("painelreg", registro_start)],
        states={
            REG_SELECT_AGE: [CallbackQueryHandler(reg_callback)],
            REG_SELECT_ROLES: [CallbackQueryHandler(reg_callback)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
  )
