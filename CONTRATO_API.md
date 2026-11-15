# Contrato de nucleo.py para la interfaz (Gonzalo)

Regla: la interfaz solo llama a estas funciones. Durante el reparto NO lee
`estado["recursos"]` (trae mínimos y óptimos ocultos); usa `recursos_visibles`.
Hasta el cierre del Bloque 8 se pueden AÑADIR campos, pero no cambian los nombres.

## Archivos que deben estar juntos
```
nucleo.py  fisica.py  potencia_costo.py
datos/parametros_misiones.json  datos/destinos.json  datos/mensajes.json
```
`datos/misiones.json` YA NO SE USA: la parrilla sale de `parametros_misiones.json`.
Probar sin interfaz: `python jugar_consola.py` (usa solo estas funciones).
Verificar los datos: `python nucleo.py --verificar`.

## Niveles
Hay 5 niveles fijos: Easy, Normal, Hard, Harder, Insane. Cada nivel tiene UNA misión,
la que tiene ese valor en su campo `dificultad` de `parametros_misiones.json`.
Cada nivel añade un recurso al anterior (2, 3, 4, 5 y 6 recursos).

## Flujo de una misión
```python
progreso = nuevo_progreso()                       # una vez por jugador
parrilla = cargar_misiones(progreso)              # pantalla de misiones
if puede_jugar(progreso, "easy_cubesat"):
    estado = iniciar_mision(cargar_parametros("easy_cubesat"))
    paso = paso_dinero(estado)                    # paso de los botones - y +
    repartir(estado, "estructura", 8.5)           # las veces que quiera el jugador
    repartir(estado, "propulsion", 6.0)
    rev = revisar(estado)                         # {'ok', 'exceso_musd', 'mensaje'}
    if rev["ok"]:
        simular(estado)
        info = revelar(estado)                    # pantalla de resultados
        registrar_resultado(progreso, estado)     # guarda el mejor puntaje
```

## Funciones
| Función | Cuándo | Devuelve |
|---|---|---|
| `nuevo_progreso()` | al empezar | `{'completadas': {id: mejor_puntaje}}` |
| `cargar_misiones(progreso)` | parrilla | lista de los 5 niveles en orden (ver abajo) |
| `puede_jugar(progreso, id)` | al elegir misión | `True` si está disponible o completada |
| `cargar_parametros(id)` | al jugar | diccionario de la misión |
| `iniciar_mision(parametros)` | al jugar | `estado` |
| `paso_dinero(estado)` | al jugar | paso (M USD) para los botones − y + de esa misión |
| `repartir(estado, clave, dinero_musd)` | reparto | `estado` (no bloquea si se pasa del presupuesto) |
| `recursos_visibles(estado)` | reparto | lista de recursos sin mínimos ni óptimos |
| `presupuesto_restante(estado)` | reparto | M USD sin repartir (negativo si se pasó) |
| `revisar(estado)` | botón "lanzar" | `{'ok', 'exceso_musd', 'mensaje'}` |
| `simular(estado)` | tras `revisar` ok | `{'exito', 'falla', 'fallas', 'bajo_minimo'}` |
| `revelar(estado)` | pantalla de resultados | ver abajo |
| `registrar_resultado(progreso, estado)` | tras `simular` | `progreso` |

Campos de `estado` que la interfaz puede leer: `mision`, `destino`, `cohete`,
`presupuesto_musd`, `pistas` (lista de textos), `fase`.

## Éxito, fallas y estrellas
- **Éxito:** ningún recurso quedó bajo su mínimo. Lo demás (puntaje) solo decide las estrellas.
- **Fallas:** cada recurso bajo su mínimo es una falla, y TODAS cuentan igual.
  `revelar` las trae todas en `fallas`, cada una con su mensaje.

| Recurso | Falla |
|---|---|
| estructura | `explota` |
| propulsion | `no_llega` |
| potencia | `se_apaga` |
| comunicaciones | `incomunicada` |
| datos | `sin_ciencia` |
| tiempo | `fuera_de_tiempo` |

- **Estrellas:** 0 = no se completó. 1 = misión completada (cualquier puntaje).
  2 = puntaje de 70 o más. 3 = puntaje de 85 o más. Completar solo pide no fallar, así
  que con 1 estrella ya se desbloquea el siguiente nivel; las estrellas invitan a repetir.
  Una misión puede traer su propio `"estrellas": [dos, tres]` en el JSON.
- **Puntaje:** promedio de los puntos por recurso. Cada recurso da
  `100 × (1 − |valor − óptimo| / óptimo)`: quedarse corto o pasarse del óptimo resta por igual.

