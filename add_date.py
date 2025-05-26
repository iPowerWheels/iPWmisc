import os
from PIL import Image, ImageDraw, ImageFont
import piexif
from datetime import datetime

# --- Configuración ---

# Directorio donde están tus fotos originales
# ¡Crea este directorio y coloca tus fotos dentro antes de ejecutar el script!
INPUT_DIR = '/Users/danielmendoza/Downloads/input_photos'

# Directorio donde se guardarán las fotos procesadas con el texto
# El script creará este directorio si no existe
OUTPUT_DIR = '/Users/danielmendoza/Downloads/output_photos_with_text'

# Extensiones de archivo de imagen a procesar (puedes añadir más si es necesario)
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']

# Formato de la fecha y hora que se mostrará en la imagen
# %Y: Año (ej: 2023), %m: Mes (01-12), %d: Día (01-31)
# %H: Hora (00-23), %M: Minutos (00-59), %S: Segundos (00-59)
# Puedes modificar el formato si lo deseas (ej: "%d/%m/%Y %H:%M")
DATE_FORMAT = "%Y:%m:%d %H:%M:%S"

# --- Apariencia del Texto ---

# Color del texto (R, G, B) - Blanco en este caso
TEXT_COLOR = (243, 206, 50)

# Color del contorno del texto (para mejor legibilidad en fondos variables) - Negro
OUTLINE_COLOR = (0, 0, 0)
TEXT_OUTLINE_WIDTH = 1 # Grosor del contorno en píxeles

# Tamaño de la fuente. Ajusta según la resolución de tus fotos.
FONT_SIZE = 100

# Ruta al archivo de fuente (.ttf).
# Intenta usar una fuente común del sistema. Si no se encuentra, se usará una fuente por defecto de PIL (menos estética).
# Puedes cambiar esta ruta a la de una fuente específica que tengas.
FONT_PATH = None # Inicialmente None, intentaremos encontrar una fuente.
try:
    # Intentar rutas comunes en Windows
    #if os.path.exists("C:/Windows/Fonts/arial.ttf"):
    #    FONT_PATH = "C:/Windows/Fonts/arial.ttf"
    #elif os.path.exists("C:/Windows/Fonts/msgothic.ttc"): # Otra fuente común en Windows
    #     FONT_PATH = "C:/Windows/Fonts/msgothic.ttc"
    # Puedes añadir rutas comunes para macOS o Linux aquí
    if os.path.exists("/Users/danielmendoza/Library/Fonts/LiberationSans-Regular.ttf"):
        FONT_PATH = "/Users/danielmendoza/Library/Fonts/LiberationSans-Regular.ttf"
    elif os.path.exists("/Users/danielmendoza/Library/Fonts/DejaVuSans.ttf"):
        FONT_PATH = "/Users/danielmendoza/Library/Fonts/DejaVuSans.ttf"
    # Si no se encuentra ninguna de las anteriores, FONT_PATH seguirá siendo None
except Exception as e:
    print(f"Error al buscar fuentes comunes: {e}")
    FONT_PATH = None # Asegurarse de que es None en caso de error

if FONT_PATH:
    try:
        # Verificar si la fuente se puede cargar
        ImageFont.truetype(FONT_PATH, FONT_SIZE)
        # Si llega aquí, la fuente se puede usar
    except IOError:
        print(f"Advertencia: La fuente '{FONT_PATH}' no se pudo cargar. Usando fuente por defecto de PIL (podría verse diferente).")
        FONT_PATH = None # Usar fuente por defecto si la especificada falla

# Posición del texto en la imagen (esquina inferior izquierda)
PADDING = 100 # Píxeles de margen desde los bordes

# --- Funciones ---

def get_date_from_exif(image_path):
    """
    Extrae la fecha y hora de los metadatos EXIF de una imagen.
    Retorna un objeto datetime o None si no se encuentra la información.
    """
    try:
        img = Image.open(image_path)
        exif_data = None
        if 'exif' in img.info:
            exif_data = piexif.load(img.info['exif'])

        date_str = None
        if exif_data:
            # Priorizar DateTimeOriginal (fecha y hora de toma de la foto)
            if piexif.ExifIFD.DateTimeOriginal in exif_data.get("Exif", {}):
                date_bytes = exif_data["Exif"][piexif.ExifIFD.DateTimeOriginal]
                date_str = date_bytes.decode('utf-8')
            # Fallback a DateTime (fecha y hora de modificación de los datos de la imagen)
            elif piexif.ImageIFD.DateTime in exif_data.get("0th", {}):
                 date_bytes = exif_data["0th"][piexif.ImageIFD.DateTime]
                 date_str = date_bytes.decode('utf-8')

        if date_str:
            # El formato EXIF es YYYY:MM:DD HH:MM:SS
            # Intentamos parsear esta cadena a un objeto datetime
            try:
                # Manejar posibles espacios nulos al final que algunos dispositivos añaden
                date_str = date_str.strip('\x00')
                dt_object = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                return dt_object
            except ValueError:
                print(f"Advertencia: Formato de fecha EXIF inesperado para {os.path.basename(image_path)}: '{date_str}'.")
                return None # No pudimos parsear la fecha

    except Exception as e:
        #print(f"Error al leer EXIF de {os.path.basename(image_path)}: {e}") # Descomentar para depurar
        return None

