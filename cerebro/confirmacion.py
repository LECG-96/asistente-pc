import re
import unicodedata

AFIRMATIVAS = {"si", "confirmo", "confirmar", "confirmado", "dale", "adelante",
               "hazlo", "claro", "ok", "okey", "afirmativo"}
NEGATIVAS = {"no", "cancela", "cancelar", "cancelado", "negativo", "espera", "detente"}


class Confirmacion:
    """Una acción delicada que espera un sí o un no antes de ejecutarse."""

    def __init__(self, pregunta, accion):
        self.pregunta = pregunta
        self.accion = accion          # función sin argumentos que devuelve lo que dirá


def _palabras(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return set(re.sub(r"[^a-z ]", " ", texto).split())


def es_afirmativo(texto):
    p = _palabras(texto)
    return bool(p & AFIRMATIVAS) and not (p & NEGATIVAS)