import winsound

from cerebro.intenciones import procesar
from voz.activacion import esperar_activacion
from voz.escuchar import escuchar
from voz.hablar import hablar

print("Jarvis en espera. Di 'Jarvis' o 'Vamos a trabajar', o presiona Ctrl+Alt+J. (Ctrl+C para salir)")

try:
    while True:
        origen = esperar_activacion()
        print(f"Activado por: {origen}")

        if origen == "vamos a trabajar":
            hablar("Modo trabajo activado.")   # provisional: en el Paso 6 abrirá tus apps
            print("En espera...")
            continue

        winsound.Beep(900, 150)
        texto = escuchar()
        print("Entendí:", texto)

        if not texto:
            hablar("No te escuché.")
        else:
            hablar(procesar(texto) or "No entendí esa orden.")
        print("En espera...")
except KeyboardInterrupt:
    print("Jarvis desactivado.")