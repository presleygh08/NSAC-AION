# laboratorio.py
# Laboratorio (sección 4 de la especificación): el núcleo jugable.
#
#   Izquierda: sala de control vista desde arriba, donde el avatar CAMINA
#              (flechas o WASD) y choca con las paredes y los muebles.
#       arriba    -> computadora ("!" azul, CML 1)
#       derecha   -> mesa de control: una estación por recurso ("i" azul; "✓" ya confirmada)
#       izquierda -> archivo ("!" verde = pistas; "!" morado = revisión del presupuesto)
#   Debajo de la sala: HUD "Budget: $X" con su indicador verde/rojo (v2, D1) y el cuadro de
#   diálogo de AION (título del CML).
#   Derecha: hangar con el cohete (tapado con cortinas hasta confirmar CML 1).
#
# Al estar cerca (RADIO_INTERACCION px) de un marcador activo aparece "[E] Interact";
# con E (o clic sobre ese marcador) se abre su ventana. Con una ventana abierta el
# avatar no se mueve.
#
# Fases (ui["lab"]["fase"]): cml1 -> cml2 -> cml3 -> cml4. Ventanas (ui["lab"]["ventana"]):
#   "briefing", "pistas", "pistas_guardadas", "archivo", "estacion", "revision" o None.
#
# Regla del contrato: aquí NUNCA se lee estado["recursos"] (trae mínimos y óptimos
# ocultos). Se usa nucleo.recursos_visibles y cotizar. Tampoco se muestra cuánto se lleva
# gastado ni cuánto queda (especificación 4.1): el HUD solo dice el presupuesto asignado y
# un color (nucleo.dentro_del_presupuesto).
#
# Esc sin ventana abierta = menú de pausa (lo maneja app.py). Enter = botón principal.

import math

import pygame

import nucleo
from interfaz import config, estilo, hangar, sprites
from interfaz.componentes import (Boton, CajaTexto, dibujar_hud_presupuesto, dibujar_ventana,
                                  formatear_musd, formatear_numero, info_mision, info_recurso,
                                  nombre_destino, nombre_recurso, unidad_recurso)

# --- Distribución de la pantalla (640x360) ---
SALA = pygame.Rect(8, 8, 376, 238)           # paredes
SUELO = SALA.inflate(-12, -12)               # donde se puede caminar
Y_HUD = SALA.bottom + 4                      # franja del HUD entre la sala y el NPC
DIALOGO = pygame.Rect(8, 266, 376, 86)
HANGAR = pygame.Rect(392, 8, 240, 344)
VENTANA = pygame.Rect(90, 50, 460, 260)

# --- Muebles: se dibujan con estos rectángulos y el avatar choca con ellos ---
MESA_COMPUTADORA = pygame.Rect(156, 14, 80, 26)
MESA_CONTROL = pygame.Rect(338, 46, 34, 180)
ESTANTES = pygame.Rect(14, 56, 32, 150)
OBSTACULOS = [MESA_COMPUTADORA, MESA_CONTROL, ESTANTES]

# --- Dónde están los marcadores ---
POS_COMPUTADORA = (196, 50)
POS_ARCHIVO_VERDE = (60, 96)
POS_ARCHIVO_MORADO = (60, 164)
X_ESTACIONES = 322

# --- El avatar ---
POS_INICIAL = (190, 150)       # posición de los pies al empezar
ANCHO_PIES = 14                # caja de choque: solo los pies (así puede pasar "por delante" de los muebles)
ALTO_PIES = 8
TIEMPO_PASO = 0.15             # segundos entre un paso y el siguiente (animación)


