from typing import Optional
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from auth_graph_app import list_users, list_user_chats, list_chat_messages
from message_analyzer import analyze_message
from db_client import get_supabase_client
from db_repository import save_risk_metrics


def _load_workspace_membership():
    """Devuelve dict: email -> set(workspace_id) desde workspace_members de Supabase."""
    supabase = get_supabase_client()
    if not supabase:
        return {}
    try:
        res = supabase.table("workspace_members").select("user_email, workspace_id").execute()
        email_ws = {}
        for r in (res.data or []):
            email_ws.setdefault(r["user_email"], set()).add(r["workspace_id"])
        return email_ws
    except Exception as e:
        print(f"⚠️ No se pudo cargar workspace_members: {e}")
        return {}


def _get_interlocutor_id(chat_id: str, current_user_id: str) -> Optional[str]:
    """
    Extrae el ID del otro participante de un chat 1-a-1.
    Formato del chat_id: 19:UUID1_UUID2@unq.gbl.spaces
    """
    try:
        inner = chat_id.split(":")[1].split("@")[0]   # "UUID1_UUID2"
        ids = inner.split("_")
        for uid in ids:
            if uid != current_user_id:
                return uid
    except Exception:
        pass
    return None


def analyze_my_tfg_messages():
    users = [
        u for u in list_users()
        if ".tfg@" in (u.get("userPrincipalName") or "")
    ]
    print(f"🔎 Usuarios TFG encontrados: {len(users)}")

    id_to_email    = {u["id"]: u["userPrincipalName"] for u in users}
    email_workspaces = _load_workspace_membership()  # email -> set(workspace_id)
    processed_ids  = set()  # deduplicación global por (message_id, ws_id)

    for user in users:
        user_email = user["userPrincipalName"]
        user_id    = user["id"]
        print(f"\n👤 Usuario: {user_email}")

        try:
            chats = list_user_chats(user_id)
        except Exception as e:
            print(f"⚠️ Error recuperando chats de {user_email}: {e}")
            continue

        for chat in chats:
            chat_id = chat["id"]

            # Identificar interlocutor y workspaces compartidos
            interlocutor_id    = _get_interlocutor_id(chat_id, user_id)
            interlocutor_email = id_to_email.get(interlocutor_id)
            sender_ws          = email_workspaces.get(user_email, set())
            interlocutor_ws    = email_workspaces.get(interlocutor_email, set()) if interlocutor_email else set()
            shared_ws          = sender_ws & interlocutor_ws

            # Omitir chats sin workspace compartido
            if not shared_ws:
                print(f"  ⏭️  Chat {chat_id[:50]}… omitido "
                      f"(interlocutor={interlocutor_email or '?'}, sin workspace compartido)")
                continue

            print(f"📂 Chat ID: {chat_id} (ws compartidos: {shared_ws})")

            try:
                messages = list_chat_messages(chat_id, top=50)
            except Exception as e:
                print(f"⚠️ Error recuperando mensajes del chat {chat_id}: {e}")
                continue

            print(f"   └── 📨 Mensajes recuperados: {len(messages)}")

            for msg in messages:
                message_id = msg.get("id")
                if not message_id:
                    continue

                # Deduplicar por (message_id, workspace)
                for ws_id in shared_ws:
                    key = f"{message_id}_{ws_id}"
                    if key in processed_ids:
                        continue
                    processed_ids.add(key)

                    raw_from     = msg.get("raw_from") or {}
                    sender_id    = (raw_from.get("user") or {}).get("id")
                    sender_email = id_to_email.get(sender_id, user_email)

                    analysis = analyze_message(msg["text"])
                    if not analysis:
                        continue

                    save_risk_metrics(
                        supabase=supabase,
                        user_email=sender_email,
                        timestamp=msg["createdDateTime"],
                        scores=analysis["labels"],
                        message_id=key,
                        workspace_id=ws_id,
                    )

                    print(f"       🕒 {msg['createdDateTime']} [{sender_email.split('@')[0]}] → ws{ws_id}")
                    for label, score in analysis["labels"].items():
                        if score > 0.4:
                            print(f"         - {label}: {score:.2f}")


if __name__ == "__main__":
    analyze_my_tfg_messages()
