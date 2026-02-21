import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth_graph_app import list_users, list_user_chats, list_chat_messages

users = list_users()

for user in users[:1]:  # solo 1 usuario para prueba
    print(f"\n👤 Usuario: {user['userPrincipalName']}")
    chats = list_user_chats(user["id"])

    for chat in chats[:1]:  # solo 1 chat
        print(f"📂 Chat ID: {chat['id']} ({chat.get('chatType')})")
        messages = list_chat_messages(chat["id"], top=10)

        print(f"   └── 📨 Mensajes recuperados: {len(messages)}")
        for m in messages:
            print(f"       - [{m['from']}]: {m['text'][:80]}")
