import heapq
import os
from collections import Counter

# Clase nodo
class NodoHuffman:
    def __init__(self, byte, frecuencia):
        self.byte = byte
        self.frecuencia = frecuencia
        self.izquierda = None
        self.derecha = None

    def __lt__(self, otro):
        return self.frecuencia < otro.frecuencia

# Funcion para contruir el arbol binario
def construir_arbol_huffman(datos):
    frecuencias = Counter(datos)
    cola = []

    for byte, frecuencia in frecuencias.items():
        heapq.heappush(cola, NodoHuffman(byte, frecuencia))

    while len(cola) > 1:
        izquierda = heapq.heappop(cola)
        derecha = heapq.heappop(cola)

        nodo_combinado = NodoHuffman(None, izquierda.frecuencia + derecha.frecuencia)
        nodo_combinado.izquierda = izquierda
        nodo_combinado.derecha = derecha

        heapq.heappush(cola, nodo_combinado)

    return heapq.heappop(cola)

# Funcion para generar los codigos
def generar_codigos(nodo, codigo_actual="", codigos={}):
    if nodo is None:
        return

    if nodo.byte is not None:
        codigos[nodo.byte] = codigo_actual
        return

    generar_codigos(nodo.izquierda, codigo_actual + "0", codigos)
    generar_codigos(nodo.derecha, codigo_actual + "1", codigos)

    return codigos

# Funcion para comprimir la cancion mp3
def comprimir_archivo(nombre_mp3):
    ruta_mp3 = os.path.join(os.getcwd(), nombre_mp3)

    # Leer archivo MP3 como bytes
    with open(ruta_mp3, "rb") as f:
        datos = f.read()

    # Construir Huffman
    arbol = construir_arbol_huffman(datos)
    codigos = generar_codigos(arbol)

    # Convertir a bits
    datos_codificados = "".join(codigos[byte] for byte in datos)

    # Asegurar multiplos de 8 bits
    relleno = 8 - len(datos_codificados) % 8
    datos_codificados += "0" * relleno

    # Convertir a bytes reales
    datos_como_bytes = bytearray()
    for i in range(0, len(datos_codificados), 8):
        byte = datos_codificados[i:i+8]
        datos_como_bytes.append(int(byte, 2))

    # Guardar comprimido
    archivo_bin = "archivo_comprimido.bin"
    with open(archivo_bin, "wb") as f:
        f.write(bytes([relleno]))
        f.write(datos_como_bytes)

    print(f"Archivo comprimido creado: {archivo_bin}")
    return arbol

# Funcion para decodificar los bits
def decodificar_bits(bits, arbol):
    resultado = bytearray()
    nodo = arbol

    for bit in bits:
        nodo = nodo.izquierda if bit == "0" else nodo.derecha

        if nodo.byte is not None:
            resultado.append(nodo.byte)
            nodo = arbol

    return resultado

# Funcion para descomprimir el bin
def descomprimir_archivo(arbol):
    archivo_bin = "archivo_comprimido.bin"

    with open(archivo_bin, "rb") as f:
        relleno = f.read(1)[0]
        datos = f.read()

    bits = "".join(f"{byte:08b}" for byte in datos)
    bits = bits[:-relleno]

    datos_originales = decodificar_bits(bits, arbol)

    archivo_salida = "archivo_descomprimido.mp3"
    with open(archivo_salida, "wb") as f:
        f.write(datos_originales)

    print(f"Archivo descomprimido creado: {archivo_salida}")

# Funcion principal
def main():
    archivo = input("Ingresa el nombre del archivo MP3: ")

    print("\n--- COMPRIMIENDO ---")
    arbol = comprimir_archivo(archivo)

    print("\n--- DESCOMPRIMIENDO ---")
    descomprimir_archivo(arbol)

if __name__ == "__main__":
    main()