def nuevo_lab():
    """Sub-estado del laboratorio al empezar (o reintentar) una misión."""
    return {
        "fase": "cml1",
        "ventana": None,
        "hechas": [],               # claves de las estaciones confirmadas al menos una vez
        "escrito": {},              # {clave: texto que escribió el jugador} (TRY AGAIN lo conserva)
        "partes": {},               # {clave: segundo en que se confirmó} para el ensamblaje
        "cortinas_t0": None,        # segundo en que empezaron a abrirse las cortinas
        "pistas_vistas": False,
        "clave": None,              # estación abierta
        "caja": CajaTexto(VENTANA.x + 150, VENTANA.y + 88, 140, 22, maximo=10, solo_numeros=True),
        "error": False,             # "Enter a valid number"
        "revision": None,           # lo que devolvió nucleo.revisar()
        # Avatar
        "x": float(POS_INICIAL[0]),  # pies del avatar
        "y": float(POS_INICIAL[1]),
        "direccion": "abajo",
        "cuadro": 0,                 # 0 o 1: paso de la caminata
        "tiempo_caminando": 0.0,
        "cerca": None,               # marcador al alcance (o None)
    }


# ---------------------------------------------------------------------------
# Ayudas
# ---------------------------------------------------------------------------

def leer_numero(contenido):
    """Convierte el texto de la caja a número. Devuelve None si no es válido o es negativo."""
    try:
        valor = float(contenido)
    except ValueError:
        return None
    if valor < 0:
        return None
    return valor


def buscar_visible(estado, clave):
    """Fila de recursos_visibles de esa clave (dinero asignado y valor actual)."""
    for recurso in nucleo.recursos_visibles(estado):
        if recurso["clave"] == clave:
            return recurso
    return None


def posiciones_estaciones(estado):
    """Lista de (clave, x, y): una estación por recurso, repartidas en la mesa de control.
    Sale de los datos: si la misión tiene 6 recursos, hay 6 estaciones."""
    claves = [r["clave"] for r in nucleo.recursos_visibles(estado)]
    lista = []
    for i in range(len(claves)):
        y = MESA_CONTROL.y + int((i + 0.5) * MESA_CONTROL.h / len(claves))
        lista.append((claves[i], X_ESTACIONES, y))
    return lista


def apertura_cortinas(lab, tiempo):
    """0 = cortinas cerradas, 1 = abiertas del todo."""
    if lab["cortinas_t0"] is None:
        return 0.0
    return min(1.0, (tiempo - lab["cortinas_t0"]) / config.DURACION_CORTINAS)


def marcadores_activos(ui):
    """Marcadores que se ven y se pueden usar en la fase actual. Cada uno es un
    diccionario {accion, valor, x, y, simbolo, color}. Esta lista la usan el dibujo,
    la cercanía y el clic, así la regla está en un solo lugar."""
    lab = ui["lab"]
    fase = lab["fase"]
    lista = []
    if fase == "cml1":
        lista.append({"accion": "abrir_briefing", "valor": None, "x": POS_COMPUTADORA[0],
                      "y": POS_COMPUTADORA[1], "simbolo": "!", "color": config.AZUL})
    if fase in ("cml3", "cml4"):
        lista.append({"accion": "abrir_archivo", "valor": None, "x": POS_ARCHIVO_VERDE[0],
                      "y": POS_ARCHIVO_VERDE[1], "simbolo": "!", "color": config.VERDE})
        for clave, x, y in posiciones_estaciones(ui["estado"]):
            if clave in lab["hechas"]:
                simbolo, color = "v", config.VERDE        # ✓: ya confirmada (sigue editable)
            else:
                simbolo, color = "i", config.AZUL
            lista.append({"accion": "abrir_estacion", "valor": clave, "x": x, "y": y,
                          "simbolo": simbolo, "color": color})
    if fase == "cml4":
        lista.append({"accion": "abrir_revision", "valor": None, "x": POS_ARCHIVO_MORADO[0],
                      "y": POS_ARCHIVO_MORADO[1], "simbolo": "!", "color": config.MORADO})
    return lista


# ---------------------------------------------------------------------------
# Movimiento del avatar
# ---------------------------------------------------------------------------

