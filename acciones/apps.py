import os
import subprocess

from rapidfuzz import fuzz, process

from config import CFG

APPS = CFG["apps"]
CARPETAS = CFG["carpetas"]


def _abrir_app(comando):
    # El comando sale de config.json, nunca de lo que dices por voz
    ruta = os.path.expandvars(os.path.expanduser(comando))
    if os.path.exists(ruta):
        os.startfile(ruta)
    else:
        subprocess.Popen(f'start "" {comando}', shell=True)


def abrir(m):
    destino = m.group(1).strip()
    claves = list(APPS) + list(CARPETAS)
    r = process.extractOne(destino, claves, scorer=fuzz.WRatio, score_cutoff=75)
    if not r:
        return f"No sé abrir {destino}. Puedes agregarlo en el archivo de configuración."
    clave = r[0]
    if clave in APPS:
        _abrir_app(APPS[clave])
    else:
        os.startfile(os.path.expanduser(CARPETAS[clave]))
    return f"Abriendo {clave}."


def modo_trabajo(texto=""):
    abiertas = []
    for nombre in CFG["rutina_trabajo"]:
        if nombre in APPS:
            _abrir_app(APPS[nombre])
            abiertas.append(nombre)
    if not abiertas:
        return "Modo trabajo activado, pero no hay aplicaciones configuradas."
    return "Modo trabajo activado. Abriendo " + " y ".join(abiertas) + "."