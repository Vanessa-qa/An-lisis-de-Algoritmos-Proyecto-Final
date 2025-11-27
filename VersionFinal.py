#prim y huffman
import os
import heapq
import itertools
import threading
import queue
import shutil
import struct
import pygame 
from collections import Counter
from tkinter import (
    Tk, Button, Label, Frame, filedialog, Toplevel, Scale,
    LEFT, BOTH, END, DISABLED, NORMAL, HORIZONTAL
)
from tkinter.scrolledtext import ScrolledText


def construir_grafo(datos):
    frecuencias = Counter(datos)
    simbolos = list(frecuencias.keys())
    grafo = {s: [] for s in simbolos}
    for a, b in itertools.combinations(simbolos, 2):
        peso = abs(a - b)
        grafo[a].append((b, peso))
        grafo[b].append((a, peso))
    return grafo, simbolos

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

def aplicar_reasignacion_mst(datos, orden_mst):
    posicion = {simbolo: i for i, simbolo in enumerate(orden_mst)}
    nuevos = bytearray(posicion[b] for b in datos)
    return bytes(nuevos), orden_mst

def revertir_reasignacion_mst(datos, orden_mst):
    originales = bytearray(orden_mst[i] for i in datos)
    return bytes(originales)

class NodoHuffman:
    def __init__(self, byte, frecuencia):
        self.byte = byte
        self.frecuencia = frecuencia
        self.izquierda = None
        self.derecha = None
    def __lt__(self, otro):
        return self.frecuencia < otro.frecuencia

def construir_arbol_huffman_desde_datos(datos):
    frecuencias = Counter(datos)
    return construir_arbol_huffman_desde_frecuencias(frecuencias)

def construir_arbol_huffman_desde_frecuencias(frecuencias):
    # frecuencias
    cola = []
    for byte, frecuencia in frecuencias.items():
        heapq.heappush(cola, NodoHuffman(byte, frecuencia))
    if not cola:
        return None
    while len(cola) > 1:
        izquierda = heapq.heappop(cola)
        derecha = heapq.heappop(cola)
        nodo = NodoHuffman(None, izquierda.frecuencia + derecha.frecuencia)
        nodo.izquierda = izquierda
        nodo.derecha = derecha
        heapq.heappush(cola, nodo)
    return heapq.heappop(cola)

def generar_codigos(nodo, codigo_actual="", codigos=None):
    if codigos is None:
        codigos = {}
    if nodo is None:
        return codigos
    if nodo.byte is not None:
        codigos[nodo.byte] = codigo_actual
        return codigos
    generar_codigos(nodo.izquierda, codigo_actual + "0", codigos)
    generar_codigos(nodo.derecha, codigo_actual + "1", codigos)
    return codigos

def decodificar_bits(bits, arbol):
    resultado = bytearray()
    if arbol is None:
        return bytes(resultado)
    nodo = arbol
    for bit in bits:
        nodo = nodo.izquierda if bit == "0" else nodo.derecha
        if nodo.byte is not None:
            resultado.append(nodo.byte)
            nodo = arbol
    return bytes(resultado)

def serializar_tabla_frecuencias(freqs):
    items = list(freqs.items())
    n = len(items)
    out = bytearray()
    out += struct.pack(">I", n)
    for symbol, freq in items:
        out += struct.pack("B", symbol)
        out += struct.pack(">Q", freq)
    return bytes(out)

def deserializar_tabla_frecuencias(b):
    if not b:
        return {}
    offset = 0
    n = struct.unpack_from(">I", b, offset)[0]; offset += 4
    freqs = {}
    for _ in range(n):
        symbol = struct.unpack_from("B", b, offset)[0]; offset += 1
        freq = struct.unpack_from(">Q", b, offset)[0]; offset += 8
        freqs[symbol] = freq
    return freqs

# Compresion / Descompresion

def comprimir_bytes(datos, usar_prim=True):
    orden_mst_guardada = None
    datos_pre = datos
    if usar_prim:
        grafo, simbolos = construir_grafo(datos)
        mst = prim(grafo, simbolos)
        orden_mst = construir_orden_mst(mst, simbolos)
        datos_pre, orden_mst = aplicar_reasignacion_mst(datos, orden_mst)
        orden_mst_guardada = bytes(orden_mst)
    # Huffman
    arbol = construir_arbol_huffman_desde_datos(datos_pre)
    codigos = generar_codigos(arbol)
    datos_codificados = "".join(codigos[b] for b in datos_pre)
    relleno = (8 - len(datos_codificados) % 8) % 8
    datos_codificados += "0" * relleno
    datos_bytes = bytearray()
    for i in range(0, len(datos_codificados), 8):
        datos_bytes.append(int(datos_codificados[i:i+8], 2))
    # guardar tabla de frecuencias
    freqs = Counter(datos_pre)
    freq_bytes = serializar_tabla_frecuencias(freqs)
    return arbol, codigos, bytes(datos_bytes), relleno, orden_mst_guardada, freq_bytes

