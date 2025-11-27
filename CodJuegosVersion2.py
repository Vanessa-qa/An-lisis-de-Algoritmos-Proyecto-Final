from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox, QSizePolicy)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import requests
import re
import sys
from io import BytesIO

def LimpiarHTML(texto_html): #Funcion que elimina las etiquetas HTML
    # Reemplaza etiquetas de lista <li> por un guion y un salto de linea para formatear
    texto = texto_html.replace('<li>', '\n- ').replace('<br>', '\n')
    # Usa una expresion regular para encontrar y eliminar cualquier otra etiqueta HTML (<...>)
    limpio = re.sub(r'<.*?>', '', texto)
    # Elimina espacios o lineas en blanco al inicio y al final
    return limpio.strip()

def LocalizarJuego(nombre): #Funcion para buscar los juegos, pasamos el parametro
    url = "https://store.steampowered.com/api/storesearch/" #Api de steam que nos permite obtener informacion de los juegos 
    parametros = {"term": nombre, "cc": "mx", "l": "spanish"} #parametros a utilizar, term es lo que inserta el ususario, cc - es la region, y l es el idioma de la respuesta
    #request pide los datos a un servidor, en este caso a la "url" que le pasamos que seria el api de steam definida previamente
    r = requests.get(url, params=parametros, timeout=10) #esto convierte la url a algo como (url)../?term=Portal&cc=mx&l=spanish 
    data = r.json() #esto convierte la respuesta a un formato JSON aceptable para python
    if data.get("total", 0) == 0: #Si el resultado indica que no encontro ningun juego
        return None #devuelve None
    item = data["items"][0] #En caso de encotnrar el juego
    return {"appid": item["id"], "name": item["name"]} #regresa  el "id" que steam usa para identificar el juego y el nombre(name)

def ObtenerDetalles(appid): #funcion para obtener los detalles mediante el id del juego
    url = f"https://store.steampowered.com/api/appdetails/" #Api de steam que permite obtener detalles de un juego
    parametros = {"appids": appid, "cc": "mx", "l": "spanish"} #los parametros a utilizar son el id del juego, region, y lenguaje (esp)
    r = requests.get(url, params= parametros, timeout=10) #le pide los datos al servidor especificado 
    data = r.json() #convierte los datos a formato json

    if not data.get(str(appid), {}).get("success", False): #si la api no da detalles
        return None  #regresa none
      
    detalles = data[str(appid)]["data"] #obtiene la informacion del juego del json
    nombre = detalles.get("name", "Desconocido") #obtiene el nombre del juego de detalles
    precio = detalles.get("price_overview", {}) #obtiene el precio del juego si no existe retorna un diccionario vacio
    if precio: #si existe
        precio_str = f'{precio.get("final_formatted", "desconocido")}' #extrae el precio en formato con moneda y si no existe imprime "desconocido"
    else: #si no hay informacion del precio
        precio_str = "Gratis / no disponible" #imprime que el juego es gratis o no se encontro el precio
    
    plataformas = detalles.get("platforms", {}) #obtiene la informacion de las plataformas para las que esta disponible
    plataformas_str = ", ".join([k for k,v in plataformas.items() if v]) #convierte el directorio en una cadena separada por comas

    requisitos_min_html = detalles.get("pc_requirements", {}).get("minimum", "no disponible") #obtiene de detalles los requisitos minimos a traves de <pc_requirements>
    requisitos_rec_html = detalles.get("pc_requirements", {}).get("recommended", "No disponible") #obtiene de detalles los requisitos recomendados a traves de <pc_requirements>

    cpu_min, gpu_min, ram_min = ObtenerRequisitos(requisitos_min_html) #extrae cpu, gpu y ram de los requisitos minimos
    cpu_rec, gpu_rec, ram_rec = ObtenerRequisitos(requisitos_rec_html) #extrae cpu, gpu y ram de los requisitos recomendados

    imagen_url = detalles.get("header_image", None)

    return { #devuelve un directorio con toda la informacion que se va a necesitar
        "nombre": nombre,
        "precio": precio_str,
        "plataformas": plataformas_str,
        "requisitos_minimos": LimpiarHTML(requisitos_min_html),
        "requisitos_recomentados": LimpiarHTML(requisitos_rec_html),
        "cpu_min": cpu_min,
        "gpu_min": gpu_min,
        "ram_min": ram_min,
        "cpu_rec": cpu_rec,
        "gpu_rec": gpu_rec,
        "ram_rec": ram_rec,
        "header_image": imagen_url
    }

