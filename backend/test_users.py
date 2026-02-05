from auth_graph_app import list_users

users = list_users()
for u in users:
    print(u["id"], u["userPrincipalName"])
