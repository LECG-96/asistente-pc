from datetime import datetime

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def decir_hora(texto=""):
    ahora = datetime.now()
    h = ahora.hour % 12 or 12
    m = ahora.minute
    verbo = "Es la" if h == 1 else "Son las"
    h_txt = "una" if h == 1 else str(h)
    if ahora.hour < 6:
        periodo = "de la madrugada"
    elif ahora.hour < 12:
        periodo = "de la mañana"
    elif ahora.hour < 20:
        periodo = "de la tarde"
    else:
        periodo = "de la noche"
    minutos = "en punto" if m == 0 else f"con {m} minutos"
    return f"{verbo} {h_txt} {minutos} {periodo}."


def decir_fecha(texto=""):
    hoy = datetime.now()
    return f"Hoy es {DIAS[hoy.weekday()]} {hoy.day} de {MESES[hoy.month - 1]} de {hoy.year}."