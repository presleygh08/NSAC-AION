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


EXPRESIONES_NPC = ["neutral", "feliz", "pensativo", "preocupado", "sorprendido"]


def dibujar_npc(sup, x, y, expresion="neutral"):
    """Retrato del NPC (directora/director de vuelo) de 32x32 px con auriculares.
    expresion: "neutral", "feliz", "pensativo", "preocupado" o "sorprendido"."""
    oscuro = (30, 30, 40)
    boca = (150, 70, 70)
    pygame.draw.rect(sup, config.GRIS_OSCURO, (x, y, 32, 32))
    pygame.draw.rect(sup, (200, 150, 110), (x + 9, y + 7, 14, 15))      # cara
    pygame.draw.rect(sup, (170, 170, 175), (x + 8, y + 4, 16, 5))       # pelo gris

    # Ojos y cejas
    if expresion == "sorprendido":
        pygame.draw.rect(sup, oscuro, (x + 12, y + 12, 2, 3))           # ojos grandes
        pygame.draw.rect(sup, oscuro, (x + 18, y + 12, 2, 3))
        pygame.draw.rect(sup, oscuro, (x + 11, y + 10, 4, 1))           # cejas altas
        pygame.draw.rect(sup, oscuro, (x + 17, y + 10, 4, 1))
    elif expresion == "pensativo":
        pygame.draw.rect(sup, oscuro, (x + 13, y + 12, 2, 2))           # mira hacia arriba
        pygame.draw.rect(sup, oscuro, (x + 19, y + 12, 2, 2))
        pygame.draw.rect(sup, oscuro, (x + 17, y + 10, 4, 1))           # una ceja levantada
    elif expresion == "preocupado":
        pygame.draw.rect(sup, oscuro, (x + 12, y + 13, 2, 2))
        pygame.draw.rect(sup, oscuro, (x + 18, y + 13, 2, 2))
        pygame.draw.line(sup, oscuro, (x + 11, y + 12), (x + 14, y + 11))   # cejas inclinadas
        pygame.draw.line(sup, oscuro, (x + 18, y + 11), (x + 21, y + 12))
    else:                                                               # neutral y feliz
        pygame.draw.rect(sup, oscuro, (x + 12, y + 13, 2, 2))
        pygame.draw.rect(sup, oscuro, (x + 18, y + 13, 2, 2))

    # Boca
    if expresion == "feliz":
        pygame.draw.rect(sup, boca, (x + 13, y + 18, 6, 1))
        pygame.draw.rect(sup, boca, (x + 12, y + 17, 1, 1))             # comisuras arriba
        pygame.draw.rect(sup, boca, (x + 19, y + 17, 1, 1))
    elif expresion == "preocupado":
        pygame.draw.rect(sup, boca, (x + 13, y + 18, 6, 1))
        pygame.draw.rect(sup, boca, (x + 12, y + 19, 1, 1))             # comisuras abajo
        pygame.draw.rect(sup, boca, (x + 19, y + 19, 1, 1))
    elif expresion == "sorprendido":
        pygame.draw.rect(sup, boca, (x + 15, y + 17, 3, 3), 1)          # boca en "o"
    elif expresion == "pensativo":
        pygame.draw.rect(sup, boca, (x + 15, y + 18, 4, 1))             # boca de lado
    else:
        pygame.draw.rect(sup, boca, (x + 13, y + 18, 6, 1))

    pygame.draw.rect(sup, oscuro, (x + 6, y + 10, 3, 6))                # auricular
    pygame.draw.rect(sup, oscuro, (x + 7, y + 16, 1, 5))                # micrófono
    pygame.draw.rect(sup, config.AZUL, (x + 7, y + 23, 18, 9))          # uniforme


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


def dibujar_cortinas(sup, rect, apertura):
    """Cortinas rojas que tapan el cohete. apertura: 0 = cerradas, 1 = abiertas del todo."""
    r = pygame.Rect(rect)
    mitad = r.w // 2
    ancho = int(mitad * (1 - apertura))
    if ancho <= 0:
        return
    for i in range(2):
        if i == 0:
            zona = pygame.Rect(r.x, r.y, ancho, r.h)                # izquierda
        else:
            zona = pygame.Rect(r.right - ancho, r.y, ancho, r.h)   # derecha
        pygame.draw.rect(sup, (150, 30, 40), zona)
        for xx in range(zona.x + 3, zona.right, 6):                 # pliegues
            pygame.draw.line(sup, (110, 20, 30), (xx, zona.y), (xx, zona.bottom))


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
        pygame.draw.circle(sup, config.TIERRA_AZUL, (r.x + 14, r.y + 14), 6)
    else:                                         # LEO: la Tierra
        pygame.draw.circle(sup, config.TIERRA_AZUL, (cx, cy), radio)
        pygame.draw.circle(sup, config.TIERRA_VERDE, (cx - radio // 3, cy - radio // 5), radio // 3)
        pygame.draw.circle(sup, config.TIERRA_VERDE, (cx + radio // 3, cy + radio // 3), radio // 4)
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
    cx = config.ANCHO // 2
    pygame.draw.circle(sup, config.AZUL_OSCURO, (cx, config.ALTO + 236), 306)   # borde de atmósfera
    pygame.draw.circle(sup, config.TIERRA_AZUL, (cx, config.ALTO + 230), 300)
    pygame.draw.circle(sup, config.TIERRA_VERDE, (cx - 120, config.ALTO + 10), 60)
    pygame.draw.circle(sup, config.TIERRA_VERDE, (cx + 150, config.ALTO + 30), 70)
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
