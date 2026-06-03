import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth.auth_graph_web import build_auth_url

url = build_auth_url({})
print(url)