def caja_pies(x, y):
    """Rectángulo de los pies del avatar (lo único que choca)."""
    return pygame.Rect(int(x) - ANCHO_PIES // 2, int(y) - ALTO_PIES // 2, ANCHO_PIES, ALTO_PIES)


def choca(x, y):
    """True si en (x, y) los pies saldrían del suelo o tocarían un mueble."""
    pies = caja_pies(x, y)
    if not SUELO.contains(pies):
        return True
    for mueble in OBSTACULOS:
        if pies.colliderect(mueble):
            return True
    return False


def calcular_cerca(ui):
    """El marcador activo más cercano al avatar, si está a RADIO_INTERACCION o menos."""
    lab = ui["lab"]
    # Medimos desde el centro del cuerpo (un poco arriba de los pies).
    cx = lab["x"]
    cy = lab["y"] - 10
    mejor = None
    mejor_distancia = config.RADIO_INTERACCION
    for marcador in marcadores_activos(ui):
        distancia = math.hypot(marcador["x"] - cx, marcador["y"] - cy)
        if distancia <= mejor_distancia:
            mejor = marcador
            mejor_distancia = distancia
    return mejor


def actualizar(ui, dx, dy, dt):
    """Se llama en cada cuadro. dx, dy = -1, 0 o 1 según las teclas; dt = segundos del cuadro.
    Mueve al avatar con colisiones y calcula qué marcador tiene cerca."""
    lab = ui["lab"]
    if lab["ventana"] is not None:          # con una ventana abierta no se camina
        lab["cuadro"] = 0
        return
    velocidad = config.VELOCIDAD_JUGADOR
    if dx != 0 and dy != 0:
        velocidad = velocidad * 0.7         # en diagonal no debe ir más rápido
    paso = velocidad * dt

    # Colisión por ejes: primero x, luego y. Si un eje choca, solo ese se deshace,
    # así el avatar "se desliza" a lo largo de una pared.
    nueva_x = lab["x"] + dx * paso
    if not choca(nueva_x, lab["y"]):
        lab["x"] = nueva_x
    nueva_y = lab["y"] + dy * paso
    if not choca(lab["x"], nueva_y):
        lab["y"] = nueva_y

    # Hacia dónde mira y animación de los pasos
    if dy > 0:
        lab["direccion"] = "abajo"
    elif dy < 0:
        lab["direccion"] = "arriba"
    elif dx > 0:
        lab["direccion"] = "derecha"
    elif dx < 0:
        lab["direccion"] = "izquierda"
    if dx != 0 or dy != 0:
        lab["tiempo_caminando"] = lab["tiempo_caminando"] + dt
        lab["cuadro"] = int(lab["tiempo_caminando"] / TIEMPO_PASO) % 2
    else:
        lab["cuadro"] = 0

    lab["cerca"] = calcular_cerca(ui)


# ---------------------------------------------------------------------------
# Dibujo de la sala, el NPC y el hangar
# ---------------------------------------------------------------------------

def dibujar_muebles(sup, textos):
    """Paredes, suelo de baldosas y muebles (con los mismos rectángulos que chocan)."""
    t = textos["laboratorio"]
    pygame.draw.rect(sup, config.GRIS_OSCURO, SALA)
    for fila in range(SUELO.h // 16 + 1):
        for col in range(SUELO.w // 16 + 1):
            color = config.GRIS_SUELO if (fila + col) % 2 == 0 else config.GRIS_SUELO_2
            rect = pygame.Rect(SUELO.x + col * 16, SUELO.y + fila * 16, 16, 16).clip(SUELO)
            pygame.draw.rect(sup, color, rect)

    # Mesa de la computadora con su monitor
    pygame.draw.rect(sup, config.GRIS, MESA_COMPUTADORA)
    pygame.draw.rect(sup, config.NEGRO, (MESA_COMPUTADORA.centerx - 16, MESA_COMPUTADORA.y + 4, 32, 16))
    pygame.draw.rect(sup, config.CIAN, (MESA_COMPUTADORA.centerx - 14, MESA_COMPUTADORA.y + 6, 28, 12))
    estilo.texto(sup, t["computadora"], MESA_COMPUTADORA.x - 6, MESA_COMPUTADORA.y + 8,
                 config.LETRA_PEQUENA, derecha=True)
    # Mesa de control larga
    pygame.draw.rect(sup, config.GRIS, MESA_CONTROL)
    pygame.draw.rect(sup, config.GRIS_CLARO, (MESA_CONTROL.x, MESA_CONTROL.y, MESA_CONTROL.w, 2))
    # Estantes del archivo
    pygame.draw.rect(sup, config.MARRON, ESTANTES)
    for yy in range(ESTANTES.y + 6, ESTANTES.bottom, 14):
        pygame.draw.line(sup, (90, 60, 40), (ESTANTES.x, yy), (ESTANTES.right - 1, yy))
    estilo.texto(sup, t["archivo"], ESTANTES.centerx + 4, ESTANTES.bottom + 10, config.LETRA_PEQUENA,
                 centrado=True)


def dibujar_sala(sup, ui, textos, botones):
    """Sala con muebles, estaciones, avatar, marcadores y la etiqueta "[E] Interact".
    'botones' recibe el botón invisible del marcador cercano (para el clic)."""
    lab = ui["lab"]
    tiempo = ui["tiempo"]
    dibujar_muebles(sup, textos)

    # Pantallitas de las estaciones sobre la mesa y sus nombres
    for clave, x, y in posiciones_estaciones(ui["estado"]):
        color = config.VERDE if clave in lab["hechas"] else config.AZUL
        if lab["fase"] in ("cml1", "cml2"):
            color = config.GRIS_OSCURO               # apagadas hasta CML 3
        pygame.draw.rect(sup, config.NEGRO, (MESA_CONTROL.x + 10, y - 6, 16, 12))
        pygame.draw.rect(sup, color, (MESA_CONTROL.x + 12, y - 4, 12, 8))

    # Marcadores (flotan sobre los muebles)
    for marcador in marcadores_activos(ui):
        rect = sprites.dibujar_marcador(sup, marcador["x"], marcador["y"], marcador["simbolo"],
                                        marcador["color"], tiempo)
        if marcador["accion"] == "abrir_estacion":
            estilo.texto(sup, nombre_recurso(textos, marcador["valor"]), marcador["x"] - 12,
                         marcador["y"] - 4, config.LETRA_PEQUENA, derecha=True)
        # Solo el marcador cercano se puede clicar
        if lab["cerca"] is not None and lab["cerca"]["accion"] == marcador["accion"] \
                and lab["cerca"]["valor"] == marcador["valor"]:
            botones.append(Boton("", rect.x - 4, rect.y - 4, rect.w + 8, rect.h + 8,
                                 marcador["accion"], marcador["valor"], visible=False))

    # Avatar (desde arriba), después de los marcadores: así, al pararse junto a uno,
    # el avatar queda "delante". Sus pies están en (x, y); el sprite mide 32x32.
    sprites.dibujar_avatar_arriba(sup, ui["jugador"]["avatar"], int(lab["x"]) - 16, int(lab["y"]) - 28,
                                  lab["direccion"], lab["cuadro"], 2)

    # Etiqueta "[E] Interact" sobre el marcador cercano
    if lab["cerca"] is not None and lab["ventana"] is None:
        contenido = textos["laboratorio"]["interactuar"]
        ancho = estilo.fuente(config.LETRA_PEQUENA).size(contenido)[0] + 8
        caja = pygame.Rect(0, 0, ancho, 13)
        caja.midbottom = (lab["cerca"]["x"], lab["cerca"]["y"] - 10)
        caja.clamp_ip(SALA)
        pygame.draw.rect(sup, config.NEGRO, caja)
        pygame.draw.rect(sup, config.AMARILLO, caja, 1)
        estilo.texto(sup, contenido, caja.centerx, caja.centery, config.LETRA_PEQUENA, config.AMARILLO,
                     centrado=True, sombra=False)

    # HUD de presupuesto (siempre visible, abajo a la izquierda, fuera del suelo).
    # Es FIJO: solo el presupuesto asignado, nunca lo gastado ni lo que queda (4.1).
    dibujar_hud_presupuesto(sup, textos, ui["estado"]["presupuesto_musd"], SALA.x + 2, Y_HUD,
                            nucleo.dentro_del_presupuesto(ui["estado"]))


def dibujar_npc(sup, ui, textos):
    """Cuadro de diálogo: título del CML en rojo, la instrucción y la ayuda de teclas,
    con el retrato del NPC a la derecha."""
    t = textos["laboratorio"]
    fase = t["fases"][ui["lab"]["fase"]]
    estilo.panel(sup, DIALOGO)
    estilo.texto(sup, fase["titulo"], DIALOGO.x + 10, DIALOGO.y + 8, config.LETRA_PEQUENA, config.ROJO)
    contenido = fase["texto"].replace("{nombre}", ui["jugador"]["nombre"])
    estilo.texto_multilinea(sup, contenido, DIALOGO.x + 10, DIALOGO.y + 26, DIALOGO.w - 90,
                            config.LETRA_PEQUENA)
    estilo.texto(sup, t["ayuda_mover"], DIALOGO.x + 10, DIALOGO.bottom - 16, config.LETRA_PEQUENA,
                 config.COLOR_TEXTO_SUAVE)
    sprites.dibujar_npc(sup, DIALOGO.right - 46, DIALOGO.y + 12)
    estilo.texto(sup, t["npc_nombre"], DIALOGO.right - 50, DIALOGO.y + 56,
                 config.LETRA_PEQUENA, config.COLOR_TEXTO_SUAVE, centrado=True)


def dibujar_hangar(sup, ui, textos):
    """Ventana al hangar (sección 4.6): ver interfaz/hangar.py."""
    lab = ui["lab"]
    hangar.dibujar(sup, HANGAR, lab, ui["estado"]["cohete"], ui["tiempo"],
                   apertura_cortinas(lab, ui["tiempo"]), textos["laboratorio"]["hangar"])


# ---------------------------------------------------------------------------
# Ventanas
# ---------------------------------------------------------------------------

def fila_informativa(sup, etiqueta, valor, x, y, ancho):
    """Una fila de texto: etiqueta en cian y el dato a su derecha. Devuelve la y siguiente."""
    estilo.texto(sup, etiqueta + ":", x, y, config.LETRA_PEQUENA, config.CIAN)
    return estilo.texto_multilinea(sup, valor, x + 90, y, ancho - 90, config.LETRA_PEQUENA) + 10


def ventana_briefing(sup, ui, textos, botones):
    """Mission briefing (v2, punto 6): solo texto informativo (meta, destino y cohete) y CONFIRM."""
    t = textos["laboratorio"]["briefing"]
    estado = ui["estado"]
    y = dibujar_ventana(sup, VENTANA, t["titulo"], config.AZUL) + 6
    meta = info_mision(textos, ui["mision_id"]).get("objetivo", ui["mision_nombre"])
    x = VENTANA.x + 16
    ancho = VENTANA.w - 32
    y = fila_informativa(sup, t["meta"], meta, x, y, ancho)
    y = fila_informativa(sup, t["destino"], nombre_destino(textos, estado["destino"]), x, y, ancho)
    fila_informativa(sup, t["cohete"], estado["cohete"], x, y, ancho)
    botones.append(Boton(textos["botones"]["confirmar"], VENTANA.centerx - 60, VENTANA.bottom - 36,
                         120, config.ALTO_BOTON, "confirmar_briefing", color=config.AZUL, principal=True))


def ventana_pistas(sup, ui, textos, botones, titulo, boton_texto, accion, color):
    """Lista de pistas (estado["pistas"], se muestran tal cual vienen)."""
    y = dibujar_ventana(sup, VENTANA, titulo, color)
    for pista in ui["estado"]["pistas"]:
        estilo.texto(sup, "-", VENTANA.x + 14, y, config.LETRA_PEQUENA, config.VERDE)
        y = estilo.texto_multilinea(sup, pista, VENTANA.x + 26, y, VENTANA.w - 44,
                                    config.LETRA_PEQUENA) + 8
    botones.append(Boton(boton_texto, VENTANA.centerx - 60, VENTANA.bottom - 36, 120,
                         config.ALTO_BOTON, accion, color=color, principal=True))


def ventana_pistas_guardadas(sup, ui, textos, botones):
    rect = pygame.Rect(140, 120, 360, 110)
    y = dibujar_ventana(sup, rect, textos["laboratorio"]["pistas"]["titulo"], config.VERDE)
    estilo.texto_multilinea(sup, textos["laboratorio"]["pistas"]["guardadas"], rect.x + 14, y,
                            rect.w - 28, config.LETRA_PEQUENA)
    botones.append(Boton(textos["botones"]["aceptar"], rect.centerx - 50, rect.bottom - 32, 100,
                         config.ALTO_BOTON, "aceptar_pistas", color=config.VERDE, principal=True))


def ventana_estacion(sup, ui, textos, botones):
    """Estación de un recurso: el jugador escribe la CANTIDAD y ve el costo en vivo."""
    t = textos["laboratorio"]["estacion"]
    lab = ui["lab"]
    estado = ui["estado"]
    clave = lab["clave"]
    recurso = buscar_visible(estado, clave)
    unidad = unidad_recurso(textos, clave, recurso["unidad"])     # v2 (D12): de la guía

    titulo = nombre_recurso(textos, clave) + " - " + unidad
    y = dibujar_ventana(sup, VENTANA, titulo, config.AZUL)
    x = VENTANA.x + 16
    explicacion = info_recurso(textos, clave).get("que_es", "")
    y = estilo.texto_multilinea(sup, explicacion, x, y, VENTANA.w - 32, config.LETRA_PEQUENA,
                                config.COLOR_TEXTO_SUAVE) + 6
    estilo.texto(sup, t["actual"] + ": " + formatear_numero(recurso["valor"]) + " " + unidad
                 + "  (" + formatear_musd(recurso["dinero_musd"]) + ")", x, y, config.LETRA_PEQUENA)

    # Caja de cantidad (posición fija dentro de la ventana)
    caja = lab["caja"]
    estilo.texto(sup, t["cantidad"] + " (" + unidad + "):", x, caja.rect.y + 5, config.LETRA_PEQUENA,
                 config.CIAN)
    caja.dibujar(sup, ui["tiempo"])

    # Costo en vivo de ESTE recurso solamente (4.4): nada de total gastado ni de lo que queda.
    y = caja.rect.bottom + 12
    valor = leer_numero(caja.texto)
    if valor is not None:
        costo = nucleo.cotizar(estado, clave, valor)
        estilo.texto(sup, t["costo"] + ": " + formatear_musd(costo), x, y, config.LETRA_NORMAL,
                     config.AMARILLO)
    if lab["error"]:
        estilo.texto(sup, t["invalido"], x, y + 24, config.LETRA_PEQUENA, config.COLOR_ERROR)

    botones.append(Boton(textos["botones"]["cancelar"], VENTANA.x + 16, VENTANA.bottom - 36, 110,
                         config.ALTO_BOTON, "cerrar_ventana"))
    botones.append(Boton(textos["botones"]["confirmar"], VENTANA.right - 126, VENTANA.bottom - 36, 110,
                         config.ALTO_BOTON, "confirmar_estacion", color=config.VERDE, principal=True))


def ventana_revision(sup, ui, textos, botones):
    """Budget review (CML 4). Solo dice si el reparto entra o no en el presupuesto."""
    t = textos["laboratorio"]["revision"]
    revision = ui["lab"]["revision"]
    titulo = t["titulo"] + ": " + ui["mision_nombre"]          # "BUDGET REVIEW: <misión>" (v2, punto 7)
    y = dibujar_ventana(sup, VENTANA, titulo, config.MORADO)
    x = VENTANA.x + 16
    ancho = VENTANA.w - 32
    if revision["ok"]:
        y = estilo.texto_multilinea(sup, t["ok"], x, y + 10, ancho, config.LETRA_NORMAL, config.COLOR_OK)
        estilo.texto_multilinea(sup, t["aviso_ok"], x, y + 8, ancho, config.LETRA_PEQUENA,
                                config.COLOR_TEXTO_SUAVE)
        # Con ok=True el núcleo ya pasó a la simulación: no hay botón para volver.
        botones.append(Boton(textos["botones"]["confirmar_lanzamiento"], VENTANA.centerx - 95,
                             VENTANA.bottom - 36, 190, config.ALTO_BOTON, "confirmar_lanzamiento",
                             color=config.ROJO, principal=True))
    else:
        # Se pasó: solo se dice ESO, sin cifras (4.5). No se muestran exceso_musd ni el
        # mensaje de revisar (que trae el costo total y el presupuesto).
        estilo.texto_multilinea(sup, t["excedido"], x, y + 10, ancho, config.LETRA_NORMAL, config.COLOR_ERROR)
        botones.append(Boton(textos["botones"]["aceptar"], VENTANA.centerx - 50, VENTANA.bottom - 36,
                             100, config.ALTO_BOTON, "cerrar_ventana", color=config.MORADO, principal=True))


# ---------------------------------------------------------------------------
# Dibujo principal
# ---------------------------------------------------------------------------

def dibujar(sup, ui, textos):
    lab = ui["lab"]
    sup.fill(config.COLOR_FONDO)
    botones = []

    # En CML 2 la ventana de pistas se abre sola cuando las cortinas terminan de abrirse.
    if (lab["fase"] == "cml2" and lab["ventana"] is None and not lab["pistas_vistas"]
            and apertura_cortinas(lab, ui["tiempo"]) >= 1):
        lab["ventana"] = "pistas"

    if lab["ventana"] is None:
        dibujar_sala(sup, ui, textos, botones)       # los marcadores solo funcionan sin ventana
    else:
        lab["cerca"] = None
        dibujar_sala(sup, ui, textos, [])
    dibujar_npc(sup, ui, textos)
    dibujar_hangar(sup, ui, textos)

    ventana = lab["ventana"]
    t_pistas = textos["laboratorio"]["pistas"]
    if ventana == "briefing":
        ventana_briefing(sup, ui, textos, botones)
    elif ventana == "pistas":
        ventana_pistas(sup, ui, textos, botones, t_pistas["titulo"], textos["botones"]["siguiente"],
                       "pistas_siguiente", config.VERDE)
    elif ventana == "pistas_guardadas":
        ventana_pistas_guardadas(sup, ui, textos, botones)
    elif ventana == "archivo":
        ventana_pistas(sup, ui, textos, botones, t_pistas["archivo_titulo"], textos["botones"]["aceptar"],
                       "cerrar_ventana", config.VERDE)
    elif ventana == "estacion":
        ventana_estacion(sup, ui, textos, botones)
    elif ventana == "revision":
        ventana_revision(sup, ui, textos, botones)
    return botones


# ---------------------------------------------------------------------------
# Acciones (las llama app.py) y teclado
# ---------------------------------------------------------------------------

def conservar_reparto(lab, estado, escrito, tiempo):
    """TRY AGAIN (v2, punto 2): en la misión nueva, cada estación vuelve con la cantidad
    que el jugador escribió antes ('escrito' = {clave: texto}). El costo se calcula otra vez
    con nucleo.cotizar y se reparte con nucleo.repartir. Las estaciones quedan confirmadas
    (✓) y sus partes ya montadas en el hangar, sin animación."""
    for clave in escrito:
        valor = leer_numero(escrito[clave])
        if valor is None:
            continue
        nucleo.repartir(estado, clave, nucleo.cotizar(estado, clave, valor))
        lab["escrito"][clave] = escrito[clave]
        if clave not in lab["hechas"]:
            lab["hechas"].append(clave)
        lab["partes"][clave] = tiempo - config.DURACION_ENSAMBLAJE - 1    # ya terminada


def todas_hechas(lab, estado):
    """True si todas las estaciones de la misión se confirmaron al menos una vez."""
    todas = [r["clave"] for r in nucleo.recursos_visibles(estado)]
    return len(lab["hechas"]) == len(todas)


def abrir_estacion(lab, estado, clave):
    """Abre la ventana de una estación con la cantidad actual escrita en la caja
    (el texto exacto que escribió el jugador, si existe)."""
    lab["ventana"] = "estacion"
    lab["clave"] = clave
    lab["error"] = False
    valor = buscar_visible(estado, clave)["valor"]
    if clave in lab["escrito"]:
        lab["caja"].texto = lab["escrito"][clave]
    elif valor > 0:
        lab["caja"].texto = formatear_numero(valor)
    else:
        lab["caja"].texto = ""


def confirmar_estacion(lab, estado, tiempo):
    """Valida el número, reparte su costo y marca la estación como hecha."""
    valor = leer_numero(lab["caja"].texto)
    if valor is None:
        lab["error"] = True
        return
    clave = lab["clave"]
    costo = nucleo.cotizar(estado, clave, valor)
    nucleo.repartir(estado, clave, costo)
    lab["escrito"][clave] = lab["caja"].texto
    if clave not in lab["hechas"]:
        lab["hechas"].append(clave)
    lab["partes"][clave] = tiempo         # empieza la animación de ensamblaje en el hangar
    lab["ventana"] = None
    # Cuando TODAS las estaciones se confirmaron al menos una vez -> CML 4
    if lab["fase"] == "cml3" and todas_hechas(lab, estado):
        lab["fase"] = "cml4"


def aplicar(ui, accion, valor):
    """Acciones propias del laboratorio. Devuelve True si la acción era de aquí."""
    lab = ui["lab"]
    estado = ui["estado"]
    if accion == "interactuar":
        # Tecla E: la acción del marcador que el avatar tiene cerca (si hay uno).
        marcador = calcular_cerca(ui)
        if marcador is not None and lab["ventana"] is None:
            aplicar(ui, marcador["accion"], marcador["valor"])
    elif accion == "abrir_briefing":
        lab["ventana"] = "briefing"
    elif accion == "confirmar_briefing":
        lab["ventana"] = None
        lab["fase"] = "cml2"
        lab["cortinas_t0"] = ui["tiempo"]           # empiezan a abrirse las cortinas
    elif accion == "pistas_siguiente":
        lab["ventana"] = "pistas_guardadas"
        lab["pistas_vistas"] = True
    elif accion == "aceptar_pistas":
        lab["ventana"] = None
        # Tras TRY AGAIN las estaciones ya están confirmadas: directo a CML 4.
        if todas_hechas(lab, estado):
            lab["fase"] = "cml4"
        else:
            lab["fase"] = "cml3"
    elif accion == "abrir_archivo":
        lab["ventana"] = "archivo"
    elif accion == "abrir_estacion":
        abrir_estacion(lab, estado, valor)
    elif accion == "confirmar_estacion":
        confirmar_estacion(lab, estado, ui["tiempo"])
    elif accion == "abrir_revision":
        lab["revision"] = nucleo.revisar(estado)
        lab["ventana"] = "revision"
    elif accion == "cerrar_ventana":
        lab["ventana"] = None
    else:
        return False
    return True


def tecla(ui, evento):
    """Teclado del laboratorio: E interactúa, números en la estación, Enter confirma,
    Esc cierra. (Caminar con flechas/WASD se lee en actualizar, cada cuadro.)
    Sin ventana, Esc abre la pausa (app.py); Enter en las demás ventanas activa su botón
    principal (app.py)."""
    lab = ui["lab"]
    ventana = lab["ventana"]
    if ventana == "estacion":
        if evento.key == pygame.K_ESCAPE:
            return ("cerrar_ventana", None)
        lab["error"] = False
        if lab["caja"].escribir(evento):
            return ("confirmar_estacion", None)
        return None
    if ventana is None and evento.key == pygame.K_e:
        return ("interactuar", None)
    if evento.key == pygame.K_ESCAPE:
        # Esc NO cierra las ventanas que exigen confirmar (briefing, pistas de CML 2 y
        # la revisión aprobada, que ya no tiene vuelta atrás).
        if ventana == "archivo":
            return ("cerrar_ventana", None)
        if ventana == "revision" and not lab["revision"]["ok"]:
            return ("cerrar_ventana", None)
    return None
