import re
import unicodedata

from rapidfuzz import fuzz, process

from acciones import hora_fecha

UMBRAL = 80   # sube si activa órdenes equivocadas; baja si no entiende

# (frases de ejemplo, función que devuelve lo que Jarvis dirá)
INTENCIONES = [
    (["que hora es", "dime la hora", "la hora"], hora_fecha.decir_hora),
    (["que fecha es hoy", "que dia es hoy", "dime la fecha", "la fecha"], hora_fecha.decir_fecha),
]


def normalizar(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[^a-z0-9 ]", " ", texto)
    texto = re.sub(r"\bjarvis\b", " ", texto)      # ignora el nombre si lo dices
    return re.sub(r"\s+", " ", texto).strip()


def procesar(texto):
    """Devuelve lo que Jarvis debe responder, o None si no entendió."""
    t = normalizar(texto)
    if not t:
        return None

    mejor_funcion, mejor_puntaje = None, 0
    for frases, funcion in INTENCIONES:
        _, puntaje, _ = process.extractOne(t, frases, scorer=fuzz.token_set_ratio)
        if puntaje > mejor_puntaje:
            mejor_funcion, mejor_puntaje = funcion, puntaje

    if mejor_funcion and mejor_puntaje >= UMBRAL:
        return mejor_funcion(t)
    return None