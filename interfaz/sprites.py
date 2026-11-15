# sprites.py
# Dibujos del juego hechos con pygame.draw (rectángulos y círculos), para no depender
# de archivos de imagen. Cada función dibuja en la superficie que recibe; más adelante
# se puede reemplazar por un PNG de assets/ sin cambiar el resto del código.
#
# Truco usado en el avatar: dibujamos sobre una "cuadrícula" de 16 x 32 celdas y cada
# celda mide "u" píxeles. Así el mismo dibujo sirve grande (avatar) o pequeño.

import math

import pygame

from interfaz import config, estilo

# --- Colores de las opciones del avatar (el texto de cada opción está en textos_en.json) ---
TONOS_PIEL = [(255, 224, 189), (241, 194, 150), (224, 172, 105),
              (198, 134, 66), (141, 85, 36), (92, 56, 30)]
COLORES_PELO = [(30, 26, 26), (100, 60, 30), (230, 200, 110),
                (190, 70, 30), (160, 160, 165), (90, 200, 220)]     # el último es de fantasía
COLORES_OJOS = [(60, 40, 30), (60, 110, 180), (60, 140, 80), (120, 120, 130)]

# Prendas de arriba: (color principal, color de detalle, forma).
# Formas: "polera" (manga corta), "rayas", "poleron" (capucha y bolsillo),
#         "casaca" (cierre y cuello), "traje" (traje de vuelo, con parche y cinturón).
POLOS = [
    ((60, 110, 220), (40, 80, 170), "polera"),
    ((210, 60, 60), (240, 240, 248), "rayas"),
    ((60, 160, 90), (40, 110, 60), "poleron"),
    ((230, 190, 50), (240, 240, 248), "casaca"),
    ((235, 130, 40), (60, 60, 70), "traje"),
]
# Prendas de abajo: (color del pantalón, color de los zapatos, forma).
# Formas: "largo", "botas", "corto" (shorts: se ve la piel), "jogger" (puños).
PANTALONES = [
    ((50, 80, 150), (240, 240, 248), "largo"),      # jeans + zapatillas
    ((35, 35, 45), (110, 70, 40), "botas"),          # pantalón negro + botas
    ((180, 160, 110), (240, 240, 248), "corto"),     # shorts caqui + zapatillas
    ((120, 125, 135), (60, 110, 220), "jogger"),     # buzo gris + zapatillas
    ((235, 130, 40), (40, 40, 50), "botas"),         # traje de vuelo + botas
]
COLORES_POLO = [p[0] for p in POLOS]               # para las muestras de color
COLORES_PANTALON = [p[0] for p in PANTALONES]

# Siluetas (Body 1, 2 y 3), medidas en celdas de la cuadrícula de 16 x 32.
# Solo cambian la forma; no son "de chico" ni "de chica": todo sirve con todo.
CUERPOS = [
    {"hombros": 6, "cintura": 5, "cadera": 6, "pierna": 2.4},    # Body 1: delgado
    {"hombros": 8, "cintura": 6, "cadera": 7, "pierna": 3.0},    # Body 2: hombros anchos
    {"hombros": 7, "cintura": 8, "cadera": 8, "pierna": 3.4},    # Body 3: redondeado
]

# Cuántas opciones tiene cada categoría (lo usa la pantalla de avatar).
CANTIDAD_OPCIONES = {
    "cuerpo": len(CUERPOS),
    "piel": len(TONOS_PIEL),
    "pelo": 7,
    "color_pelo": len(COLORES_PELO),
    "ojos": 4,
    "color_ojos": len(COLORES_OJOS),
    "accesorio": 6,
    "polo": len(POLOS),
    "pantalon": len(PANTALONES),
}

# Estilos de pelo y accesorios por número (el nombre en inglés está en textos_en.json).
PELO_CORTO, PELO_LARGO, PELO_RIZADO, PELO_AFRO, PELO_TRENZAS, PELO_RAPADO, PELO_CALVO = range(7)
ACC_NINGUNO, ACC_LENTES, ACC_GORRA, ACC_AUDIFONOS, ACC_PANUELO, ACC_CASCO = range(6)
COLOR_PANUELO = (150, 80, 200)
COLOR_GORRA = (210, 60, 60)
COLOR_OSCURO = (30, 30, 40)


def avatar_inicial():
    """Diccionario de índices del avatar (todas las opciones en la primera)."""
    avatar = {}
    for categoria in CANTIDAD_OPCIONES:
        avatar[categoria] = 0
    return avatar


def _celda(sup, color, x0, y0, u, cx, cy, cw, ch):
    """Pinta un rectángulo de la cuadrícula: columna cx, fila cy, ancho cw, alto ch."""
    pygame.draw.rect(sup, color, (x0 + int(cx * u), y0 + int(cy * u),
                                  max(1, int(cw * u)), max(1, int(ch * u))))


def _poligono(sup, color, x0, y0, u, puntos):
    """Polígono con puntos en celdas de la cuadrícula."""
    pygame.draw.polygon(sup, color, [(x0 + int(px * u), y0 + int(py * u)) for (px, py) in puntos])


def _pelo_detras(sup, avatar, x0, y0, u):
    """Pelo que va DETRÁS de la cabeza y el cuerpo (largo, trenzas, afro)."""
    pelo = COLORES_PELO[avatar["color_pelo"]]
    estilo = avatar["pelo"]
    if estilo == PELO_LARGO:
        _celda(sup, pelo, x0, y0, u, 4.2, 2.5, 7.6, 9.5)
    elif estilo == PELO_TRENZAS:
        for cx in (3.8, 11.2):
            for i in range(5):                                  # trenza = bolitas en fila
                _celda(sup, pelo, x0, y0, u, cx, 4 + i * 1.6, 1.2, 1.3)
    elif estilo == PELO_AFRO:
        pygame.draw.circle(sup, pelo, (x0 + 8 * u, y0 + int(4.3 * u)), int(4.8 * u))


