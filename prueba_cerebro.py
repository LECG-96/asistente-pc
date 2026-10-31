from cerebro.intenciones import normalizar, procesar

print("Escribe una orden (Enter vacío para salir)")
while True:
    texto = input("> ").strip()
    if not texto:
        break
    print("Normalizado:", normalizar(texto))
    print("Respuesta:  ", procesar(texto))