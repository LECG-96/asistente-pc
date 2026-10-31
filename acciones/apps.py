import os
import subprocess

import keyboard
from rapidfuzz import fuzz, process

from acciones.web import _abrir_url
from cerebro.confirmacion import Confirmacion
from config import CFG

CARPETAS = CFG["carpetas"]
PAGINAS = CFG.get("paginas", {})
ATAJOS = CFG.get("atajos", {})

# Cada nombre y alias apunta a la ficha de su aplicación
APPS = {}
for _app in CFG["apps"]:
    for _nombre in [_app["nombre"], *_app.get("alias", [])]:
        APPS[_nombre] = _app

TECLAS = {"control": "ctrl", "ctrl": "ctrl", "alt": "alt", "mayusculas": "shift",
          "shift": "shift", "windows": "win", "tab": "tab", "enter": "enter",
          "escape": "esc", "suprimir": "delete", "espacio": "space"}


def _mejor(texto, opciones, corte=75, scorer=fuzz.WRatio):
    r = process.extractOne(texto, list(opciones), scorer=scorer, score_cutoff=corte)
    return r[0] if r else None


def _abrir_app(comando):
    # El comando sale de config.json, nunca de lo que dices por voz
    if isinstance(comando, list):                      # programa con argumentos
        exe = os.path.expandvars(comando[0])
        subprocess.Popen([exe, *comando[1:]], cwd=os.path.dirname(exe) or None)
        return
    ruta = os.path.expandvars(os.path.expanduser(comando))
    if os.path.exists(ruta):
        os.startfile(ruta, cwd=os.path.dirname(ruta))  # OBS y otras apps lo necesitan
    else:
        subprocess.Popen(f'start "" {comando}', shell=True)


# ---------- abrir ----------
def buscar(destino):
    return _mejor(destino, [*APPS, *CARPETAS, *PAGINAS])


def abrir_destino(destino):
    clave = buscar(destino)
    if not clave:
        return f"No sé abrir {destino}. Puedes agregarlo en el archivo de configuración."
    if clave in APPS:
        _abrir_app(APPS[clave]["abrir"])
    elif clave in PAGINAS:
        _abrir_url(PAGINAS[clave])
    else:
        os.startfile(os.path.expanduser(CARPETAS[clave]))
    return f"Abriendo {clave}."


def abrir(m):
    return abrir_destino(m.group(1).strip())


# ---------- cerrar ----------
def buscar_proceso(destino):
    clave = _mejor(destino, APPS)
    return clave if clave and APPS[clave].get("cerrar") else None


def _terminar(nombres, forzar):
    if isinstance(nombres, str):
        nombres = [nombres]
    cerrado = False
    for nombre in nombres:
        orden = ["taskkill", "/IM", nombre] + (["/F", "/T"] if forzar else [])
        if subprocess.run(orden, capture_output=True).returncode == 0:
            cerrado = True
    return cerrado


def cerrar_destino(destino):
    clave = buscar_proceso(destino)
    if not clave:
        return f"No sé cerrar {destino}. Agrega la clave cerrar a esa aplicación en el archivo de configuración."
    app = APPS[clave]

    def ejecutar():
        if _terminar(app["cerrar"], app.get("forzar", False)):
            return f"Cerrando {clave}."
        return f"No pude cerrar {clave}. Puede que no esté abierto."

    if app.get("confirmar"):
        return Confirmacion(
            f"¿Seguro que quieres cerrar {clave}? Podrías perder una partida. Di sí o no.",
            ejecutar,
        )
    return ejecutar()


def cerrar(m):
    return cerrar_destino(m.group(1).strip())


# ---------- teclas ----------
def combinacion(texto):
    """Convierte 'control shift t' en 'ctrl+shift+t'. Devuelve None si no la entiende."""
    partes = []
    for p in texto.split():
        if p in ("mas", "y"):
            continue
        if p in TECLAS:
            partes.append(TECLAS[p])
        elif len(p) == 1 or (p[0] == "f" and p[1:].isdigit()):
            partes.append(p)
        else:
            return None
    return "+".join(partes) if partes else None


def presionar_combo(combo):
    keyboard.send(combo)
    return f"Listo, {combo}."


def presionar(m):
    combo = combinacion(m.group(1).strip())
    return presionar_combo(combo) if combo else "No entendí qué teclas presionar."


def atajo_configurado(t):
    clave = _mejor(t, ATAJOS, corte=88, scorer=fuzz.ratio)
    return presionar_combo(ATAJOS[clave]) if clave else None


# ---------- rutina ----------
def modo_trabajo(texto=""):
    abiertas = []
    for nombre in CFG["rutina_trabajo"]:
        if nombre in APPS:
            _abrir_app(APPS[nombre]["abrir"])
            abiertas.append(nombre)
    if not abiertas:
        return "Modo trabajo activado, pero no hay aplicaciones configuradas."
    return "Modo trabajo activado. Abriendo " + " y ".join(abiertas) + "."