## Paso de los botones − y +
NO usar un paso fijo. `paso_dinero(estado)` da el paso de cada misión:

| Misión | Paso (M USD) |
|---|---|
| easy_cubesat | 0.5 |
| normal_leo | 1 |
| hard_mro_marte | 5 |
| harder_perseverance | 5 |
| insane_artemis1 | 4 |

Con pasos de 5, Easy (14.5 M USD) sería imposible: sus mínimos cuestan ~11 y habría
que gastar 15. Usar `repartir(estado, clave, round(dinero + paso, 6))`, sin bajar de 0.

## Ejemplos reales
`cargar_misiones(progreso)` -> una fila por nivel, con SOLO estos campos
(nunca mínimos ni óptimos): `id, nombre, nivel, dificultad, destino, cohete,
presupuesto_musd, estado, mejor_puntaje, estrellas`.
`estado` es `'completada'`, `'disponible'`, `'bloqueada'` o `'proximamente'`
(parámetros incompletos). `estrellas` es 0 si no está completada, y 1 a 3 si lo está.
```python
{'id': 'easy_cubesat', 'nombre': 'CubeSat in orbit', 'nivel': 1, 'dificultad': 'Easy',
 'destino': 'LEO', 'cohete': 'Electron', 'presupuesto_musd': 14.5,
 'mejor_puntaje': None, 'estrellas': 0, 'estado': 'disponible'}
```

`recursos_visibles(estado)`
```python
[{'clave': 'estructura', 'unidad': 'kg',  'dinero_musd': 8.5, 'valor': 8.5},
 {'clave': 'propulsion', 'unidad': 'm/s', 'dinero_musd': 6.0, 'valor': 297.37}]
```

`revisar(estado)` con el reparto pasado de presupuesto
```python
{'ok': False, 'exceso_musd': 5.5, 'mensaje': 'The mission stopped before launch: it costs 20 M USD ...'}
```
Con `ok: True`, `mensaje` es `None` y la misión pasa a la fase de simulación
(desde ahí ya no se puede volver a repartir).

`revelar(estado)` con éxito
```python
{'puntaje': 87, 'exito': True, 'optimo': False, 'falla': None, 'fallas': [],
 'mensaje': 'Mission complete! Your ship reached LEO and every limit held, ...',
 'estrellas': 3, 'siguiente_estrella_pts': None,
 'recursos': [
   {'clave': 'propulsion', 'unidad': 'm/s', 'valor': 297.37, 'minimo': 250, 'optimo': 400,
    'puntos': 74, 'bajo_minimo': False, 'cerca_optimo': False, 'fuente': 'https://...'},
   ...]}
```
`revelar(estado)` con dos fallas a la vez
```python
{'puntaje': 0, 'exito': False, 'falla': 'explota',          # 'falla' = solo la primera (compatibilidad)
 'fallas': [{'clave': 'estructura', 'falla': 'explota',  'mensaje': 'The ship broke apart ...'},
            {'clave': 'propulsion', 'falla': 'no_llega', 'mensaje': 'The mission stopped: this trip needs 250 m/s ...'}],
 'mensaje': '<los dos mensajes juntos, uno por párrafo>',
 'estrellas': 0, 'siguiente_estrella_pts': None, 'recursos': [...]}
```
- Para mostrar las fallas por separado, recorrer `fallas`; para un solo bloque de texto, usar `mensaje`.
- `siguiente_estrella_pts` es el puntaje que falta alcanzar para la próxima estrella
  (`None` si la misión falló o ya tiene 3).
- Si la misión falló, `puntaje` es 0. Los mensajes vienen de `datos/mensajes.json`, en inglés.

## Errores que la interfaz debe esperar
`ValueError` si: se reparte dinero negativo, el recurso no existe, se llama una
función fuera de su fase (por ejemplo `simular` antes de `revisar`) o la misión no existe.

## Pendiente de otros
- Pistas (`estado["pistas"]`) siguen en español: Justin decide su traducción y dónde se guarda.
- Faltan en `mensajes.json` las claves `explota`, `incomunicada`, `sin_ciencia` y `fuera_de_tiempo` (hay borradores de respaldo en el código).
- Los presupuestos por nivel son de referencia; Chambi puede cambiarlos tras su investigación. Si cambian, repetir `python nucleo.py` (comprueba que las 3 estrellas sigan siendo alcanzables).
- `destino` y los nombres de recursos se muestran traducidos por la interfaz (el núcleo los devuelve como están en los JSON).
