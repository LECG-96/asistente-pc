import sys
import threading
import time
import traceback
import winsound

from config import BASE, CFG

# Sin consola (pythonw), lo que se imprime va a un archivo de registro
if sys.stdout is None:
    sys.stdout = sys.stderr = open(BASE / "jarvis.log", "a", encoding="utf-8", buffering=1)

import sounddevice as sd

import bandeja
from acciones import apps, rutinas
from cerebro.confirmacion import Confirmacion, es_afirmativo
from cerebro.intenciones import procesar
from voz.activacion import esperar_activacion
from voz.escuchar import escuchar
from voz.hablar import hablar, precalentar


def elegir_microfono(nombre):
    for i, d in enumerate(sd.query_devices()):
        if d["max_input_channels"] > 0 and nombre.lower() in d["name"].lower():
            sd.default.device = (i, sd.default.device[1])
            print(f"Micrófono: {d['name']}")
            return
    print(f"No encontré un micrófono con el nombre '{nombre}'; uso el predeterminado de Windows.")


if CFG.get("microfono"):
    elegir_microfono(CFG["microfono"])


def frases_comunes():
    """Frases que Jarvis dice seguido: se dejan listas para que respondan al instante."""
    frases = ["Jarvis en línea.", "No te escuché.", "No entendí esa orden.", "Cancelado.",
              "Operación cancelada.", "Silenciado.", "Sonido activado.", "Equipo bloqueado.",
              "Listo.", "Siguiente canción.", "Canción anterior.",
              "Temporizador cancelado.", "No hay temporizadores activos."]
    frases += [f"Volumen al {n} por ciento." for n in range(0, 101, 10)]
    frases += [f"Abriendo {d}." for d in [*apps.APPS, *apps.CARPETAS, *apps.PAGINAS]]
    frases += [f"Cerrando {n}." for n, a in apps.APPS.items() if a.get("cerrar")]
    frases += [f"Listo, {combo}." for combo in apps.ATAJOS.values()]
    frases += [rutinas.mensaje_de(r) for r in rutinas.RUTINAS.values()]
    return frases


def atender(origen, orden=None):
    if origen.startswith("rutina:"):
        hablar(rutinas.ejecutar(rutinas.RUTINAS[origen.split(":", 1)[1]]))
        return

    if orden:                              # "Jarvis, abre Steam": ya viene la orden
        texto = orden
    else:                                  # "Jarvis" ... pitido ... orden
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
            resultado = esperar_activacion(bandeja.pausado.is_set)
            if resultado is None:
                continue
            origen, orden = resultado
            print(f"Activado por: {origen}")
            atender(origen, orden)
            print("En espera...")
        except Exception:
            traceback.print_exc()      # un error no debe matar a Jarvis
            time.sleep(2)


if __name__ == "__main__":
    print("Jarvis iniciado. Usa el ícono de la bandeja para pausar o salir.")
    threading.Thread(target=bucle, daemon=True).start()
    threading.Thread(target=lambda: precalentar(frases_comunes()), daemon=True).start()
    bandeja.iniciar()