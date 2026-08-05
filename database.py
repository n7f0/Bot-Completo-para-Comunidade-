import json
import os
from config import DATA_FILE

def load_data():
    """Carrega os dados do arquivo JSON."""
    if not os.path.exists(DATA_FILE):
        return {
            "admin_role": "Admin",        # cargo que tem acesso ao painel admin
            "available_roles": ["Membro", "VIP", "Moderador"],
            "age_options": ["+16", "+18", "+25"]  # fixo, mas pode ser alterado via código
        }
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    """Salva os dados no arquivo JSON."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)