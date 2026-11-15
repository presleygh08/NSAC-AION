# config.py
# Constantes de la interfaz: resolución, escala, paleta de colores, tamaños de letra,
# rutas de archivos y umbrales provisionales.
# Si quieres cambiar un color o un tamaño, cámbialo aquí y se actualiza en todo el juego.

import os

import pygame

# --- Resolución (estilo 16 bits) ---
# Todo se dibuja en una superficie pequeña de 640x360 y luego se agranda ESCALA veces
# (x2 = ventana de 1280x720) sin suavizar, para que se vean los píxeles.
ANCHO = 640           # píxeles "lógicos" (todas las coordenadas del juego usan esto)
ALTO = 360
ESCALA = 2            # cambia a 3 para una ventana de 1920x1080
FPS = 60              # cuadros por segundo

# --- Paleta limitada (rojo, verde, azul) ---
# Fondos y metales
NEGRO = (8, 8, 16)
AZUL_NOCHE = (12, 16, 40)        # fondo espacial
AZUL_MARINO = (24, 32, 72)       # paneles
AZUL_PANEL = (36, 48, 100)
GRIS_OSCURO = (52, 56, 72)       # laboratorio: paredes
GRIS = (96, 102, 120)            # laboratorio: muebles
GRIS_CLARO = (150, 156, 175)
GRIS_SUELO = (70, 76, 92)        # baldosas
GRIS_SUELO_2 = (78, 84, 100)
BLANCO = (240, 240, 248)
CIAN = (120, 220, 240)           # texto destacado
CIELO = (90, 150, 220)           # cielo de la simulación
TIERRA_AZUL = (50, 110, 200)
TIERRA_VERDE = (60, 150, 80)
MARRON = (120, 80, 50)
NARANJA = (240, 140, 50)
# Acentos con significado fijo (sección 1 de la especificación)
VERDE = (70, 200, 110)           # éxito / archivo de pistas
AMARILLO = (240, 200, 60)        # advertencia / estrellas
ROJO = (220, 70, 70)             # falla / peligro
AZUL = (70, 130, 240)            # interacción (CML 1 y estaciones)
MORADO = (160, 90, 220)          # revisión de presupuesto (CML 4)

# Tonos extra para las fotos pixeladas de las misiones (Marte, Luna, metal, nubes)
OXIDO = (170, 80, 50)
OXIDO_OSCURO = (110, 50, 35)
ARENA = (210, 160, 110)
PIEL_CLARA = (240, 200, 160)
GRIS_LUNA = (190, 190, 185)
VERDE_OSCURO = (30, 80, 50)
AZUL_OSCURO = (20, 50, 110)
CIAN_OSCURO = (40, 110, 130)

# Paleta completa del juego (32 colores). Las fotos de las misiones se reducen a estos
# colores (sección 8), así todo el juego comparte el mismo "look" 16 bits.
PALETA = [NEGRO, AZUL_NOCHE, AZUL_MARINO, AZUL_PANEL, GRIS_OSCURO, GRIS, GRIS_CLARO,
          GRIS_SUELO, GRIS_SUELO_2, BLANCO, CIAN, CIELO, TIERRA_AZUL, TIERRA_VERDE, MARRON,
          NARANJA, VERDE, AMARILLO, ROJO, AZUL, MORADO, OXIDO, OXIDO_OSCURO, ARENA,
          PIEL_CLARA, GRIS_LUNA, VERDE_OSCURO, AZUL_OSCURO, CIAN_OSCURO,
          (60, 60, 64), (130, 130, 128), (225, 225, 220)]

# Nombres "de uso" (así las pantallas no dependen del color exacto)
COLOR_FONDO = AZUL_NOCHE
COLOR_TEXTO = BLANCO
COLOR_TEXTO_SUAVE = GRIS_CLARO
COLOR_SOMBRA = NEGRO
COLOR_PANEL = AZUL_MARINO
COLOR_BORDE = GRIS_CLARO
COLOR_BOTON = AZUL_PANEL
COLOR_BOTON_HOVER = AZUL
COLOR_BOTON_INACTIVO = GRIS_OSCURO
COLOR_OK = VERDE
COLOR_AVISO = AMARILLO
COLOR_ERROR = ROJO

