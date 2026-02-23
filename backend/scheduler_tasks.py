# nightly_job.py
from auth_graph_app import list_users, list_user_chats, list_chat_messages
from message_analyzer import analyze_message
from db_supabase import save_risk_metrics
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
    body = msg.get("body") or {}
    return clean_text(body.get("content") or msg.get("text") or "")

def run_nightly_analysis():
    print(f"🌙 Nightly analysis [{datetime.datetime.now()}]")

    users = [u for u in list_users() if TFG_FILTER in (u.get("userPrincipalName","").lower())]
    print(f"👥 Usuarios: {len(users)}")

    for u in users:
        user_id = u.get("id")
        user_email = u.get("userPrincipalName")
        if not user_id or not user_email:
            continue

        try:
            chats = list_user_chats(user_id)
        except Exception as e:
            print(f"⚠️ Chats error {user_email}: {e}")
            continue

        for chat in chats:
            chat_id = chat.get("id")
            if not chat_id:
                continue

            try:
                messages = list_chat_messages(chat_id, top=TOP_MESSAGES_PER_CHAT)
            except Exception as e:
                print(f"⚠️ Messages error chat {chat_id}: {e}")
                continue

            messages = sorted(messages, key=lambda m: m.get("createdDateTime") or "")

            for m in messages:
                message_id = m.get("id")
                created = m.get("createdDateTime")
                text = get_text(m)

                if not message_id or not created or len(text) < 3:
                    continue

                try:
                    analysis = analyze_message(text)
                    if not analysis:
                        continue

                    save_risk_metrics(
                        user_email=user_email,
                        timestamp=created,
                        scores=analysis["labels"],   # debe incluir TRISTEZA y resto
                        message_id=message_id,
                    )
                except Exception as e:
                    print(f"⚠️ Save/analyze error: {e}")

    print(f"✅ Done [{datetime.datetime.now()}]")

if __name__ == "__main__":
    run_nightly_analysis()