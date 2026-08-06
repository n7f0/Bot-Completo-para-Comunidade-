import json
import os
from config import DATA_FILE

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "admin_role_id": None,
            "available_roles": [],
            "autorole_id": None,
            "welcome_channel_id": None,
            "welcome_text": "Bem-vindo ao nosso servidor, {user}! Leia as regras e divirta-se.",
            "welcome_image": "",
            "admin_image": "",
            "reg_image": "",
            "ticket_image": "",
            "rules_image": "",
            "rules_text": "Escreva suas regras aqui...",
            
            "role_16": None,
            "role_18": None,
            "role_25": None,
            
            "ticket_cat_denuncia": None,
            "ticket_cat_parceria": None,
            "ticket_cat_compra": None,
            "ticket_cat_duvida": None,
            "ticket_name_denuncia": "🚨 Denúncias",
            "ticket_name_parceria": "🤝 Parcerias",
            "ticket_name_compra": "🛒 Compras",
            "ticket_name_duvida": "❓ Dúvidas",

            "stats_cat_members": None,
            "stats_cat_voice": None,
            "stats_voice_channel": None,

            # NOVOS CAMPOS PARA BOOSTER
            "booster_title": "🚀 Impulsione o Servidor!",
            "booster_description": (
                "Ao impulsionar o servidor, você desbloqueia benefícios exclusivos:\n"
                "• 🎨 Mais slots de emojis\n"
                "• 🔊 Qualidade de áudio superior\n"
                "• 📈 Upload de arquivos maiores\n"
                "• 🏷️ Cargo especial de Booster\n\n"
                "Clique no botão abaixo para impulsionar agora!"
            ),
            "booster_image": "",
            "booster_button_label": "⭐ Impulsionar Servidor"
        }
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)