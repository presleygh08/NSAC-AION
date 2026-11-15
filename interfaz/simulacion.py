# simulacion.py
# Animación del lanzamiento (sección 5 de la especificación).
#   - Antes de animar, app.py llama a nucleo.simular(estado) y guarda el resultado en
#     ui["sim"]["resultado"]. Aquí NO se muestra hasta el final.
#   - Despega el MISMO cohete que el jugador armó en el hangar (hangar.imagen_cohete).
#   - Primeros DURACION_COMUN segundos iguales para éxito y falla (tensión):
#     cuenta regresiva, ignición con humo y temblor, despegue y GIRO POR GRAVEDAD
#     (v2, punto 15): el cohete sube recto, luego se va inclinando hasta ANGULO_FIN_COMUN
#     grados y su camino se curva, dejando una trayectoria punteada.
#   - Luego la animación se ramifica según el resultado (todas empiezan con el cohete
#     inclinado, en la misma posición en que terminó la parte común):
#       éxito en LEO -> se apaga el motor, el cohete queda horizontal, se abre la cofia y
#                       el satélite queda dando vueltas a la Tierra en su órbita punteada
#       Marte / Luna -> viaje de transferencia y llegada: órbita (Marte, Luna) o
#                       aterrizaje con paracaídas y rover (superficie de Marte)
#       explota      -> el cohete tiembla, se desarma en 3 pedazos y explota
#       no_llega     -> LEO: el motor se apaga y no alcanza la órbita; lejos: se queda a
#                       mitad del viaje y se va a la deriva
#       se_apaga, incomunicada, sin_ciencia, fuera_de_tiempo -> la nave llega pero se
#                       apaga / la señal se corta / el instrumento no obtiene nada / se acaba el tiempo
#   - v2 (D7): la simulación NUNCA se puede saltar (no hay SKIP) y dura 12-15 s.
#     Al terminar, app.py pasa a "resultados".
#   - v2 (punto 10): el cohete despega con paneles y antena PLEGADOS; se abren al llegar a
#     órbita (separación del satélite en LEO, o al salir hacia Marte / la Luna).
#   - v2 (D11): pitidos de cuenta regresiva, rugido de ignición y sonido de éxito o falla
#     (interfaz/sonido.py). Cada sonido suena una sola vez (sim["sonados"]).
#
# Ángulos: 0 = cohete vertical, 90 = horizontal apuntando a la derecha.
# "Cámara": el cohete sube; cuando pasa cierta altura, la cámara lo sigue y el suelo,
# las nubes y el humo se mueven por la pantalla.

import math
import random

import pygame

from interfaz import config, estilo, hangar, sonido, sprites

CENTRO_X = config.ANCHO // 2
Y_SUELO = 290                      # y del suelo en pantalla antes del despegue
SUBIDA_LIBRE = 40                  # px que sube el cohete antes de que la cámara lo siga
DIALOGO = pygame.Rect(16, 300, 500, 52)
T_IGNICION = 3 * config.SEGUNDOS_POR_CUENTA        # al aparecer "IGNITION!"
T_DESPEGUE = T_IGNICION + 0.6
DURACION_DESPLIEGUE = 0.6          # segundos que tardan en abrirse paneles y antena
ALTO_BASE_IMAGEN = hangar.ALTO_IMAGEN - 8     # y de la base del cohete dentro de su imagen
BAJO_CENTRO = ALTO_BASE_IMAGEN - hangar.ALTO_IMAGEN / 2   # de su centro a su base (px)

# Giro por gravedad
ACELERACION = 130                  # px/s²: la velocidad del cohete crece con el tiempo
T_INICIO_GIRO = 0.8                # segundos después del despegue en que empieza a inclinarse
ANGULO_FIN_COMUN = 60              # inclinación al terminar la parte común (grados)
CORRIMIENTO_FIN = 80               # px que la base se corre a la izquierda en pantalla al inclinarse
SUBIDA_FIN = 70                    # px que la base sube en pantalla al inclinarse (así se ve la estela)
PASO_CALCULO = 1 / 60              # paso de tiempo para calcular la trayectoria
Y_HORIZONTE = 290                  # y del borde de la Tierra al llegar al espacio
# Dónde termina la base del cohete en pantalla al final de la parte común
BASE_FIN = (CENTRO_X - CORRIMIENTO_FIN, Y_SUELO - SUBIDA_LIBRE - SUBIDA_FIN)


def nueva_sim(resultado, tiempo):
    """Sub-estado de la simulación."""
    sprites.imagen_horizonte(config.ANCHO, 150, 420)     # se calcula ya (tarda ~0,06 s una vez)
    return {"t0": tiempo, "resultado": resultado, "terminada": False, "imagen": None,
            "sonados": set()}


# ---------------------------------------------------------------------------
# Ayudas
# ---------------------------------------------------------------------------

def mezclar(color1, color2, f):
    """Color intermedio: f = 0 da color1, f = 1 da color2."""
    f = max(0.0, min(1.0, f))
    return (int(color1[0] + (color2[0] - color1[0]) * f),
            int(color1[1] + (color2[1] - color1[1]) * f),
            int(color1[2] + (color2[2] - color1[2]) * f))


def suave(f):
    """Curva suave de 0 a 1 (empieza y termina despacio)."""
    f = max(0.0, min(1.0, f))
    return f * f * (3 - 2 * f)


def sonar_una_vez(sim, nombre, clave=None):
    """Reproduce un sonido solo la primera vez que se llama con esa clave."""
    if clave is None:
        clave = nombre
    if clave not in sim["sonados"]:
        sim["sonados"].add(clave)
        sonido.tocar(nombre)


