import os
import threading

import pystray
from PIL import Image, ImageDraw

pausado = threading.Event()

ACTIVO = "#35d4ff"
PAUSA = "#6b7280"


def _icono(color):
    img = Image.new("RGB", (64, 64), "#0b1220")
    d = ImageDraw.Draw(img)
    d.ellipse((6, 6, 58, 58), outline=color, width=5)
    d.ellipse((22, 22, 42, 42), fill=color)
    return img


def iniciar():
    def alternar(icono, item):
        if pausado.is_set():
            pausado.clear()
            icono.icon = _icono(ACTIVO)
        else:
            pausado.set()
            icono.icon = _icono(PAUSA)

    def salir(icono, item):
        icono.stop()
        os._exit(0)

    menu = pystray.Menu(
        pystray.MenuItem(
            lambda item: "Reanudar" if pausado.is_set() else "Pausar",
            alternar,
            default=True,
        ),
        pystray.MenuItem("Salir", salir),
    )
    pystray.Icon("jarvis", _icono(ACTIVO), "Jarvis", menu).run()