def add_text_to_photo(input_path, output_path, text):
    """
    Abre una imagen, añade texto con contorno y la guarda.
    """
    try:
        img = Image.open(input_path).convert("RGB") # Convertir a RGB para evitar problemas de paletas/transparencia
        draw = ImageDraw.Draw(img)

        # Cargar fuente o usar la por defecto
        font = None
        if FONT_PATH:
             try:
                font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
             except IOError:
                 # Si la fuente especificada falla (aunque ya lo verificamos antes),
                 # caemos a la por defecto. Esto no debería pasar si la verificación inicial funciona.
                 pass
        # Si FONT_PATH es None o la carga falla, usar la fuente por defecto
        if font is None:
            print(f"Usando fuente por defecto de PIL para {os.path.basename(input_path)}.")
            font = ImageFont.load_default()
            # Nota: la fuente por defecto es muy pequeña, el FONT_SIZE no le afecta.
            # Podrías dibujar el texto varias veces para "simular" una fuente más grande,
            # pero es más complejo. Usar una fuente .ttf es muy recomendable.

        # Obtener el tamaño del texto para calcular la posición
        # textbbox es más preciso (requiere Pillow 8.0+)
        try:
            # left, top, right, bottom
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
        except AttributeError:
            # Fallback para versiones antiguas de Pillow: estimación menos precisa
            print("Advertencia: textbbox no disponible. Usando estimación de tamaño de texto (Pillow < 8.0).")
            try:
                 text_width = draw.textlength(text, font=font) # Pillow 8.0+
                 text_height = font.getbbox(text)[3] - font.getbbox(text)[1] # Altura aproximada
            except AttributeError:
                 # Versiones muy antiguas podrían solo tener textsize
                 text_width, text_height = draw.textsize(text, font=font)


        # Calcular la posición (esquina inferior izquierda)
        x_pos = PADDING
        y_pos = img.height - text_height - PADDING

        # Dibujar contorno (dibujar el texto varias veces ligeramente desplazado)
        for dx in range(-TEXT_OUTLINE_WIDTH, TEXT_OUTLINE_WIDTH + 1):
            for dy in range(-TEXT_OUTLINE_WIDTH, TEXT_OUTLINE_WIDTH + 1):
                if dx != 0 or dy != 0: # No dibujar el contorno en la posición central
                     draw.text((x_pos + dx, y_pos + dy), text, fill=OUTLINE_COLOR, font=font)

        # Dibujar el texto principal
        draw.text((x_pos, y_pos), text, fill=TEXT_COLOR, font=font)

        # Asegurarse de que el directorio de salida existe
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Guardar la imagen modificada
        # Si la entrada es JPG, intentamos guardar como JPG. PNG como PNG, etc.
        # La calidad 95 es alta para JPG.
        if input_path.lower().endswith(('.jpg', '.jpeg')):
             img.save(output_path, format='JPEG', quality=95)
        elif input_path.lower().endswith('.png'):
             img.save(output_path, format='PNG')
        else:
             # Para otros formatos, guardar como PNG por defecto
             print(f"Guardando {os.path.basename(input_path)} como PNG.")
             img.save(output_path, format='PNG')


        print(f"Procesado: {os.path.basename(input_path)} -> {os.path.basename(output_path)} con texto '{text}'")

    except FileNotFoundError:
         print(f"Error: Archivo no encontrado - {input_path}")
    except Exception as e:
        print(f"Error procesando {os.path.basename(input_path)}: {e}")


# --- Ejecución Principal ---

if __name__ == "__main__":
    # Crear el directorio de salida si no existe
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Buscando imágenes en: {INPUT_DIR}")
    print(f"Guardando imágenes procesadas en: {OUTPUT_DIR}")

    processed_count = 0
    skipped_count = 0
    no_exif_count = 0

    # Iterar a través de los archivos en el directorio de entrada
    for filename in os.listdir(INPUT_DIR):
        input_filepath = os.path.join(INPUT_DIR, filename)
        output_filepath = os.path.join(OUTPUT_DIR, filename) # Usar el mismo nombre en la salida

        # Verificar si es un archivo y tiene una extensión de imagen soportada
        if os.path.isfile(input_filepath) and os.path.splitext(filename)[1].lower() in IMAGE_EXTENSIONS:
            date_obj = get_date_from_exif(input_filepath)

            if date_obj:
                display_text = date_obj.strftime(DATE_FORMAT)
                add_text_to_photo(input_filepath, output_filepath, display_text)
                processed_count += 1
            else:
                print(f"Omitido: {filename} - No se encontró fecha/hora en metadatos EXIF.")
                no_exif_count += 1
                # Opcionalmente, puedes copiar el archivo original al directorio de salida:
                # import shutil
                # shutil.copy2(input_filepath, output_filepath)
                # print(f"Copiado original: {os.path.basename(input_filepath)}")

        elif os.path.isfile(input_filepath):
            print(f"Omitido: {filename} - No es un formato de imagen soportado.")
            skipped_count += 1
        # Ignorar directorios o archivos no reconocidos

    print("\n--- Resumen ---")
    print(f"Total de archivos encontrados en el directorio de entrada: {len(os.listdir(INPUT_DIR))}")
    print(f"Imágenes procesadas con texto: {processed_count}")
    print(f"Imágenes omitidas (sin metadatos EXIF): {no_exif_count}")
    print(f"Archivos omitidos (no son imágenes soportadas): {skipped_count}")
    print(f"Las imágenes procesadas se guardaron en '{OUTPUT_DIR}'")
    print("Por favor, revisa el directorio de salida para ver los resultados.")
