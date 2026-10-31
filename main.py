import sys
import threading
import time
import traceback
import winsound

from config import BASE

# Sin consola (pythonw), lo que se imprime va a un archivo de registro
if sys.stdout is None:
    sys.stdout = sys.stderr = open(BASE / "jarvis.log", "a", encoding="utf-8", buffering=1)

import bandeja
from acciones.apps import modo_trabajo
from cerebro.confirmacion import Confirmacion, es_afirmativo
from cerebro.intenciones import procesar
from voz.activacion import esperar_activacion
from voz.escuchar import escuchar
from voz.hablar import hablar


def atender(origen):
    if origen == "vamos a trabajar":
        hablar(modo_trabajo())
        return

    winsound.Beep(900, 150)
    texto = escuchar()
    print("Entendí:", texto)
    if not texto:
        hablar("No te escuché.")
        return

    respuesta = procesar(texto)
    if isinstance(respuesta, Confirmacion):
        hablar(respuesta.pregunta)
        winsound.Beep(900, 150)
        confirmacion = escuchar(4)
        print("Confirmación:", confirmacion)
        hablar(respuesta.accion() if es_afirmativo(confirmacion) else "Cancelado.")
    else:
        hablar(respuesta or "No entendí esa orden.")


def bucle():
    try:
        hablar("Jarvis en línea.")
    except Exception:
        traceback.print_exc()

    while True:
        try:
            if bandeja.pausado.is_set():
                time.sleep(0.5)
                continue
            origen = esperar_activacion(bandeja.pausado.is_set)
            if origen is None:
                continue
            print(f"Activado por: {origen}")
            atender(origen)
            print("En espera...")
        except Exception:
            traceback.print_exc()      # un error no debe matar a Jarvis
            time.sleep(2)


if __name__ == "__main__":
    print("Jarvis iniciado. Usa el ícono de la bandeja para pausar o salir.")
    threading.Thread(target=bucle, daemon=True).start()
    bandeja.iniciar()