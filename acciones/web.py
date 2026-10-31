import os
import webbrowser
from urllib.parse import quote_plus

from config import CFG


def _abrir_url(url):
    ruta = os.path.expandvars(os.path.expanduser(CFG.get("navegador", "")))
    if ruta and os.path.exists(ruta):
        webbrowser.register("navegador", None, webbrowser.BackgroundBrowser(ruta))
        webbrowser.get("navegador").open(url)
    else:
        webbrowser.open(url)       # si no encuentra Opera GX, usa el predeterminado


def buscar_google(m):
    consulta = m.group(1).strip()
    _abrir_url(f"https://www.google.com/search?q={quote_plus(consulta)}")
    return f"Buscando {consulta} en Google."


def buscar_youtube(m):
    consulta = m.group(1).strip()
    _abrir_url(f"https://www.youtube.com/results?search_query={quote_plus(consulta)}")
    return f"Buscando {consulta} en YouTube."