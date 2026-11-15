# sonido.py
# Sonidos del juego GENERADOS POR CÓDIGO (v2, D11): no hay archivos de audio con licencia.
#
# Cada sonido es una lista de muestras (números de -32767 a 32767) que se calcula con
# senos, ondas cuadradas y ruido, y se guarda en un array("h") (enteros de 16 bits).
# pygame.mixer.Sound(buffer=...) lo convierte en un sonido que se puede reproducir.
#
# Uso:
#     sonido.iniciar()            # una vez, después de pygame.init()
#     sonido.tocar("pitido")      # en cualquier parte
#     sonido.alternar_silencio()  # tecla M
#
# Si la computadora no tiene audio (o pygame.mixer falla), DISPONIBLE queda en False y
# todas las funciones simplemente no hacen nada: el juego sigue sin sonido.

import math
import random
from array import array

import pygame

FRECUENCIA = 22050          # muestras por segundo
VOLUMEN = 0.35              # volumen general (0 a 1)
MAXIMO = 32767              # valor más alto de una muestra de 16 bits

DISPONIBLE = False          # True si el audio se pudo iniciar
SILENCIO = False            # True = tecla M apretada
SONIDOS = {}                # {nombre: pygame.mixer.Sound}


# ---------------------------------------------------------------------------
# Ondas básicas (devuelven listas de números entre -1 y 1)
# ---------------------------------------------------------------------------

def cantidad_muestras(segundos):
    return int(FRECUENCIA * segundos)


def onda_cuadrada(frecuencia, segundos):
    """Onda cuadrada (sonido "8 bits"): +1 la mitad del ciclo y -1 la otra mitad."""
    muestras = []
    for i in range(cantidad_muestras(segundos)):
        fase = (i * frecuencia / FRECUENCIA) % 1
        muestras.append(1.0 if fase < 0.5 else -1.0)
    return muestras


def onda_seno(frecuencia, segundos):
    muestras = []
    for i in range(cantidad_muestras(segundos)):
        muestras.append(math.sin(2 * math.pi * frecuencia * i / FRECUENCIA))
    return muestras


def barrido(frecuencia_inicio, frecuencia_fin, segundos, cuadrada=True):
    """Tono que cambia de frecuencia poco a poco (sube o baja)."""
    muestras = []
    fase = 0.0
    total = cantidad_muestras(segundos)
    for i in range(total):
        f = frecuencia_inicio + (frecuencia_fin - frecuencia_inicio) * i / total
        fase = fase + f / FRECUENCIA
        if cuadrada:
            muestras.append(1.0 if fase % 1 < 0.5 else -1.0)
        else:
            muestras.append(math.sin(2 * math.pi * fase))
    return muestras


def ruido_grave(segundos, suavidad):
    """Ruido "filtrado": cada muestra se acerca un poco a un valor al azar.
    Más 'suavidad' (0 a 1) = sonido más grave (como un rugido)."""
    azar = random.Random(7)
    muestras = []
    valor = 0.0
    for _ in range(cantidad_muestras(segundos)):
        valor = valor * suavidad + (azar.random() * 2 - 1) * (1 - suavidad)
        muestras.append(valor)
    # El filtro baja mucho el volumen: lo normalizamos para que el más alto valga 1.
    mayor = max(abs(m) for m in muestras) or 1.0
    return [m / mayor for m in muestras]


def envolvente(muestras, ataque, caida):
    """Sube el volumen al empezar ('ataque' s) y lo baja al final ('caida' s), para que
    el sonido no haga "clic"."""
    total = len(muestras)
    n_ataque = max(1, cantidad_muestras(ataque))
    n_caida = max(1, cantidad_muestras(caida))
    resultado = []
    for i in range(total):
        factor = 1.0
        if i < n_ataque:
            factor = i / n_ataque
        if i > total - n_caida:
            factor = min(factor, (total - i) / n_caida)
        resultado.append(muestras[i] * factor)
    return resultado


def silencio(segundos):
    return [0.0] * cantidad_muestras(segundos)


def mezclar(lista1, lista2, peso2):
    """Suma dos sonidos (el segundo con 'peso2'). El más corto se rellena con silencio."""
    largo = max(len(lista1), len(lista2))
    resultado = []
    for i in range(largo):
        a = lista1[i] if i < len(lista1) else 0.0
        b = lista2[i] if i < len(lista2) else 0.0
        resultado.append(a + b * peso2)
    mayor = max(1.0, max(abs(m) for m in resultado))
    return [m / mayor for m in resultado]


