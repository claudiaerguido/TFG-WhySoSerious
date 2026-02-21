from auth_graph_app import list_users, list_user_chats, list_chat_messages
from message_analyzer import analyze_message
from db_supabase import save_risk_metrics
import datetime, time, re

TFG_FILTER = ".tfg@"
TOP_MESSAGES_PER_CHAT = 50


def retry(fn, *args, tries=5, base_sleep=1.0, **kwargs):
    for i in range(tries):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            msg = str(e).lower()
            if "429" in msg or "throttle" in msg or "too many requests" in msg:
                time.sleep(base_sleep * (2 ** i))
                continue
            raise


def msg_text(msg: dict) -> str:
    # Graph suele traer msg["body"]["content"] (HTML)
    content = (msg.get("body") or {}).get("content") or msg.get("text") or ""
    if not content:
        return ""
    # quita HTML + normaliza espacios
    content = re.sub(r"<[^>]+>", " ", content)
    content = re.sub(r"\s+", " ", content).strip()
    return content


def run_nightly_analysis():
    print(f"🌙 Ejecutando análisis nocturno... [{datetime.datetime.now()}]")

    try:
        users = [
            u for u in retry(list_users)
            if TFG_FILTER in ((u.get("userPrincipalName") or "").lower())
        ]
        print(f"🔎 Usuarios a analizar: {len(users)}")

        for u in users:
            user_id = u.get("id")
            user_email = u.get("userPrincipalName")
            if not user_id or not user_email:
                continue

            # 1) chats del usuario
            try:
                chats = retry(list_user_chats, user_id)
            except Exception as e:
                print(f"⚠️ Error listando chats para {user_email}: {e}")
                continue

            for chat in chats:
                chat_id = chat.get("id")
                if not chat_id:
                    continue

                # 2) mensajes del chat
                try:
                    messages = retry(list_chat_messages, chat_id, top=TOP_MESSAGES_PER_CHAT)
                except Exception as e:
                    print(f"⚠️ Error leyendo mensajes de chat {chat_id}: {e}")
                    continue

                # ordenar de viejo a nuevo
                messages = sorted(messages, key=lambda m: m.get("createdDateTime") or "")

                for m in messages:
                    try:
                        message_id = m.get("id")
                        created = m.get("createdDateTime")
                        if not message_id or not created:
                            continue

                        # 3) filtrar: solo mensajes escritos por el usuario del bucle
                        author_raw = m.get("raw_from") or {}
                        author = author_raw.get("user") or {}
                        author_id = author.get("id")
                        author_upn = (author.get("userPrincipalName") or "").lower()
                        if author_id:
                            if author_id != user_id:
                                continue
                        else:
                            if author_upn and author_upn != user_email.lower():
                                continue
                            if not author_upn:  # sin autor => ignora
                                continue

                        text = msg_text(m)
                        if len(text) < 3:
                            continue

                        analysis = analyze_message(text)
                        if not analysis:
                            continue

                        save_risk_metrics(
                            user_email=user_email,
                            timestamp=created,
                            scores=analysis["labels"],
                            message_id=message_id,
                        )

                    except Exception as e:
                        print(f"⚠️ Error procesando mensaje en chat {chat_id}: {e}")

        print(f"✅ Análisis nocturno completado [{datetime.datetime.now()}]")

    except Exception as e:
        print(f"❌ Error crítico: {e}")


if __name__ == "__main__":
    run_nightly_analysis()