def _pelo_arriba(sup, avatar, x0, y0, u):
    """Pelo que va SOBRE la cabeza (flequillo, rizos, rapado)."""
    pelo = COLORES_PELO[avatar["color_pelo"]]
    estilo = avatar["pelo"]
    if estilo in (PELO_CORTO, PELO_LARGO, PELO_TRENZAS):
        _celda(sup, pelo, x0, y0, u, 5, 1.5, 6, 1.7)
        _celda(sup, pelo, x0, y0, u, 4.6, 2, 0.9, 3)
        _celda(sup, pelo, x0, y0, u, 10.5, 2, 0.9, 3)
        if estilo == PELO_CORTO:
            _celda(sup, pelo, x0, y0, u, 5.5, 3, 2, 0.8)          # flequillo de lado
    elif estilo == PELO_RIZADO:
        for cx in (5, 6.5, 8, 9.5, 11):
            pygame.draw.circle(sup, pelo, (x0 + int(cx * u), y0 + int(2.2 * u)), int(1.1 * u))
        for cy in (3.5, 5):
            pygame.draw.circle(sup, pelo, (x0 + int(4.8 * u), y0 + int(cy * u)), int(0.9 * u))
            pygame.draw.circle(sup, pelo, (x0 + int(11.2 * u), y0 + int(cy * u)), int(0.9 * u))
    elif estilo == PELO_AFRO:
        _celda(sup, pelo, x0, y0, u, 5, 1.4, 6, 1.4)
    elif estilo == PELO_RAPADO:
        _celda(sup, pelo, x0, y0, u, 5, 1.8, 6, 0.8)
    # PELO_CALVO: sin pelo


def _ojos(sup, avatar, x0, y0, u):
    ojo = COLORES_OJOS[avatar["color_ojos"]]
    forma = avatar["ojos"]
    for cx in (6.3, 8.7):
        if forma == 0:                                     # round
            _celda(sup, config.BLANCO, x0, y0, u, cx - 0.2, 4.8, 1.4, 1.2)
            _celda(sup, ojo, x0, y0, u, cx + 0.2, 5, 0.8, 1)
        elif forma == 1:                                   # narrow
            _celda(sup, ojo, x0, y0, u, cx - 0.2, 5.3, 1.4, 0.5)
        elif forma == 2:                                   # wide
            _celda(sup, config.BLANCO, x0, y0, u, cx - 0.3, 4.6, 1.6, 1.6)
            _celda(sup, ojo, x0, y0, u, cx + 0.1, 4.9, 1, 1.1)
        else:                                              # sleepy (párpado)
            _celda(sup, ojo, x0, y0, u, cx, 5.4, 1, 0.6)
            _celda(sup, COLOR_OSCURO, x0, y0, u, cx - 0.2, 5.1, 1.4, 0.35)


def _polo(sup, avatar, x0, y0, u, cuerpo, piel):
    """Torso y brazos con la prenda elegida."""
    color, detalle, forma = POLOS[avatar["polo"]]
    h, c, k = cuerpo["hombros"], cuerpo["cintura"], cuerpo["cadera"]
    torso = [(8 - h / 2, 9), (8 + h / 2, 9), (8 + c / 2, 14), (8 + k / 2, 18),
             (8 - k / 2, 18), (8 - c / 2, 14)]
    # Brazos: por fuera de lo más ancho del torso
    ancho_max = max(h, c)
    x_izq = 8 - ancho_max / 2 - 1.8
    x_der = 8 + ancho_max / 2 - 0.2
    manga_larga = forma in ("poleron", "casaca", "traje")
    fin_manga = 16.5 if manga_larga else 12
    for x in (x_izq, x_der):
        _celda(sup, color, x0, y0, u, x, 9.3, 2, fin_manga - 9.3)
        _celda(sup, piel, x0, y0, u, x, fin_manga, 2, 18.5 - fin_manga)
    if forma == "poleron":                                 # capucha detrás del cuello
        _celda(sup, detalle, x0, y0, u, 6, 8.2, 4, 1.4)
    _poligono(sup, color, x0, y0, u, torso)
    if forma == "rayas":
        for y in (10.5, 12.5, 14.5, 16.5):
            ancho = c if y < 14 else k
            _celda(sup, detalle, x0, y0, u, 8 - ancho / 2 + 0.2, y, ancho - 0.4, 0.7)
    elif forma == "poleron":                               # bolsillo canguro
        _celda(sup, detalle, x0, y0, u, 6.3, 14.5, 3.4, 1.8)
    elif forma == "casaca":                                # polo blanco debajo + cierre
        _celda(sup, detalle, x0, y0, u, 7.4, 9, 1.2, 9)
        _celda(sup, COLOR_OSCURO, x0, y0, u, 7.9, 9.5, 0.3, 8.5)
        _celda(sup, color, x0, y0, u, 6.4, 9, 1, 1)        # cuello
        _celda(sup, color, x0, y0, u, 8.6, 9, 1, 1)
    elif forma == "traje":                                 # parche (sin logos) y cinturón
        _celda(sup, config.AZUL, x0, y0, u, 9, 10.5, 1.6, 1.2)
        _celda(sup, detalle, x0, y0, u, 8 - c / 2, 15.3, c, 0.8)


def _pantalon(sup, avatar, x0, y0, u, cuerpo, piel):
    color, zapato, forma = PANTALONES[avatar["pantalon"]]
    p = cuerpo["pierna"]
    piernas = (8 - 0.3 - p, 8 + 0.3)
    for x in piernas:
        if forma == "corto":
            _celda(sup, color, x0, y0, u, x, 18, p, 4.5)
            _celda(sup, piel, x0, y0, u, x + 0.3, 22.5, p - 0.6, 5.5)
        else:
            _celda(sup, color, x0, y0, u, x, 18, p, 10)
            if forma == "jogger":                          # puños del buzo
                _celda(sup, COLOR_OSCURO, x0, y0, u, x, 27, p, 0.7)
        if forma == "botas":
            _celda(sup, zapato, x0, y0, u, x - 0.2, 25.5, p + 0.4, 4.5)
        else:
            _celda(sup, zapato, x0, y0, u, x - 0.2, 28, p + 0.6, 2)
            _celda(sup, COLOR_OSCURO, x0, y0, u, x - 0.2, 29.6, p + 0.6, 0.4)   # suela
    # Unión de las piernas con la cadera
    _celda(sup, color, x0, y0, u, 8 - cuerpo["cadera"] / 2, 17.5, cuerpo["cadera"], 1.5)


