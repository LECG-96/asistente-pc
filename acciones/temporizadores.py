import re
import threading
import time
import traceback
import winsound

from voz.hablar import hablar

UNIDADES = {
    "un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12,
    "trece": 13, "catorce": 14, "quince": 15, "dieciseis": 16, "diecisiete": 17,
    "dieciocho": 18, "diecinueve": 19, "veinte": 20, "veintiuno": 21, "veintidos": 22,
    "veintitres": 23, "veinticuatro": 24, "veinticinco": 25, "veintiseis": 26,
    "veintisiete": 27, "veintiocho": 28, "veintinueve": 29, "treinta": 30,
    "cuarenta": 40, "cincuenta": 50, "sesenta": 60,
}
UNIDAD_SEG = {"segundo": 1, "minuto": 60, "hora": 3600}

_W = "|".join(sorted(UNIDADES, key=len, reverse=True))
_NUM = rf"(\d+|(?:{_W})(?: y (?:{_W}))?)"        # "10", "quince", "treinta y cinco"


def _numero(texto):
    return sum(int(p) if p.isdigit() else UNIDADES[p] for p in texto.split(" y "))


PATRONES = [
    (re.compile(rf"\b(?:{_NUM}\s+)?horas?\s+y\s+media\b"),
     lambda m: (_numero(m.group(1)) if m.group(1) else 1) * 3600 + 1800),
    (re.compile(r"\bmedia hora\b"), lambda m: 1800),
    (re.compile(rf"\b{_NUM}\s+(segundo|minuto|hora)s?\b"),
     lambda m: _numero(m.group(1)) * UNIDAD_SEG[m.group(2)]),
]

_activos = []
_lock = threading.Lock()
_contador = 0


def _extraer(texto):
    """Devuelve (segundos totales, texto del recordatorio) a partir de la frase."""
    coincidencias = [
        (m.start(), m.end(), valor(m))
        for patron, valor in PATRONES
        for m in patron.finditer(texto)
    ]
    if not coincidencias:
        return 0, ""

    total, fin = 0, 0
    # Si dos patrones empiezan en el mismo punto, "una hora y media" gana a "una hora".
    for inicio, siguiente, segundos in sorted(coincidencias, key=lambda dato: (dato[0], -dato[1])):
        if inicio < fin:
            continue
        if fin and not re.fullmatch(r"\s*(?:y\s+)?", texto[fin:inicio]):
            break
        total += segundos
        fin = siguiente
    etiqueta = re.sub(r"^(?:que|de|para|a|por|y)\s+", "", texto[fin:].strip())
    return total, etiqueta


def _fmt(seg):
    seg = int(round(seg))
    h, resto = divmod(seg, 3600)
    m, s = divmod(resto, 60)
    partes = []
    if h:
        partes.append(f"{h} hora{'s' if h != 1 else ''}")
    if m:
        partes.append(f"{m} minuto{'s' if m != 1 else ''}")
    if s and not h:
        partes.append(f"{s} segundo{'s' if s != 1 else ''}")
    return " y ".join(partes) if partes else "0 segundos"


def _terminar(ident, duracion, etiqueta):
    with _lock:
        _activos[:] = [a for a in _activos if a["id"] != ident]
    for _ in range(3):                       # alarma, por si no hay internet para la voz
        winsound.Beep(1000, 250)
        time.sleep(0.1)
    mensaje = (f"Recordatorio: {etiqueta}." if etiqueta
               else f"El temporizador de {_fmt(duracion)} ha terminado.")
    try:
        hablar(mensaje)
    except Exception:
        traceback.print_exc()


def crear(m):
    global _contador
    total, etiqueta = _extraer(m.string)
    if total <= 0:
        return "No entendí cuánto tiempo."
    if total > 24 * 3600:
        return "Es demasiado tiempo. El máximo es 24 horas."
    with _lock:
        _contador += 1
        ident = _contador
        timer = threading.Timer(total, _terminar, args=(ident, total, etiqueta))
        timer.daemon = True
        _activos.append({"id": ident, "fin": time.time() + total,
                         "etiqueta": etiqueta, "timer": timer})
        timer.start()
    return f"Listo, te aviso en {_fmt(total)}."


def cancelar(m=None):
    with _lock:
        n = len(_activos)
        for a in _activos:
            a["timer"].cancel()
        _activos.clear()
    if not n:
        return "No hay temporizadores activos."
    return "Temporizador cancelado." if n == 1 else f"Cancelé {n} temporizadores."


def estado(m=None):
    with _lock:
        pendientes = sorted(_activos, key=lambda a: a["fin"])
    if not pendientes:
        return "No hay temporizadores activos."
    partes = []
    for a in pendientes:
        resto = _fmt(max(0, a["fin"] - time.time()))
        partes.append(f"faltan {resto}" + (f" para {a['etiqueta']}" if a["etiqueta"] else ""))
    if len(partes) == 1:
        return partes[0].capitalize() + "."
    return f"Tienes {len(partes)} temporizadores: " + "; ".join(partes) + "."
