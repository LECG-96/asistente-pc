from ctypes import POINTER, cast

from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

NUMEROS = {"diez": 10, "veinte": 20, "treinta": 30, "cuarenta": 40, "cincuenta": 50,
           "sesenta": 60, "setenta": 70, "ochenta": 80, "noventa": 90, "cien": 100}
PALABRAS_NUMERO = "|".join(NUMEROS)


def _endpoint():
    dispositivo = AudioUtilities.GetSpeakers()
    if hasattr(dispositivo, "EndpointVolume"):          # pycaw reciente
        return dispositivo.EndpointVolume
    interfaz = dispositivo.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interfaz, POINTER(IAudioEndpointVolume))


def _poner(porcentaje):
    porcentaje = max(0, min(100, porcentaje))
    ep = _endpoint()
    ep.SetMute(0, None)
    ep.SetMasterVolumeLevelScalar(porcentaje / 100, None)
    return f"Volumen al {porcentaje} por ciento."


def fijar(m):
    valor = m.group(1)
    return _poner(int(valor) if valor.isdigit() else NUMEROS[valor])


def subir(m=None):
    actual = round(_endpoint().GetMasterVolumeLevelScalar() * 100)
    return _poner(actual + 10)


def bajar(m=None):
    actual = round(_endpoint().GetMasterVolumeLevelScalar() * 100)
    return _poner(actual - 10)


def silenciar(m=None):
    _endpoint().SetMute(1, None)
    return "Silenciado."


def activar_sonido(m=None):
    _endpoint().SetMute(0, None)
    return "Sonido activado."