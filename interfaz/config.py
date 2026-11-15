# config.py
# Constantes de la interfaz: tamaño de la ventana, colores, rutas de archivos
# y límites de los controles. Si quieres cambiar un color o un tamaño,
# cámbialo aquí y se actualiza en todo el juego.

import os

# --- Ventana ---
ANCHO = 1000          # píxeles
ALTO = 700            # píxeles
FPS = 30              # cuadros por segundo

# --- Colores (rojo, verde, azul), cada uno de 0 a 255 ---
COLOR_FONDO = (12, 16, 32)          # azul muy oscuro, como el espacio
COLOR_TEXTO = (235, 235, 245)
COLOR_TEXTO_SUAVE = (150, 155, 175)
COLOR_BOTON = (45, 60, 110)
COLOR_BOTON_HOVER = (70, 90, 150)   # cuando el mouse está encima
COLOR_BOTON_ELEGIDO = (40, 130, 110)  # opción seleccionada
COLOR_BOTON_INACTIVO = (40, 42, 52)
COLOR_BORDE = (120, 140, 200)
COLOR_PANEL = (24, 30, 54)
COLOR_BARRA_FONDO = (50, 54, 70)
COLOR_BARRA_OK = (60, 180, 110)      # verde: hay margen
COLOR_BARRA_JUSTO = (220, 180, 60)   # amarillo: casi al límite
COLOR_BARRA_EXCEDE = (210, 70, 70)   # rojo: se pasó del límite

# --- Tamaños de letra ---
LETRA_TITULO = 44
LETRA_NORMAL = 26
LETRA_PEQUENA = 20

# --- Rutas de archivos ---
# RUTA_PROYECTO es la carpeta NSAC-AION (la carpeta "padre" de interfaz/).
# Así los archivos se encuentran aunque ejecutes el juego desde otra carpeta.
RUTA_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_TEXTOS = os.path.join(RUTA_PROYECTO, "interfaz", "textos_en.json")
RUTA_LANZADORES = os.path.join(RUTA_PROYECTO, "datos", "lanzadores.json")
RUTA_DESTINOS = os.path.join(RUTA_PROYECTO, "datos", "destinos.json")
RUTA_MENSAJES = os.path.join(RUTA_PROYECTO, "datos", "mensajes.json")

# --- Orden de las pantallas (los botones Next/Back siguen esta lista) ---
# Flujo de v4 (versión reducida): parrilla -> objetivo -> taller -> revisión -> resultado.
ORDEN_PANTALLAS = ["parrilla", "objetivo", "taller", "revision", "resultado"]

# --- Qué columna de lanzadores.json corresponde a cada destino ---
# lanzadores.json solo tiene LEO, Luna y Marte, pero destinos.json usa
# nombres más detallados. Este diccionario los une.
# PENDIENTE: confirmar con Emanuel; si él define esta tabla en juego.py, usar la suya.
COLUMNA_CAPACIDAD = {
    "LEO": "capacidad_leo_kg",
    "órbita lunar": "capacidad_luna_kg",
    "órbita de Marte": "capacidad_marte_kg",
    "superficie de Marte": "capacidad_marte_kg",
}

# --- Controles de la pantalla de diseño: (mínimo, máximo, paso) ---
LIMITES_DISENO = {
    "masa_seca_kg": (100, 20000, 100),      # kg
    "area_paneles_m2": (1, 100, 1),         # m²
    "isp_s": (200, 450, 10),                # s
}
