# simulacion.py
# Animación del lanzamiento (sección 5 de la especificación).
#   - Antes de animar, app.py llama a nucleo.simular(estado) y guarda el resultado en
#     ui["sim"]["resultado"]. Aquí NO se muestra hasta el final.
#   - Despega el MISMO cohete que el jugador armó en el hangar (hangar.imagen_cohete).
#   - Primeros DURACION_COMUN segundos iguales para éxito y falla (tensión):
#     cuenta regresiva, ignición con humo y temblor, despegue y ascenso del cielo al espacio.
#   - Luego la animación se ramifica según el resultado:
#       éxito en LEO -> se apaga el motor, se abre la cofia y el satélite queda en órbita
#       Marte / Luna -> viaje de transferencia y llegada: órbita (Marte, Luna) o
#                       aterrizaje con paracaídas (superficie de Marte)
#       explota      -> el cohete tiembla, se desarma en 3 pedazos y explota
#       no_llega     -> LEO: el motor se apaga y no alcanza la órbita; lejos: se queda a
#                       mitad del viaje y se va a la deriva
#       se_apaga, incomunicada, sin_ciencia, fuera_de_tiempo -> la nave llega pero se
#                       apaga / la señal se corta / el instrumento no obtiene nada / se acaba el tiempo
#   - SKIP (o Espacio) salta al final. Al terminar, app.py pasa a "resultados".
#
# "Cámara": el cohete sube; cuando pasa cierta altura, la cámara lo sigue y el suelo,
# las nubes y el humo bajan por la pantalla.

import math
import random

import pygame

from interfaz import config, estilo, hangar, sprites
from interfaz.componentes import Boton

CENTRO_X = config.ANCHO // 2
Y_SUELO = 290                      # y del suelo en pantalla antes del despegue
SUBIDA_LIBRE = 40                  # px que sube el cohete antes de que la cámara lo siga
DIALOGO = pygame.Rect(16, 300, 500, 52)
T_IGNICION = 1.8
T_DESPEGUE = 2.4
ALTO_BASE_IMAGEN = hangar.ALTO_IMAGEN - 8     # y de la base del cohete dentro de su imagen
BAJO_CENTRO = ALTO_BASE_IMAGEN - hangar.ALTO_IMAGEN / 2   # de su centro a su base (px)


def nueva_sim(resultado, tiempo):
    """Sub-estado de la simulación."""
    return {"t0": tiempo, "resultado": resultado, "terminada": False, "imagen": None}


# ---------------------------------------------------------------------------
# Ayudas
# ---------------------------------------------------------------------------

def mezclar(color1, color2, f):
    """Color intermedio: f = 0 da color1, f = 1 da color2."""
    f = max(0.0, min(1.0, f))
    return (int(color1[0] + (color2[0] - color1[0]) * f),
            int(color1[1] + (color2[1] - color1[1]) * f),
            int(color1[2] + (color2[2] - color1[2]) * f))


def tipo_final(resultado):
    """'exito', 'explota', 'no_llega' o la falla que sea (usa la primera falla)."""
    if resultado["exito"]:
        return "exito"
    return resultado["falla"]


def preparar_imagen(ui):
    """Imagen del cohete de la misión con las partes montadas (se hace una sola vez)."""
    sim = ui["sim"]
    if sim["imagen"] is None:
        claves = list(ui["lab"]["partes"].keys()) if ui.get("lab") else []
        imagen, medidas = hangar.imagen_cohete(ui["estado"]["cohete"], claves)
        sim["imagen"] = imagen
        sim["medidas"] = medidas
    return sim["imagen"], sim["medidas"]


def pedazo(imagen, y_arriba, y_abajo):
    """Copia de una franja horizontal de la imagen del cohete (para romperlo en pedazos)."""
    return imagen.subsurface((0, y_arriba, imagen.get_width(), y_abajo - y_arriba)).copy()


def pegar_centrado(sup, imagen, cx, cy, angulo=0, escala=1.0):
    """Pega una imagen centrada en (cx, cy), girada 'angulo' grados y escalada (sin suavizar)."""
    if escala != 1.0:
        ancho = max(1, int(imagen.get_width() * escala))
        alto = max(1, int(imagen.get_height() * escala))
        imagen = pygame.transform.scale(imagen, (ancho, alto))
    if angulo != 0:
        imagen = pygame.transform.rotate(imagen, angulo)
    rect = imagen.get_rect(center=(int(cx), int(cy)))
    sup.blit(imagen, rect)


