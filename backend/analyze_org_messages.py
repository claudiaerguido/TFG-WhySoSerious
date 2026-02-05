from auth_graph_app import list_users, list_user_chats, list_chat_messages
from message_analyzer import analyze_message
from db_supabase import save_risk_metrics

def analyze_my_tfg_messages():
    # 1. Filtramos solo tus usuarios ficticios (.tfg)
    users = [
        u for u in list_users()
        if ".tfg@" in (u.get("userPrincipalName") or "")
    ]

    print(f"🔎 Usuarios TFG encontrados: {len(users)}")

    for user in users:
        user_email = user["userPrincipalName"]
        print(f"\n👤 Usuario: {user_email}")

        try:
            chats = list_user_chats(user["id"])
        except Exception as e:
            print(f"⚠️ Error recuperando chats de {user_email}: {e}")
            continue

        for chat in chats:
            print(f"📂 Chat ID: {chat['id']}")
            try:
                messages = list_chat_messages(chat["id"], top=10)
            except Exception as e:
                print(f"⚠️ Error recuperando mensajes del chat {chat['id']}: {e}")
                continue

            print(f"   └── 📨 Mensajes recuperados: {len(messages)}")

            for msg in messages:
                analysis = analyze_message(msg["text"])
                if not analysis:
                    continue
                
                # --- NUEVO: Guardar en Supabase ---
                save_risk_metrics(
                    user_email=user_email,
                    timestamp=msg["createdDateTime"],
                    scores=analysis["labels"]
                )

                print(f"       🕒 {msg['createdDateTime']}")
                for label, score in analysis["labels"].items():
                    if score > 0.4:
                        print(f"         - {label}: {score:.2f}")

if __name__ == "__main__":
    analyze_my_tfg_messages()
