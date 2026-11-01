import keyboard


def _tecla(nombre, mensaje):
    keyboard.send(nombre)
    return mensaje


def pausa_play(texto=""):
    return _tecla("play/pause media", "Listo.")


def siguiente(texto=""):
    return _tecla("next track", "Siguiente canción.")


def anterior(texto=""):
    return _tecla("previous track", "Canción anterior.")