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
            "ticket_category_id": None,
            "ticket_role_id": None
        }
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