def tipo_final(resultado):
    """'exito', 'explota', 'no_llega' o la falla que sea (usa la primera falla)."""
    if resultado["exito"]:
        return "exito"
    return resultado["falla"]


def tipo_potencia(ui):
    """"solar" o "mmrtg" (v3, A: Harder usa un generador nuclear, sin paneles)."""
    return ui["estado"].get("tipo_potencia", "solar")


def bateria(sup, x, y, nivel):
    """Indicador de batería (v3, A): nivel de 0 a 1. Se pone rojo cuando queda poco."""
    pygame.draw.rect(sup, config.BLANCO, (x, y, 26, 12), 1)
    pygame.draw.rect(sup, config.BLANCO, (x + 26, y + 3, 2, 6))
    color = config.VERDE if nivel > 0.5 else (config.AMARILLO if nivel > 0.2 else config.ROJO)
    ancho = int(22 * max(0.0, min(1.0, nivel)))
    if ancho > 0:
        pygame.draw.rect(sup, color, (x + 2, y + 2, ancho, 8))


def claves_montadas(ui):
    return list(ui["lab"]["partes"].keys()) if ui.get("lab") else []


def preparar_imagen(ui):
    """Imagen del cohete de la misión con las partes montadas y los paneles y la antena
    PLEGADOS (despegue). Se hace una sola vez."""
    sim = ui["sim"]
    if sim["imagen"] is None:
        imagen, medidas = hangar.imagen_cohete(ui["estado"]["cohete"], claves_montadas(ui), 0.0,
                                               tipo_potencia=tipo_potencia(ui))
        sim["imagen"] = imagen
        sim["medidas"] = medidas
    return sim["imagen"], sim["medidas"]


def imagen_abierta(ui, apertura):
    """El mismo cohete SIN la cofia (la nave ya se separó) y con paneles y antena abiertos
    en 'apertura' (0 a 1). Se guardan 5 imágenes (0, 0.25, 0.5, 0.75 y 1) para no dibujar
    el cohete en cada cuadro. Sirve para recortar la nave o el satélite."""
    sim = ui["sim"]
    paso = round(max(0.0, min(1.0, apertura)) * 4)       # 0, 1, 2, 3 o 4
    if "abiertas" not in sim:
        sim["abiertas"] = {}
    if paso not in sim["abiertas"]:
        imagen, _ = hangar.imagen_cohete(ui["estado"]["cohete"], claves_montadas(ui), paso / 4,
                                         con_nariz=False, tipo_potencia=tipo_potencia(ui))
        sim["abiertas"][paso] = imagen
    return sim["abiertas"][paso]


def pedazo(imagen, y_arriba, y_abajo):
    """Copia de una franja horizontal de la imagen del cohete (para romperlo en pedazos)."""
    return imagen.subsurface((0, y_arriba, imagen.get_width(), y_abajo - y_arriba)).copy()


def pegar_centrado(sup, imagen, cx, cy, angulo=0, escala=1.0):
    """Pega una imagen centrada en (cx, cy), girada 'angulo' grados (positivo = contra
    las agujas del reloj, como pygame) y escalada (sin suavizar)."""
    if escala != 1.0:
        ancho = max(1, int(imagen.get_width() * escala))
        alto = max(1, int(imagen.get_height() * escala))
        imagen = pygame.transform.scale(imagen, (ancho, alto))
    if angulo != 0:
        imagen = pygame.transform.rotate(imagen, angulo)
    rect = imagen.get_rect(center=(int(cx), int(cy)))
    sup.blit(imagen, rect)


# --- Cohete inclinado -------------------------------------------------------

def punto_cohete(base, angulo, adelante, costado=0.0):
    """Punto de la pantalla a 'adelante' px de la base del cohete (hacia la nariz) y
    'costado' px hacia su derecha, con el cohete inclinado 'angulo' grados."""
    r = math.radians(angulo)
    hacia_nariz = (math.sin(r), -math.cos(r))
    hacia_derecha = (math.cos(r), math.sin(r))
    return (base[0] + hacia_nariz[0] * adelante + hacia_derecha[0] * costado,
            base[1] + hacia_nariz[1] * adelante + hacia_derecha[1] * costado)


def distancia_desde_base(y_arriba, y_abajo):
    """Distancia (px) entre la base del cohete y el centro de la franja y_arriba..y_abajo
    de su imagen. Sirve para ubicar cada pedazo cuando el cohete está inclinado."""
    return ALTO_BASE_IMAGEN - (y_arriba + y_abajo) / 2


def pegar_pedazo(sup, imagen, base, angulo, adelante, costado=0.0, giro_extra=0.0, escala=1.0):
    """Pega una imagen (el cohete o un pedazo) centrada a 'adelante' px de la base,
    inclinada igual que el cohete (más 'giro_extra' grados)."""
    x, y = punto_cohete(base, angulo, adelante * escala, costado * escala)
    pegar_centrado(sup, imagen, x, y, angulo=-(angulo + giro_extra), escala=escala)


def dibujar_llama(sup, cx, y_base, t, largo=18, escala=1.0, angulo=0.0):
    """Llama del motor que parpadea, saliendo de la base (cx, y_base) hacia atrás
    del cohete inclinado 'angulo' grados."""
    largo = (largo + 6 * abs(math.sin(t * 25))) * escala
    ancho = 8 * escala
    base = (cx, y_base)

    def p(costado, atras):
        return punto_cohete(base, angulo, -atras, costado)

    pygame.draw.polygon(sup, config.NARANJA, [p(-ancho, 0), p(ancho, 0), p(0, largo)])
    pygame.draw.polygon(sup, config.AMARILLO, [p(-ancho / 2, 0), p(ancho / 2, 0), p(0, largo * 2 / 3)])