def dibujar_llama(sup, cx, y_base, t, largo=18, escala=1.0):
    """Llama del motor que parpadea, debajo de (cx, y_base)."""
    largo = int((largo + 6 * abs(math.sin(t * 25))) * escala)
    ancho = int(8 * escala)
    pygame.draw.polygon(sup, config.NARANJA, [(cx - ancho, y_base), (cx + ancho, y_base), (cx, y_base + largo)])
    pygame.draw.polygon(sup, config.AMARILLO, [(cx - ancho // 2, y_base), (cx + ancho // 2, y_base),
                                               (cx, y_base + largo * 2 // 3)])


def dibujar_estrellas(sup, brillo):
    """Estrellas fijas que aparecen a medida que se sube (brillo 0 a 1)."""
    if brillo <= 0:
        return
    azar = random.Random(11)
    color = mezclar(config.CIELO, config.BLANCO, brillo)
    for _ in range(70):
        sup.set_at((azar.randrange(config.ANCHO), azar.randrange(config.ALTO)), color)


def dibujar_tierra_curva(sup, y_arriba):
    """Curva de la Tierra vista desde la órbita, con su atmósfera."""
    centro = (CENTRO_X, y_arriba + 420)
    pygame.draw.circle(sup, config.CIELO, centro, 424)
    pygame.draw.circle(sup, config.TIERRA_AZUL, centro, 420)
    pygame.draw.ellipse(sup, config.TIERRA_VERDE, (CENTRO_X - 190, y_arriba + 30, 110, 40))
    pygame.draw.ellipse(sup, config.TIERRA_VERDE, (CENTRO_X + 90, y_arriba + 45, 130, 50))
    for i in range(4):                                           # nubes (cerca del centro: sobre la Tierra)
        x = CENTRO_X - 150 + i * 90
        pygame.draw.rect(sup, config.BLANCO, (x, y_arriba + 22 + (i % 2) * 14, 30, 4))


def dibujar_dialogo(sup, frase):
    estilo.panel(sup, DIALOGO)
    sprites.dibujar_npc(sup, DIALOGO.right - 42, DIALOGO.y + 10)
    estilo.texto_multilinea(sup, frase, DIALOGO.x + 10, DIALOGO.y + 10, DIALOGO.w - 60,
                            config.LETRA_PEQUENA)


# ---------------------------------------------------------------------------
# Parte común: cuenta regresiva, ignición, despegue y ascenso
# ---------------------------------------------------------------------------

def altura(t):
    """Cuántos px subió el cohete en el segundo t (acelera después del despegue)."""
    if t < T_DESPEGUE:
        return 0.0
    return 55 * (t - T_DESPEGUE) ** 2


def parte_comun(sup, ui, textos, t):
    imagen, _ = preparar_imagen(ui)
    h = altura(t)
    camara = max(0.0, h - SUBIDA_LIBRE)          # cuánto bajó todo lo demás
    espacio = min(1.0, camara / 320)             # 0 = cielo, 1 = espacio

    sup.fill(mezclar(config.CIELO, config.AZUL_NOCHE, espacio))
    dibujar_estrellas(sup, (espacio - 0.4) / 0.6)

    # Nubes (quedan atrás mientras se sube)
    for i in range(5):
        y = 60 + i * 45 + camara * 1.2 - 120
        if -10 < y < config.ALTO:
            x = (i * 137) % 560 + 20
            pygame.draw.rect(sup, config.BLANCO, (x, int(y), 46, 6))
            pygame.draw.rect(sup, config.BLANCO, (x + 10, int(y) - 4, 24, 4))

    temblor = 0
    if T_IGNICION <= t < T_DESPEGUE + 0.8:
        temblor = 1 if int(t * 30) % 2 == 0 else -1

    # Suelo, plataforma y torre (bajan con la cámara)
    y_suelo = Y_SUELO + camara
    if y_suelo < config.ALTO:
        pygame.draw.rect(sup, config.TIERRA_VERDE, (0, int(y_suelo), config.ANCHO, config.ALTO))
        pygame.draw.rect(sup, config.GRIS_OSCURO, (CENTRO_X - 50, int(y_suelo), 100, 6))
        x_torre = CENTRO_X - 75
        sprites.dibujar_torre(sup, x_torre, int(y_suelo), 190)
        # Brazos de la torre: se apartan al despegar
        largo = 40 if t < T_DESPEGUE else max(0, int(40 - (t - T_DESPEGUE) * 80))
        for y_brazo in (int(y_suelo) - 150, int(y_suelo) - 100):
            if largo > 0:
                pygame.draw.rect(sup, config.GRIS_CLARO, (x_torre + 6, y_brazo, largo, 3))

    # Estela de humo detrás del cohete
    y_base = Y_SUELO - h + camara                # base del cohete en pantalla
    if t >= T_IGNICION:
        azar = random.Random(4)
        for k in range(14):
            alt = k * 26                          # altura a la que quedó esa nube
            if alt > h:
                break
            y = Y_SUELO - alt + camara + 6
            if -20 < y < config.ALTO + 20:
                radio = 6 + min(14, (h - alt) * 0.08) + azar.random() * 3
                pygame.draw.circle(sup, config.GRIS_CLARO, (CENTRO_X + azar.randint(-6, 6), int(y)), int(radio))
        # Humo grande en la plataforma
        if y_suelo < config.ALTO + 20:
            crecer = min(1.0, (t - T_IGNICION) / 1.5)
            for lado in (-1, 1):
                for j in range(3):
                    x = CENTRO_X + lado * (20 + j * 22 * crecer)
                    pygame.draw.circle(sup, config.GRIS_CLARO, (int(x), int(y_suelo) - 4), int(8 + 10 * crecer))

    # El cohete y su llama
    if t >= T_IGNICION:
        dibujar_llama(sup, CENTRO_X + temblor, int(y_base), t)
    sup.blit(imagen, (CENTRO_X - imagen.get_width() // 2 + temblor, int(y_base) - ALTO_BASE_IMAGEN))

    # Cuenta regresiva
    cuenta = textos["simulacion"]["cuenta"]
    indice = int(t / 0.6)
    if indice < len(cuenta):
        estilo.texto_contorno(sup, cuenta[indice], CENTRO_X, 60, config.LETRA_GIGANTE, config.AMARILLO,
                              config.NEGRO, 2)


# ---------------------------------------------------------------------------
# Ramas
# ---------------------------------------------------------------------------

Y_BASE_EN_ORBITA = Y_SUELO - SUBIDA_LIBRE      # donde quedó la base del cohete al terminar la parte común


def fondo_espacio(sup):
    sup.fill(config.AZUL_NOCHE)
    dibujar_estrellas(sup, 1.0)


def final_exito_leo(sup, ui, t):
    """Éxito en LEO: motor apagado, cofia que se abre y satélite que queda en órbita."""
    imagen, m = preparar_imagen(ui)
    fondo_espacio(sup)
    dibujar_tierra_curva(sup, 250 - int(min(t, 1.0) * 30))
    # Órbita punteada alrededor de la Tierra
    if t > 1.6:
        for i in range(0, 40):
            angulo = math.pi + i * math.pi / 40
            x = CENTRO_X + math.cos(angulo) * 300
            y = 400 + math.sin(angulo) * 260
            if i % 2 == 0:
                pygame.draw.rect(sup, config.CIAN, (int(x), int(y), 2, 2))

    y_base = Y_BASE_EN_ORBITA - t * 12                       # sigue subiendo despacio
    if t < 0.6:
        dibujar_llama(sup, CENTRO_X, int(y_base), t, 12)
    y_img = y_base - ALTO_BASE_IMAGEN                         # y de la imagen en pantalla

    # Pedazos de la imagen: cofia (nariz), satélite (módulo de carga) y la etapa (tanque + motor)
    cofia = pedazo(imagen, m.y_nariz - 18, m.y_carga)
    satelite = pedazo(imagen, m.y_carga, m.y_franja)
    etapa = pedazo(imagen, m.y_franja, hangar.ALTO_IMAGEN)

    separa = max(0.0, t - 1.0)                                # 0 hasta el segundo 1
    # Etapa: se queda atrás y baja
    pegar_centrado(sup, etapa, CENTRO_X - separa * 10, y_img + m.y_franja + etapa.get_height() / 2 + separa * 40,
                   angulo=separa * 12)
    # Satélite: sube un poco y se va a la derecha
    sx = CENTRO_X + separa * 50
    sy = y_img + m.y_carga + satelite.get_height() / 2 - separa * 25
    pegar_centrado(sup, satelite, sx, sy)
    # Paneles del satélite (tipo CubeSat) que se despliegan
    if t > 1.6:
        largo = int(min(1.0, (t - 1.6) / 0.6) * 18)
        pygame.draw.rect(sup, config.AZUL, (int(sx) - 14 - largo, int(sy) - 2, largo, 5))
        pygame.draw.rect(sup, config.AZUL, (int(sx) + 14, int(sy) - 2, largo, 5))
    # Cofia: se abre en dos mitades que se alejan girando
    mitad = cofia.get_width() // 2
    izquierda = cofia.subsurface((0, 0, mitad, cofia.get_height())).copy()
    derecha = cofia.subsurface((mitad, 0, mitad, cofia.get_height())).copy()
    cy = y_img + m.y_nariz - 18 + cofia.get_height() / 2 - separa * 20
    pegar_centrado(sup, izquierda, CENTRO_X - mitad / 2 - separa * 40, cy, angulo=separa * 40)
    pegar_centrado(sup, derecha, CENTRO_X + mitad / 2 + separa * 40, cy, angulo=-separa * 40)


def final_explota(sup, ui, t):
    """El cohete tiembla, se desarma en 3 pedazos y explota."""
    imagen, m = preparar_imagen(ui)
    fondo_espacio(sup)
    y_img = Y_BASE_EN_ORBITA - ALTO_BASE_IMAGEN
    T_ROTURA = 0.8
    if t < T_ROTURA:
        temblor = int(math.sin(t * 90) * 3)
        dibujar_llama(sup, CENTRO_X + temblor, Y_BASE_EN_ORBITA, t)
        sup.blit(imagen, (CENTRO_X - imagen.get_width() // 2 + temblor, y_img))
        if int(t * 8) % 2 == 0:                                # alarma roja que parpadea
            alarma = pygame.Surface((config.ANCHO, config.ALTO))
            alarma.set_alpha(60)
            alarma.fill(config.ROJO)
            sup.blit(alarma, (0, 0))
        return

    d = t - T_ROTURA
    # Tres pedazos: arriba (nariz + carga), tanque y motor, cada uno con su velocidad y giro
    pedazos = [
        (pedazo(imagen, m.y_nariz - 18, m.y_franja), -35, -55, 160),
        (pedazo(imagen, m.y_franja, m.y_motor), 30, -10, -120),
        (pedazo(imagen, m.y_motor, hangar.ALTO_IMAGEN), -5, 50, 90),
    ]
    arriba = m.y_nariz - 18
    for img, vx, vy, giro in pedazos:
        cy0 = y_img + arriba + img.get_height() / 2
        arriba = arriba + img.get_height()
        pegar_centrado(sup, img, CENTRO_X + vx * d, cy0 + vy * d + 20 * d * d, angulo=giro * d)

    # Bola de fuego y escombros
    centro = (CENTRO_X, int(y_img + m.y_franja))
    radio = int(10 + d * 70)
    if radio < 110:
        pygame.draw.circle(sup, config.ROJO, centro, radio)
        pygame.draw.circle(sup, config.NARANJA, centro, int(radio * 0.7))
        pygame.draw.circle(sup, config.AMARILLO, centro, int(radio * 0.4))
    else:
        for i in range(8):                                     # humo que queda
            angulo = i * 0.8
            pygame.draw.circle(sup, config.GRIS, (int(centro[0] + math.cos(angulo) * 50),
                                                  int(centro[1] + math.sin(angulo) * 40 - d * 10)), 18)
    azar = random.Random(5)
    for _ in range(18):
        angulo = azar.random() * 6.28
        velocidad = 50 + azar.random() * 80
        x = centro[0] + math.cos(angulo) * velocidad * d
        y = centro[1] + math.sin(angulo) * velocidad * d + 15 * d * d
        pygame.draw.rect(sup, config.GRIS_CLARO, (int(x), int(y), 4, 3))
    # Destello blanco los primeros 0.4 s
    if d < 0.4:
        destello = pygame.Surface((config.ANCHO, config.ALTO))
        destello.set_alpha(int(220 * (1 - d / 0.4)))
        destello.fill(config.BLANCO)
        sup.blit(destello, (0, 0))


def final_no_llega(sup, ui, textos, t):
    """El motor se apaga antes de tiempo: el cohete no alcanza la órbita objetivo y cae.
    Es un pequeño diagrama: se ve la órbita a la que debía llegar y lo que le faltó."""
    imagen, _ = preparar_imagen(ui)
    fondo_espacio(sup)
    dibujar_tierra_curva(sup, 300)
    # Órbita objetivo: línea punteada arriba
    Y_ORBITA = 56
    for x in range(20, config.ANCHO - 20, 12):
        pygame.draw.rect(sup, config.CIAN, (x, Y_ORBITA, 6, 2))
    estilo.texto(sup, textos["simulacion"]["orbita_objetivo"], 24, Y_ORBITA - 14, config.LETRA_PEQUENA, config.CIAN)

    # Se aleja la cámara: el cohete se achica a la mitad en 0.4 s
    escala = 1.0 - 0.5 * min(1.0, t / 0.4)
    # Altura: sube más despacio cada vez, llega a su punto más alto y cae
    T_CORTE = 0.8          # el motor se apaga
    T_CIMA = 1.6
    y_inicio = 230
    y_cima = 120           # nunca llega a la órbita
    if t < T_CIMA:
        f = t / T_CIMA
        y = y_inicio + (y_cima - y_inicio) * (1 - (1 - f) ** 2)
    else:
        y = y_cima + 90 * (t - T_CIMA) ** 2
    x = CENTRO_X + t * 30
    angulo = 0 if t < T_CIMA else -(t - T_CIMA) * 60     # se inclina al caer

    # Trayectoria (puntos que va dejando)
    for k in range(int(t / 0.08)):
        tk = k * 0.08
        if tk < T_CIMA:
            yk = y_inicio + (y_cima - y_inicio) * (1 - (1 - tk / T_CIMA) ** 2)
        else:
            yk = y_cima + 90 * (tk - T_CIMA) ** 2
        pygame.draw.rect(sup, config.GRIS_CLARO, (int(CENTRO_X + tk * 30), int(yk + BAJO_CENTRO * 0.5), 2, 2))
    # Lo que le faltó: flecha roja punteada de la cima a la órbita
    if t >= T_CIMA:
        x_cima = CENTRO_X + T_CIMA * 30
        y_punta = int(y_cima - BAJO_CENTRO * 0.5)              # punta del cohete en la cima
        for yy in range(Y_ORBITA + 4, y_punta, 8):
            pygame.draw.rect(sup, config.ROJO, (int(x_cima), yy, 2, 4))

    # Llama que "tose" antes de apagarse
    if t < T_CORTE and int(t * 12) % 3 != 0:
        dibujar_llama(sup, int(x), int(y + BAJO_CENTRO * escala), t, 10, escala)
    pegar_centrado(sup, imagen, x, y, angulo=angulo, escala=escala)


# ---------------------------------------------------------------------------
# Destinos lejanos (Marte, Luna) y fallas genéricas
# ---------------------------------------------------------------------------

T_VIAJE = 1.2                       # segundos del viaje de transferencia
POS_TIERRA_VIAJE = (70, 160)
POS_DESTINO_VIAJE = (540, 140)
CONTROL_ARCO = (300, 30)            # "tira" del arco hacia arriba
CENTRO_PLANETA = (CENTRO_X, 150)    # planeta grande al llegar
RADIO_PLANETA = 62


def es_marte(destino):
    return destino in ("órbita de Marte", "superficie de Marte")


def dibujar_planeta(sup, destino, cx, cy, r):
    """Planeta simple: Marte (rojo con casquete polar), la Luna (gris con cráteres) o la Tierra."""
    cx, cy, r = int(cx), int(cy), int(r)
    if es_marte(destino):
        pygame.draw.circle(sup, config.OXIDO, (cx, cy), r)
        pygame.draw.circle(sup, config.OXIDO_OSCURO, (cx - r // 3, cy + r // 5), r // 4)
        pygame.draw.circle(sup, config.OXIDO_OSCURO, (cx + r // 3, cy - r // 4), r // 6)
        pygame.draw.ellipse(sup, config.BLANCO, (cx - r // 3, cy - r + 1, 2 * r // 3, max(2, r // 6)))
    elif destino == "órbita lunar":
        pygame.draw.circle(sup, config.GRIS_LUNA, (cx, cy), r)
        for dx, dy, rr in ((-0.35, -0.2, 0.18), (0.3, 0.25, 0.22), (0.15, -0.45, 0.1), (-0.2, 0.45, 0.12)):
            pygame.draw.circle(sup, (130, 130, 128), (cx + int(dx * r), cy + int(dy * r)), max(1, int(rr * r)))
    else:
        pygame.draw.circle(sup, config.TIERRA_AZUL, (cx, cy), r)
        pygame.draw.circle(sup, config.TIERRA_VERDE, (cx - r // 3, cy - r // 5), max(1, r // 3))
        pygame.draw.circle(sup, config.TIERRA_VERDE, (cx + r // 3, cy + r // 3), max(1, r // 4))


def punto_arco(s):
    """Punto del arco de transferencia (s = 0 en la Tierra, s = 1 en el destino)."""
    a, c, b = POS_TIERRA_VIAJE, CONTROL_ARCO, POS_DESTINO_VIAJE
    x = (1 - s) ** 2 * a[0] + 2 * (1 - s) * s * c[0] + s ** 2 * b[0]
    y = (1 - s) ** 2 * a[1] + 2 * (1 - s) * s * c[1] + s ** 2 * b[1]
    return x, y


def nave(ui):
    """La nave = el módulo de carga del cohete armado (con paneles, antena, caja...)."""
    sim = ui["sim"]
    if sim.get("nave") is None:
        imagen, m = preparar_imagen(ui)
        sim["nave"] = pedazo(imagen, m.y_carga - 18, m.y_franja)
    return sim["nave"]


def nave_apagada(ui):
    """La misma nave, oscurecida (sin energía)."""
    sim = ui["sim"]
    if sim.get("nave_apagada") is None:
        copia = nave(ui).copy()
        copia.fill((80, 80, 90), special_flags=pygame.BLEND_RGB_MULT)
        sim["nave_apagada"] = copia
    return sim["nave_apagada"]


def etiqueta(sup, contenido, x, y, color):
    """Cartelito tipo ícono de estado ("NO SIGNAL", "POWER 0%"...)."""
    ancho = estilo.fuente(config.LETRA_PEQUENA).size(contenido)[0] + 10
    caja = pygame.Rect(0, 0, ancho, 14)
    caja.center = (int(x), int(y))
    pygame.draw.rect(sup, config.NEGRO, caja)
    pygame.draw.rect(sup, color, caja, 1)
    estilo.texto(sup, contenido, caja.centerx, caja.centery, config.LETRA_PEQUENA, color, centrado=True,
                 sombra=False)


def viaje(sup, ui, destino, t, s_max=1.0):
    """Viaje de transferencia: Tierra pequeña, destino, arco punteado y la nave que avanza.
    Devuelve la posición de la nave."""
    fondo_espacio(sup)
    dibujar_planeta(sup, "LEO", POS_TIERRA_VIAJE[0], POS_TIERRA_VIAJE[1], 14)
    dibujar_planeta(sup, destino, POS_DESTINO_VIAJE[0], POS_DESTINO_VIAJE[1], 34)
    for i in range(0, 41, 2):                                     # arco objetivo punteado
        x, y = punto_arco(i / 40)
        pygame.draw.rect(sup, config.CIAN, (int(x), int(y), 2, 2))
    s = min(s_max, t / T_VIAJE)
    x, y = punto_arco(s)
    pegar_centrado(sup, nave(ui), x, y, escala=0.35)
    return x, y


def posicion_en_orbita(angulo, radio_x=150, radio_y=55):
    return (CENTRO_PLANETA[0] + math.cos(angulo) * radio_x, CENTRO_PLANETA[1] + math.sin(angulo) * radio_y)


def orbita(sup, ui, destino, ta, imagen_nave, gira=True, deriva=0.0):
    """Planeta grande con la nave en órbita elíptica (detrás del planeta en la mitad de arriba).
    gira=False: la nave se detiene delante del planeta y se aleja 'deriva' segundos.
    Devuelve la posición de la nave."""
    fondo_espacio(sup)
    if destino == "órbita lunar":                                # la Tierra asoma en una esquina
        dibujar_planeta(sup, "LEO", 560, 40, 14)
    for i in range(0, 60, 2):                                     # órbita punteada
        x, y = posicion_en_orbita(i * math.pi / 30)
        pygame.draw.rect(sup, config.CIAN, (int(x), int(y), 2, 2))
    angulo = math.pi * 0.9 + (ta * 0.9 if gira else 0)
    x, y = posicion_en_orbita(angulo)
    x = x - deriva * 8                                           # a la deriva, alejándose
    y = y + deriva * 4
    detras = math.sin(angulo) < 0 and gira
    if detras:
        pegar_centrado(sup, imagen_nave, x, y, escala=0.5)
    if destino == "LEO":
        dibujar_tierra_curva(sup, 230)
    else:
        dibujar_planeta(sup, destino, CENTRO_PLANETA[0], CENTRO_PLANETA[1], RADIO_PLANETA)
    if not detras:
        pegar_centrado(sup, imagen_nave, x, y, escala=0.5)
    return x, y


def final_exito_lejos(sup, ui, t, destino):
    """Éxito en Marte o la Luna: viaje + llegada (órbita o aterrizaje)."""
    if t < T_VIAJE:
        viaje(sup, ui, destino, t)
        return
    ta = t - T_VIAJE
    if destino == "superficie de Marte":
        aterrizaje(sup, ui, ta)
        return
    x, y = orbita(sup, ui, destino, ta, nave(ui))
    if ta < 0.8:                                                 # encendido de frenado
        largo = int(10 + 4 * math.sin(ta * 30))
        pygame.draw.polygon(sup, config.NARANJA, [(int(x) + 12, int(y) - 3), (int(x) + 12, int(y) + 3),
                                                  (int(x) + 12 + largo, int(y))])


def aterrizaje(sup, ui, ta):
    """Superficie de Marte: entrada con brillo, paracaídas, cohetes de frenado y polvo."""
    Y_SUELO_MARTE = 250
    sup.fill(mezclar((40, 20, 30), config.ARENA, min(1.0, ta / 1.2)))     # el cielo marciano aparece
    pygame.draw.rect(sup, config.OXIDO, (0, Y_SUELO_MARTE, config.ANCHO, config.ALTO))
    for x, ancho in ((80, 40), (230, 24), (450, 50), (560, 30)):         # rocas y colinas
        pygame.draw.ellipse(sup, config.OXIDO_OSCURO, (x, Y_SUELO_MARTE - 6, ancho, 12))
    imagen = nave(ui)
    if ta < 0.8:                                                  # entrada: baja en diagonal y brilla
        x = 120 + ta * 150
        y = 40 + ta * 60
        pygame.draw.circle(sup, config.NARANJA, (int(x) + 6, int(y) + 10), 16)
        pygame.draw.circle(sup, config.AMARILLO, (int(x) + 4, int(y) + 8), 9)
    elif ta < 2.0:                                                # paracaídas
        x = 240
        y = 88 + (ta - 0.8) * 70
        pygame.draw.circle(sup, config.BLANCO, (x, int(y) - 40), 18, draw_top_left=True, draw_top_right=True)
        pygame.draw.circle(sup, config.ROJO, (x, int(y) - 40), 18, 2, draw_top_left=True, draw_top_right=True)
        for dx in (-17, 0, 17):
            pygame.draw.line(sup, config.GRIS_CLARO, (x + dx, int(y) - 40), (x, int(y) - 8))
    else:                                                         # cohetes de frenado y aterrizaje
        x = 240
        f = min(1.0, (ta - 2.0) / 0.8)
        y = 172 + f * (Y_SUELO_MARTE - 14 - 172)
        if f < 1:
            for dx in (-8, 8):
                pygame.draw.polygon(sup, config.NARANJA, [(x + dx - 3, int(y) + 12), (x + dx + 3, int(y) + 12),
                                                          (x + dx, int(y) + 22)])
        else:                                                     # polvo al tocar el suelo
            d = ta - 2.8
            for lado in (-1, 1):
                for j in range(3):
                    pygame.draw.circle(sup, config.ARENA, (x + lado * int(14 + j * 10 + d * 20), Y_SUELO_MARTE - 3),
                                       max(1, int(6 - d * 3)))
    pegar_centrado(sup, imagen, x, y, escala=0.45)
    if ta >= 0.8:                                                 # patas del módulo
        for dx in (-10, 10):
            pygame.draw.line(sup, config.GRIS_CLARO, (int(x) + dx // 2, int(y) + 8), (int(x) + dx, int(y) + 14), 2)


def final_no_llega_lejos(sup, ui, textos, t, destino):
    """Sin delta-v suficiente para llegar a Marte o la Luna: la nave se queda a mitad
    del arco de transferencia y se va a la deriva."""
    S_MAXIMO = 0.55
    f = min(1.0, t / 2.0)
    s = S_MAXIMO * (1 - (1 - f) ** 2)                             # cada vez más lento
    fondo_espacio(sup)
    dibujar_planeta(sup, "LEO", POS_TIERRA_VIAJE[0], POS_TIERRA_VIAJE[1], 14)
    dibujar_planeta(sup, destino, POS_DESTINO_VIAJE[0], POS_DESTINO_VIAJE[1], 34)
    for i in range(0, 41, 2):
        x, y = punto_arco(i / 40)
        color = config.ROJO if t >= 2.0 and i / 40 > S_MAXIMO else config.CIAN    # lo que faltó, en rojo
        pygame.draw.rect(sup, color, (int(x), int(y), 2, 2))
    estilo.texto(sup, textos["simulacion"]["orbita_objetivo"], POS_DESTINO_VIAJE[0], POS_DESTINO_VIAJE[1] + 44,
                 config.LETRA_PEQUENA, config.CIAN, centrado=True)
    x, y = punto_arco(s)
    deriva = max(0.0, t - 2.0)
    x = x + deriva * 6
    y = y + deriva * 10
    if t < 0.6 and int(t * 12) % 3 != 0:                          # el motor tose
        pygame.draw.polygon(sup, config.NARANJA, [(int(x) - 8, int(y) - 3), (int(x) - 8, int(y) + 3),
                                                  (int(x) - 18, int(y))])
    pegar_centrado(sup, nave(ui), x, y, angulo=deriva * 25, escala=0.35)


def final_falla_generica(sup, ui, textos, t, falla, destino):
    """se_apaga, incomunicada, sin_ciencia, fuera_de_tiempo: la nave LLEGA pero algo falla.
    En destinos lejanos primero hace el viaje; en LEO empieza ya en órbita."""
    iconos = textos["simulacion"]["iconos"]
    if destino != "LEO":
        if t < T_VIAJE:
            viaje(sup, ui, destino, t)
            return
        ta = t - T_VIAJE
    else:
        ta = t

    T_FALLA = 1.2                                                  # cuándo empieza a fallar
    apagada = False
    if falla == "se_apaga":
        # parpadea entre 1.2 y 1.8 s y luego queda apagada
        if ta >= T_FALLA + 0.6 or (ta >= T_FALLA and int(ta * 10) % 2 == 0):
            apagada = True
    if falla == "fuera_de_tiempo" and ta >= T_FALLA + 0.8:
        apagada = True
    imagen = nave_apagada(ui) if apagada else nave(ui)
    # Sin energía, sin datos o sin tiempo, la nave deja de maniobrar y se va a la deriva
    detenida = apagada or (falla == "sin_ciencia" and ta > T_FALLA + 0.6)
    if detenida:
        x, y = orbita(sup, ui, destino, 0, imagen, gira=False, deriva=max(0.0, ta - T_FALLA))
    else:
        x, y = orbita(sup, ui, destino, ta, imagen)

    if falla == "se_apaga" and ta >= T_FALLA + 0.6:
        etiqueta(sup, iconos["sin_energia"], x, y - 26, config.ROJO)
    elif falla == "incomunicada":
        # Ondas hacia la Tierra (arriba a la izquierda) que se cortan a mitad de camino
        tierra = (40, 40)
        if destino != "LEO":
            dibujar_planeta(sup, "LEO", tierra[0], tierra[1], 10)
        for k in range(4):
            f = ((ta * 0.8) + k / 4) % 1
            if f < 0.5:                                           # pasada la mitad, la señal se pierde
                px = x + (tierra[0] - x) * f
                py = y + (tierra[1] - y) * f
                pygame.draw.circle(sup, config.CIAN, (int(px), int(py)), 3 + int(f * 8), 1)
        if ta >= T_FALLA:
            etiqueta(sup, iconos["sin_senal"], x, y - 26, config.AMARILLO)
    elif falla == "sin_ciencia":
        if ta < T_FALLA + 0.6:                                    # rayo del instrumento que escanea
            cx, cy = CENTRO_PLANETA if destino != "LEO" else (CENTRO_X, 260)
            ancho = 18 + int(8 * math.sin(ta * 12))
            pygame.draw.polygon(sup, config.CIAN_OSCURO, [(int(x), int(y) + 6), (cx - ancho, cy - 10),
                                                         (cx + ancho, cy - 10)], 1)
        else:
            etiqueta(sup, iconos["sin_datos"], x, y - 26, config.AMARILLO)
    elif falla == "fuera_de_tiempo":
        # Reloj que corre rápido hasta llegar a cero
        cx, cy = 50, 50
        pygame.draw.circle(sup, config.BLANCO, (cx, cy), 14, 2)
        vuelta = min(1.0, ta / (T_FALLA + 0.8))
        angulo = -math.pi / 2 + vuelta * 2 * math.pi
        pygame.draw.line(sup, config.ROJO if vuelta >= 1 else config.BLANCO, (cx, cy),
                         (cx + int(math.cos(angulo) * 11), cy + int(math.sin(angulo) * 11)), 2)
        if vuelta >= 1:
            etiqueta(sup, iconos["sin_tiempo"], cx, cy + 26, config.ROJO)


def duracion_final(final, destino):
    """Los destinos lejanos tienen un viaje antes de llegar: su final dura más.
    La explosión ocurre en el ascenso, así que dura lo mismo en cualquier destino."""
    if destino == "LEO" or final == "explota":
        return config.DURACION_FINAL
    return config.DURACION_FINAL_LEJOS


def dibujar(sup, ui, textos):
    sim = ui["sim"]
    t = ui["tiempo"] - sim["t0"]
    frases = textos["simulacion"]["frases"]
    final = tipo_final(sim["resultado"])
    destino = ui["estado"]["destino"]

    if t < config.DURACION_COMUN:
        parte_comun(sup, ui, textos, t)
        frase = frases["despegue"]
    else:
        t2 = t - config.DURACION_COMUN
        if final == "exito" and destino == "LEO":
            final_exito_leo(sup, ui, t2)
        elif final == "exito":
            final_exito_lejos(sup, ui, t2, destino)
        elif final == "explota":
            final_explota(sup, ui, t2)
        elif final == "no_llega" and destino == "LEO":
            final_no_llega(sup, ui, textos, t2)
        elif final == "no_llega":
            final_no_llega_lejos(sup, ui, textos, t2, destino)
        else:
            final_falla_generica(sup, ui, textos, t2, final, destino)
        frase = frases.get(final, frases["despegue"])
        if t2 >= duracion_final(final, destino):
            sim["terminada"] = True        # app.py pasa a resultados

    dibujar_dialogo(sup, frase.replace("{nombre}", ui["jugador"]["nombre"]))
    estilo.texto(sup, textos["simulacion"]["ayuda_saltar"], config.ANCHO - 16, 12, config.LETRA_PEQUENA,
                 config.COLOR_TEXTO_SUAVE, derecha=True)
    return [Boton(textos["botones"]["saltar"], 530, 314, 94, config.ALTO_BOTON, "saltar_simulacion")]


def tecla(ui, evento):
    """Espacio = saltar al final."""
    if evento.key == pygame.K_SPACE:
        return ("saltar_simulacion", None)
    return None
