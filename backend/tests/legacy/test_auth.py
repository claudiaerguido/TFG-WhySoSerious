from auth.auth_graph_web import build_auth_url

def test_build_auth_url_returns_string():
    url = build_auth_url({})
    assert isinstance(url, str)
    assert "login.microsoftonline.com" in url