# --- Fondos -----------------------------------------------------------------

def dibujar_estrellas(sup, brillo):
    """Estrellas fijas que aparecen a medida que se sube (brillo 0 a 1)."""
    if brillo <= 0:
        return
    azar = random.Random(11)
    color = mezclar(config.CIELO, config.BLANCO, brillo)
    for _ in range(70):
        sup.set_at((azar.randrange(config.ANCHO), azar.randrange(config.ALTO)), color)


def dibujar_tierra_curva(sup, y_arriba):
    """Curva de la Tierra (con continentes) vista desde la órbita; su borde de arriba
    queda en y_arriba."""
    alto = max(1, config.ALTO - int(y_arriba) + 6)
    imagen = sprites.imagen_horizonte(config.ANCHO, 150, 420)
    sup.blit(imagen, (0, int(y_arriba) - 4), (0, 0, config.ANCHO, alto))


def fondo_espacio(sup):
    sup.fill(config.AZUL_NOCHE)
    dibujar_estrellas(sup, 1.0)


def dibujar_dialogo(sup, frase, expresion="neutral"):
    """Cuadro de AION abajo, con su expresión (v2, D5)."""
    estilo.panel(sup, DIALOGO)
    sprites.dibujar_npc(sup, DIALOGO.right - 42, DIALOGO.y + 10, expresion)
    estilo.texto_multilinea(sup, frase, DIALOGO.x + 10, DIALOGO.y + 10, DIALOGO.w - 60,
                            config.LETRA_PEQUENA)


# ---------------------------------------------------------------------------
# Parte común: cuenta regresiva, ignición, despegue y giro por gravedad
# ---------------------------------------------------------------------------

def angulo_ascenso(t):
    """Inclinación del cohete (grados) en el segundo t: 0 hasta T_INICIO_GIRO después
    del despegue y luego sube suavemente hasta ANGULO_FIN_COMUN al final de la parte común."""
    vuelo = t - T_DESPEGUE
    if vuelo < T_INICIO_GIRO:
        return 0.0
    duracion_giro = config.DURACION_COMUN - T_DESPEGUE - T_INICIO_GIRO
    return ANGULO_FIN_COMUN * suave((vuelo - T_INICIO_GIRO) / duracion_giro)


def trayectoria(t):
    """Lista de posiciones (x, h) de la base del cohete desde el despegue hasta el
    segundo t, en px "del mundo" (x hacia la derecha, h = altura sobre la plataforma).
    Se calcula paso a paso: la velocidad crece y apunta hacia donde mira el cohete,
    por eso el camino se curva cuando el cohete se inclina."""
    puntos = [(0.0, 0.0)]
    x = 0.0
    h = 0.0
    pasos = int(max(0.0, t - T_DESPEGUE) / PASO_CALCULO)
    for i in range(pasos):
        tiempo = T_DESPEGUE + i * PASO_CALCULO
        velocidad = ACELERACION * (tiempo - T_DESPEGUE)
        angulo = math.radians(angulo_ascenso(tiempo))
        x = x + velocidad * math.sin(angulo) * PASO_CALCULO
        h = h + velocidad * math.cos(angulo) * PASO_CALCULO
        puntos.append((x, h))
    return puntos


ALTURA_FIN = trayectoria(config.DURACION_COMUN)[-1][1]     # altura al final de la parte común


def camara(t, x, h):
    """Cuánto se movió la cámara (cam_x, cam_y) para seguir al cohete, y dónde queda la
    base del cohete en pantalla."""
    giro = angulo_ascenso(t) / ANGULO_FIN_COMUN        # 0 = vertical, 1 = inclinación final
    base_x = CENTRO_X - CORRIMIENTO_FIN * giro
    cam_x = x - (base_x - CENTRO_X)
    cam_y = max(0.0, h - SUBIDA_LIBRE - SUBIDA_FIN * giro)
    base = (base_x, Y_SUELO - h + cam_y)
    return cam_x, cam_y, base


def a_pantalla(x, h, cam_x, cam_y):
    """De coordenadas del mundo (x, altura) a la pantalla."""
    return CENTRO_X + x - cam_x, Y_SUELO - h + cam_y


