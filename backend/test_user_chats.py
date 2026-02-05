from auth_graph_app import list_users, list_user_chats, list_chat_messages

users = list_users()

# Coge el primer usuario del tenant
user = users[0]
user_id = user["id"]
email = user.get("userPrincipalName")

print(f"👤 Usuario: {email}")

chats = list_user_chats(user_id)

print(f"💬 Chats encontrados: {len(chats)}")
for c in chats:
    chat_id = c["id"]
    chat_type = c.get("chatType", "unknown")
    print(f"\n📂 Chat ID: {chat_id} ({chat_type})")
    
    # Descargar mensajes
    msgs = list_chat_messages(chat_id)
    print(f"   └── 📨 Mensajes recuperados: {len(msgs)}")
    
    for m in msgs:
        print(f"       - [{m['from']}]: {m['text'][:60]}...")
