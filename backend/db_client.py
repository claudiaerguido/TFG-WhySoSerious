import os
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import Optional

load_dotenv()

def get_supabase_client() -> Optional[Client]:
    """Crea y devuelve el cliente de Supabase usando variables de entorno."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("❌ Faltan credenciales de Supabase en .env")
        return None
    return create_client(url, key)
