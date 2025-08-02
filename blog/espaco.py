frase1 = "edivan balbueno da silva."


# Divide a frase em uma lista de palavras
#palavras = frase.strip().replace(" ", "")


def semespacos(name):
    frase = name
    # Divide a frase em uma lista de palavras
    palavras = frase.strip().replace(" ", "")
    return(palavras)

print(semespacos(frase1))