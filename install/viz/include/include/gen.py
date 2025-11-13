import cv2 as cv
import cv2.aruco as aruco
import os
import numpy as np

ARUCO_DICTIONARY_NAME = 'DICT_4X4_1000'
NUM_MARKERS_TO_GENERATE = 1000
MARKER_SIDE_PIXELS = 200
OUTPUT_DIR = 'aruco_patterns'

def generate_aruco_patterns():
    if ARUCO_DICTIONARY_NAME not in aruco.__dict__:
        print(f"Error: Diccionario '{ARUCO_DICTIONARY_NAME}' no encontrado en cv2.aruco.")
        return

    try:
        aruco_dict = aruco.Dictionary_get(getattr(aruco, ARUCO_DICTIONARY_NAME))
    except AttributeError:
        aruco_dict = aruco.getPredefinedDictionary(getattr(aruco, ARUCO_DICTIONARY_NAME))
    except Exception as e:
        print(f"Error al cargar el diccionario ArUco: {e}")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Directorio de salida creado: {OUTPUT_DIR}")

    print(f"Generando {NUM_MARKERS_TO_GENERATE} marcadores...")
    
    for i in range(NUM_MARKERS_TO_GENERATE):
        if i >= aruco_dict.bytesList.shape[0]:
            print(f"Advertencia: El diccionario {ARUCO_DICTIONARY_NAME} solo tiene IDs hasta {i-1}. Deteniendo la generación.")
            break
            
        marker_image = aruco.drawMarker(aruco_dict, i, MARKER_SIDE_PIXELS)
        border_size = 10 
        final_image = cv.copyMakeBorder(
            marker_image,
            border_size, border_size, border_size, border_size,
            cv.BORDER_CONSTANT, value=255
        )
        
        filename = os.path.join(OUTPUT_DIR, f"{i:04d}.png")
        cv.imwrite(filename, final_image)

    print("\nGeneración completa.")
    print(f"Archivos guardados en: {os.path.abspath(OUTPUT_DIR)}")

if __name__ == '__main__':
    generate_aruco_patterns()
