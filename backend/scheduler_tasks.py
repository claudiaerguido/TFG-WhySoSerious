# nightly_job.py
from auth_graph_app import list_users, list_user_chats, list_chat_messages, list_chat_members
from message_analyzer import analyze_message
from db_client import get_supabase_client
from db_repository import save_risk_metrics
from services.risk_service import get_all_workspaces_with_members
import datetime
import re

TFG_FILTER = ".tfg@"
TOP_MESSAGES_PER_CHAT = 50

def clean_text(s: str) -> str:
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def get_text(msg: dict) -> str:
    # list_chat_messages ya devuelve el texto limpio en 'text'
    return msg.get("text") or ""

def find_best_project(chat_members: list, all_projects: list) -> int:
    """
    Busca el mejor proyecto para un conjunto de miembros de chat.
    Prioriza el proyecto que contiene a TODOS los miembros del chat.
    """
    if not chat_members:
        return None
    
    # Normalizar miembros del chat
    chat_members_set = {m.lower() for m in chat_members if "@" in m}
    if not chat_members_set:
        return None

    for prj in all_projects:
        prj_members_set = {m.lower() for m in prj.get("members", [])}
        # Si el chat es un subconjunto de los miembros del proyecto, lo vinculamos
        if chat_members_set.issubset(prj_members_set):
            return prj["id"]
    
    return None

def run_nightly_analysis():
    print(f"🌙 Nightly analysis [{datetime.datetime.now()}]")
    supabase = get_supabase_client()
    if not supabase: return

    # 1. Cachear Proyectos oficiales
    all_workspaces = get_all_workspaces_with_members()
    all_projects = all_workspaces.get("projects", [])
    
    print(f"🏢 Proyectos cargados para mapeo: {len(all_projects)}")

    # 2. Obtener usuarios a escanear y poblar caché
    try:
        raw_users = list_users()
        # Poblar caché de emails para evitar miles de llamadas individuales
        from auth_graph_app import USER_CACHE
        for u in raw_users:
            uid = u.get("id")
            email = u.get("userPrincipalName") or u.get("mail")
            if uid and email:
                USER_CACHE[uid] = email.lower()
                
        users = [u for u in raw_users if TFG_FILTER in (u.get("userPrincipalName","").lower())]
    except Exception as e:
        print(f"❌ Error listando usuarios: {e}")
        return

    print(f"👥 Usuarios a escanear: {len(users)}")

    for u in users:
        user_id = u.get("id")
        user_email = u.get("userPrincipalName")
        if not user_id or not user_email:
            continue

        print(f"🔍 Escaneando {user_email}...")

        try:
            chats = list_user_chats(user_id)
        except Exception as e:
            print(f"⚠️ Chats error {user_email}: {e}")
            continue

        for chat in chats:
            chat_id = chat.get("id")
            if not chat_id:
                continue

            # Obtener miembros del chat para saber si es de un proyecto
            chat_members = list_chat_members(chat_id)
            
            # Buscamos SOLO en proyectos reales
            project_id = find_best_project(chat_members, all_projects)
            
            # Si no coincide con ningún proyecto táctico, project_id = None
            # Esto significa que el riesgo cuenta para el Global del empleado, pero no para un proyecto.

            try:
                messages = list_chat_messages(chat_id, top=TOP_MESSAGES_PER_CHAT)
            except Exception as e:
                print(f"⚠️ Messages error chat {chat_id}: {e}")
                continue

            if not messages:
                continue

            # Ordenar por fecha (opcional pero ayuda al debug)
            messages = sorted(messages, key=lambda m: m.get("createdDateTime") or "")
            print(f"  💬 Chat {chat_id}: {len(messages)} mensajes. Proyecto: {project_id}")

            for m in messages:
                message_id = m.get("id")
                created = m.get("createdDateTime")
                text = m.get("text") or ""
                # ¡IMPORTANTE! Usar el remitente real, no la persona escaneada
                sender_email = m.get("sender_email")

                if not message_id or not created or not sender_email or len(text) < 3:
                    continue

                try:
                    analysis = analyze_message(text)
                    if not analysis:
                        continue

                    save_risk_metrics(
                        supabase=supabase,
                        user_email=sender_email,
                        timestamp=created,
                        scores=analysis["labels"],  
                        message_id=message_id,
                        project_id=project_id
                    )
                except Exception as e:
                    print(f"⚠️ Save/analyze error: {e}")

    print(f"✅ Done [{datetime.datetime.now()}]")

if __name__ == "__main__":
    run_nightly_analysis()