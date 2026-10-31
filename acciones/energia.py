import subprocess

from cerebro.confirmacion import Confirmacion


def _shutdown(*args):
    subprocess.run(["shutdown", *args], check=False)


def apagar(m=None):
    def ejecutar():
        _shutdown("/s", "/t", "15")
        return "Apagando el equipo en 15 segundos. Di cancelar apagado para detenerlo."
    return Confirmacion("¿Seguro que quieres apagar el equipo? Di sí o no.", ejecutar)


def reiniciar(m=None):
    def ejecutar():
        _shutdown("/r", "/t", "15")
        return "Reiniciando el equipo en 15 segundos. Di cancelar reinicio para detenerlo."
    return Confirmacion("¿Seguro que quieres reiniciar el equipo? Di sí o no.", ejecutar)


def cancelar(m=None):
    _shutdown("/a")
    return "Operación cancelada."


def bloquear(m=None):
    subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=False)
    return "Equipo bloqueado."