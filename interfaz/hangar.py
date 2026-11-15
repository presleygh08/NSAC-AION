# hangar.py
# Hangar del laboratorio (sección 4.6 de la especificación): la "ventana" de la derecha.
#   - El cohete de la misión, en pixel art, junto a su torre de lanzamiento.
#   - Antes de CML 1 lo tapan unas cortinas que se abren hacia los lados (~1 s).
#   - Cada vez que el jugador confirma una estación, se reproduce una animación de
#     ensamblaje de ~1,5 s con su herramienta (brazo robótico, manguera, grúa...).
#     No bloquea al jugador: depende solo del tiempo, se dibuja cuadro a cuadro.
#   - El cohete muestra qué partes ya se montaron, pero NO si alcanzan su mínimo
#     (por ejemplo, el tanque siempre se ve lleno, sea cual sea la cantidad elegida).
#   - v2 (punto 10): los paneles solares y la antena se montan PLEGADOS. Solo se abren en
#     la simulación, al llegar a órbita (parámetro 'apertura': 0 = plegado, 1 = abierto).
#
# Todas las medidas son relativas a 'rect' (el recuadro del hangar) para poder moverlo.

import math

import pygame

from interfaz import config, estilo, sprites

# --- Estilo del cohete según la misión (sale de estado["cohete"]; sin logos) ---
ESTILO_POR_DEFECTO = {"cuerpo": config.BLANCO, "nariz": config.ROJO, "franja": config.GRIS,
                      "propulsores": None, "aletas": config.ROJO}
ESTILOS_COHETE = {
    "Electron": {"cuerpo": (40, 40, 48), "nariz": config.BLANCO, "franja": (80, 80, 92),
                 "propulsores": None, "aletas": (80, 80, 92)},
    "Falcon 9": {"cuerpo": config.BLANCO, "nariz": config.BLANCO, "franja": config.NEGRO,
                 "propulsores": None, "aletas": config.GRIS_OSCURO},
    "Falcon Heavy": {"cuerpo": config.BLANCO, "nariz": config.BLANCO, "franja": config.NEGRO,
                     "propulsores": config.BLANCO, "aletas": config.GRIS_OSCURO},
    "SLS block 1": {"cuerpo": config.NARANJA, "nariz": config.BLANCO, "franja": config.BLANCO,
                    "propulsores": config.BLANCO, "aletas": config.GRIS_OSCURO},
}

ANCHO_COHETE = 28
COLOR_PARED = (30, 34, 50)
COLOR_PARED_LINEA = (40, 46, 66)
COLOR_BORDE_COHETE = (20, 20, 28)


def avance(lab, clave, tiempo):
    """0 a 1: cuánto avanzó la animación de ensamblaje de ese recurso.
    None si el recurso aún no se confirmó."""
    if clave not in lab["partes"]:
        return None
    return max(0.0, min(1.0, (tiempo - lab["partes"][clave]) / config.DURACION_ENSAMBLAJE))


def mezcla(a, b, f):
    """Punto intermedio entre a y b (f = 0 da a, f = 1 da b). Sirve para números y para (x, y)."""
    if isinstance(a, tuple):
        return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
    return a + (b - a) * f


