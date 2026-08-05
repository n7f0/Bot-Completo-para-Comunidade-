import logging
from telegram.ext import Application, CommandHandler
from config import TOKEN
from handlers.admin import admin_conversation_handler
from handlers.registro import registro_conversation_handler

# Configuração de logs
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    # Cria a aplicação
    application = Application.builder().token(TOKEN).build()

    # Adiciona os handlers de conversação
    application.add_handler(admin_conversation_handler())
    application.add_handler(registro_conversation_handler())

    # Inicia o bot
    logger.info("Bot iniciado...")
    application.run_polling()

if __name__ == "__main__":
    main()