def ObtenerRequisitos(texto): #funcion para obtener el gpu, cpu y ram de un juego
    cpu = None
    gpu = None
    ram = None
    
    if texto != "no disponible" and texto != "No disponible": #si hay texto de requisitos 
        cpu_match = re.search(r"CPU:\s*([^\n]+)", texto) #Busca la linea que contiene la CPU y extrae su nombre
        gpu_match = re.search(r"(?:GPU|Tarjeta grafica|Graphics):\s*([^\n]+)", texto) #Busca la linea que contiene la GPU y extrae su nombre
        ram_match = re.search(r"RAM:\s*([^\n]+)", texto) #Busca la linea que contiene la RAM y extrae la cantidad
        if cpu_match:
            cpu = cpu_match.group(1).strip() #Si encontro CPU, guarda el texto limpio sin espacios 
        if gpu_match:
            gpu = gpu_match.group(1).strip() #Si encontro GPU, guarda el texto
        if ram_match:
            ram = ram_match.group(1).strip() #Si encontro RAM, guarda el texto 
    return cpu, gpu, ram #regresa los daatos obtenidos

def CargarComponentes(): #devuelve listas de cpus, gpus y precios para ram en MXN
    # cada componente: nombre, benchmark (score), precio_mxn
    cpus = [
        {"name":"Intel Core i5-2500","score":5200,"price":1200},
        {"name":"Intel Core i7-6700","score":8400,"price":2500},
        {"name":"AMD Ryzen 5 3600","score":13000,"price":4000},
        {"name":"AMD Ryzen 5 5600","score":18000,"price":6000},
        {"name":"Intel Core i5-10400","score":11000,"price":2200}
    ]
    gpus = [
        {"name":"NVIDIA GeForce GTX 970","score":6700,"price":2000},
        {"name":"NVIDIA GeForce GTX 1060","score":8000,"price":3200},
        {"name":"NVIDIA GeForce RTX 2060","score":15000,"price":5000},
        {"name":"NVIDIA GeForce RTX 3060","score":22000,"price":9000},
        {"name":"NVIDIA GeForce GTX 1650","score":6000,"price":2200}
    ]
    ram_options = {8:800, 16:1500, 32:3000} #precio aproximado en MXN
    return cpus, gpus, ram_options

def BuscarComponentes(lista, nombre): #busca componente por coincidencia simple
    if not nombre:
        return None
    nombre_l = nombre.lower()
    mejores = []
    for c in lista:
        n = c["name"].lower()
        if nombre_l in n or n in nombre_l: #coincidencia por substring
            mejores.append(c)
    if mejores:
        # elegir el de mayor score entre coincidencias
        mejores.sort(key=lambda x: x["score"], reverse=True)
        return mejores[0]
    return None