class Medidas:
    """Puntos importantes del cohete (y del hangar), calculados a partir del centro
    del cohete 'cx' y de la y del suelo 'suelo'. 'interior' es el recuadro del hangar
    (solo hace falta para la grúa y las herramientas)."""

    def __init__(self, cx, suelo, interior=None):
        if interior is None:
            interior = pygame.Rect(cx - 120, suelo - 300, 240, 336)
        self.interior = pygame.Rect(interior)
        self.suelo = suelo                              # y del suelo (base del cohete)
        self.cx = cx                                    # centro del cohete
        self.izq = self.cx - ANCHO_COHETE // 2          # bordes del cuerpo
        self.der = self.cx + ANCHO_COHETE // 2
        # Secciones del cohete, de abajo hacia arriba
        self.y_tobera = self.suelo - 8
        self.y_motor = self.y_tobera - 34               # motor: y_motor .. y_tobera
        self.y_tanque = self.y_motor - 60               # tanque: y_tanque .. y_motor
        self.y_franja = self.y_tanque - 4               # franja entre etapas
        self.y_carga = self.y_franja - 40               # módulo de carga: y_carga .. y_franja
        self.y_nariz = self.y_carga - 30                # nariz: y_nariz .. y_carga
        # Torre y grúa
        self.x_torre = self.izq - 54
        self.y_torre = self.y_nariz - 30
        self.y_grua = self.interior.y + 28
        # Dónde quedan las partes
        self.anillos = [self.y_carga + 35, self.y_tanque + 4, self.y_tanque + 34, self.y_motor + 26]
        self.y_paneles = self.y_carga + 12
        self.pos_antena = (self.der - 2, self.y_carga - 2)
        self.pos_caja = (self.cx - 6, self.y_carga + 24)
        self.y_baterias = self.y_motor + 8


def medidas_hangar(rect):
    """Medidas del cohete dentro del recuadro del hangar."""
    interior = pygame.Rect(rect).inflate(-8, -8)
    return Medidas(interior.centerx + 8, interior.bottom - 36, interior)


# ---------------------------------------------------------------------------
# Fondo, torre y cohete
# ---------------------------------------------------------------------------

