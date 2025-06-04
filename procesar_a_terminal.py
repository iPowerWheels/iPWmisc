import sys
import xml.etree.ElementTree as ET
import os

def extraer_total_y_uuid(xml_path):
    """
    Extrae el Total y el UUID de un archivo XML.
    Retorna una tupla (Total, UUID) si los encuentra, de lo contrario (None, None).
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        total = None
        uuid = None

        # Buscar atributo 'Total' en cualquier etiqueta (como en tu script original)
        for elem in root.iter():
            if 'Total' in elem.attrib:
                total = elem.attrib['Total']
                break  # Solo queremos el primero que encontremos

        # Buscar UUID en cualquier etiqueta
        for elem in root.iter():
            if 'UUID' in elem.attrib:
                uuid = elem.attrib['UUID']
                break  # También solo el primero
        
        return total, uuid

    except FileNotFoundError:
        print(f"Error: Archivo no encontrado: {os.path.basename(xml_path)}")
        return None, None
    except ET.ParseError as e:
        print(f"Error al parsear el XML '{os.path.basename(xml_path)}': {e}")
        return None, None
    except Exception as e:
        print(f"Ocurrió un error inesperado al procesar '{os.path.basename(xml_path)}': {e}")
        return None, None

def procesar_carpeta_xml_a_terminal(carpeta_xml):
    """
    Procesa todos los archivos XML en la carpeta especificada,
    extrae sus Totales y UUIDs, y los imprime en la terminal.
    """
    if not os.path.isdir(carpeta_xml):
        print(f"Error: La carpeta '{carpeta_xml}' no existe o no es un directorio válido.")
        return

    print(f"Procesando archivos XML en: {carpeta_xml}\n")

    found_any = False # Para saber si encontramos al menos un XML válido

    for filename in os.listdir(carpeta_xml):
        if filename.endswith(".xml"):
            xml_path = os.path.join(carpeta_xml, filename)
            
            total, uuid = extraer_total_y_uuid(xml_path)
            
            if total is not None or uuid is not None:
                found_any = True
                if total:
                    print(f"Total: {total}")
                else:
                    print(f"Total: No encontrado en {filename}")
                
                if uuid:
                    print(f"{uuid}") # Imprime solo el UUID como lo solicitaste
                else:
                    print(f"UUID: No encontrado en {filename}")
                '''print("---")''' # Separador para mejor legibilidad entre archivos
            else:
                # Si ambos son None, significa que hubo un error o no se encontró nada
                # Ya el manejador de errores de extraer_total_y_uuid imprimió un mensaje
                pass 
    
    if not found_any:
        print("No se encontraron archivos XML válidos o con datos extraíbles en el directorio especificado.")
    else:
        print("\nProceso de extracción terminado.")

if __name__ == "__main__":
    # Define la carpeta donde están tus archivos XML.
    # Puedes usar os.path.dirname(os.path.abspath(__file__)) para la carpeta actual del script,
    # o una ruta específica como en el ejemplo.
    
    # --- MODIFICA ESTA LÍNEA CON LA RUTA DE TU CARPETA DE XMLs ---
    carpeta_a_procesar = "/Users/danielmendoza/Downloads/" 
    # -----------------------------------------------------------

    # Si se pasa un argumento, lo usa como la carpeta a procesar
    if len(sys.argv) > 1:
        carpeta_a_procesar = sys.argv[1]

    procesar_carpeta_xml_a_terminal(carpeta_a_procesar)
