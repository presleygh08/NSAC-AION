# pantalla_info.py
# Ficha de la misión (sección 3.4): descripción, objetivo, cohete, destino, recursos a
# repartir y presupuesto. A la derecha, la misma foto de la parrilla, más grande.
#
# Descripción y objetivo (v2, D10): de interfaz/guia_misiones_en.json -> misiones.<id>;
# si no están, "Coming soon".

import nucleo
from interfaz import config, estilo, imagenes
from interfaz.componentes import Boton, formatear_musd, info_mision, nombre_destino, nombre_recurso


def textos_mision(textos, parametros):
    """(descripcion, objetivo) en inglés, o "Coming soon" si aún no existen."""
    pendiente = textos["info"]["proximamente"]
    mision = info_mision(textos, parametros["mision"])
    return mision.get("descripcion", pendiente), mision.get("objetivo", pendiente)


def datos_ficha(ui):
    """Lee los datos de la misión UNA vez y los guarda en ui["ficha"] (no en cada cuadro)."""
    if ui.get("ficha") is None or ui["ficha"]["id"] != ui["mision_id"]:
        parametros = nucleo.cargar_parametros(ui["mision_id"])
        # Para saber qué recursos tiene la misión creamos un estado temporal y usamos
        # recursos_visibles (así nunca tocamos los mínimos ni los óptimos).
        visibles = nucleo.recursos_visibles(nucleo.iniciar_mision(parametros))
        ui["ficha"] = {"id": ui["mision_id"], "parametros": parametros,
                       "claves": [r["clave"] for r in visibles],
                       "unidades": {r["clave"]: r["unidad"] for r in visibles}}
    return ui["ficha"]


def dibujar(sup, ui, textos):
    t = textos["info"]
    estilo.fondo_estrellas(sup, ui["tiempo"])
    ficha = datos_ficha(ui)
    parametros = ficha["parametros"]
    claves = ficha["claves"]
    descripcion, objetivo = textos_mision(textos, parametros)

    estilo.panel(sup, (16, 16, 340, 290))
    x = 28
    ancho = 316
    estilo.texto(sup, ui["mision_nombre"], x, 26, config.LETRA_TITULO, config.AMARILLO)
    y = 60
    estilo.texto(sup, t["descripcion"], x, y, config.LETRA_PEQUENA, config.CIAN)
    y = estilo.texto_multilinea(sup, descripcion, x, y + 15, ancho, config.LETRA_PEQUENA) + 6
    estilo.texto(sup, t["objetivo"], x, y, config.LETRA_PEQUENA, config.CIAN)
    y = estilo.texto_multilinea(sup, objetivo, x, y + 15, ancho, config.LETRA_PEQUENA) + 8

    filas = [
        (t["cohete"], parametros["cohete"]),
        (t["destino"], nombre_destino(textos, parametros["destino"])),
        (t["recursos"], ", ".join(nombre_recurso(textos, c) for c in claves)),
        (t["presupuesto"], formatear_musd(parametros["presupuesto_musd"])),
    ]
    for etiqueta, valor in filas:
        estilo.texto(sup, etiqueta + ":", x, y, config.LETRA_PEQUENA, config.CIAN)
        y = estilo.texto_multilinea(sup, valor, x + 140, y, ancho - 140, config.LETRA_PEQUENA) + 4

    estilo.panel(sup, (370, 16, 254, 290))
    imagenes.dibujar_imagen_mision(sup, (378, 24, 238, 274), ui["mision_id"], parametros["destino"],
                                   ui["mision_nombre"], ui["tiempo"])

    return [
        Boton(textos["botones"]["atras"], 16, 318, 100, config.ALTO_BOTON, "volver_misiones"),
        Boton(textos["botones"]["correr"], 494, 314, 130, 32, "correr", color=config.ROJO,
              tamano=config.LETRA_TITULO, principal=True),
    ]
