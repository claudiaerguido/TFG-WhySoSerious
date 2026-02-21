import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth_graph_app import list_users

users = list_users()
for u in users:
    print(u["id"], u["userPrincipalName"])