def decodificar_bytes_from_compressed(datos_bytes, relleno, freq_bytes, orden_mst_guardada):
    # reconstruir el arbol
    freqs = deserializar_tabla_frecuencias(freq_bytes)
    arbol = construir_arbol_huffman_desde_frecuencias(freqs)
    bits = "".join(f"{byte:08b}" for byte in datos_bytes)
    if relleno:
        bits = bits[:-relleno]
    datos_originales = decodificar_bits(bits, arbol)
    if orden_mst_guardada:
        orden_mst = list(orden_mst_guardada)
        datos_originales = revertir_reasignacion_mst(datos_originales, orden_mst)
    return datos_originales

# GUI

class App:
    def __init__(self, root):
        self.root = root

        # Inicializar pygame mixer para audio
        pygame.mixer.init()

        self.colors = {
            'bg': '#7f3667',
            'log_bg': '#a53e76',
            'btn_bg': '#bb437e',
            'btn_active': '#e44b8d',
            'fg': '#eec4dc',
            'slider': '#eec4dc'
        }
        
        self.font_main = ("Helvetica", 10)
        self.font_btn = ("Helvetica", 10, "bold")
        
        self.btn_style = {
            'bg': self.colors['btn_bg'],
            'fg': self.colors['fg'],
            'activebackground': self.colors['btn_active'],
            'activeforeground': self.colors['fg'],
            'relief': 'flat',
            'bd': 0,
            'padx': 10,
            'pady': 5,
            'font': self.font_btn
        }

        root.title("Compressor MP3 🤏")
        root.geometry("820x600") # Aumente altura para el slider
        root.configure(bg=self.colors['bg'])

        btn_frame = Frame(root, bg=self.colors['bg'])
        btn_frame.pack(padx=8, pady=8) 

        self.btn_select = Button(btn_frame, text="Seleccionar archivo", command=self.select_file, **self.btn_style) 
        self.btn_select.pack(side=LEFT, padx=6)

        self.btn_decompress = Button(btn_frame, text="Descomprimir", command=self.select_compressed_for_decompress, **self.btn_style)
        self.btn_decompress.pack(side=LEFT, padx=6)

        self.btn_show_codes = Button(btn_frame, text="Mostrar codigos", command=self.show_codes, **self.btn_style)
        self.btn_show_codes.pack(side=LEFT, padx=6)

        log_label = Label(root, text="Acciones / Estado:", bg=self.colors['bg'], fg=self.colors['fg'], font=self.font_main)
        log_label.pack(anchor="nw", padx=8)

        self.log = ScrolledText(root, height=20, bg=self.colors['log_bg'], fg=self.colors['fg'], relief='flat', bd=1, font=self.font_main, insertbackground=self.colors['fg'])
        self.log.pack(fill=BOTH, expand=True, padx=8, pady=(0,8))

        self.dynamic_frame = Frame(root, bg=self.colors['bg'])
        self.dynamic_frame.pack(fill="x", padx=8, pady=(0,8)) 
        
        # botones
        self.compressed_button = None
        self.decompressed_button = None
        
        # Botones de reproduccion y volumen
        self.btn_play = None
        self.btn_stop = None
        self.volume_slider = None
        self.lbl_vol = None

        self._log_queue = queue.Queue()
        self.root.after(100, self._poll_log_queue)

        self.current_codes = None
        self.current_compressed_path = None
        self.current_decompressed_path = None
        self.current_compressed_meta = None

        self.selected_compressed_for_decompress = None
        
        # Variables para logica de reproduccion
        self.temp_audio_path = None
        self.audio_source_path = None 

    def log_message(self, msg):
        self._log_queue.put(msg)

    def _poll_log_queue(self):
        try:
            while True:
                msg = self._log_queue.get_nowait()
                self.log.insert(END, msg + "\n")
                self.log.see(END)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_log_queue)

    # Seleccionar MP3 
    def select_file(self):
        path = filedialog.askopenfilename(title="Selecciona archivo .mp3", filetypes=[("MP3 files", "*.mp3"), ("All files","*.*")])
        if not path:
            return
        name = os.path.basename(path)
        self.log_message(f"Archivo seleccionado para comprimir: {name}")
        compressed_default = os.path.splitext(name)[0] + "_compressed.bin"
        self._limpiar_dynamic_frame()
        
        btn = Button(self.dynamic_frame, text=f"{compressed_default}  [DESCARGAR]", command=lambda p=path: self.start_compress(p), **self.btn_style)
        btn.pack(pady=4) 
        self.compressed_button = btn
        self.decompressed_button = None
        self.current_compressed_path = None
        self.current_compressed_meta = None
        self.current_codes = None
        
        self._reset_playback_state()

    def _limpiar_dynamic_frame(self):
        for w in self.dynamic_frame.winfo_children():
            w.destroy()
        self.compressed_button = None
        self.decompressed_button = None
        self.btn_play = None
        self.btn_stop = None
        self.volume_slider = None
        self.lbl_vol = None

    def _reset_playback_state(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            try:
                pygame.mixer.music.unload()
            except:
                pass
        
        # Asegurar borrar temporal si existe al cambiar de modo
        if self.temp_audio_path and os.path.exists(self.temp_audio_path):
            try:
                os.remove(self.temp_audio_path)
            except:
                pass
                
        self.temp_audio_path = None
        self.audio_source_path = None

    # Compresion 
    def start_compress(self, filepath):
        if self.compressed_button:
            self.compressed_button.config(state=DISABLED, text="Descargando...", bg=self.colors['log_bg'])
        self.log_message("Iniciando compresion (Prim + Huffman)...")
        t = threading.Thread(target=self._compress_thread, args=(filepath,), daemon=True)
        t.start()

    def _compress_thread(self, filepath):
        try:
            with open(filepath, "rb") as f:
                datos = f.read()
            self.log_message("Leyendo archivo completo...")
            arbol, codigos, datos_bytes, relleno, orden_mst_guardada, freq_bytes = comprimir_bytes(datos, usar_prim=True)
            base = os.path.splitext(os.path.basename(filepath))[0]
            compressed_name = base + "_compressed.bin"
            compressed_path = os.path.join(os.path.dirname(filepath), compressed_name)
            # Guardar con formato
            with open(compressed_path, "wb") as f:
                f.write(bytes([relleno]))
                f.write(struct.pack(">I", len(freq_bytes)))
                if freq_bytes:
                    f.write(freq_bytes)
                if orden_mst_guardada:
                    f.write(struct.pack(">I", len(orden_mst_guardada)))
                    f.write(orden_mst_guardada)
                else:
                    f.write(struct.pack(">I", 0))
                f.write(datos_bytes)
            self.current_codes = codigos
            self.current_compressed_path = compressed_path
            self.current_compressed_meta = {
                "relleno": relleno,
                "freq_bytes": freq_bytes,
                "order": orden_mst_guardada
            }
            self.log_message(f">> Archivo comprimido creado: {compressed_path}")
            self.root.after(0, lambda: self._update_compressed_button_after_success(compressed_name, compressed_path))
        except Exception as e:
            self.log_message(f"Error en compresion: {e}")
            if self.compressed_button:
                self.root.after(0, lambda: self.compressed_button.config(state=NORMAL, text="Error - Reintentar", **self.btn_style))

    def _update_compressed_button_after_success(self, label_name, src_path):
        if self.compressed_button:
            def do_save():
                default = label_name
                save_to = filedialog.asksaveasfilename(title="Guardar archivo comprimido", initialfile=default, defaultextension=os.path.splitext(default)[1])
                if save_to:
                    try:
                        shutil.copy(src_path, save_to)
                        self.log_message(f"Archivo comprimido guardado en: {save_to}")
                    except Exception as e:
                        self.log_message(f"Error al guardar comprimido: {e}")
            self.compressed_button.config(text=f"{label_name}  [DESCARGAR]", command=do_save, state=NORMAL, **self.btn_style)
        else:
            btn = Button(self.dynamic_frame, text=f"{label_name}  [DESCARGAR]", command=lambda: shutil.copy(src_path, filedialog.asksaveasfilename(initialfile=label_name)), **self.btn_style)
            btn.pack(pady=4) 
            self.compressed_button = btn

    # Seleccionar .bin para DESCOMPRIMIR
    def select_compressed_for_decompress(self):
        path = filedialog.askopenfilename(title="Selecciona archivo comprimido (.bin)", filetypes=[("BIN files", "*.bin"), ("All files","*.*")])
        if not path:
            return
        name = os.path.basename(path)
        self.log_message(f"Archivo comprimido seleccionado: {name}")
        decompressed_default = os.path.splitext(name)[0] + "_decompressed.mp3"
        
        self._limpiar_dynamic_frame()
        # Parar musica si habia otra
        self._reset_playback_state()
        
        # Boton Descargar
        btn = Button(self.dynamic_frame, text=f"{decompressed_default}  [DESCARGAR]", command=lambda p=path, n=decompressed_default: self.start_decompress_on_click(p, n), **self.btn_style)
        btn.pack(pady=4, side="top") 
        self.decompressed_button = btn
        
        self.btn_play = Button(self.dynamic_frame, text="▶ Reproducir Cancion", command=self.trigger_play_logic, **self.btn_style)
        self.btn_play.pack(pady=4, side="top")
        
        # Boton Detener 
        self.btn_stop = Button(self.dynamic_frame, text="⏹ Detener", command=self.stop_music, **self.btn_style)
        # No lo empaquetamos aun
        
        # barra de volumen
        self.lbl_vol = Label(self.dynamic_frame, text="Volumen:", bg=self.colors['bg'], fg=self.colors['fg'], font=self.font_main)
        self.lbl_vol.pack(pady=(8,0), side="top")
        
        self.volume_slider = Scale(self.dynamic_frame, from_=0, to=100, orient=HORIZONTAL, 
                                   command=self.set_volume, 
                                   bg=self.colors['bg'], fg=self.colors['fg'], 
                                   troughcolor=self.colors['btn_bg'], 
                                   highlightthickness=0, bd=0, length=200)
        self.volume_slider.set(50) # Volumen inicial
        self.volume_slider.pack(pady=0, side="top")
        
        self.selected_compressed_for_decompress = path

    def set_volume(self, val):
        # Pygame usa float de 0.0 a 1.0
        volume = int(val) / 100
        pygame.mixer.music.set_volume(volume)

    def trigger_play_logic(self):
        if (self.selected_compressed_for_decompress == self.audio_source_path 
            and self.temp_audio_path 
            and os.path.exists(self.temp_audio_path)):
            
            self.log_message("Cancion ya estaba descomprimida en cache. Reproduciendo...")
            self.play_music_file()
        else:
            #descomprimir en backend
            self.log_message("Descomprimiendo para reproducir (segundo plano)...")
            # Cambiar UI para indicar carga
            self.btn_play.config(state=DISABLED, text="Cargando...", bg=self.colors['log_bg'])
            
            t = threading.Thread(target=self._backend_decompress_for_play_thread, args=(self.selected_compressed_for_decompress,), daemon=True)
            t.start()

    def _backend_decompress_for_play_thread(self, compressed_path):
        try:
            # Logica de descompresion 
            with open(compressed_path, "rb") as f:
                relleno = f.read(1)[0]
                len_freq = struct.unpack(">I", f.read(4))[0]
                freq_bytes = f.read(len_freq) if len_freq > 0 else b""
                len_order = struct.unpack(">I", f.read(4))[0]
                order_bytes = f.read(len_order) if len_order > 0 else None
                payload = f.read()
            
            datos_originales = decodificar_bytes_from_compressed(payload, relleno, freq_bytes, order_bytes)
            
            # Guardar en archivo temporal 
            temp_filename = "_temp_playback.mp3"
            with open(temp_filename, "wb") as f:
                f.write(datos_originales)
                
            # Actualizar estado
            self.temp_audio_path = temp_filename
            self.audio_source_path = compressed_path
            
            # Llamar al play en el hilo principal
            self.root.after(0, self.play_music_file)
            
        except Exception as e:
            self.log_message(f"Error al procesar audio para reproducir: {e}")
            # Restaurar boton
            self.root.after(0, lambda: self.btn_play.config(state=NORMAL, text="▶ Reproducir Cancion", bg=self.colors['btn_bg']))

    def play_music_file(self):
        try:
            pygame.mixer.music.load(self.temp_audio_path)
            pygame.mixer.music.play()
            
            # Aplicar volumen actual del slider
            if self.volume_slider:
                curr_vol = self.volume_slider.get() / 100
                pygame.mixer.music.set_volume(curr_vol)
                
            self.log_message("Reproduciendo...")
            
            # Intercambiar botones
            self.btn_play.pack_forget()
            self.btn_play.config(state=NORMAL, text="▶ Reproducir Cancion", bg=self.colors['btn_bg']) 
            self.btn_stop.pack(pady=4, side="top", before=self.lbl_vol) # Mostrar antes del volumen
            
        except Exception as e:
            self.log_message(f"Error al intentar reproducir con pygame: {e}")
            self.btn_play.config(state=NORMAL, text="▶ Reproducir Cancion", bg=self.colors['btn_bg'])

    def stop_music(self):
        pygame.mixer.music.stop()
        try:
            pygame.mixer.music.unload()
        except AttributeError:
            pass 
        
        # Borrar el archivo temporal inmediatamente
        if self.temp_audio_path and os.path.exists(self.temp_audio_path):
            try:
                os.remove(self.temp_audio_path)
                self.log_message("Reproduccion detenida y archivo temporal eliminado.")
            except Exception as e:
                self.log_message(f"Se detuvo, pero hubo error al borrar temp: {e}")
        else:
            self.log_message("Reproduccion detenida.")

        # Resetear rutas para forzar descompresion la proxima vez
        self.temp_audio_path = None
        
        # Intercambiar botones
        self.btn_stop.pack_forget()
        self.btn_play.pack(pady=4, side="top", before=self.lbl_vol)

    def start_decompress_on_click(self, compressed_path, decompressed_default_name):
        if self.decompressed_button:
            self.decompressed_button.config(state=DISABLED, text="Descargando...", bg=self.colors['log_bg'])
        self.log_message("Se inicio la descompresion (cuando el usuario lo solicito).")
        t = threading.Thread(target=self._decompress_thread, args=(compressed_path, decompressed_default_name), daemon=True)
        t.start()

    def _decompress_thread(self, compressed_path, decompressed_default_name):
        try:
            with open(compressed_path, "rb") as f:
                relleno = f.read(1)[0]
                len_freq = struct.unpack(">I", f.read(4))[0]
                freq_bytes = f.read(len_freq) if len_freq > 0 else b""
                len_order = struct.unpack(">I", f.read(4))[0]
                order_bytes = f.read(len_order) if len_order > 0 else None
                payload = f.read()
            self.log_message("Metadatos leidos: reconstruyendo Huffman usando la tabla de frecuencias almacenada...")
            datos_originales = decodificar_bytes_from_compressed(payload, relleno, freq_bytes, order_bytes)
            # Guardar resultado
            decompressed_name = decompressed_default_name
            decompressed_path = os.path.join(os.path.dirname(compressed_path), decompressed_name)
            with open(decompressed_path, "wb") as f:
                f.write(datos_originales)
            self.current_decompressed_path = decompressed_path
            self.log_message(f">> Archivo descomprimido creado: {decompressed_path}")
            self.root.after(0, lambda: self._update_decompressed_button_after_success(decompressed_name, decompressed_path))
        except Exception as e:
            self.log_message(f"Error en descompresion: {e}")
            if self.decompressed_button:
                self.root.after(0, lambda: self.decompressed_button.config(state=NORMAL, text="Error - Reintentar", **self.btn_style))

    def _update_decompressed_button_after_success(self, label_name, src_path):
        if self.decompressed_button:
            def do_save():
                default = label_name
                save_to = filedialog.asksaveasfilename(title="Guardar archivo descomprimido", initialfile=default, defaultextension=os.path.splitext(default)[1])
                if save_to:
                    try:
                        shutil.copy(src_path, save_to)
                        self.log_message(f"Archivo descomprimido guardado en: {save_to}")
                    except Exception as e:
                        self.log_message(f"Error al guardar descomprimido: {e}")
            self.decompressed_button.config(text=f"{label_name}  [DESCARGAR]", command=do_save, state=NORMAL, **self.btn_style)

    #  Mostrar codigos 
    def show_codes(self):
        if not self.current_codes:
            self.log_message("No hay codigos disponibles. Comprime un archivo primero.")
            return
        top = Toplevel(self.root)
        top.title("Codigos Huffman (byte -> codigo)")
        top.geometry("400x500")
        top.configure(bg=self.colors['bg'])
        
        txt = ScrolledText(top, width=80, height=30, bg=self.colors['log_bg'], fg=self.colors['fg'], relief='flat', bd=0, font=self.font_main, insertbackground=self.colors['fg'])
        txt.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        for b, code in sorted(self.current_codes.items(), key=lambda x: x[0]):
            txt.insert(END, f"{b} -> {code}\n")
        txt.configure(state="disabled")

def main():
    root = Tk()
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main()