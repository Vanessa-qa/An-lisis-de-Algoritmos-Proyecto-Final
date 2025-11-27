Compresor MP3-Prim + Huffman

Este proyecto implementa un compresor y descompresor de archivos MP3 utilizando una combinación de reestructuración por Árbol de Expansión Mínima (MST) mediante el algoritmo de Prim, seguida de codificación del algoritmo de Huffman. Incluye además una interfaz gráfica (GUI) con Tkinter y un reproductor integrado usando pygame.

REQUISITOS DEL SISTEMA
-Python.10 o +
-Librerias
Utilizamos librerias ya incluidas en la instalacion estandar de Python, es decir no requiere una instalacion que son las siguientes:
    -os
    -heapq
    -itertools
    -threading
    -queue
    -shutil
    -struct
    -collections.Counter
    -tkinter
        submodulos de tkinter
        -tkinter.scrolledtext
        -tkinter.filedialog
        -tkinter.*

Nuestra unica libreria que necesita una descarga es:
    -pygame
    La podemos instalar con el siguiente comando desde la terminal:
        pip install pygame 

Que hace el programa?
Tenemos dos funciones dentro del programa, la compresion y descompresion.

-Compresión
    Lee un archivo MP3 completo en bytes.
    Construye un grafo de símbolos basados en los bytes presentes en el archivo.
    Ejecuta Prim para generar un MST y obtener un ordenamiento optimizado de símbolos.
    Reasigna los bytes usando ese orden.
    Construye un árbol Huffman a partir de los datos reasignados.
    Codifica los datos en bits y genera un archivo .bin con:
    Relleno de bits usado
    Tabla de frecuencias serializada
    Orden MST utilizado
    Datos comprimidos

-Descompresión
    Lee el .bin y recupera:
    Relleno
    Tabla de frecuencias
    Orden MST
    Datos comprimidos
    Reconstruye Huffman y decodifica los bits.
    Revierte la reasignación del MST.
    Genera el MP3 original.

Tambien nuestro programa cuenta con una Interfaz grafica donde permite un facil acceso para el usuario y utilizar la logica de manera sencilla e intuitiva.

Para ejecutar la aplicacion lo podemos hacer desde la terminal python VersionFinal.py

