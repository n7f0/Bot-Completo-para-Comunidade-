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
            "welcome_text": (
                "### 👋 1 · Boas-Vindas\n"
                "Olá {user}, seja muito bem-vindo(a) ao nosso servidor!\n\n"
                "### 📜 2 · Regras\n"
                "Por favor, leia as regras para mantermos uma boa convivência.\n\n"
                "### 💬 3 · Interaja\n"
                "Fique à vontade para conversar, explorar os canais e fazer novas amizades!"
            ),
            "welcome_image": "",
            "admin_image": "",
            "reg_image": "",
            "ticket_image": "",
            "rules_image": "",
            "rules_text": (
                "### 🛑 1 · Respeito\n"
                "Seja respeitoso com todos os membros. Não toleramos ofensas.\n\n"
                "### 🚫 2 · Sem Spam\n"
                "Evite enviar mensagens repetidas ou links não solicitados."
            ),
            
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

            "booster_title": "🚀 Booster · Impulsione o Servidor",
            "booster_description": (
                "### ⭐ 1 · Benefícios Exclusivos\n"
                "Ao impulsionar o servidor, você desbloqueia vantagens únicas.\n\n"
                "### 🎨 2 · Mais Personalização\n"
                "Desbloqueie mais slots de emojis e um cargo especial.\n\n"
                "### 🔊 3 · Qualidade Superior\n"
                "Áudio aprimorado nas calls e maior limite de upload de arquivos.\n\n"
                "### 🚀 4 · Como Impulsionar\n"
                "Clique no botão abaixo para impulsionar agora!"
            ),
            "booster_image": "",
            "booster_button_label": "⭐ Impulsionar Servidor",

            "comandos_title": "📋 Comandos · Central do Servidor",
            "comandos_description": (
                "### 🔎 1 · Navegação\n"
                "Abaixo estão todos os comandos disponíveis no servidor.\n\n"
                "### 📑 2 · Páginas\n"
                "Use os botões abaixo para navegar entre as diferentes categorias."
            ),
            "comandos_image": "",
            "comandos_channel_id": None,

            "overview_role_id": None,
            "report_channel_id": None,
            "mute_role_id": None,
            "castigo_role_id": None,
            "overview_image": "",
            "overview_channel_id": None,

            "staff_channel_id": None,
            "staff_category_id": None,
            "staff_recruiter_role_id": None,
            "staff_image": "",

            "tellonym_channel_id": None,
            "tellonym_send_channel_id": None,
            "tellonym_image": "",

            # CONFIGURAÇÕES DO INSTAGRAM SEPARADAS POR GÊNERO
            "instagram_channel_id": None,
            "instagram_post_channel_masc": None,
            "instagram_post_channel_fem": None,
            "instagram_image": ""
        }
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