def Build(presupuesto, cpu_req_name, gpu_req_name):
    cpus, gpus, ram_options = CargarComponentes() # carga las listas de CPUs, GPUs y las opciones de RAM disponibles
    cpu_obj = BuscarComponentes(cpus, cpu_req_name) # busca la CPU que mejor coincide con el requisito extraido del juego
    gpu_obj = BuscarComponentes(gpus, gpu_req_name) # busca la GPU que mejor coincide con el requisito extraido del juego
    cpu_target = cpu_obj["score"] if cpu_obj else 0 # obtiene el score objetivo de la CPU si se encontro coincidencia, si no 0
    gpu_target = gpu_obj["score"] if gpu_obj else 0 # obtiene el score objetivo de la GPU si se encontro coincidencia, si no 0

    gpu_ram_combos = [] # inicializa la lista para almacenar combinaciones parciales GPU+RAM con su precio y puntuacion parcial
    for gpu in gpus: # itera cada GPU disponible
        for ram_size, ram_price in ram_options.items(): # itera cada opcion de RAM (tamaño y precio)
            price = gpu["price"] + ram_price # calcula el precio combinado de GPU + RAM
            partial_score = (0.6 * gpu["score"]) + (0.1 * (ram_size * 1000)) # calcula la puntuacion parcial ponderando GPU y RAM
            gpu_ram_combos.append({"gpu": gpu, "ram_size": ram_size, "ram_price": ram_price, "price": price, "partial_score": partial_score}) # añade la combinacion parcial a la lista

    # ordenar por precio para poder hacer busquedas rapidas por presupuesto
    gpu_ram_combos.sort(key=lambda x: x["price"]) # ordena las combinaciones parciales por precio ascendente

    # construir arreglo de "mejor hasta aqui" para obtener la mejor combinacion parcial por cualquier tope de precio
    prefix_best = [] # inicializa una lista para guardar la mejor combinacion parcial hasta cada indice de precio
    best_combo = None # variable que guardara la mejor combinacion parcial encontrada hasta ahora
    for combo in gpu_ram_combos: # itera sobre combinaciones parciales ordenadas por precio
        if best_combo is None or combo["partial_score"] > best_combo["partial_score"]: # si la combinacion actual mejora la mejor parcial, actualiza
            best_combo = combo # actualiza la mejor combinacion parcial
        prefix_best.append(best_combo) # guarda la mejor combinacion hasta este precio en prefix_best

    import bisect # importa bisect para realizar busqueda binaria en la lista de precios

    mejores = None # variable para almacenar la mejor build encontrada
    mejor_val = -1 # valor de referencia para comparar metricas (mejor mayor que esto)

    # Para cada CPU, busco la mejor combinacion de GPU+RAM que quepa en el presupuesto restante usando busqueda binaria
    prices = [c["price"] for c in gpu_ram_combos] # lista de precios de las combinaciones GPU+RAM para busqueda binaria
    for cpu in cpus: # itera cada CPU disponible
        remaining = presupuesto - cpu["price"] # calcula el presupuesto restante despues de elegir la CPU
        if remaining < 0: # si la CPU sola supera el presupuesto, omite esta CPU
            continue
        # encontrar indice maximo con precio <= remaining
        idx = bisect.bisect_right(prices, remaining) - 1 # encuentra el indice maximo de combinacion GPU+RAM cuyo precio <= presupuesto restante
        if idx >= 0:
            best_partial = prefix_best[idx] # selecciona la mejor combinacion parcial que entra en el presupuesto restante
            total_price = cpu["price"] + best_partial["price"] # calcula el precio total de la build (CPU + GPU+RAM)
            score = (0.3 * cpu["score"]) + best_partial["partial_score"] # calcula la puntuacion total ponderando CPU y la parcial de GPU+RAM
            val = score / max(1, total_price) # normaliza la puntuacion por el precio para obtener calidad/precio
            cumple_objetivo = (cpu["score"] >= cpu_target) and (best_partial["gpu"]["score"] >= gpu_target) # comprueba si CPU y GPU alcanzan los scores objetivos
            if cumple_objetivo: # si la build cumple los requisitos recomendados, aplicar bonificacion
                val *= 1.15
            if val > mejor_val: # si la metrica es mejor que la mejor registrada, actualiza la mejor build
                mejor_val = val
                mejores = {"cpu": cpu, "gpu": best_partial["gpu"], "ram": {"size": best_partial["ram_size"], "price": best_partial["ram_price"]}, "total": total_price} # guarda la build actual como la mejor encontrada

    # fallback si no entra en presupuesto, devolver la mas barata posible
    if not mejores:
        cpu_choice = min(cpus, key=lambda x: x["price"]) if cpus else None
        gpu_choice = min(gpus, key=lambda x: x["price"]) if gpus else None
        ram_size, ram_price = min(ram_options.items(), key=lambda x: x[1])
        ram_choice = {"size": ram_size, "price": ram_price}
        total_price = (cpu_choice["price"] if cpu_choice else 0) + (gpu_choice["price"] if gpu_choice else 0) + ram_choice["price"]
        mejores = {"cpu": cpu_choice, "gpu": gpu_choice, "ram": ram_choice, "total": total_price}

    return mejores # devuelve la mejor build encontrada (o el fallback si no hay combinaciones dentro del presupuesto)

