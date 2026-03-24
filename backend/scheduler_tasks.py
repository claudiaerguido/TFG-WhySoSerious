import datetime
from auth_graph_app import list_users, list_user_chats, list_chat_messages, list_chat_members, USER_CACHE
from message_analyzer import analyze_message
from db_client import get_supabase_client
from db_repository import save_risk_metrics
from services.risk_service import get_all_teams_and_projects_with_members

TFG_FILTER = ".tfg@"
TOP_MESSAGES_PER_CHAT = 50

def find_best_project(chat_members: list, all_projects: list) -> int:
    """
    Identifica el proyecto al que pertenece un chat basándose en sus miembros.
    
    LÓGICA DE CLASIFICACIÓN (TFG):
    1. Obtenemos los participantes del chat actual.
    2. Comparamos con todos los proyectos registrados en la base de datos.
    3. Si TODOS los participantes del chat forman parte de un proyecto específico
       (es decir, el chat es un subconjunto del grupo del proyecto), 
       asumimos que la conversación pertenece a ese contexto táctico.
    4. Si no hay coincidencia, se clasifica como 'Global' (None).
    """
    if not chat_members:
        return None
    
    # Limpiamos y normalizamos los correos del chat actual
    chat_members_set = {m.lower() for m in chat_members if "@" in m}
    if not chat_members_set:
        return None

    # Buscamos en la lista de proyectos de la organización
    for project in all_projects:
        # Obtenemos los miembros que pertenecen a este proyecto específico
        project_members_set = {m.lower() for m in project.get("members", [])}
        
        # Si el chat actual está contenido dentro de los miembros de este proyecto...
        if chat_members_set.issubset(project_members_set):
            # ...entonces el mensaje se etiqueta con el ID de este proyecto (Riesgo Táctico)
            return project["id"]
    
    # Si el grupo de personas no encaja con ningún proyecto (ej. equipo completo hablando),
    # el mensaje se queda sin ID de proyecto y computa para el Riesgo Global.
    return None

def run_nightly_analysis():
    """Proceso principal de análisis de organización."""
    start_time = datetime.datetime.now()
    print(f"🌙 Iniciando análisis nocturno [{start_time}]")
    
    stats = {"users": 0, "chats": 0, "messages_analyzed": 0, "saved": 0, "errors": 0}
    
    supabase = get_supabase_client()
    if not supabase:
        print("❌ Error: No se pudo conectar con Supabase")
        return

    # 1. Cargar proyectos para el mapeo
    try:
        # Nota: get_all_teams_and_projects_with_members devuelve teams y projects.
        # Aquí solo nos interesan los proyectos tácticos para el mapeo de riesgo.
        raw_data = get_all_teams_and_projects_with_members()
        all_projects = raw_data.get("projects", [])
    except Exception as e:
        print(f"❌ Error cargando proyectos: {e}")
        return

    # 2. Obtener y filtrar usuarios .tfg
    try:
        raw_users = list_users()
        # Actualizamos caché global de emails para el mapeo de IDs de Graph
        for u in raw_users:
            uid = u.get("id")
            email = u.get("userPrincipalName") or u.get("mail")
            if uid and email:
                USER_CACHE[uid] = email.lower()
                
        tfg_users = [u for u in raw_users if TFG_FILTER in (u.get("userPrincipalName", "").lower())]
        stats["users"] = len(tfg_users)
    except Exception as e:
        print(f"❌ Error obteniendo usuarios: {e}")
        return

    print(f"👥 Procesando {stats['users']} usuarios (.tfg)")

    # 3. Escaneo de chats y análisis de mensajes
    for user in tfg_users:
        user_id = user.get("id")
        user_email = user.get("userPrincipalName")
        if not user_id or not user_email:
            continue

        # Obtención de chats del usuario
        try:
            chats = list_user_chats(user_id)
        except Exception as e:
            print(f"⚠️ Error leyendo chats de {user_email}: {e}")
            stats["errors"] += 1
            continue

        for chat in chats:
            chat_id = chat.get("id")
            if not chat_id: continue
            stats["chats"] += 1

            # Identificación de proyecto y mensajes
            try:
                members = list_chat_members(chat_id)
                project_id = find_best_project(members, all_projects)

                messages = list_chat_messages(chat_id, top=TOP_MESSAGES_PER_CHAT)
                if not messages: continue

                for msg in messages:
                    msg_id = msg.get("id")
                    created = msg.get("createdDateTime")
                    text = msg.get("text") or ""
                    sender = msg.get("sender_email")

                    if not msg_id or not created or not sender or len(text) < 3:
                        continue

                    # Análisis y persistencia
                    try:
                        stats["messages_analyzed"] += 1
                        analysis = analyze_message(text)
                        if analysis and "labels" in analysis:
                            save_risk_metrics(
                                supabase=supabase,
                                user_email=sender,
                                timestamp=created,
                                scores=analysis["labels"],
                                message_id=msg_id,
                                project_id=project_id
                            )
                            stats["saved"] += 1
                    except Exception as e:
                        print(f"⚠️ Error analizando/guardando mensaje {msg_id}: {e}")
                        stats["errors"] += 1

            except Exception as e:
                print(f"⚠️ Error procesando chat {chat_id} de {user_email}: {e}")
                stats["errors"] += 1

    duration = datetime.datetime.now() - start_time
    print(f"✅ Análisis completado en {duration.total_seconds():.1f}s")
    print(f"📊 Resumen: {stats['messages_analyzed']} analizados, {stats['saved']} guardados, {stats['errors']} errores.")

if __name__ == "__main__":
    run_nightly_analysis()