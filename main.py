import winsound

from voz.activacion import esperar_activacion
from voz.escuchar import escuchar
from voz.hablar import hablar

print("Jarvis en espera. Di 'Jarvis' o 'Vamos a trabajar', o presiona Ctrl+Alt+J. (Ctrl+C para salir)")

try:
    while True:
        origen = esperar_activacion()
        print(f"Activado por: {origen}")
        winsound.Beep(900, 150)          # aviso instantáneo de que te escucha
        texto = escuchar()
        print("Entendí:", texto)
        if texto:
            hablar(f"Dijiste: {texto}")
        print("En espera...")
except KeyboardInterrupt:
    print("Jarvis desactivado.")