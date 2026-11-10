import re
import sys
import threading
import time
import traceback
import winsound

from config import BASE, CFG, DEPURAR_VOZ

# Sin consola (pythonw), lo que se imprime va a un archivo de registro
if sys.stdout is None:
    sys.stdout = sys.stderr = open(BASE / "jarvis.log", "a", encoding="utf-8", buffering=1)

import sounddevice as sd

import bandeja
from acciones import apps, ia, rutinas
from cerebro.confirmacion import Confirmacion, es_afirmativo
from cerebro.intenciones import normalizar, procesar
from voz.activacion import esperar_activacion
from voz.escuchar import escuchar
from voz.hablar import hablar, precalentar

# Frases con las que das por terminada una charla con la IA
FIN_CHARLA = re.compile(r"\b(?:gracias|eso es todo|nada mas|ya esta|listo|adios|hasta luego|terminar conversacion)\b")


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
              "Temporizador cancelado.", "No hay temporizadores activos.",
              "Dictado terminado.", "De nada.", "Conversación reiniciada."]
    frases += [f"Volumen al {n} por ciento." for n in range(0, 101, 10)]
    frases += [f"Abriendo {d}." for d in [*apps.APPS, *apps.CARPETAS, *apps.PAGINAS]]
    frases += [f"Cerrando {n}." for n, a in apps.APPS.items() if a.get("cerrar")]
    frases += [f"Listo, {combo}." for combo in apps.ATAJOS.values()]
    frases += [rutinas.mensaje_de(r) for r in rutinas.RUTINAS.values()]
    return frases


def ejecutar_orden(texto):
    """Procesa la orden y la dice en voz alta. Devuelve la respuesta."""
    respuesta = procesar(texto)
    if isinstance(respuesta, Confirmacion):
        hablar(respuesta.pregunta)
        winsound.Beep(900, 150)
        confirmacion = escuchar(espera=5, maximo=6)
        if DEPURAR_VOZ:
            print("Confirmación:", confirmacion)
        hablar(respuesta.accion() if es_afirmativo(confirmacion) else "Cancelado.")
    else:
        hablar(respuesta or "No entendí esa orden.")
    return respuesta


def seguir_conversacion():
    """Tras una respuesta de la IA sigue escuchando, sin que tengas que decir 'Jarvis'."""
    while True:
        winsound.Beep(900, 150)
        texto = escuchar(espera=6)
        if DEPURAR_VOZ:
            print("Seguimiento:", texto)
        if not texto:
            return                                   # silencio: termina la charla
        if FIN_CHARLA.search(normalizar(texto)):
            hablar("De nada.")
            return
        respuesta = ejecutar_orden(texto)
        if not isinstance(respuesta, ia.RespuestaIA):
            return                                   # era una orden normal: termina la charla


def atender(origen, orden=None):
    if origen.startswith("rutina:"):
        hablar(rutinas.ejecutar(rutinas.RUTINAS[origen.split(":", 1)[1]]))
        return

    if orden:                              # "Jarvis, abre Steam": ya viene la orden
        texto = orden
    else:                                  # "Jarvis" ... pitido ... orden
        winsound.Beep(900, 150)
        texto = escuchar()
    if DEPURAR_VOZ:
        print("Entendí:", texto)

    if not texto:
        hablar("No te escuché.")
        return

    respuesta = ejecutar_orden(texto)
    if isinstance(respuesta, ia.RespuestaIA):
        seguir_conversacion()


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
