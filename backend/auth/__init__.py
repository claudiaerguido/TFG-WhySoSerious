from bs4 import BeautifulSoup


def html_to_text(html: str) -> str:
    """Convierte HTML de Teams en texto plano para que el modelo NLP no reciba etiquetas."""
    if not html:
        return ""
    try:
        return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    except Exception:
        return html
