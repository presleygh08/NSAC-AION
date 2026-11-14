# Motor del juego: funciones disponibles

Unidades: kg, m/s, s (Isp), W, M USD, UA. Ninguna función imprime nada:
todas reciben y devuelven datos.

## Flujo de una partida
    from juego import *

    datos = cargar_datos()                      # una sola vez, al iniciar
    mision = nueva_mision()
    elegir_destino(mision, "órbita lunar")      # nombre exacto de datos["destinos"]
    disenar_nave(mision, 500, 320, datos)       # m_seca_kg, isp
    # el jugador ajusta sus decisiones directamente en el diccionario:
    #   area_panel_m2, eficiencia_panel (0-1), consumos_w (lista de W),
    #   costo_nave_musd, costo_instrumentos_musd, m_prop_cargada_kg
    elegir_lanzador(mision, "Falcon Heavy")     # nombre exacto de datos["lanzadores"]
    evaluar_mision(mision, datos)               # simula y deja el resultado

## Opciones para menús
    [f["destino"] for f in datos["destinos"]]
    [f["nombre"]  for f in datos["lanzadores"]]

## Qué lee la interfaz después de evaluar_mision
    mision["resultado"]   # "exito" o la clave de falla
    mision["mensaje"]     # texto que explica el resultado
    mision["puntaje"]     # entero
    mision["potencia_w"], mision["consumo_w"]
    mision["reglas"]      # lista de 4 dicts: clave, ok, valor, limite, unidad

## Para medidores en vivo (antes de evaluar)
    masa_total_kg(mision)               # kg, nave + propelente cargado
    propelente_cargado_kg(mision)       # kg
    mision["m_prop_kg"]                 # propelente mínimo necesario
    mision["delta_v_m_s"]               # delta-v que exige el destino a la nave
    compatibilidad_lanzador(mision, datos)   # ok, masa_kg, capacidad_kg, margen_kg
    distancia_ua_destino(datos, destino)

## Avisos
- capacidad_kg (y el "limite" de la regla de masa) puede ser None: el lanzador
  no tiene capacidad registrada para ese destino. Mostrar "no disponible".
- Se puede evaluar varias veces la misma misión: el azar se vuelve a tirar.
- Nombres inválidos lanzan ValueError con la lista de opciones disponibles.