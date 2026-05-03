import os
import json
import hashlib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTH_FILE = os.path.join(BASE_DIR, "data", "users.json")

def _hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode()).hexdigest()

def _load_users() -> dict:
    if not os.path.exists(AUTH_FILE):
        return {}
    try:
        with open(AUTH_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_users(users: dict):
    os.makedirs(os.path.dirname(AUTH_FILE), exist_ok=True)
    with open(AUTH_FILE, "w") as f:
        json.dump(users, f, indent=4)

def register_user(username: str, pin: str) -> tuple[bool, str]:
    if not username or not pin:
        return False, "Username and PIN are required."
    
    users = _load_users()
    uname_lower = username.lower()
    
    if uname_lower in users:
        return False, "Username already exists."
        
    users[uname_lower] = {
        "username": username,
        "pin_hash": _hash_pin(pin)
    }
    _save_users(users)
    return True, "Registration successful."

def authenticate_user(username: str, pin: str) -> tuple[bool, str]:
    if not username or not pin:
        return False, "Username and PIN are required."
        
    users = _load_users()
    uname_lower = username.lower()
    
    if uname_lower not in users:
        return False, "Username not found."
        
    if users[uname_lower]["pin_hash"] == _hash_pin(pin):
        return True, "Authentication successful."
    else:
        return False, "Incorrect PIN."
