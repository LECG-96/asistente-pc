import re
import unicodedata

AFIRMATIVAS = {"si", "confirmo", "confirmar", "confirmado", "dale", "adelante",
               "hazlo", "claro", "ok", "okey", "afirmativo"}


class Confirmacion:
    """Una acción delicada que espera un sí o un no antes de ejecutarse."""

    def __init__(self, pregunta, accion):
        self.pregunta = pregunta
        self.accion = accion          # función sin argumentos que devuelve lo que dirá


def es_afirmativo(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    frase = re.sub(r"[^a-z0-9\s]", " ", texto).strip()
    return frase in AFIRMATIVAS
