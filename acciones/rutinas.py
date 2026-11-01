import time

from acciones import apps, energia, volumen
from config import CFG

RUTINAS = {r["nombre"]: r for r in CFG.get("rutinas", [])}


def mensaje_de(rutina):
    return rutina.get("mensaje") or f"Modo {rutina['nombre']} activado."


def ejecutar(rutina):
    omitidas, problemas = [], []
    for paso in rutina.get("acciones", []):
        if "abrir" in paso:
            if apps.buscar(paso["abrir"]):
                apps.abrir_destino(paso["abrir"])
            else:
                problemas.append(paso["abrir"])
        elif "cerrar" in paso:
            resultado = apps.cerrar_silencioso(paso["cerrar"])
            if resultado is None:
                omitidas.append(paso["cerrar"])
            elif resultado is False:
                problemas.append(paso["cerrar"])
        elif "volumen" in paso:
            volumen._poner(int(paso["volumen"]))
        elif "presionar" in paso:
            apps.presionar_combo(paso["presionar"])
        elif "esperar" in paso:
            time.sleep(float(paso["esperar"]))
        elif paso.get("bloquear"):
            energia.bloquear()

    mensaje = mensaje_de(rutina)
    if omitidas:
        mensaje += " No cerré " + " ni ".join(omitidas) + " porque pide confirmación."
    if problemas:
        mensaje += " No encontré " + " ni ".join(problemas) + "."
    return mensaje