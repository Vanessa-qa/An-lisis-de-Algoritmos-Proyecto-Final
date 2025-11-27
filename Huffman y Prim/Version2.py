import heapq
import os
from collections import Counter, defaultdict
import itertools

# Construcción del grafo entre símbolos
def construir_grafo(datos):
    frecuencias = Counter(datos)
    simbolos = list(frecuencias.keys())
    grafo = {s: [] for s in simbolos}

    for a, b in itertools.combinations(simbolos, 2):
        peso = abs(a - b)
        grafo[a].append((b, peso))
        grafo[b].append((a, peso))

    return grafo, simbolos


# Prim
def prim(grafo, simbolos):
    if not simbolos:
        return []

    inicio = simbolos[0]
    visitado = {inicio}
    aristas_mst = []
    heap = []

    for vecino, peso in grafo[inicio]:
        heapq.heappush(heap, (peso, inicio, vecino))

    while heap and len(visitado) < len(simbolos):
        peso, u, v = heapq.heappop(heap)
        if v in visitado:
            continue

        visitado.add(v)
        aristas_mst.append((u, v, peso))

        for vecino, peso2 in grafo[v]:
            if vecino not in visitado:
                heapq.heappush(heap, (peso2, v, vecino))

    return aristas_mst


# Ordenamiento del MST con DFS
def construir_orden_mst(mst, simbolos):
    if not simbolos:
        return []

    g = {s: [] for s in simbolos}
    for u, v, _ in mst:
        g[u].append(v)
        g[v].append(u)

    inicio = simbolos[0]
    visitado = set()
    orden = []

    def dfs(n):
        visitado.add(n)
        orden.append(n)
        for vecino in g[n]:
            if vecino not in visitado:
                dfs(vecino)

    dfs(inicio)
    return orden


#PREPROCESADO REAL BASADO EN MST(REQUISITO CLAVE)

def aplicar_reasignacion_mst(datos, orden_mst):
    # símbolo -> índice en el MST
    posicion = {simbolo: i for i, simbolo in enumerate(orden_mst)}

    # Reemplazamos cada byte por el índice MST (preprocesado)
    nuevos = bytearray(posicion[b] for b in datos)
    return bytes(nuevos), orden_mst


def revertir_reasignacion_mst(datos, orden_mst):
    # El valor de cada byte es un índice dentro del orden MST
    originales = bytearray(orden_mst[i] for i in datos)
    return bytes(originales)


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

        nodo = NodoHuffman(None, izquierda.frecuencia + derecha.frecuencia)
        nodo.izquierda = izquierda
        nodo.derecha = derecha

        heapq.heappush(cola, nodo)

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

    usar_prim = True

    if usar_prim:
        print(">> Ejecutando preprocesado con Prim...")

        # 1 Grafo
        grafo, simbolos = construir_grafo(datos)

        # 2.MST con Prim
        mst = prim(grafo, simbolos)

        # 3.Orden MST
        orden_mst = construir_orden_mst(mst, simbolos)

        # 4.Reasignación basada en MST (PREPROCESADO REAL)
        datos, orden_mst = aplicar_reasignacion_mst(datos, orden_mst)

        # 5.Guardamos orden MST para descompresión
        with open("orden_mst.bin", "wb") as f:
            f.write(bytes(orden_mst))

    # Construir Huffman
    arbol = construir_arbol_huffman(datos)
    codigos = generar_codigos(arbol)

    # Convertir a bits
    datos_codificados = "".join(codigos[b] for b in datos)

    # Asegurar multiplos de 8 bits
    relleno = 8 - len(datos_codificados) % 8
    datos_codificados += "0" * relleno

     # Convertir a bytes reales
    datos_bytes = bytearray()
    for i in range(0, len(datos_codificados), 8):
        datos_bytes.append(int(datos_codificados[i:i+8], 2))

    # Guardar comprimido
    with open("archivo_comprimido.bin", "wb") as f:
        f.write(bytes([relleno]))
        f.write(datos_bytes)

    print(">> Archivo comprimido creado: archivo_comprimido.bin")
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
def descomprimir_archico(arbol):
    with open("archivo_comprimido.bin", "rb") as f:
        relleno = f.read(1)[0]
        datos = f.read()

    bits = "".join(f"{byte:08b}" for byte in datos)
    bits = bits[:-relleno]

    # Huffman decode
    datos_originales = decodificar_bits(bits, arbol)


    if os.path.exists("orden_mst.bin"):
        with open("orden_mst.bin", "rb") as f:
            orden_mst = list(f.read())

        datos_originales = revertir_reasignacion_mst(datos_originales, orden_mst)
    
    with open("archivo_descomprimido.mp3", "wb") as f:
        f.write(datos_originales)

    print(">> Archivo descomprimido creado: archivo_descomprimido.mp3")

# Funcion principal
def main():
    archivo = input("Ingresa el nombre del archivo MP3: ")

    print("\n--- COMPRIMIENDO ---")
    arbol = comprimir_archivo(archivo)

    print("\n--- DESCOMPRIMIENDO ---")
    descomprimir_archico(arbol)


if __name__ == "__main__":
    main()
