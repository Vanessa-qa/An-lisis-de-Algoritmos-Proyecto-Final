# ReadMe de Recomendador de Builds (Steam)

La aplicación es un **recomendador de builds** para juegos en Steam desarrollado con **PySide6**. Permite buscar un juego por nombre usando la API publica de Steam, obtener sus requisitos mínimos y recomendados, y sugerir una combinación de CPU, GPU y RAM acorde al **presupuesto** ingresado. La interfaz muestra la imagen del juego, las plataformas compatibles (íconos SVG) y un resumen con la build recomendada.

## Funcionamiento
- Ingresar el **nombre del juego** y el **presupuesto (MXN)** en los campos correspondientes.  
- Pulsar **Buscar Juego**: la aplicación consulta la API de Steam (funciones `LocalizarJuego()` y `ObtenerDetalles()`), limpia y extrae la información relevante (`LimpiarHTML()` y `ObtenerRequisitos()`).  
- Mientras se realiza la consulta, el trabajo se ejecuta en un hilo separado (`Worker(QThread)`) para no bloquear la GUI.  
- Cuando la búsqueda termina se muestra: imagen del juego, plataformas (Windows / Mac / Linux), requisitos y la **Build sugerida** calculada por la función `Build()` a partir de una lista de componentes simulados.  
- La interfaz usa estilos QSS personalizados (tema oscuro con acentos neón) y presenta los resultados en un área desplazable.

## Requisitos
- **Python 3.x**  
- Conexión a internet para consultar la API de Steam y descargar imágenes.

## Librerías externas usadas
- **PySide6**: creación de la GUI y manejo de señales/slots (QThread, widgets, layouts).  
- **requests**: llamadas HTTP a la API de Steam y descarga de imágenes.  
- **re** (estándar): extracción y parseo de texto (requisitos).  
- **io**, **sys** (estándar): utilidades generales.  

## Notas importantes
- La base de componentes (CPUs, GPUs y precios de RAM) es simulada dentro del código (función `CargarComponentes()`), por lo que los precios y puntuaciones son aproximados y se usan solo para la lógica de recomendación.  
- Si la API no devuelve requisitos o imagen, la aplicación maneja el caso mostrando un mensaje de error o continuando sin la imagen.  
- Para evitar bloqueos de la GUI, todas las operaciones de red y cálculo se realizan en `Worker` y sus resultados se devuelven mediante señales (`result_ready`, `image_ready`, `error`).

## Cómo ejecutar
1. Instalar dependencias:
```bash
pip install PySide6 requests