def dibujar_fondo(sup, m, textos_hangar):
    """Pared con paneles, viga de la grúa con focos, suelo con franja de seguridad."""
    i = m.interior
    pygame.draw.rect(sup, COLOR_PARED, i)
    for x in range(i.x + 12, i.right, 24):
        pygame.draw.line(sup, COLOR_PARED_LINEA, (x, i.y), (x, m.suelo))
    # Viga de la grúa con focos debajo
    pygame.draw.rect(sup, config.GRIS, (i.x, m.y_grua - 4, i.w, 5))
    for x in range(i.x + 20, i.right, 50):
        pygame.draw.rect(sup, config.AMARILLO, (x, m.y_grua + 1, 6, 2))
    # Suelo y franja amarilla y negra
    pygame.draw.rect(sup, config.GRIS_OSCURO, (i.x, m.suelo, i.w, i.bottom - m.suelo))
    for x in range(i.x, i.right, 8):
        color = config.AMARILLO if (x // 8) % 2 == 0 else config.NEGRO
        pygame.draw.rect(sup, color, (x, m.suelo, 8, 3))
    estilo.texto(sup, textos_hangar, i.centerx, i.y + 10, config.LETRA_PEQUENA,
                 config.COLOR_TEXTO_SUAVE, centrado=True)


def dibujar_torre(sup, m, con_propulsores):
    """Torre de celosía a la izquierda del cohete con dos brazos de servicio que llegan
    al cuerpo (o al propulsor lateral, si el cohete los tiene)."""
    x = m.x_torre
    ancho = 14
    pygame.draw.rect(sup, config.GRIS, (x, m.y_torre, 2, m.suelo - m.y_torre))
    pygame.draw.rect(sup, config.GRIS, (x + ancho - 2, m.y_torre, 2, m.suelo - m.y_torre))
    for y in range(m.y_torre, m.suelo, 10):                       # celosía en zigzag
        pygame.draw.line(sup, config.GRIS, (x, y), (x + ancho, y + 10))
        pygame.draw.line(sup, config.GRIS_OSCURO, (x, y + 10), (x + ancho, y))
    pygame.draw.rect(sup, config.ROJO, (x + 5, m.y_torre - 4, 4, 4))  # luz de la punta
    # Brazos de servicio: uno al módulo de carga y otro al tanque
    hasta = m.izq - 13 if con_propulsores else m.izq - 1
    for y in (m.y_carga + 20, m.y_tanque + 26):
        pygame.draw.rect(sup, config.GRIS_CLARO, (x + ancho, y, hasta - (x + ancho), 3))


def dibujar_propulsores(sup, m, color):
    """Dos propulsores laterales (Falcon Heavy, SLS)."""
    for x in (m.izq - 12, m.der + 2):
        y_arriba = m.y_franja + 6
        pygame.draw.rect(sup, COLOR_BORDE_COHETE, (x - 1, y_arriba - 1, 12, m.y_tobera - y_arriba + 2))
        pygame.draw.rect(sup, color, (x, y_arriba, 10, m.y_tobera - y_arriba))
        for i in range(5):                                         # nariz escalonada
            pygame.draw.rect(sup, color, (x + 5 - i, y_arriba - 10 + i * 2, 2 * i, 2))
        pygame.draw.rect(sup, config.GRIS_OSCURO, (x + 2, m.y_tobera, 6, 6))  # tobera


def dibujar_cohete(sup, m, nombre_cohete, con_nariz=True):
    """Cuerpo del cohete con su estilo, sin partes montadas.
    con_nariz=False: sin la cofia (la nave ya se separó en órbita)."""
    e = ESTILOS_COHETE.get(nombre_cohete, ESTILO_POR_DEFECTO)
    if e["propulsores"] is not None:
        dibujar_propulsores(sup, m, e["propulsores"])
    # Aletas y tobera
    for lado in (-1, 1):
        borde = m.izq if lado == -1 else m.der
        puntos = [(borde, m.y_motor + 6), (borde + lado * 10, m.suelo - 2), (borde, m.y_tobera)]
        pygame.draw.polygon(sup, e["aletas"], puntos)
    pygame.draw.rect(sup, config.GRIS_OSCURO, (m.cx - 7, m.y_tobera, 14, 8))
    # Cuerpo (con un borde oscuro para que se vea sobre cualquier fondo)
    alto = m.y_tobera - m.y_carga
    pygame.draw.rect(sup, COLOR_BORDE_COHETE, (m.izq - 1, m.y_carga - 1, ANCHO_COHETE + 2, alto + 2))
    pygame.draw.rect(sup, e["cuerpo"], (m.izq, m.y_carga, ANCHO_COHETE, alto))
    pygame.draw.rect(sup, e["franja"], (m.izq, m.y_franja, ANCHO_COHETE, 4))
    # Nariz escalonada (15 escalones de 2 px)
    for i in range(15 if con_nariz else 0):
        ancho = int(ANCHO_COHETE * (i + 1) / 15)
        pygame.draw.rect(sup, e["nariz"], (m.cx - ancho // 2, m.y_nariz + i * 2, ancho, 2))
    # Ventana del módulo de carga y ranura del tanque (vacía hasta cargar combustible)
    pygame.draw.circle(sup, COLOR_BORDE_COHETE, (m.cx, m.y_carga + 13), 5)
    pygame.draw.circle(sup, config.CIAN, (m.cx, m.y_carga + 13), 3)
    pygame.draw.rect(sup, COLOR_BORDE_COHETE, (m.cx - 4, m.y_tanque + 4, 8, m.y_motor - m.y_tanque - 8))


# ---------------------------------------------------------------------------
# Partes montadas (estado final) — se dibujan con el avance 'a' (1 = terminado)
# ---------------------------------------------------------------------------

def parte_estructura(sup, m, anillos_puestos):
    for y in m.anillos[:anillos_puestos]:
        pygame.draw.rect(sup, config.GRIS, (m.izq - 2, y, ANCHO_COHETE + 4, 3))
        pygame.draw.rect(sup, config.GRIS_CLARO, (m.izq - 2, y, ANCHO_COHETE + 4, 1))


def parte_propulsion(sup, m, nivel):
    """Combustible en la ranura del tanque. nivel 0 a 1 (al terminar, siempre 1)."""
    alto_total = m.y_motor - m.y_tanque - 8
    alto = int(alto_total * nivel)
    pygame.draw.rect(sup, config.NARANJA, (m.cx - 3, m.y_motor - 4 - alto, 6, alto))


def parte_potencia(sup, m, a, apertura=0.0):
    """Paneles solares. a = avance del montaje (0 a 1); apertura = 0 plegados (una tira
    angosta pegada a cada costado), 1 abiertos (3 segmentos de 10 px a cada lado)."""
    if apertura <= 0:
        alto = int(12 * a)                                       # la tira plegada "crece" al montarse
        for lado in (-1, 1):
            x = m.izq - 4 if lado == -1 else m.der + 1
            if alto > 0:
                pygame.draw.rect(sup, COLOR_BORDE_COHETE, (x - 1, m.y_paneles - 3, 5, alto + 2))
                pygame.draw.rect(sup, config.AZUL, (x, m.y_paneles - 2, 3, alto))
        return
    largo = int(4 + 26 * apertura)
    for lado in (-1, 1):
        borde = m.izq if lado == -1 else m.der
        x = borde - largo if lado == -1 else borde
        if largo > 0:
            pygame.draw.rect(sup, COLOR_BORDE_COHETE, (x, m.y_paneles - 1, largo, 10))
            pygame.draw.rect(sup, config.AZUL, (x, m.y_paneles, largo, 8))
            for paso in range(10, largo, 10):                    # líneas entre segmentos
                xx = borde - paso if lado == -1 else borde + paso
                pygame.draw.line(sup, config.AZUL_OSCURO, (xx, m.y_paneles), (xx, m.y_paneles + 7))
        pygame.draw.rect(sup, config.GRIS, (borde - 1 if lado == -1 else borde, m.y_paneles + 3, 2, 2))


def dibujar_antena(sup, x, y):
    """Antena parabólica: plato (semicírculo) con su receptor. (x, y) = base del plato."""
    pygame.draw.circle(sup, config.GRIS_CLARO, (int(x), int(y) - 6), 7, draw_top_right=True,
                       draw_top_left=True)
    pygame.draw.rect(sup, config.GRIS_CLARO, (int(x) - 7, int(y) - 6, 15, 2))
    pygame.draw.line(sup, config.GRIS, (int(x), int(y) - 6), (int(x), int(y) - 13))
    pygame.draw.rect(sup, config.ROJO, (int(x) - 1, int(y) - 14, 2, 2))


def dibujar_antena_plegada(sup, x, y):
    """Antena plegada: el plato cerrado y acostado junto a su poste. (x, y) = base."""
    pygame.draw.rect(sup, COLOR_BORDE_COHETE, (int(x) - 1, int(y) - 6, 9, 5))
    pygame.draw.rect(sup, config.GRIS_CLARO, (int(x), int(y) - 5, 7, 3))
    pygame.draw.rect(sup, config.ROJO, (int(x) + 6, int(y) - 5, 1, 1))


def parte_comunicaciones(sup, m, apertura=0.0):
    """Antena: plegada (apertura < 0.5) o abierta con su plato."""
    x, y = m.pos_antena
    pygame.draw.rect(sup, config.GRIS, (x, y - 2, 2, 4))              # poste
    if apertura < 0.5:
        dibujar_antena_plegada(sup, x - 4, y)
    else:
        dibujar_antena(sup, x + 1, y - 2)


def dibujar_caja(sup, x, y):
    """Caja de instrumentos (amarilla, 12x8)."""
    pygame.draw.rect(sup, COLOR_BORDE_COHETE, (int(x) - 1, int(y) - 1, 14, 10))
    pygame.draw.rect(sup, config.AMARILLO, (int(x), int(y), 12, 8))
    pygame.draw.rect(sup, config.NEGRO, (int(x) + 3, int(y) + 3, 6, 2))


def parte_datos(sup, m):
    dibujar_caja(sup, m.pos_caja[0], m.pos_caja[1])


def parte_tiempo(sup, m, baterias):
    """Baterías verdes en el motor (0 a 3)."""
    for i in range(baterias):
        x = m.izq + 3 + i * 8
        pygame.draw.rect(sup, COLOR_BORDE_COHETE, (x - 1, m.y_baterias - 1, 8, 10))
        pygame.draw.rect(sup, config.VERDE, (x, m.y_baterias, 6, 8))
        pygame.draw.rect(sup, config.BLANCO, (x + 2, m.y_baterias - 2, 2, 2))


# ---------------------------------------------------------------------------
# Herramientas de las animaciones (solo mientras a < 1)
# ---------------------------------------------------------------------------

def brazo_robotico(sup, m, a):
    """Brazo de 2 segmentos que sale del suelo a la derecha y coloca 4 anillos.
    Cada cuarto del tiempo lleva una viga a un anillo."""
    hombro = (m.interior.right - 22, m.suelo - 6)
    recogida = (m.interior.right - 34, m.suelo - 10)        # donde toma cada viga
    indice = min(3, int(a * 4))
    sub = (a * 4) - indice                                  # 0 a 1 dentro del cuarto
    destino = (m.der + 6, m.anillos[indice] + 1)
    if sub < 0.6:                                           # va con la viga hasta el anillo
        punta = mezcla(recogida, destino, sub / 0.6)
        lleva_viga = True
    else:                                                   # vuelve vacío a buscar otra
        punta = mezcla(destino, recogida, (sub - 0.6) / 0.4)
        lleva_viga = False
    codo = ((hombro[0] + punta[0]) / 2 + 14, min(hombro[1], punta[1]) - 18)
    pygame.draw.rect(sup, config.GRIS_OSCURO, (hombro[0] - 8, m.suelo - 4, 16, 4))   # base
    pygame.draw.line(sup, config.AMARILLO, hombro, codo, 4)
    pygame.draw.line(sup, config.AMARILLO, codo, punta, 3)
    pygame.draw.circle(sup, config.GRIS_OSCURO, (int(codo[0]), int(codo[1])), 3)
    pygame.draw.circle(sup, config.GRIS_OSCURO, (int(hombro[0]), int(hombro[1])), 3)
    if lleva_viga:
        pygame.draw.rect(sup, config.GRIS_CLARO, (int(punta[0]) - 10, int(punta[1]) - 1, 12, 3))
    return indice + (1 if sub >= 0.6 else 0)                # anillos ya colocados


def manguera(sup, m, a, tiempo):
    """Manguera del brazo de la torre al tanque, con "gotas" que avanzan."""
    inicio = (m.x_torre + 14, m.y_tanque + 27)
    fin = (m.izq, m.y_tanque + 40)
    puntos = []
    for i in range(11):
        f = i / 10
        x, y = mezcla(inicio, fin, f)
        puntos.append((x, y + math.sin(math.pi * f) * 10))      # cuelga un poco
    pygame.draw.lines(sup, config.NEGRO, False, puntos, 3)
    for k in range(3):                                           # flujo
        f = (tiempo * 1.5 + k / 3) % 1
        x, y = mezcla(inicio, fin, f)
        pygame.draw.rect(sup, config.NARANJA, (int(x) - 1, int(y + math.sin(math.pi * f) * 10) - 1, 3, 3))


def grua(sup, m, x_carro, y_gancho):
    """Carro de la grúa en la viga y su cable hasta el gancho."""
    pygame.draw.rect(sup, config.AMARILLO, (int(x_carro) - 5, m.y_grua - 6, 10, 5))
    pygame.draw.line(sup, config.GRIS_CLARO, (int(x_carro), m.y_grua), (int(x_carro), int(y_gancho)))


def antena_bajando(sup, m, a):
    """La grúa baja la antena (plegada) desde la viga hasta su soporte."""
    x, y_final = m.pos_antena
    y = mezcla(m.y_grua + 20, y_final, a)
    grua(sup, m, x - 1, y - 6)
    dibujar_antena_plegada(sup, x - 4, y)


def caja_con_grua(sup, m, a):
    """La grúa sube la caja desde el suelo (primera mitad) y la lleva al cohete (segunda)."""
    x_inicio = m.interior.right - 30
    x_final, y_final = m.pos_caja
    y_alta = m.y_carga - 20
    if a < 0.5:
        x = x_inicio
        y = mezcla(m.suelo - 10, y_alta, a / 0.5)
    elif a < 0.8:
        x = mezcla(x_inicio, x_final, (a - 0.5) / 0.3)
        y = y_alta
    else:
        x = x_final
        y = mezcla(y_alta, y_final, (a - 0.8) / 0.2)
    grua(sup, m, x + 6, y)
    dibujar_caja(sup, x, y)


def carrito(sup, m, a):
    """Carrito con baterías que entra rodando hasta la base del cohete (70 % del tiempo)."""
    x = mezcla(m.interior.right + 10, m.der + 14, min(1.0, a / 0.7))
    y = m.suelo - 10
    pygame.draw.rect(sup, config.GRIS, (int(x), y, 24, 7))
    for rueda in (4, 19):
        pygame.draw.circle(sup, config.NEGRO, (int(x) + rueda, m.suelo - 2), 2)
    if a < 0.7:                                       # baterías arriba del carrito
        for i in range(3):
            pygame.draw.rect(sup, config.VERDE, (int(x) + 2 + i * 7, y - 6, 5, 6))
    return 0 if a < 0.7 else min(3, 1 + int((a - 0.7) / 0.1))


def chispas(sup, x, y, tiempo, intensidad=1.0):
    """Destellos (cruces) alrededor de un punto."""
    for i in range(6):
        angulo = i * 1.05 + tiempo * 6
        r = 8 + 6 * intensidad
        px = int(x + math.cos(angulo) * r)
        py = int(y + math.sin(angulo) * r)
        color = config.AMARILLO if i % 2 == 0 else config.BLANCO
        pygame.draw.rect(sup, color, (px - 2, py, 5, 1))
        pygame.draw.rect(sup, color, (px, py - 2, 1, 5))


def punto_de_la_parte(m, clave):
    """Dónde salen las chispas al terminar de montar cada parte."""
    puntos = {"estructura": (m.cx, m.y_tanque + 20), "propulsion": (m.cx, m.y_tanque + 30),
              "potencia": (m.cx, m.y_paneles + 4), "comunicaciones": m.pos_antena,
              "datos": (m.pos_caja[0] + 6, m.pos_caja[1] + 4), "tiempo": (m.cx, m.y_baterias + 4)}
    return puntos.get(clave, (m.cx, m.y_tanque))


# ---------------------------------------------------------------------------
# Dibujo principal
# ---------------------------------------------------------------------------

def dibujar_partes_y_animaciones(sup, m, lab, tiempo):
    """Partes montadas + herramientas de las animaciones en curso + chispas al terminar."""
    a = {}
    for clave in lab["partes"]:
        a[clave] = avance(lab, clave, tiempo)

    # 1. Partes (con su avance; 1 = estado final)
    if "estructura" in a:
        if a["estructura"] < 1:
            anillos = brazo_robotico(sup, m, a["estructura"])
        else:
            anillos = 4
        parte_estructura(sup, m, anillos)
    if "propulsion" in a:
        parte_propulsion(sup, m, a["propulsion"])          # al terminar: lleno (no revela el mínimo)
        if a["propulsion"] < 1:
            manguera(sup, m, a["propulsion"], tiempo)
    if "potencia" in a:
        parte_potencia(sup, m, a["potencia"])               # plegados (v2)
    if "comunicaciones" in a:
        if a["comunicaciones"] < 1:
            antena_bajando(sup, m, a["comunicaciones"])
        else:
            parte_comunicaciones(sup, m)
    if "datos" in a:
        if a["datos"] < 1:
            caja_con_grua(sup, m, a["datos"])
        else:
            parte_datos(sup, m)
    if "tiempo" in a:
        if a["tiempo"] < 1:
            parte_tiempo(sup, m, carrito(sup, m, a["tiempo"]))
        else:
            parte_tiempo(sup, m, 3)

    # 2. Recursos que no tienen dibujo propio: chispas mientras se "montan"
    for clave in a:
        if clave not in ("estructura", "propulsion", "potencia", "comunicaciones", "datos", "tiempo") \
                and a[clave] < 1:
            chispas(sup, m.cx, m.y_tanque, tiempo, a[clave])

    # 3. Destello de 0,3 s al terminar cada parte
    for clave in lab["partes"]:
        pasado = tiempo - lab["partes"][clave] - config.DURACION_ENSAMBLAJE
        if 0 <= pasado < 0.3:
            x, y = punto_de_la_parte(m, clave)
            chispas(sup, x, y, tiempo, pasado / 0.3)


def dibujar_partes_finales(sup, m, claves, apertura=0.0):
    """Partes ya montadas (estado final, sin herramientas) de las claves dadas.
    apertura: 0 = paneles y antena plegados, 1 = abiertos."""
    if "estructura" in claves:
        parte_estructura(sup, m, 4)
    if "propulsion" in claves:
        parte_propulsion(sup, m, 1)
    if "potencia" in claves:
        parte_potencia(sup, m, 1, apertura)
    if "comunicaciones" in claves:
        parte_comunicaciones(sup, m, apertura)
    if "datos" in claves:
        parte_datos(sup, m)
    if "tiempo" in claves:
        parte_tiempo(sup, m, 3)


def dibujar_cohete_mision(sup, cx, suelo, nombre_cohete, claves, apertura=0.0, con_nariz=True):
    """El cohete de la misión con las partes que el jugador montó (lo usa la simulación).
    cx = centro; suelo = y de la base. Devuelve sus Medidas."""
    m = Medidas(cx, suelo)
    dibujar_cohete(sup, m, nombre_cohete, con_nariz)
    dibujar_partes_finales(sup, m, claves, apertura)
    return m


# Tamaño de la imagen del cohete completo (con paneles abiertos y antena)
ANCHO_IMAGEN = 100
ALTO_IMAGEN = 220


def imagen_cohete(nombre_cohete, claves, apertura=0.0, con_nariz=True):
    """El cohete de la misión dibujado en una imagen transparente de 100x220 px
    (para moverlo o romperlo en pedazos en la simulación). Devuelve (imagen, medidas):
    las medidas están en coordenadas de la imagen; la base queda en y = ALTO_IMAGEN - 8.
    apertura: 0 = paneles y antena plegados (despegue), 1 = abiertos (en órbita).
    con_nariz=False: sin la cofia (para recortar la nave ya separada)."""
    imagen = pygame.Surface((ANCHO_IMAGEN, ALTO_IMAGEN), pygame.SRCALPHA)
    m = dibujar_cohete_mision(imagen, ANCHO_IMAGEN // 2, ALTO_IMAGEN - 8, nombre_cohete, claves,
                              apertura, con_nariz)
    return imagen, m


def dibujar(sup, rect, lab, nombre_cohete, tiempo, apertura, texto_hangar):
    """Dibuja todo el hangar en 'rect'.
    apertura: 0 = cortinas cerradas, 1 = abiertas (la calcula el laboratorio)."""
    m = medidas_hangar(rect)
    pygame.draw.rect(sup, config.NEGRO, rect)
    recorte_anterior = sup.get_clip()
    sup.set_clip(m.interior)                    # nada se sale del hangar (p. ej. el carrito)

    dibujar_fondo(sup, m, texto_hangar)
    estilo_cohete = ESTILOS_COHETE.get(nombre_cohete, ESTILO_POR_DEFECTO)
    dibujar_torre(sup, m, estilo_cohete["propulsores"] is not None)
    dibujar_cohete(sup, m, nombre_cohete)
    dibujar_partes_y_animaciones(sup, m, lab, tiempo)

    # Cortinas con su barra arriba
    sprites.dibujar_cortinas(sup, m.interior, apertura)
    pygame.draw.rect(sup, config.GRIS_CLARO, (m.interior.x, m.interior.y, m.interior.w, 3))

    sup.set_clip(recorte_anterior)
    pygame.draw.rect(sup, config.COLOR_BORDE, rect, 2)