def parte_comun(sup, ui, textos, t):
    imagen, _ = preparar_imagen(ui)
    puntos = trayectoria(t)
    x, h = puntos[-1]
    cam_x, cam_y, base = camara(t, x, h)
    angulo = angulo_ascenso(t)
    espacio = min(1.0, cam_y / (ALTURA_FIN - SUBIDA_LIBRE - SUBIDA_FIN)) ** 0.8   # 0 = cielo, 1 = espacio

    sup.fill(mezclar(config.CIELO, config.AZUL_NOCHE, espacio))
    dibujar_estrellas(sup, (espacio - 0.4) / 0.6)
    # La Tierra aparece abajo cuando ya casi estamos en el espacio
    if espacio > 0.55:
        y_borde = config.ALTO + 20 - (config.ALTO + 20 - Y_HORIZONTE) * suave((espacio - 0.55) / 0.45)
        dibujar_tierra_curva(sup, y_borde)

    # Nubes (quedan atrás mientras se sube; arriba, en el espacio, ya no hay)
    for i in range(5 if espacio < 0.5 else 0):
        y = 60 + i * 45 + cam_y * 1.2 - 120
        if -10 < y < config.ALTO:
            xn = ((i * 137 - cam_x * 1.2) % 700) - 40
            pygame.draw.rect(sup, config.BLANCO, (int(xn), int(y), 46, 6))
            pygame.draw.rect(sup, config.BLANCO, (int(xn) + 10, int(y) - 4, 24, 4))

    temblor = 0
    if T_IGNICION <= t < T_DESPEGUE + 0.8:
        temblor = 1 if int(t * 30) % 2 == 0 else -1

    # Suelo, plataforma y torre (se mueven con la cámara)
    x_plataforma, y_suelo = a_pantalla(0, 0, cam_x, cam_y)
    if y_suelo < config.ALTO:
        pygame.draw.rect(sup, config.TIERRA_VERDE, (0, int(y_suelo), config.ANCHO, config.ALTO))
        pygame.draw.rect(sup, config.GRIS_OSCURO, (int(x_plataforma) - 50, int(y_suelo), 100, 6))
        x_torre = int(x_plataforma) - 75
        sprites.dibujar_torre(sup, x_torre, int(y_suelo), 190)
        # Brazos de la torre: se apartan al despegar
        largo = 40 if t < T_DESPEGUE else max(0, int(40 - (t - T_DESPEGUE) * 80))
        for y_brazo in (int(y_suelo) - 150, int(y_suelo) - 100):
            if largo > 0:
                pygame.draw.rect(sup, config.GRIS_CLARO, (x_torre + 6, y_brazo, largo, 3))

    if t >= T_IGNICION:
        # Humo grande en la plataforma
        if y_suelo < config.ALTO + 20:
            crecer = min(1.0, (t - T_IGNICION) / 1.5)
            for lado in (-1, 1):
                for j in range(3):
                    xh = x_plataforma + lado * (20 + j * 22 * crecer)
                    pygame.draw.circle(sup, config.GRIS_CLARO, (int(xh), int(y_suelo) - 4), int(8 + 10 * crecer))
        # Estela de humo cerca del suelo (cada vez más ancha) ...
        azar = random.Random(4)
        for k in range(0, len(puntos), 8):
            px, ph = puntos[k]
            if ph > 260 or espacio > 0.6:
                break
            sx, sy = a_pantalla(px, ph, cam_x, cam_y)
            edad = (len(puntos) - k) * PASO_CALCULO
            radio = 5 + min(14, edad * 6) + azar.random() * 3
            if -20 < sy < config.ALTO + 20:
                pygame.draw.circle(sup, config.GRIS_CLARO, (int(sx), int(sy) + 6), int(radio))
        # ... y la trayectoria punteada (se ve curvarse con el giro por gravedad)
        for k in range(0, len(puntos), 4):
            sx, sy = a_pantalla(puntos[k][0], puntos[k][1], cam_x, cam_y)
            if 0 <= sx < config.ANCHO and 0 <= sy < config.ALTO and (k // 4) % 2 == 0:
                pygame.draw.rect(sup, config.AMARILLO, (int(sx) - 1, int(sy) - 1, 3, 3))

    # El cohete (inclinado) y su llama
    base_temblor = (base[0] + temblor, base[1])
    if t >= T_IGNICION:
        dibujar_llama(sup, base_temblor[0], base_temblor[1], t, angulo=angulo)
    pegar_pedazo(sup, imagen, base_temblor, angulo, BAJO_CENTRO)

    # Cuenta regresiva
    cuenta = textos["simulacion"]["cuenta"]
    indice = int(t / config.SEGUNDOS_POR_CUENTA)
    if indice < len(cuenta):
        estilo.texto_contorno(sup, cuenta[indice], CENTRO_X, 60, config.LETRA_GIGANTE, config.AMARILLO,
                              config.NEGRO, 2)


# ---------------------------------------------------------------------------
# Ramas en LEO y explosión (empiezan con el cohete en BASE_FIN, inclinado)
# ---------------------------------------------------------------------------

T_MECO = 0.6            # se apaga el motor principal
T_SEPARA = 1.0          # se separan cofia, satélite y etapa
T_ABRE = 1.6            # el satélite abre paneles y antena
T_VISTA_ORBITA = 2.6    # cambia a la vista de la Tierra entera con la órbita


def final_exito_leo(sup, ui, t):
    """Éxito en LEO: el cohete termina de inclinarse hasta quedar horizontal (inserción en
    órbita), se apaga el motor, se abre la cofia y el satélite se libera. Luego, vista
    de la Tierra entera con el satélite dando vueltas en su órbita punteada."""
    if t >= T_VISTA_ORBITA:
        orbita(sup, ui, "LEO", t - T_VISTA_ORBITA, nave(ui))
        return
    imagen, m = preparar_imagen(ui)
    fondo_espacio(sup)
    dibujar_tierra_curva(sup, Y_HORIZONTE + t * 8)              # la Tierra se aleja despacio
    angulo = ANGULO_FIN_COMUN + (90 - ANGULO_FIN_COMUN) * suave(t / 1.0)
    base = (BASE_FIN[0] + t * 12, BASE_FIN[1] - t * 6)
    if t < T_MECO:
        dibujar_llama(sup, base[0], base[1], t, 12, angulo=angulo)
    if t < T_SEPARA:
        pegar_pedazo(sup, imagen, base, angulo, BAJO_CENTRO)
        return

    # Pedazos: cofia (en dos mitades), satélite y la etapa (tanque + motor).
    separa = t - T_SEPARA
    cofia = pedazo(imagen, m.y_nariz - 18, m.y_carga)
    etapa = pedazo(imagen, m.y_franja, hangar.ALTO_IMAGEN)
    satelite = nave(ui, (t - T_ABRE) / DURACION_DESPLIEGUE)    # abre paneles y antena ya libre
    # La etapa se queda atrás y cae hacia la Tierra
    pegar_pedazo(sup, etapa, base, angulo, distancia_desde_base(m.y_franja, hangar.ALTO_IMAGEN) - separa * 30,
                 separa * 14, giro_extra=separa * 12)
    # El satélite sigue adelante
    pegar_pedazo(sup, satelite, base, angulo, distancia_desde_base(m.y_carga - 18, m.y_franja) + separa * 22,
                 -separa * 3)
    # La cofia se abre en dos mitades que se alejan girando
    mitad = cofia.get_width() // 2
    izquierda = cofia.subsurface((0, 0, mitad, cofia.get_height())).copy()
    derecha = cofia.subsurface((mitad, 0, mitad, cofia.get_height())).copy()
    adelante = distancia_desde_base(m.y_nariz - 18, m.y_carga) + separa * 30
    pegar_pedazo(sup, izquierda, base, angulo, adelante, -mitad / 2 - separa * 40, giro_extra=-separa * 40)
    pegar_pedazo(sup, derecha, base, angulo, adelante, mitad / 2 + separa * 40, giro_extra=separa * 40)


def final_explota(sup, ui, t):
    """El cohete tiembla, se desarma en 3 pedazos y explota."""
    imagen, m = preparar_imagen(ui)
    fondo_espacio(sup)
    dibujar_tierra_curva(sup, Y_HORIZONTE)
    angulo = ANGULO_FIN_COMUN
    T_ROTURA = 0.8
    if t < T_ROTURA:
        temblor = math.sin(t * 90) * 3
        base = punto_cohete(BASE_FIN, angulo, 0, temblor)
        dibujar_llama(sup, base[0], base[1], t, angulo=angulo)
        pegar_pedazo(sup, imagen, base, angulo, BAJO_CENTRO, giro_extra=temblor)
        if int(t * 8) % 2 == 0:                                # alarma roja que parpadea
            alarma = pygame.Surface((config.ANCHO, config.ALTO))
            alarma.set_alpha(60)
            alarma.fill(config.ROJO)
            sup.blit(alarma, (0, 0))
        return

    d = t - T_ROTURA
    # Tres pedazos: arriba (nariz + carga), tanque y motor, cada uno con su velocidad y giro
    pedazos = [
        (m.y_nariz - 18, m.y_franja, -35, -55, 160),
        (m.y_franja, m.y_motor, 30, -10, -120),
        (m.y_motor, hangar.ALTO_IMAGEN, -5, 50, 90),
    ]
    for y_arriba, y_abajo, vx, vy, giro in pedazos:
        img = pedazo(imagen, y_arriba, y_abajo)
        x0, y0 = punto_cohete(BASE_FIN, angulo, distancia_desde_base(y_arriba, y_abajo))
        pegar_centrado(sup, img, x0 + vx * d, y0 + vy * d + 20 * d * d, angulo=-angulo + giro * d)

    # Bola de fuego y escombros
    cx, cy = punto_cohete(BASE_FIN, angulo, ALTO_BASE_IMAGEN - m.y_franja)
    centro = (int(cx), int(cy))
    radio = int(10 + d * 70)
    if radio < 110:
        pygame.draw.circle(sup, config.ROJO, centro, radio)
        pygame.draw.circle(sup, config.NARANJA, centro, int(radio * 0.7))
        pygame.draw.circle(sup, config.AMARILLO, centro, int(radio * 0.4))
    else:
        for i in range(8):                                     # humo que queda
            a = i * 0.8
            pygame.draw.circle(sup, config.GRIS, (int(centro[0] + math.cos(a) * 50),
                                                  int(centro[1] + math.sin(a) * 40 - d * 10)), 18)
    azar = random.Random(5)
    for _ in range(18):
        a = azar.random() * 6.28
        velocidad = 50 + azar.random() * 80
        x = centro[0] + math.cos(a) * velocidad * d
        y = centro[1] + math.sin(a) * velocidad * d + 15 * d * d
        pygame.draw.rect(sup, config.GRIS_CLARO, (int(x), int(y), 4, 3))
    # Destello blanco los primeros 0.4 s
    if d < 0.4:
        destello = pygame.Surface((config.ANCHO, config.ALTO))
        destello.set_alpha(int(220 * (1 - d / 0.4)))
        destello.fill(config.BLANCO)
        sup.blit(destello, (0, 0))


# --- no_llega en LEO: un pequeño diagrama -------------------------------------
INICIO_DIAGRAMA = (60.0, 250.0)     # donde empieza el cohete (pequeño) en el diagrama
VELOCIDAD_DIAGRAMA = 120            # px/s al empezar, en la dirección de ANGULO_FIN_COMUN
EMPUJE_DIAGRAMA = 60                # px/s² mientras el motor funciona
GRAVEDAD_DIAGRAMA = 35              # px/s² hacia abajo
COMPRESION_X = 0.6                  # el diagrama se "aprieta" a lo ancho para que quepa
T_CORTE = 0.9                       # el motor se apaga antes de tiempo
Y_ORBITA = 56                       # línea de la órbita objetivo


def vuelo_corto(t):
    """Trayectoria del cohete que no llega: lista de (x, y, angulo) en pantalla.
    Mientras el motor funciona acelera; luego solo lo frena la gravedad y cae."""
    a = math.radians(ANGULO_FIN_COMUN)
    vx = VELOCIDAD_DIAGRAMA * math.sin(a)
    vy = -VELOCIDAD_DIAGRAMA * math.cos(a)
    x, y = INICIO_DIAGRAMA
    puntos = []
    for i in range(int(t / PASO_CALCULO) + 1):
        tiempo = i * PASO_CALCULO
        if tiempo < T_CORTE:
            rapidez = math.hypot(vx, vy)
            vx = vx + vx / rapidez * EMPUJE_DIAGRAMA * PASO_CALCULO
            vy = vy + vy / rapidez * EMPUJE_DIAGRAMA * PASO_CALCULO
        vy = vy + GRAVEDAD_DIAGRAMA * PASO_CALCULO
        x = x + vx * PASO_CALCULO
        y = y + vy * PASO_CALCULO
        # El cohete mira hacia donde se mueve (en el diagrama apretado)
        angulo = math.degrees(math.atan2(vx * COMPRESION_X, -vy))
        puntos.append((INICIO_DIAGRAMA[0] + (x - INICIO_DIAGRAMA[0]) * COMPRESION_X, y, angulo))
    return puntos


def final_no_llega(sup, ui, textos, t):
    """El motor se apaga antes de tiempo: el cohete no alcanza la órbita objetivo y cae.
    La cámara se aleja y se ve el camino curvo y lo que le faltó."""
    imagen, _ = preparar_imagen(ui)
    fondo_espacio(sup)
    dibujar_tierra_curva(sup, 300)
    # Órbita objetivo: línea punteada arriba
    for x in range(20, config.ANCHO - 20, 12):
        pygame.draw.rect(sup, config.CIAN, (x, Y_ORBITA, 6, 2))
    estilo.texto(sup, textos["simulacion"]["orbita_objetivo"], 24, Y_ORBITA - 14, config.LETRA_PEQUENA, config.CIAN)

    puntos = vuelo_corto(t)
    x, y, angulo = puntos[-1]
    # Los primeros 0,5 s la cámara se aleja: el cohete pasa de su tamaño y lugar al diagrama
    f = suave(t / 0.5)
    escala = 1.0 - 0.6 * f
    base = (BASE_FIN[0] + (x - BASE_FIN[0]) * f, BASE_FIN[1] + (y - BASE_FIN[1]) * f)
    angulo = ANGULO_FIN_COMUN + (angulo - ANGULO_FIN_COMUN) * f

    # Trayectoria (puntos que va dejando)
    for k in range(0, len(puntos), 5):
        if (k // 5) % 2 == 0:
            pygame.draw.rect(sup, config.GRIS_CLARO, (int(puntos[k][0]), int(puntos[k][1]), 2, 2))
    # Lo que le faltó: línea roja punteada de la cima a la órbita
    cima = min(puntos, key=lambda p: p[1])
    if cima is not puntos[-1]:
        for yy in range(Y_ORBITA + 4, int(cima[1]) - 4, 8):
            pygame.draw.rect(sup, config.ROJO, (int(cima[0]), yy, 2, 4))

    # Llama que "tose" antes de apagarse
    if t < T_CORTE and int(t * 12) % 3 != 0:
        dibujar_llama(sup, base[0], base[1], t, 10, escala, angulo)
    pegar_pedazo(sup, imagen, base, angulo, BAJO_CENTRO, escala=escala)


# ---------------------------------------------------------------------------
# Destinos lejanos (Marte, Luna), órbitas y fallas genéricas
# ---------------------------------------------------------------------------

T_VIAJE = 1.2                       # segundos del viaje de transferencia
POS_TIERRA_VIAJE = (70, 160)
POS_DESTINO_VIAJE = (540, 140)
CONTROL_ARCO = (300, 30)            # "tira" del arco hacia arriba
CENTRO_PLANETA = (CENTRO_X, 150)    # planeta grande al llegar
RADIO_PLANETA = 62
ANGULO_LLEGADA = math.pi * 0.9      # donde entra la nave en su órbita


def es_marte(destino):
    return destino in ("órbita de Marte", "superficie de Marte")


def dibujar_planeta(sup, destino, cx, cy, r, giro=0.0):
    """Planeta: Marte (rojo con casquete polar), la Luna (gris con cráteres) o la Tierra
    (con continentes, ver sprites.dibujar_tierra)."""
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
        sprites.dibujar_tierra(sup, cx, cy, r, giro)


def punto_arco(s):
    """Punto del arco de transferencia (s = 0 en la Tierra, s = 1 en el destino)."""
    a, c, b = POS_TIERRA_VIAJE, CONTROL_ARCO, POS_DESTINO_VIAJE
    x = (1 - s) ** 2 * a[0] + 2 * (1 - s) * s * c[0] + s ** 2 * b[0]
    y = (1 - s) ** 2 * a[1] + 2 * (1 - s) * s * c[1] + s ** 2 * b[1]
    return x, y


def paneles_cubesat(ui, imagen, m, apertura):
    """Si la nave no lleva el recurso potencia (Easy), igual abre dos paneles pequeños
    tipo CubeSat. Dibuja sobre 'imagen' (la nave recortada)."""
    if "potencia" in ui["lab"]["partes"] or apertura <= 0:
        return
    largo = int(18 * apertura)
    y = 18 + 20 - 2              # mitad del módulo de carga (la nave empieza 18 px sobre él)
    pygame.draw.rect(imagen, config.AZUL, (m.izq - largo, y, largo, 5))
    pygame.draw.rect(imagen, config.AZUL, (m.der, y, largo, 5))


def nave(ui, apertura=1.0):
    """La nave = el módulo de carga del cohete armado (con paneles, antena, caja...).
    apertura: cuánto están abiertos los paneles y la antena (1 = del todo, ya en órbita)."""
    sim = ui["sim"]
    _, m = preparar_imagen(ui)
    paso = round(max(0.0, min(1.0, apertura)) * 4)
    clave = "nave_" + str(paso)
    if sim.get(clave) is None:
        imagen = pedazo(imagen_abierta(ui, paso / 4), m.y_carga - 18, m.y_franja)
        paneles_cubesat(ui, imagen, m, paso / 4)
        sim[clave] = imagen
    return sim[clave]


def nave_apagada(ui):
    """La misma nave, oscurecida (sin energía)."""
    sim = ui["sim"]
    if sim.get("nave_apagada") is None:
        copia = nave(ui).copy()
        copia.fill((80, 80, 90), special_flags=pygame.BLEND_RGB_MULT)
        sim["nave_apagada"] = copia
    return sim["nave_apagada"]


def nave_paneles_apagados(ui, celdas):
    """La nave con 'celdas' segmentos de sus paneles solares apagados (0 a 6), de las
    puntas hacia el cuerpo, alternando izquierda y derecha. Si la nave no tiene paneles
    (no se montó potencia), devuelve la nave tal cual."""
    sim = ui["sim"]
    if "potencia" not in ui["lab"]["partes"] or celdas <= 0:
        return nave(ui)
    clave = "paneles_" + str(celdas)
    if sim.get(clave) is None:
        _, m = preparar_imagen(ui)
        copia = nave(ui).copy()
        y = m.y_paneles - (m.y_carga - 18)                       # fila de los paneles dentro de la nave
        orden = [m.izq - 30, m.der + 20, m.izq - 20, m.der + 10, m.izq - 10, m.der]   # de afuera hacia adentro
        for x in orden[:celdas]:
            pygame.draw.rect(copia, config.GRIS_OSCURO, (x, y, 10, 8))
            pygame.draw.line(copia, config.NEGRO, (x, y), (x, y + 7))
        sim[clave] = copia
    return sim[clave]


def luz_de_estado(sup, x, y, color):
    """Lucecita de estado de la nave (verde = bien, amarilla = alerta, roja = apagada)."""
    pygame.draw.rect(sup, config.NEGRO, (int(x) - 1, int(y) - 1, 6, 6))
    pygame.draw.rect(sup, color, (int(x), int(y), 4, 4))


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
    # Recién salida de la órbita de la Tierra: abre sus paneles y su antena
    pegar_centrado(sup, nave(ui, t / DURACION_DESPLIEGUE), x, y, escala=0.35)
    return x, y


def posicion_en_orbita(angulo, radio_x=150, radio_y=55):
    return (CENTRO_PLANETA[0] + math.cos(angulo) * radio_x, CENTRO_PLANETA[1] + math.sin(angulo) * radio_y)


def dibujar_orbita_punteada(sup, angulo_nave, gira):
    """Órbita elíptica punteada: tenue completa y, si la nave está girando, en cian brillante
    el tramo que ya recorrió (así se ve cómo la órbita "se dibuja")."""
    for i in range(0, 60, 2):
        angulo = i * math.pi / 30
        x, y = posicion_en_orbita(angulo)
        recorrido = (angulo - ANGULO_LLEGADA) % (2 * math.pi)
        if gira and recorrido <= (angulo_nave - ANGULO_LLEGADA):
            color = config.CIAN
        else:
            color = config.AZUL_PANEL
        pygame.draw.rect(sup, color, (int(x), int(y), 2, 2))


def orbita(sup, ui, destino, ta, imagen_nave, gira=True, deriva=0.0):
    """Planeta grande con la nave en órbita elíptica (detrás del planeta en la mitad de arriba).
    En LEO el planeta es la Tierra entera con continentes, girando.
    gira=False: la nave se detiene delante del planeta y queda a la deriva 'deriva' segundos:
    se aleja despacio y da vueltas sobre sí misma (ya no la controla nadie).
    Devuelve la posición de la nave."""
    fondo_espacio(sup)
    if destino == "órbita lunar":                                # la Tierra asoma en una esquina
        dibujar_planeta(sup, "LEO", 560, 40, 14)
    angulo = ANGULO_LLEGADA + (ta * 0.9 if gira else 0)
    dibujar_orbita_punteada(sup, angulo, gira)
    x, y = posicion_en_orbita(angulo)
    x = x - deriva * 8                                           # a la deriva, alejándose
    y = y + deriva * 4
    detras = math.sin(angulo) < 0 and gira
    giro = deriva * 25                                           # vueltas lentas a la deriva
    if detras:
        pegar_centrado(sup, imagen_nave, x, y, angulo=giro, escala=0.5)
    dibujar_planeta(sup, destino, CENTRO_PLANETA[0], CENTRO_PLANETA[1], RADIO_PLANETA, ta * 0.4)
    if not detras:
        pegar_centrado(sup, imagen_nave, x, y, angulo=giro, escala=0.5)
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
    if ta < 0.8:                                                 # encendido de frenado (inserción)
        largo = int(10 + 4 * math.sin(ta * 30))
        pygame.draw.polygon(sup, config.NARANJA, [(int(x) + 12, int(y) - 3), (int(x) + 12, int(y) + 3),
                                                  (int(x) + 12 + largo, int(y))])


def dibujar_rover(sup, x, y_suelo, t):
    """Rover de 6 ruedas visto de costado (pixel art). x = centro, y_suelo = donde apoya."""
    x = int(x)
    for dx in (-8, 0, 8):                                         # ruedas que giran
        pygame.draw.circle(sup, config.NEGRO, (x + dx, y_suelo - 3), 3)
        if int(t * 8) % 2 == 0:
            pygame.draw.rect(sup, config.GRIS, (x + dx - 1, y_suelo - 4, 2, 2))
    pygame.draw.rect(sup, config.GRIS_OSCURO, (x - 10, y_suelo - 8, 20, 2))     # suspensión
    pygame.draw.rect(sup, config.BLANCO, (x - 9, y_suelo - 13, 18, 5))         # cuerpo
    pygame.draw.rect(sup, config.GRIS_CLARO, (x - 9, y_suelo - 13, 18, 1))
    pygame.draw.rect(sup, config.GRIS_CLARO, (x + 5, y_suelo - 21, 2, 8))      # mástil
    pygame.draw.rect(sup, config.GRIS, (x + 3, y_suelo - 24, 6, 3))            # cámara
    pygame.draw.rect(sup, config.CIAN, (x + 7, y_suelo - 23, 1, 1))


def aterrizaje(sup, ui, ta):
    """Superficie de Marte: entrada con brillo, paracaídas, cohetes de frenado, polvo y,
    al final, el rover baja y empieza a explorar."""
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
    # El rover sale del módulo y avanza
    T_ROVER = 3.1
    if ta >= T_ROVER:
        dibujar_rover(sup, 240 + 12 + (ta - T_ROVER) * 28, Y_SUELO_MARTE + 2, ta)


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
    T_APAGADO = T_FALLA + 0.8                                      # se_apaga: ya sin energía
    apagada = False
    if destino == "LEO":
        imagen = nave(ui, ta / DURACION_DESPLIEGUE)               # recién llegada a órbita: se abre
    else:
        imagen = nave(ui)
    if falla == "se_apaga":
        # Los paneles se apagan celda por celda (0,8 s) y luego se apaga toda la nave.
        # Con MMRTG (v3) no hay paneles: las baterías se agotan y la nave se apaga.
        if ta >= T_APAGADO:
            apagada = True
            imagen = nave_apagada(ui)
        elif ta >= T_FALLA and tipo_potencia(ui) == "solar":
            imagen = nave_paneles_apagados(ui, 1 + int((ta - T_FALLA) / 0.8 * 6))
    if falla == "fuera_de_tiempo" and ta >= T_FALLA + 0.8:
        apagada = True
        imagen = nave_apagada(ui)
    # Sin energía, sin datos o sin tiempo, la nave deja de maniobrar y se va a la deriva
    detenida = apagada or (falla == "sin_ciencia" and ta > T_FALLA + 0.6)
    if detenida:
        x, y = orbita(sup, ui, destino, 0, imagen, gira=False, deriva=max(0.0, ta - T_FALLA))
    else:
        x, y = orbita(sup, ui, destino, ta, imagen)

    if falla == "se_apaga" and tipo_potencia(ui) == "mmrtg":
        bateria(sup, 36, 44, 1 - ta / T_APAGADO)                  # baterías que se agotan
    if falla == "se_apaga":
        # Luz de estado: verde, luego amarilla parpadeando y al final roja
        if ta < T_FALLA:
            luz_de_estado(sup, x + 12, y - 16, config.VERDE)
        elif ta < T_APAGADO:
            if int(ta * 8) % 2 == 0:
                luz_de_estado(sup, x + 12, y - 16, config.AMARILLO)
        else:
            luz_de_estado(sup, x + 12, y - 16, config.ROJO)
            etiqueta(sup, iconos["sin_energia"], x, y - 30, config.ROJO)
    elif falla == "incomunicada":
        # Ondas hacia la Tierra que se cortan a mitad de camino
        if destino == "LEO":
            tierra = CENTRO_PLANETA                               # la estación está en la Tierra de abajo
        else:
            tierra = (40, 40)
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
            cx, cy = CENTRO_PLANETA
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


# ---------------------------------------------------------------------------
# Sonidos (v2, D11) y dibujo principal
# ---------------------------------------------------------------------------

def sonidos_comunes(sim, t):
    """Pitidos de T-3, T-2, T-1 y, en IGNITION, el pitido final y el rugido del motor."""
    for i in range(3):
        if t >= i * config.SEGUNDOS_POR_CUENTA:
            sonar_una_vez(sim, "pitido", "cuenta_" + str(i))
    if t >= T_IGNICION:
        sonar_una_vez(sim, "pitido_final")
        sonar_una_vez(sim, "ignicion")


def sonidos_finales(sim, final, destino, t2):
    """Explosión y sonido de éxito o de falla, en el momento justo de cada rama.
    t2 = segundos dentro de la rama."""
    if final == "explota":
        if t2 >= 0.8:
            sonar_una_vez(sim, "explosion")
        if t2 >= 1.8:
            sonar_una_vez(sim, "falla")
    elif final == "exito":
        if destino == "LEO":
            momento = T_ABRE                          # el satélite queda libre
        elif destino == "superficie de Marte":
            momento = T_VIAJE + 2.8                   # toca el suelo
        else:
            momento = T_VIAJE + 0.8                   # entra en órbita
        if t2 >= momento:
            sonar_una_vez(sim, "exito")
    elif t2 >= 2.0:
        sonar_una_vez(sim, "falla")


def dibujar(sup, ui, textos):
    sim = ui["sim"]
    t = ui["tiempo"] - sim["t0"]
    frases = textos["simulacion"]["frases"]
    final = tipo_final(sim["resultado"])
    destino = ui["estado"]["destino"]

    if t < config.DURACION_COMUN:
        parte_comun(sup, ui, textos, t)
        sonidos_comunes(sim, t)
        frase = frases["despegue"]
        expresion = "neutral"
    else:
        t_real = t - config.DURACION_COMUN
        t2 = t_real * config.VELOCIDAD_FINAL         # las ramas se animan un poco más lento (D7)
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
        sonidos_finales(sim, final, destino, t2)
        frase = frases.get(final, frases["despegue"])
        expresion = "celebrando" if final == "exito" else "alerta"
        if t_real >= duracion_final(final, destino):
            sim["terminada"] = True        # app.py pasa a resultados

    dibujar_dialogo(sup, frase.replace("{nombre}", ui["jugador"]["nombre"]), expresion)
    return []                              # sin botones: la simulación no se salta (D7)
