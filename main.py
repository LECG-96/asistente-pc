from voz.escuchar import escuchar
from voz.hablar import hablar

input("Presiona Enter y habla durante 5 segundos...")
texto = escuchar()
print("Entendí:", texto)
hablar(f"Dijiste: {texto}")