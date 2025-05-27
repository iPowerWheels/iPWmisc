'''
Just in case you need to iterate

for i in {1..14}
do
    filename="OADownload.jsp-${i}.xml"
    python3 "/Users/danielmendoza/Library/Mobile Documents/com~apple~TextEdit/Documents/extract.py" "/Users/danielmendoza/Downloads/${filename}"
done

'''
import sys
import xml.etree.ElementTree as ET

def extraer_total_y_uuid(xml_path):
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        total = None
        uuid = None

        # Buscar atributo 'Total' en cualquier etiqueta
        for elem in root.iter():
            if 'Total' in elem.attrib:
                total = elem.attrib['Total']
                break  # Solo queremos el primero que encontremos

        # Buscar UUID que normalmente está en un nodo llamado Complemento -> TimbreFiscalDigital
        for elem in root.iter():
            if 'UUID' in elem.attrib:
                uuid = elem.attrib['UUID']
                break  # También solo el primero

        if total:
            print(f"Total: {total}")
        else:
            print("No se encontró el atributo Total con T mayúscula.")

        if uuid:
            print(f"{uuid}")#print(f"UUID: {uuid}")
        else:
            print("No se encontró el atributo UUID.")

    except FileNotFoundError:
        print(f"Archivo no encontrado: {xml_path}")
    except ET.ParseError as e:
        print(f"Error al parsear el XML: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python script.py archivo.xml")
    else:
        extraer_total_y_uuid(sys.argv[1])