def _accesorio(sup, avatar, x0, y0, u):
    accesorio = avatar["accesorio"]
    if accesorio == ACC_LENTES:
        for cx in (5.9, 8.4):
            pygame.draw.rect(sup, COLOR_OSCURO, (x0 + int(cx * u), y0 + int(4.5 * u),
                                                  int(1.9 * u), int(1.6 * u)), max(1, u // 3))
        _celda(sup, COLOR_OSCURO, x0, y0, u, 7.7, 5, 0.8, 0.3)
    elif accesorio == ACC_GORRA:
        _celda(sup, COLOR_GORRA, x0, y0, u, 4.8, 1, 6.4, 2)
        _celda(sup, COLOR_GORRA, x0, y0, u, 9, 2.6, 3.5, 0.8)
    elif accesorio == ACC_AUDIFONOS:
        _celda(sup, COLOR_OSCURO, x0, y0, u, 4.6, 0.8, 6.8, 0.7)
        _celda(sup, COLOR_OSCURO, x0, y0, u, 4.6, 0.8, 0.6, 3.5)
        _celda(sup, COLOR_OSCURO, x0, y0, u, 10.8, 0.8, 0.6, 3.5)
        _celda(sup, COLOR_OSCURO, x0, y0, u, 4, 4, 1.2, 2.5)
        _celda(sup, COLOR_OSCURO, x0, y0, u, 10.8, 4, 1.2, 2.5)
    elif accesorio == ACC_PANUELO:
        # Cubre el pelo y cae sobre los hombros; la cara queda visible.
        _celda(sup, COLOR_PANUELO, x0, y0, u, 4.3, 1.1, 7.4, 2.4)
        _celda(sup, COLOR_PANUELO, x0, y0, u, 4.3, 1.1, 1.3, 8.4)
        _celda(sup, COLOR_PANUELO, x0, y0, u, 10.4, 1.1, 1.3, 8.4)
        _celda(sup, COLOR_PANUELO, x0, y0, u, 5.5, 8.4, 5, 1.2)
    elif accesorio == ACC_CASCO:
        centro = (x0 + 8 * u, y0 + int(5 * u))
        pygame.draw.circle(sup, config.GRIS_CLARO, centro, int(5.3 * u), max(1, u // 2))
        pygame.draw.circle(sup, config.CIAN, centro, int(4.8 * u), max(1, u // 3))
        _celda(sup, config.BLANCO, x0, y0, u, 5, 1.6, 1, 1)          # brillo del vidrio
        _celda(sup, config.GRIS_CLARO, x0, y0, u, 5.5, 9.2, 5, 0.8)  # cuello del casco


def dibujar_avatar(sup, avatar, x0, y0, u):
    """Avatar de frente, cuerpo completo. (x0, y0) = esquina superior izquierda.
    Ocupa 16*u de ancho y 32*u de alto."""
    piel = TONOS_PIEL[avatar["piel"]]
    cuerpo = CUERPOS[avatar["cuerpo"]]
    con_panuelo = avatar["accesorio"] == ACC_PANUELO

    if not con_panuelo:
        _pelo_detras(sup, avatar, x0, y0, u)
    _pantalon(sup, avatar, x0, y0, u, cuerpo, piel)
    _polo(sup, avatar, x0, y0, u, cuerpo, piel)
    _celda(sup, piel, x0, y0, u, 7, 8, 2, 1.2)                          # cuello
    _celda(sup, piel, x0, y0, u, 5, 2, 6, 6.5)                          # cabeza
    _celda(sup, piel, x0, y0, u, 4.5, 4.3, 0.6, 1.6)                    # orejas
    _celda(sup, piel, x0, y0, u, 10.9, 4.3, 0.6, 1.6)
    _ojos(sup, avatar, x0, y0, u)
    _celda(sup, (170, 80, 80), x0, y0, u, 7.3, 7, 1.4, 0.4)            # boca
    if not con_panuelo and avatar["accesorio"] != ACC_GORRA:
        _pelo_arriba(sup, avatar, x0, y0, u)
    elif avatar["accesorio"] == ACC_GORRA and avatar["pelo"] in (PELO_RIZADO, PELO_CORTO, PELO_LARGO, PELO_TRENZAS):
        # Con gorra se ven los lados del pelo
        pelo = COLORES_PELO[avatar["color_pelo"]]
        _celda(sup, pelo, x0, y0, u, 4.6, 2.5, 0.9, 2.5)
        _celda(sup, pelo, x0, y0, u, 10.5, 2.5, 0.9, 2.5)
    _accesorio(sup, avatar, x0, y0, u)


# --- Avatar visto desde arriba (para el laboratorio) ---
DIRECCIONES = ["abajo", "derecha", "arriba", "izquierda"]


def dibujar_avatar_arriba(sup, avatar, x0, y0, direccion="abajo", cuadro=0, u=1):
    """Sprite pequeño (16x16 celdas de u px) visto desde arriba, con los mismos
    colores de piel, pelo, polo y pantalón del avatar de frente.
    direccion: "abajo", "arriba", "izquierda" o "derecha" (hacia dónde mira).
    cuadro: 0 o 1 (los dos pasos de la caminata)."""
    piel = TONOS_PIEL[avatar["piel"]]
    pelo = COLORES_PELO[avatar["color_pelo"]]
    color_polo, detalle_polo, forma_polo = POLOS[avatar["polo"]]
    color_pantalon, zapato, _ = PANTALONES[avatar["pantalon"]]
    ancho = [10, 12, 12][avatar["cuerpo"]]
    paso = 1 if cuadro == 1 else -1
    vertical = direccion in ("abajo", "arriba")

    # 1. Piernas y pies (se mueven al caminar)
    if vertical:
        for x, dy in ((5, paso), (9, -paso)):
            _celda(sup, color_pantalon, x0, y0, u, x, 11, 2, 3)
            _celda(sup, zapato, x0, y0, u, x, 13.5 + dy * 0.8, 2, 1.5)
    else:
        sentido = 1 if direccion == "derecha" else -1
        for dx in (paso, -paso):
            _celda(sup, color_pantalon, x0, y0, u, 7 + dx * 1.2, 11, 2, 3)
            _celda(sup, zapato, x0, y0, u, 7 + dx * 1.2 + sentido * 0.5, 13.5, 2, 1.5)

    # 2. Cuerpo (hombros) y brazos
    x_cuerpo = (16 - ancho) / 2
    pygame.draw.ellipse(sup, color_polo, (x0 + int(x_cuerpo * u), y0 + 6 * u, ancho * u, 6 * u))
    if forma_polo == "rayas":
        _celda(sup, detalle_polo, x0, y0, u, x_cuerpo + 1, 8.5, ancho - 2, 0.7)
    if vertical:
        for x, dy in ((x_cuerpo - 1.5, -paso), (x_cuerpo + ancho - 0.5, paso)):
            _celda(sup, color_polo, x0, y0, u, x, 7.5 + dy * 0.5, 2, 2)
            _celda(sup, piel, x0, y0, u, x, 9.5 + dy * 0.5, 2, 1.5)
    else:
        _celda(sup, color_polo, x0, y0, u, 7 + paso, 7.5, 2, 2.5)
        _celda(sup, piel, x0, y0, u, 7 + paso, 10, 2, 1.2)

    # 3. Cabeza
    centro = (x0 + 8 * u, y0 + int(4.5 * u))
    radio = int(3.6 * u)
    accesorio = avatar["accesorio"]
    if accesorio == ACC_PANUELO:
        color_cabeza = COLOR_PANUELO
    elif avatar["pelo"] == PELO_CALVO:
        color_cabeza = piel
    else:
        color_cabeza = pelo
    if avatar["pelo"] == PELO_AFRO and accesorio != ACC_PANUELO:
        radio = int(4.4 * u)
    if avatar["pelo"] in (PELO_LARGO, PELO_TRENZAS) and accesorio != ACC_PANUELO and direccion != "abajo":
        _celda(sup, pelo, x0, y0, u, 5.5, 5, 5, 3.5)                     # pelo sobre la espalda
    pygame.draw.circle(sup, color_cabeza, centro, radio)

    # 4. Cara (solo se ve hacia donde mira)
    ojo = COLORES_OJOS[avatar["color_ojos"]]
    if direccion == "abajo":
        _celda(sup, piel, x0, y0, u, 5.5, 4.5, 5, 3)
        _celda(sup, ojo, x0, y0, u, 6.3, 5.2, 1, 1)
        _celda(sup, ojo, x0, y0, u, 8.7, 5.2, 1, 1)
        if accesorio == ACC_LENTES:
            _celda(sup, COLOR_OSCURO, x0, y0, u, 5.8, 5, 4.4, 0.5)
    elif direccion in ("izquierda", "derecha"):
        x_cara = 4.6 if direccion == "izquierda" else 8.4
        _celda(sup, piel, x0, y0, u, x_cara, 4.3, 3, 2.8)
        x_ojo = x_cara + 0.4 if direccion == "izquierda" else x_cara + 1.6
        _celda(sup, ojo, x0, y0, u, x_ojo, 5, 1, 1)

    # 5. Accesorios vistos desde arriba
    if accesorio == ACC_GORRA:
        pygame.draw.circle(sup, COLOR_GORRA, centro, int(3.4 * u))
        visera = {"abajo": (6, 7, 4, 1.4), "arriba": (6, 0.6, 4, 1.4),
                  "izquierda": (3, 3.8, 1.6, 2), "derecha": (11.4, 3.8, 1.6, 2)}[direccion]
        _celda(sup, COLOR_GORRA, x0, y0, u, *visera)
    elif accesorio == ACC_AUDIFONOS:
        _celda(sup, COLOR_OSCURO, x0, y0, u, 3.8, 3.8, 1, 2)
        _celda(sup, COLOR_OSCURO, x0, y0, u, 11.2, 3.8, 1, 2)
    elif accesorio == ACC_CASCO:
        pygame.draw.circle(sup, config.CIAN, centro, int(4.4 * u), max(1, u // 2))


# --- AION, el robot guía (v2, D5) -----------------------------------------------------
# Robot pequeño y tierno de 32x32 px: cabeza redonda, ojos grandes, antena con luz.
# Expresiones: "neutral", "feliz", "alerta", "celebrando".
EXPRESIONES_AION = ["neutral", "feliz", "alerta", "celebrando"]
# Las expresiones viejas del director de vuelo siguen funcionando: se traducen a las de AION.
EXPRESIONES_NPC = EXPRESIONES_AION + ["pensativo", "preocupado", "sorprendido"]
EQUIVALENCIA_EXPRESION = {"pensativo": "neutral", "preocupado": "alerta", "sorprendido": "celebrando"}

METAL_AION = (205, 212, 228)
METAL_AION_OSCURO = (120, 128, 150)
PANTALLA_AION = (20, 28, 48)


def dibujar_aion(sup, x, y, expresion="neutral", tiempo=0.0, fondo=True):
    """Retrato de AION (32x32 px) con la esquina de arriba a la izquierda en (x, y).
    'tiempo' hace parpadear la luz de la antena. fondo=False: sin el recuadro gris
    (para el AION que flota en la sala)."""
    expresion = EQUIVALENCIA_EXPRESION.get(expresion, expresion)
    if fondo:
        pygame.draw.rect(sup, config.GRIS_OSCURO, (x, y, 32, 32))       # fondo del retrato

    # Antena con su luz (roja si está en alerta, amarilla al celebrar, cian normal)
    pygame.draw.rect(sup, METAL_AION_OSCURO, (x + 15, y + 2, 2, 5))
    if expresion == "alerta":
        luz = config.ROJO
    elif expresion == "celebrando":
        luz = config.AMARILLO
    else:
        luz = config.CIAN
    if int(tiempo * 2) % 2 == 0:
        pygame.draw.rect(sup, luz, (x + 14, y + 1, 4, 3))
    else:
        pygame.draw.rect(sup, METAL_AION_OSCURO, (x + 14, y + 1, 4, 3))

    # Cabeza: rectángulo con esquinas recortadas (se ve redonda en pixel art)
    pygame.draw.rect(sup, METAL_AION_OSCURO, (x + 5, y + 7, 22, 18))
    pygame.draw.rect(sup, METAL_AION, (x + 6, y + 6, 20, 18))
    pygame.draw.rect(sup, METAL_AION, (x + 4, y + 9, 24, 12))
    pygame.draw.rect(sup, METAL_AION_OSCURO, (x + 3, y + 12, 2, 6))     # "orejas" (tornillos)
    pygame.draw.rect(sup, METAL_AION_OSCURO, (x + 27, y + 12, 2, 6))
    # Pantalla de la cara
    pygame.draw.rect(sup, PANTALLA_AION, (x + 7, y + 9, 18, 12))

    # Ojos grandes
    ojo = config.CIAN
    if expresion == "feliz" or expresion == "celebrando":
        # ojos cerrados de alegría: "^ ^"
        for ox in (x + 9, x + 18):
            pygame.draw.rect(sup, ojo, (ox, y + 13, 1, 2))
            pygame.draw.rect(sup, ojo, (ox + 1, y + 12, 3, 1))
            pygame.draw.rect(sup, ojo, (ox + 4, y + 13, 1, 2))
    elif expresion == "alerta":
        # ojos muy abiertos con una ceja inclinada
        for ox in (x + 9, x + 18):
            pygame.draw.rect(sup, config.AMARILLO, (ox, y + 11, 5, 5))
            pygame.draw.rect(sup, PANTALLA_AION, (ox + 2, y + 13, 1, 1))
    else:
        # neutral: ojos grandes con brillo
        for ox in (x + 9, x + 18):
            pygame.draw.rect(sup, ojo, (ox, y + 11, 5, 5))
            pygame.draw.rect(sup, config.BLANCO, (ox + 1, y + 12, 1, 1))

    # Boca
    if expresion == "celebrando":
        pygame.draw.rect(sup, ojo, (x + 13, y + 17, 6, 2))              # boca abierta
    elif expresion == "feliz":
        pygame.draw.rect(sup, ojo, (x + 14, y + 18, 4, 1))
        pygame.draw.rect(sup, ojo, (x + 13, y + 17, 1, 1))
        pygame.draw.rect(sup, ojo, (x + 18, y + 17, 1, 1))
    elif expresion == "alerta":
        pygame.draw.rect(sup, config.AMARILLO, (x + 14, y + 18, 4, 1))
    else:
        pygame.draw.rect(sup, ojo, (x + 14, y + 18, 4, 1))

    # Mejillas rosadas (lo hace tierno)
    pygame.draw.rect(sup, (230, 120, 150), (x + 7, y + 19, 2, 1))
    pygame.draw.rect(sup, (230, 120, 150), (x + 23, y + 19, 2, 1))

    # Cuerpito y bracitos (levantados si celebra)
    pygame.draw.rect(sup, METAL_AION_OSCURO, (x + 10, y + 25, 12, 7))
    pygame.draw.rect(sup, config.AZUL, (x + 13, y + 27, 6, 3))           # luz del pecho
    if expresion == "celebrando":
        pygame.draw.rect(sup, METAL_AION, (x + 6, y + 22, 3, 5))
        pygame.draw.rect(sup, METAL_AION, (x + 23, y + 22, 3, 5))
    else:
        pygame.draw.rect(sup, METAL_AION, (x + 7, y + 26, 3, 5))
        pygame.draw.rect(sup, METAL_AION, (x + 22, y + 26, 3, 5))


def dibujar_aion_sala(sup, cx, y_suelo, expresion="neutral", tiempo=0.0):
    """AION de cuerpo entero dentro de la sala de control (v2, D5): flota sobre el suelo
    (sube y baja 2 px) con su sombra debajo. cx = centro, y_suelo = donde está su sombra."""
    flota = int(2 * math.sin(tiempo * 3))
    pygame.draw.ellipse(sup, (40, 44, 58), (cx - 9, y_suelo - 3, 18, 6))   # sombra
    # Propulsor debajo del cuerpo (una llamita cian que parpadea)
    if int(tiempo * 10) % 2 == 0:
        pygame.draw.rect(sup, config.CIAN, (cx - 2, y_suelo - 6 + flota, 4, 2))
    dibujar_aion(sup, cx - 16, y_suelo - 40 + flota, expresion, tiempo, fondo=False)


def dibujar_npc(sup, x, y, expresion="neutral"):
    """El guía del juego. Desde la v2 es AION (antes, un director de vuelo).
    Se mantiene este nombre para no cambiar las pantallas que ya lo usan."""
    dibujar_aion(sup, x, y, expresion, pygame.time.get_ticks() / 1000)


def dibujar_cohete(sup, cx, y_base, partes=None, tiempo=0.0, fuego=False):
    """Cohete de ~24x70 px. cx = centro horizontal, y_base = parte de abajo.
    partes: {clave_recurso: segundo en que se confirmó} -> dibuja lo ensamblado.
    Cada parte aparece poco a poco en 1.5 s (animación de ensamblaje)."""
    if partes is None:
        partes = {}
    x = cx - 8
    top = y_base - 64
    # Cuerpo, nariz y aletas
    pygame.draw.rect(sup, config.BLANCO, (x, top + 14, 16, 46))
    pygame.draw.polygon(sup, config.ROJO, [(cx, top), (x, top + 14), (x + 16, top + 14)])
    pygame.draw.polygon(sup, config.ROJO, [(x, y_base - 16), (x - 8, y_base), (x, y_base - 4)])
    pygame.draw.polygon(sup, config.ROJO, [(x + 16, y_base - 16), (x + 24, y_base), (x + 16, y_base - 4)])
    pygame.draw.rect(sup, config.GRIS, (x + 3, y_base - 4, 10, 4))     # tobera
    pygame.draw.rect(sup, config.AZUL, (cx - 3, top + 20, 6, 6))       # ventana

    def avance(clave):
        """0 a 1: cuánto se ve la parte (crece durante 1.5 s)."""
        return max(0.0, min(1.0, (tiempo - partes[clave]) / 1.5))

    if "estructura" in partes:          # vigas grises sobre el cuerpo
        a = avance("estructura")
        for i in range(int(4 * a)):
            pygame.draw.rect(sup, config.GRIS, (x, top + 30 + i * 7, 16, 2))
    if "propulsion" in partes:          # tanque que se llena
        a = avance("propulsion")
        pygame.draw.rect(sup, config.GRIS_OSCURO, (x + 4, top + 30, 8, 24))
        alto = int(24 * a)
        pygame.draw.rect(sup, config.NARANJA, (x + 4, top + 54 - alto, 8, alto))
    if "potencia" in partes:            # paneles solares a los lados
        a = avance("potencia")
        largo = int(14 * a)
        pygame.draw.rect(sup, config.AZUL, (x - largo, top + 24, largo, 6))
        pygame.draw.rect(sup, config.AZUL, (x + 16, top + 24, largo, 6))
    if "comunicaciones" in partes:      # antena parabólica arriba
        if avance("comunicaciones") > 0.3:
            pygame.draw.circle(sup, config.GRIS_CLARO, (cx + 10, top + 8), 4)
            pygame.draw.line(sup, config.GRIS_CLARO, (cx + 6, top + 12), (cx + 2, top + 16))
    if "datos" in partes:               # caja de instrumentos
        if avance("datos") > 0.3:
            pygame.draw.rect(sup, config.AMARILLO, (cx - 5, top + 15, 10, 4))
    if "tiempo" in partes:              # baterías
        if avance("tiempo") > 0.3:
            pygame.draw.rect(sup, config.VERDE, (x + 1, top + 56, 4, 3))
            pygame.draw.rect(sup, config.VERDE, (x + 11, top + 56, 4, 3))

    if fuego:                           # llama que parpadea
        largo = 10 + int(6 * abs(math.sin(tiempo * 20)))
        pygame.draw.polygon(sup, config.NARANJA, [(x + 2, y_base), (x + 14, y_base), (cx, y_base + largo)])
        pygame.draw.polygon(sup, config.AMARILLO, [(x + 5, y_base), (x + 11, y_base), (cx, y_base + largo - 5)])


def dibujar_torre(sup, x, y_base, alto):
    """Torre de lanzamiento: una columna con travesaños."""
    pygame.draw.rect(sup, config.GRIS, (x, y_base - alto, 6, alto))
    for yy in range(y_base - alto, y_base, 8):
        pygame.draw.line(sup, config.GRIS_OSCURO, (x, yy), (x + 6, yy + 8))


# --- Puertas del hangar (v2, punto 17) -------------------------------------
# Dos hojas de metal que se deslizan hacia los lados. Cada hoja se dibuja UNA vez en una
# imagen (con paneles, remaches y franjas de advertencia) y luego solo se mueve.
METAL_PUERTA = (110, 116, 134)
METAL_PUERTA_CLARO = (150, 156, 175)
METAL_PUERTA_OSCURO = (64, 68, 84)
_cache_puertas = {}


def imagen_hoja_puerta(ancho, alto, lado):
    """Una hoja de la puerta. lado = -1 (izquierda) o 1 (derecha): las franjas amarillas y
    negras quedan en el borde del centro, donde se juntan las dos hojas."""
    clave = (ancho, alto, lado)
    if clave in _cache_puertas:
        return _cache_puertas[clave]
    hoja = pygame.Surface((ancho, alto))
    hoja.fill(METAL_PUERTA)
    # Paneles horizontales con bisel (línea clara arriba, oscura abajo) y remaches
    for y in range(0, alto, 28):
        pygame.draw.line(hoja, METAL_PUERTA_OSCURO, (0, y), (ancho, y))
        pygame.draw.line(hoja, METAL_PUERTA_CLARO, (0, y + 1), (ancho, y + 1))
        for x in range(6, ancho - 14, 12):
            hoja.set_at((x, y + 5), METAL_PUERTA_CLARO)
            hoja.set_at((x + 1, y + 6), METAL_PUERTA_OSCURO)
    # Borde del centro: franja diagonal amarilla y negra de 10 px
    x_franja = ancho - 10 if lado == -1 else 0
    for y in range(-10, alto, 8):
        pygame.draw.polygon(hoja, config.AMARILLO, [(x_franja, y), (x_franja + 10, y + 10),
                                                    (x_franja + 10, y + 14), (x_franja, y + 4)])
    pygame.draw.rect(hoja, config.NEGRO, (x_franja, 0, 10, alto), 1)
    # Refuerzo vertical y manija
    x_refuerzo = 14 if lado == -1 else ancho - 18
    pygame.draw.rect(hoja, METAL_PUERTA_OSCURO, (x_refuerzo, 0, 4, alto))
    x_manija = ancho - 18 if lado == -1 else 14
    pygame.draw.rect(hoja, config.GRIS_OSCURO, (x_manija, alto // 2 - 10, 4, 20))
    pygame.draw.rect(hoja, METAL_PUERTA_CLARO, (x_manija, alto // 2 - 10, 1, 20))
    _cache_puertas[clave] = hoja
    return hoja


def dibujar_baliza(sup, x, y, tiempo, encendida):
    """Luz ámbar de advertencia que gira mientras las puertas se mueven."""
    pygame.draw.rect(sup, config.GRIS_OSCURO, (x - 5, y + 3, 10, 3))          # base
    if not encendida:
        pygame.draw.circle(sup, (120, 90, 40), (x, y), 4)
        return
    pygame.draw.circle(sup, config.NARANJA, (x, y), 4)
    pygame.draw.circle(sup, config.AMARILLO, (x, y), 2)
    angulo = tiempo * 8                                                    # haz de luz que gira
    largo = 22
    punta1 = (x + math.cos(angulo - 0.25) * largo, y + math.sin(angulo - 0.25) * largo * 0.4)
    punta2 = (x + math.cos(angulo + 0.25) * largo, y + math.sin(angulo + 0.25) * largo * 0.4)
    haz = pygame.Surface(sup.get_size(), pygame.SRCALPHA)
    pygame.draw.polygon(haz, (240, 200, 60, 90), [(x, y), punta1, punta2])
    sup.blit(haz, (0, 0))


def dibujar_puertas_hangar(sup, rect, apertura, tiempo=0.0):
    """Puertas metálicas del hangar. apertura: 0 = cerradas, 1 = abiertas del todo.
    Las hojas se deslizan hacia los lados (salen del recuadro, que recorta)."""
    r = pygame.Rect(rect)
    mitad = r.w // 2
    corrido = int(mitad * apertura)                    # cuánto se movió cada hoja
    recorte_anterior = sup.get_clip()
    sup.set_clip(r.clip(recorte_anterior) if recorte_anterior else r)
    if corrido < mitad:
        sup.blit(imagen_hoja_puerta(mitad, r.h, -1), (r.x - corrido, r.y))
        sup.blit(imagen_hoja_puerta(r.w - mitad, r.h, 1), (r.x + mitad + corrido, r.y))
    # Rieles arriba y abajo (siempre se ven)
    pygame.draw.rect(sup, METAL_PUERTA_OSCURO, (r.x, r.y, r.w, 4))
    pygame.draw.rect(sup, METAL_PUERTA_OSCURO, (r.x, r.bottom - 3, r.w, 3))
    sup.set_clip(recorte_anterior)
    # Dos balizas en las esquinas de arriba (en el centro está el letrero "HANGAR")
    moviendose = 0 < apertura < 1
    dibujar_baliza(sup, r.x + 12, r.y + 10, tiempo, moviendose)
    dibujar_baliza(sup, r.right - 12, r.y + 10, tiempo + 0.4, moviendose)


def dibujar_cortinas(sup, rect, apertura):
    """Nombre viejo (v1: telón rojo). Desde la v2 dibuja las puertas metálicas."""
    dibujar_puertas_hangar(sup, rect, apertura)


def dibujar_marcador(sup, cx, cy, simbolo, color, tiempo):
    """Marcador flotante ("!", "i" o "v") que sube y baja 2 px."""
    dy = int(2 * math.sin(tiempo * 4))
    rect = pygame.Rect(cx - 7, cy - 7 + dy, 14, 14)
    pygame.draw.rect(sup, config.NEGRO, rect.move(1, 1))
    pygame.draw.rect(sup, color, rect)
    if simbolo == "v":               # visto bueno: dibujamos un ✓ con dos líneas
        pygame.draw.line(sup, config.BLANCO, (rect.x + 3, rect.y + 7), (rect.x + 6, rect.y + 10), 2)
        pygame.draw.line(sup, config.BLANCO, (rect.x + 6, rect.y + 10), (rect.x + 11, rect.y + 3), 2)
        return rect
    estilo.texto(sup, simbolo, rect.centerx, rect.centery, config.LETRA_PEQUENA,
                 config.BLANCO, centrado=True)
    return rect


def dibujar_estrella(sup, cx, cy, radio, llena):
    """Estrella de 5 puntas: amarilla si está llena, gris si no."""
    puntos = []
    for i in range(10):
        angulo = -math.pi / 2 + i * math.pi / 5
        r = radio if i % 2 == 0 else radio * 0.45
        puntos.append((cx + r * math.cos(angulo), cy + r * math.sin(angulo)))
    color = config.AMARILLO if llena else config.GRIS_OSCURO
    pygame.draw.polygon(sup, color, puntos)


def dibujar_candado(sup, x, y):
    """Candado pequeño de 10x12 px."""
    pygame.draw.rect(sup, config.GRIS_CLARO, (x + 2, y, 6, 6), 2)
    pygame.draw.rect(sup, config.GRIS_CLARO, (x, y + 5, 10, 7))


def dibujar_destino(sup, rect, destino, tiempo, nombre="", fondo=True):
    """Imagen de reemplazo (placeholder) de una misión según su destino:
    Tierra con un satélite en órbita, Marte, o la Luna. Si se da 'nombre',
    se escribe abajo (cuando no hay foto de la misión). fondo=False: sin el recuadro negro."""
    r = pygame.Rect(rect)
    if fondo:
        pygame.draw.rect(sup, config.NEGRO, r)
    cx, cy = r.center
    radio = min(r.w, r.h) // 3
    if destino in ("órbita de Marte", "superficie de Marte"):
        pygame.draw.circle(sup, (190, 80, 50), (cx, cy), radio)
        pygame.draw.circle(sup, (150, 60, 40), (cx - radio // 3, cy + radio // 4), radio // 4)
    elif destino == "órbita lunar":
        pygame.draw.circle(sup, (170, 170, 175), (cx, cy), radio)
        pygame.draw.circle(sup, (130, 130, 135), (cx + radio // 3, cy - radio // 4), radio // 5)
        dibujar_tierra(sup, r.x + 14, r.y + 14, 6)               # la Tierra a lo lejos
    else:                                         # LEO: la Tierra con continentes, girando
        dibujar_tierra(sup, cx, cy, radio, tiempo * 0.3)
    # Satélite dando vueltas
    angulo = tiempo * 0.8
    sx = cx + int((radio + 12) * math.cos(angulo))
    sy = cy + int((radio + 12) * math.sin(angulo) * 0.5)
    pygame.draw.rect(sup, config.GRIS_CLARO, (sx - 2, sy - 2, 4, 4))
    pygame.draw.rect(sup, config.AZUL, (sx - 7, sy - 1, 4, 2))
    pygame.draw.rect(sup, config.AZUL, (sx + 3, sy - 1, 4, 2))
    if nombre:
        estilo.texto(sup, nombre, cx, r.bottom - 10, config.LETRA_PEQUENA, config.COLOR_TEXTO_SUAVE,
                     centrado=True)


def dibujar_tierra_y_cohete(sup, tiempo):
    """Ilustración de la pantalla de inicio: la Tierra abajo con nubes y un cohete
    que despega dejando una estela de humo."""
    # La Tierra con continentes: solo se ve su parte de arriba (horizonte)
    horizonte = imagen_horizonte(config.ANCHO, 80, 300)
    sup.blit(horizonte, (0, config.ALTO - 74))
    # Nubes pixeladas que se mueven despacio
    for i in range(6):
        x = int((i * 113 + tiempo * 8) % 560) + 40
        y = config.ALTO - 60 + (i % 3) * 18
        pygame.draw.rect(sup, config.BLANCO, (x, y, 22, 4))
        pygame.draw.rect(sup, config.BLANCO, (x + 5, y - 3, 12, 3))
    # Cohete que sube y vuelve a empezar, con humo detrás
    altura = int((tiempo * 25) % 260)
    y_cohete = config.ALTO - 40 - altura
    for i in range(1, 7):
        radio = 3 + i
        pygame.draw.circle(sup, config.GRIS_CLARO if i % 2 else config.GRIS, (520, y_cohete + 14 + i * 9), radio)
    dibujar_cohete(sup, 520, y_cohete, tiempo=tiempo, fuego=True)


def dibujar_parlante(sup, x, y, silenciado):
    """Ícono de parlante de 11x9 px (esquina de arriba a la derecha). Tecla M = silencio.
    silenciado=True: con una X roja; si no, con dos ondas de sonido."""
    color = config.GRIS_CLARO
    pygame.draw.rect(sup, color, (x, y + 3, 3, 3))                         # caja del parlante
    pygame.draw.polygon(sup, color, [(x + 3, y + 3), (x + 6, y), (x + 6, y + 8), (x + 3, y + 5)])
    if silenciado:
        pygame.draw.line(sup, config.ROJO, (x + 8, y + 2), (x + 11, y + 6))
        pygame.draw.line(sup, config.ROJO, (x + 11, y + 2), (x + 8, y + 6))
    else:
        pygame.draw.line(sup, color, (x + 8, y + 3), (x + 8, y + 5))
        pygame.draw.line(sup, color, (x + 10, y + 1), (x + 10, y + 7))


# ---------------------------------------------------------------------------
# La Tierra con continentes (v2, punto 16)
# ---------------------------------------------------------------------------
# Mapa del mundo de 64 x 32 celdas (proyección "rectangular": cada columna es una
# longitud, de -180° a 180°, y cada fila una latitud, de 90° a -90°).
#   "#" = tierra   "." = mar   "*" = hielo (polos y Groenlandia)
# Se ven América, Europa, África, Asia y Australia.
MAPA_MUNDO = [
    "****************************************************************",
    "****************************************************************",
    "......................*****..............###..######............",
    "...#############.....#******......#.###########################.",
    "..##################..#####......###############################",
    "..###################..........#.##############################.",
    ".......##############..........############################.....",
    ".........##########............########..##############..#......",
    ".........##########...........########...##############.##......",
    "...........########...........##.......##.###############.......",
    "...........#####............##############...#..#########.......",
    "............####...........################.###.....###.........",
    ".............###............###############.###..##.............",
    "...............###...........##########......##.####.#..........",
    ".................#######....#############....##..###.#..........",
    ".................########.....#.########.............#..........",
    ".................########........######...........########......",
    ".................#########.......######.........................",
    "..................########.........####.#.............#####.....",
    "...................######.........#######...........########....",
    "...................#####..........#####.#..........#########....",
    "...................####...........####..............########....",
    "...................###.................................#......#.",
    "...................###...................................#....#.",
    "...................##...........................................",
    "...................#............................................",
    "................................................................",
    "................................................................",
    "****************************************************************",
    "****************************************************************",
    "****************************************************************",
    "****************************************************************",
]
ANCHO_MAPA = len(MAPA_MUNDO[0])
ALTO_MAPA = len(MAPA_MUNDO)

COLORES_MAPA = {"#": config.TIERRA_VERDE, ".": config.TIERRA_AZUL, "*": config.BLANCO}
# Lo mismo, más oscuro, para el borde de la esfera (así se ve redonda)
COLORES_MAPA_SOMBRA = {"#": config.VERDE_OSCURO, ".": config.AZUL_OSCURO, "*": config.GRIS_CLARO}

PASOS_GIRO = 32              # la Tierra que gira se guarda en 32 posiciones
_cache_tierra = {}           # {(radio, paso): imagen} para no recalcular cada cuadro
_cache_horizonte = {}


def celda_mapa(latitud, longitud):
    """Letra del mapa ("#", "." o "*") en esa latitud y longitud (en radianes)."""
    fila = int((math.pi / 2 - latitud) / math.pi * ALTO_MAPA)
    columna = int((longitud + math.pi) / (2 * math.pi) * ANCHO_MAPA) % ANCHO_MAPA
    fila = max(0, min(ALTO_MAPA - 1, fila))
    return MAPA_MUNDO[fila][columna]


def color_esfera(dx, dy, radio, giro):
    """Color del punto (dx, dy) de una esfera de 'radio' vista de frente (dx, dy medidos
    desde el centro). 'giro' (radianes) rota la Tierra. Devuelve None fuera del disco."""
    distancia2 = dx * dx + dy * dy
    if distancia2 > radio * radio:
        return None
    z = math.sqrt(radio * radio - distancia2)               # "profundidad" del punto
    latitud = math.asin(max(-1.0, min(1.0, -dy / radio)))
    longitud = math.atan2(dx, z) + giro
    longitud = (longitud + math.pi) % (2 * math.pi) - math.pi
    letra = celda_mapa(latitud, longitud)
    # Sombra: el Sol ilumina desde arriba a la izquierda y un poco de frente.
    # 'luz' es cuánto mira ese punto hacia el Sol (producto punto con la dirección de la luz).
    luz = (-0.45 * dx - 0.45 * dy + 0.77 * z) / radio
    if luz < 0.12:
        return COLORES_MAPA_SOMBRA[letra]
    return COLORES_MAPA[letra]


def imagen_tierra(radio, giro=0.0):
    """Imagen transparente de la Tierra (disco de 'radio' px) con sus continentes y un
    anillo de atmósfera. Se calcula píxel a píxel UNA vez por tamaño y posición de giro."""
    radio = max(2, int(radio))
    paso = int(round(giro / (2 * math.pi) * PASOS_GIRO)) % PASOS_GIRO
    clave = (radio, paso)
    if clave in _cache_tierra:
        return _cache_tierra[clave]
    giro = paso * 2 * math.pi / PASOS_GIRO
    lado = radio * 2 + 4
    imagen = pygame.Surface((lado, lado), pygame.SRCALPHA)
    centro = radio + 2
    pygame.draw.circle(imagen, config.CIELO, (centro, centro), radio + 1)     # atmósfera
    for y in range(-radio, radio + 1):
        for x in range(-radio, radio + 1):
            color = color_esfera(x + 0.5, y + 0.5, radio, giro)
            if color is not None:
                imagen.set_at((centro + x, centro + y), color)
    _cache_tierra[clave] = imagen
    return imagen


def dibujar_tierra(sup, cx, cy, radio, giro=0.0):
    """Dibuja la Tierra con continentes centrada en (cx, cy). giro en radianes."""
    imagen = imagen_tierra(radio, giro)
    sup.blit(imagen, imagen.get_rect(center=(int(cx), int(cy))))


def imagen_horizonte(ancho, alto, radio, giro=-1.0):
    """La parte de ARRIBA de una Tierra enorme (el horizonte visto desde la órbita):
    imagen de 'ancho' x 'alto' px; el punto más alto de la Tierra queda en y = 4.
    Solo se calcula la franja visible (una esfera de radio 420 entera sería muy lenta).
    Truco simple: la longitud sale de la x (curvada hacia los bordes) y la latitud de la
    altura (de 50° N junto al horizonte a 10° S abajo), así se ven continentes conocidos."""
    clave = (ancho, alto, radio)
    if clave in _cache_horizonte:
        return _cache_horizonte[clave]
    imagen = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    cx = ancho / 2
    cy = radio + 4                                           # centro de la esfera (fuera de la imagen)
    for y in range(alto):
        dy = y + 0.5 - cy
        if abs(dy) >= radio:
            continue
        media_cuerda = math.sqrt(radio * radio - dy * dy)    # medio ancho de la Tierra en esa fila
        profundidad = (y - 4) / alto                         # 0 en el horizonte, 1 abajo
        latitud = math.radians(50 - 60 * max(0.0, profundidad) ** 0.7)
        for x in range(ancho):
            dx = x + 0.5 - cx
            distancia = math.sqrt(dx * dx + dy * dy)
            if distancia <= radio:
                u = max(-1.0, min(1.0, dx / media_cuerda))
                longitud = math.asin(u) * 0.9 + giro
                longitud = (longitud + math.pi) % (2 * math.pi) - math.pi
                letra = celda_mapa(latitud, longitud)
                if distancia > radio - 3:
                    color = COLORES_MAPA_SOMBRA[letra]       # borde más oscuro
                else:
                    color = COLORES_MAPA[letra]
                imagen.set_at((x, y), color)
            elif distancia <= radio + 4:
                imagen.set_at((x, y), config.CIELO)          # atmósfera
    _cache_horizonte[clave] = imagen
    return imagen


def dibujar_mapa_plano(sup, rect):
    """Mapa del mundo plano (para la pantalla grande de la sala de control).
    Cada celda del mapa se pinta como un rectángulo dentro de 'rect'."""
    r = pygame.Rect(rect)
    for fila in range(ALTO_MAPA):
        y0 = r.y + fila * r.h // ALTO_MAPA
        y1 = r.y + (fila + 1) * r.h // ALTO_MAPA
        for columna in range(ANCHO_MAPA):
            letra = MAPA_MUNDO[fila][columna]
            if letra == ".":
                continue                                     # el mar es el fondo de la pantalla
            x0 = r.x + columna * r.w // ANCHO_MAPA
            x1 = r.x + (columna + 1) * r.w // ANCHO_MAPA
            color = config.VERDE if letra == "#" else config.GRIS_CLARO
            pygame.draw.rect(sup, color, (x0, y0, max(1, x1 - x0), max(1, y1 - y0)))