def GUI():
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle("Buscador de Juegos Steam")
    window.setMinimumSize(600, 500)

    # Estilo oscuro basico
    dark_style = """
        QWidget {
            background-color: #121212;
            color: #eeeeee;
            font-family: Arial, sans-serif;
            font-size: 14px;
        }
        QLineEdit, QPushButton {
            background-color: #1e1e1e;
            border: 1px solid #333;
            border-radius: 4px;
            padding: 6px;
            color: #eeeeee;
        }
        QPushButton:hover {
            background-color: #333333;
        }
        QLabel#titleLabel {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #76c7c0;
        }
        QLabel#subtitleLabel {
            font-size: 16px;
            font-weight: bold;
            margin-top: 15px;
            color: #a0a0a0;
        }
    """
    window.setStyleSheet(dark_style)

    main_layout = QVBoxLayout()

    title_label = QLabel("Buscador de Juegos Steam")
    title_label.setObjectName("titleLabel")
    title_label.setAlignment(Qt.AlignCenter)
    main_layout.addWidget(title_label)

    # Input para nombre y presupuesto
    form_layout = QHBoxLayout()

    left_form = QVBoxLayout()
    label_nombre = QLabel("Nombre del juego:")
    input_nombre = QLineEdit()
    left_form.addWidget(label_nombre)
    left_form.addWidget(input_nombre)

    label_presupuesto = QLabel("Presupuesto en MXN:")
    input_presupuesto = QLineEdit()
    left_form.addWidget(label_presupuesto)
    left_form.addWidget(input_presupuesto)

    boton_buscar = QPushButton("Buscar")
    left_form.addWidget(boton_buscar)

    form_layout.addLayout(left_form)

    # Lugar para mostrar la imagen del juego
    img_label = QLabel()
    img_label.setAlignment(Qt.AlignCenter)
    img_label.setFixedSize(200, 280)
    img_label.setStyleSheet("border: 1px solid #444; background-color: #222;")
    img_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    form_layout.addWidget(img_label)

    main_layout.addLayout(form_layout)

    # Label para resultados de texto (scroll si quieres puedes agregarlo)
    resultado_label = QLabel()
    resultado_label.setWordWrap(True)
    resultado_label.setStyleSheet("background-color: #1e1e1e; padding: 10px; border-radius: 6px;")
    main_layout.addWidget(resultado_label)

    def on_buscar():
        resultado_label.clear()
        img_label.clear()

        nombre = input_nombre.text().strip()
        pres_text = input_presupuesto.text().strip()
        try:
            presupuesto = int(float(pres_text))
        except:
            presupuesto = 6000

        res = LocalizarJuego(nombre)
        if not res:
            QMessageBox.information(window, "Resultado", "No se encontro el juego ( ´⌒`)")
            return

        detalles = ObtenerDetalles(res["appid"])
        if not detalles:
            QMessageBox.information(window, "Resultado", "No se pudieron obtener los detalles del juego.")
            return

        resultado = Build(presupuesto, detalles["cpu_rec"], detalles["gpu_rec"])

        texto = f"<b>Juego:</b> {res['name']}<br>"
        texto += f"<b>Precio:</b> {detalles['precio']}<br>"
        texto += f"<b>Plataformas:</b> {detalles['plataformas']}<br><br>"

        texto += "<b>Requisitos Minimos:</b><br>" + detalles["requisitos_minimos"].replace('\n', '<br>') + "<br>"
        texto += f"CPU minimo: {detalles['cpu_min'] or 'No disponible'}<br>"
        texto += f"GPU minimo: {detalles['gpu_min'] or 'No disponible'}<br>"
        texto += f"RAM minimo: {detalles['ram_min'] or 'No disponible'}<br><br>"

        texto += "<b>Requisitos Recomendados:</b><br>" + detalles["requisitos_recomentados"].replace('\n', '<br>') + "<br>"
        texto += f"CPU recomendada: {detalles['cpu_rec'] or 'No disponible'}<br>"
        texto += f"GPU recomendada: {detalles['gpu_rec'] or 'No disponible'}<br>"
        texto += f"RAM recomendada: {detalles['ram_rec'] or 'No disponible'}<br><br>"

        texto += f"<b>Build sugerida (MXN):</b> {presupuesto}<br>"
        texto += "<b>=====- Recomendacion -=====</b><br>"
        texto += f"GPU: {resultado['gpu']['name'] if resultado['gpu'] else 'No disponible'} | Precio MXN: {resultado['gpu']['price'] if resultado['gpu'] else 'N/A'}<br>"
        texto += f"CPU: {resultado['cpu']['name'] if resultado['cpu'] else 'No disponible'} | Precio MXN: {resultado['cpu']['price'] if resultado['cpu'] else 'N/A'}<br>"
        texto += f"RAM: {resultado['ram']['size']}GB | Precio MXN: {resultado['ram']['price']}<br>"
        texto += f"<b>Precio total aprox MXN:</b> {resultado['total']}"

        resultado_label.setText(texto)

        # Intentar obtener la imagen del juego
        try:
            # Los detalles traen a veces "header_image"
            img_url = detalles.get("header_image", None)
            if img_url:
                response = requests.get(img_url)
                img_data = response.content
                pixmap = QPixmap()
                pixmap.loadFromData(img_data)
                pixmap = pixmap.scaled(img_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_label.setPixmap(pixmap)
            else:
                img_label.setText("No hay imagen")
        except Exception as e:
            img_label.setText("Error cargando imagen")

    boton_buscar.clicked.connect(on_buscar)

    window.setLayout(main_layout)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    GUI()