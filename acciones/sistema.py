import subprocess

import psutil


def _gpu():
    try:
        salida = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu,temperature.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip()
        uso, temp = [x.strip() for x in salida.split(",")]
        return f" La tarjeta gráfica está al {uso} por ciento, a {temp} grados."
    except Exception:
        return ""


def estado_pc(texto=""):
    cpu = round(psutil.cpu_percent(interval=0.5))
    mem = psutil.virtual_memory()
    usada = round(mem.used / 1024**3, 1)
    total = round(mem.total / 1024**3, 1)
    return (f"El procesador está al {cpu} por ciento. "
            f"La memoria está al {round(mem.percent)} por ciento, "
            f"{usada} de {total} gigas.{_gpu()}")