# Color de la etiqueta de cada dificultad en la parrilla.
COLORES_DIFICULTAD = {
    "Easy": VERDE,
    "Normal": CIAN,
    "Hard": AMARILLO,
    "Harder": NARANJA,
    "Insane": ROJO,
}

# --- Tamaños de letra (en píxeles lógicos) ---
LETRA_GIGANTE = 48
LETRA_TITULO = 26
LETRA_NORMAL = 18
LETRA_PEQUENA = 15

# Con la fuente pixel del juego (interfaz/fuente_pixel.py) cada tamaño es una escala
# entera de las letras de 5x7: escala 1 = 7 px de alto, escala 2 = 14 px...
# (Si Piero agrega una .ttf en assets/fuentes/, se usan los tamaños de arriba.)
ESCALA_FUENTE = {
    LETRA_GIGANTE: 4,
    LETRA_TITULO: 3,
    LETRA_NORMAL: 2,
    LETRA_PEQUENA: 1,
}

# --- Rutas de archivos ---
# RUTA_PROYECTO es la carpeta NSAC-AION (la carpeta "padre" de interfaz/).
# Así los archivos se encuentran aunque ejecutes el juego desde otra carpeta.
RUTA_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_TEXTOS = os.path.join(RUTA_PROYECTO, "interfaz", "textos_en.json")
RUTA_FUENTES = os.path.join(RUTA_PROYECTO, "assets", "fuentes")
RUTA_IMAGENES_MISIONES = os.path.join(RUTA_PROYECTO, "assets", "misiones")

# --- Medidas que se repiten ---
MARGEN = 16
ALTO_BOTON = 24

# --- Jugador ---
MAX_LETRAS_NOMBRE = 12
NOMBRE_POR_DEFECTO = "Cadet"

# --- Resultados: etiqueta según cuánto le faltó al recurso para su mínimo (%) ---
FALTANTE_POCO = 10       # menos de 10 %  -> "Just short"
FALTANTE_MEDIO = 30      # 10 a 30 %      -> "Short";  más de 30 % -> "Far below"

# --- Laboratorio: el avatar camina ---
VELOCIDAD_JUGADOR = 80       # píxeles por segundo (constante)
RADIO_INTERACCION = 20       # a esta distancia de un marcador aparece "[E] Interact"
DT_MAXIMO = 0.05             # tope del tiempo de un cuadro (si el juego se traba, no "salta")

# --- Hangar (segundos) ---
DURACION_CORTINAS = 1.0      # las cortinas se abren al confirmar CML 1
DURACION_ENSAMBLAJE = 1.5    # animación de cada recurso al confirmar su estación

# --- Simulación (segundos) ---
DURACION_COMUN = 5.0     # cuenta regresiva + despegue (igual para éxito y falla)
DURACION_FINAL = 3.5     # rama de éxito o de falla
DURACION_FINAL_LEJOS = 5.0   # Marte y Luna: viaje + llegada

# --- Notificaciones del asistente ---
DURACION_NOTIFICACION = 6.0  # segundos que queda en pantalla (o hasta un clic / Enter)

# --- Depuración ---
# F2 desbloquea TODAS las misiones (en cualquier pantalla). Sirve para probar Normal, Hard,
# Harder e Insane sin ganar las anteriores, y para la demo. No cambia ningún archivo ni el
# progreso guardado: solo apaga el desbloqueo en orden mientras el juego está abierto.
# Para la versión de entrega poner DEPURACION = False (F2 deja de hacer algo).
DEPURACION = True
TECLA_DESBLOQUEAR = pygame.K_F2
