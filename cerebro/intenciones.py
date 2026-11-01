import re
import unicodedata

from rapidfuzz import fuzz, process

from acciones import (apps, energia, hora_fecha, multimedia, rutinas, sistema,
                      temporizadores, volumen, web)

from cerebro import aprendizaje



UMBRAL = 80

# Enseñar y consultar a Jarvis (se revisan primero)
REGLAS_META = [
    (r"^aprende(?: que)?(?: cuando)?(?: yo)? (?:diga|digo)\s+(.+?)\s+(abre|abrir|cierra|cerrar|presiona|presionar|responde|responder|contesta|di)\s+(.+)$",
     aprendizaje.ensenar),
    (r"^olvida(?: el comando)?\s+(.+)$", aprendizaje.olvidar),
    (r"que (?:es lo que )?mas (?:uso|te pido)|comandos mas usados", aprendizaje.mas_usados),
    (r"que no (?:has )?entendido|que no entendiste", aprendizaje.no_entendidas),
    (r"que comandos (?:te he|me has) ensenado|comandos aprendidos", aprendizaje.listar),
]

# Órdenes con parámetro (regex sobre el texto normalizado). El orden importa.
REGLAS = [
    (r"cancela.*(?:apagado|reinicio)|aborta.*(?:apagado|reinicio)|cancelar apagado", energia.cancelar),
    (r"\b(?:apaga|apagar)\b.*\b(?:pc|computador|computadora|equipo|sistema)\b", energia.apagar),
    (r"\b(?:reinicia|reiniciar)\b.*\b(?:pc|computador|computadora|equipo|sistema)\b", energia.reiniciar),
    (r"^(?:bloquea|bloquear)\b", energia.bloquear),
    (r"cancela.*(?:temporizador|temporizadores|alarma|alarmas|recordatorio|recordatorios)", temporizadores.cancelar),
    (r"cuanto (?:falta|queda)|que temporizadores tengo|temporizadores activos", temporizadores.estado),
    (r"\b(?:temporizador|alarma|avisame|recuerdame)\b.*\b(?:segundos?|minutos?|horas?|media hora)\b", temporizadores.crear),
    (r"^(?:abre|abrir|abri|ejecuta|lanza)\s+(?:el |la |los |las |mi |mis )?(.+)$", apps.abrir),
    (r"^(?:cierra|cerrar)\s+(?:el |la |los |las |mi |mis )?(.+)$", apps.cerrar),
    (r"^(?:presiona|presionar)\s+(.+)$", apps.presionar),
    (r"^(?:busca|buscar|buscame)\s+(.+?)\s+en\s+youtube$", web.buscar_youtube),
    (r"^(?:busca|buscar|buscame)\s+(.+?)(?:\s+en\s+google)?$", web.buscar_google),
    (rf"volumen.*?\b(\d{{1,3}}|{volumen.PALABRAS_NUMERO})\b", volumen.fijar),
    (r"(?:sube|subir|aumenta|aumentar).*volumen|mas volumen", volumen.subir),
    (r"(?:baja|bajar|disminuye|reduce).*volumen|menos volumen", volumen.bajar),
    (r"(?:activa|reactiva|enciende).*sonido|quita(?:r)? el silencio|desmutea", volumen.activar_sonido),
    (r"silencia|silenciar|mutea|mutear|silencio", volumen.silenciar),
]

# Frases libres (coincidencia flexible)
INTENCIONES = [
    (["que hora es", "dime la hora", "la hora"], hora_fecha.decir_hora),
    (["que fecha es hoy", "que dia es hoy", "dime la fecha", "la fecha"], hora_fecha.decir_fecha),
    (["estado del pc", "como esta el pc", "como esta el computador", "uso de cpu",
      "estado del sistema", "como va el computador"], sistema.estado_pc),
    (["pausa la musica", "pausa", "reproduce la musica", "reanuda la musica",
      "continua la musica", "play", "para la musica"], multimedia.pausa_play),
    (["siguiente cancion", "siguiente tema", "pasa a la siguiente cancion",
      "salta la cancion", "cambia la cancion"], multimedia.siguiente),
    (["cancion anterior", "tema anterior", "vuelve a la cancion anterior",
      "pon la cancion anterior"], multimedia.anterior),
]

# Cada rutina de config.json se activa con sus frases ("Jarvis, modo estudio")
for _r in rutinas.RUTINAS.values():
    INTENCIONES.append((_r["frases"], lambda texto, r=_r: rutinas.ejecutar(r)))


def normalizar(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[^a-z0-9 ]", " ", texto)
    texto = re.sub(r"\bjarvis\b", " ", texto)
    texto = re.sub(r"\b(?:sierra|sierre|cierre)\b", "cierra", texto)   # errores típicos de Whisper
    return re.sub(r"\s+", " ", texto).strip()


def _comando_base(t):
    respuesta = apps.atajo_configurado(t)          # "cierra la pestaña", "nueva pestaña"...
    if respuesta:
        return respuesta

    for patron, funcion in REGLAS:
        m = re.search(patron, t)
        if m:
            return funcion(m)

    mejor_funcion, mejor_puntaje = None, 0
    for frases, funcion in INTENCIONES:
        _, puntaje, _ = process.extractOne(t, frases, scorer=fuzz.token_set_ratio)
        if puntaje > mejor_puntaje:
            mejor_funcion, mejor_puntaje = funcion, puntaje

    if mejor_funcion and mejor_puntaje >= UMBRAL:
        return mejor_funcion(t)
    return None


def procesar(texto):
    """Devuelve lo que Jarvis debe responder (texto o Confirmacion), o None si no entendió."""
    t = normalizar(texto)
    if not t:
        return None

    for patron, funcion in REGLAS_META:
        m = re.search(patron, t)
        if m:
            return funcion(m)

    respuesta = aprendizaje.buscar_aprendido(t)      # primero lo que le enseñaste
    if respuesta is None:
        respuesta = _comando_base(t)

    if respuesta is None:
        aprendizaje.registrar_fallo(t)
    else:
        aprendizaje.registrar_uso(t)
    return respuesta