# ---------------------------------------------------------------------------
# Los sonidos del juego
# ---------------------------------------------------------------------------

def crear_pitido():
    """Cuenta regresiva: T-3, T-2, T-1."""
    return envolvente(onda_cuadrada(880, 0.15), 0.005, 0.04)


def crear_pitido_final():
    """IGNITION: un pitido más agudo y largo."""
    return envolvente(onda_cuadrada(1320, 0.35), 0.005, 0.1)


def crear_ignicion():
    """Rugido del motor: ruido grave que empieza fuerte y se va apagando, con un tono
    bajo que cae (como cuando el cohete se aleja)."""
    rugido = ruido_grave(3.0, 0.93)
    tono = barrido(90, 40, 3.0, cuadrada=False)
    return envolvente(mezclar(rugido, tono, 0.3), 0.15, 1.6)


def crear_exito():
    """Arpegio que sube: do - mi - sol - do (agudo)."""
    muestras = []
    for frecuencia in (523, 659, 784):
        muestras = muestras + envolvente(onda_cuadrada(frecuencia, 0.12), 0.005, 0.03)
    muestras = muestras + envolvente(onda_cuadrada(1046, 0.4), 0.005, 0.25)
    return muestras


def crear_falla():
    """Dos tonos que bajan (sonido de "perdiste")."""
    primero = envolvente(barrido(440, 330, 0.3), 0.005, 0.05)
    segundo = envolvente(barrido(330, 160, 0.6), 0.005, 0.3)
    return primero + silencio(0.05) + segundo


def crear_explosion():
    """Ruido fuerte y corto que se apaga."""
    return envolvente(ruido_grave(1.2, 0.8), 0.005, 1.0)


def crear_puertas():
    """Puertas del hangar: un "clonc" metálico y el zumbido del motor que las abre."""
    golpe = envolvente(mezclar(onda_seno(180, 0.25), onda_seno(410, 0.25), 0.5), 0.002, 0.22)
    motor = envolvente(barrido(60, 75, 1.3), 0.1, 0.3)
    motor = [m * 0.35 for m in motor]
    return golpe + motor


def crear_clic():
    """Clic corto al confirmar."""
    return envolvente(onda_cuadrada(660, 0.05), 0.002, 0.03)


def a_sonido(muestras):
    """Convierte una lista de números (-1 a 1) en un pygame.mixer.Sound."""
    datos = array("h", [int(m * MAXIMO * VOLUMEN) for m in muestras])
    return pygame.mixer.Sound(buffer=datos.tobytes())


# ---------------------------------------------------------------------------
# Lo que usa el resto del juego
# ---------------------------------------------------------------------------

def iniciar():
    """Inicia el audio y crea todos los sonidos. Si algo falla, el juego sigue mudo."""
    global DISPONIBLE
    try:
        if pygame.mixer.get_init() is None:
            pygame.mixer.init(FRECUENCIA, -16, 1, 512)
        # El mixer puede quedar en estéreo aunque pidamos mono: entonces duplicamos cada muestra.
        canales = pygame.mixer.get_init()[2]
        recetas = {
            "pitido": crear_pitido,
            "pitido_final": crear_pitido_final,
            "ignicion": crear_ignicion,
            "exito": crear_exito,
            "falla": crear_falla,
            "explosion": crear_explosion,
            "puertas": crear_puertas,
            "clic": crear_clic,
        }
        for nombre in recetas:
            muestras = recetas[nombre]()
            if canales == 2:
                doble = []
                for m in muestras:
                    doble.append(m)
                    doble.append(m)
                muestras = doble
            SONIDOS[nombre] = a_sonido(muestras)
        DISPONIBLE = True
    except Exception:          # sin tarjeta de sonido, sin driver, etc.
        DISPONIBLE = False


def tocar(nombre):
    """Reproduce un sonido (si hay audio y no está en silencio)."""
    if not DISPONIBLE or SILENCIO or nombre not in SONIDOS:
        return
    try:
        SONIDOS[nombre].play()
    except Exception:
        pass


def detener_todo():
    """Corta todos los sonidos (al salir de la simulación, al silenciar)."""
    if DISPONIBLE:
        try:
            pygame.mixer.stop()
        except Exception:
            pass


def alternar_silencio():
    """Tecla M: silencia o vuelve a activar el sonido."""
    global SILENCIO
    SILENCIO = not SILENCIO
    if SILENCIO:
        detener_todo()


def silenciado():
    return SILENCIO
