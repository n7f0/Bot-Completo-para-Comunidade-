import json
import os
from config import DATA_FILE

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "admin_role_id": None,          # ID do cargo que pode acessar /paineladmin
            "available_roles": [],          # IDs dos cargos que podem ser atribuídos no registro
            "age_options": ["+16", "+18", "+25"]
        }
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
