# Cambios en `nucleo.py`

Resumen de todo lo que cambió en el núcleo desde la versión inicial (reparto de presupuesto,
parrilla y progreso) hasta hoy, 14 de noviembre de 2026. Está agrupado por tema, no por fecha.

## Resumen rápido

| Tema | Qué cambió |
|---|---|
| Física real | `convertir` usa la ecuación del cohete y la potencia solar para propulsión y potencia |
| Datos de destinos | Mínimo de propulsión y distancia al Sol salen de `destinos.json` |
| Formato de Chambi | La física se lee a nivel de misión (`isp_s`, `masa_seca_kg`, costos) |
| Mensajes | `revelar` y `revisar` traen texto explicativo de `mensajes.json` |
| Fallas | 6 fallas válidas; si fallan varios recursos se muestran todos |
| Parrilla | Sale de `parametros_misiones.json`; `misiones.json` ya no se usa |
| Niveles | 5 niveles fijos, una misión por nivel, con verificación |
| Estrellas | De 0 a 3 según el puntaje, con umbrales de 70 y 85 |
| Botones − y + | `paso_dinero` calcula el paso correcto de cada misión |

## 1. Física real en `convertir` (Bloque 4)

**Antes:** `convertir` era lineal para todos los recursos: `valor = dinero / musd_por_unidad`.

**Ahora:**
- **Propulsión:** el dinero compra propelente (`dinero / musd_por_kg_propelente`) y el delta-v sale de
  `fisica.delta_v(isp_s, m_seca + m_prop, m_seca)`. Cuesta cada vez más ganar un m/s extra.
- **Potencia:** el dinero compra área de panel (`dinero / musd_por_m2`) y la potencia sale de
  `potencia_costo.potencia_generada(distancia_ua, area, eficiencia)`.
- **Resto de recursos** (estructura, comunicaciones, datos, tiempo): siguen siendo lineales.

**Funciones nuevas o modificadas**

| Función | Qué hace |
|---|---|
| `costo_de(recurso, valor)` | Inversa de `convertir`: cuántos M USD cuesta alcanzar un valor |
| `cargar_destinos(ruta)` | Lee `destinos.json` como `{destino: datos}` |
| `delta_v_nave(destino)` | Delta-v que aporta la nave = delta-v del destino − delta-v de LEO. Da 4000 (Luna), 5000 (órbita de Marte), 9100 (superficie de Marte); para LEO da 0 |
| `preparar_parametros(m)` | Devuelve una copia de la misión lista para jugar (ver punto 2) |
| `_problemas_fisica(f)` | Valida el bloque `fisica` de un recurso |
| `recursos_provisionales(m)` / `provisionales_archivo()` | Listan recursos con `"provisional": true` (hoy ninguno) |

**Verificación:** `verificar_parametros` ya no usa `valor × tasa` para saber cuánto cuestan los mínimos
y óptimos; usa `costo_de`. Si un recurso tiene bloque `fisica`, `musd_por_unidad` deja de ser obligatorio.

**Nuevas dependencias:** `import fisica` y `import potencia_costo` (deben estar junto a `nucleo.py`).

## 2. Formato de datos de Chambi

`preparar_parametros` se encarga de adaptar los datos. Se llama sola dentro de `cargar_parametros`,
`iniciar_mision` y `verificar_parametros`, y es idempotente. Hace dos cosas:

1. Si la misión trae `isp_s`, `masa_seca_kg`, `musd_por_kg_propelente`, `eficiencia_panel` y
   `musd_por_m2_panel` a nivel de misión, crea el bloque `fisica` de los recursos `propulsion` y `potencia`.
2. Con `destinos.json`: el mínimo de propulsión pasa a ser `delta_v_nave(destino)` (si es mayor que 0), y la
   potencia recibe la distancia al Sol del destino.

No modifica el diccionario original, trabaja sobre una copia.

## 3. Mensajes de Justin (Bloque 6)

**Nuevas funciones**

| Función | Qué hace |
|---|---|
| `cargar_mensajes(ruta)` | Lee `datos/mensajes.json` (`{}` si no existe) |
| `mensaje(clave, mensajes=None, **datos)` | Llena una plantilla. Busca en `mensajes.json`, luego en el respaldo. Nunca da error por falta de clave |
| `mensajes_fallas(estado)` | Un mensaje por cada recurso bajo su mínimo |
| `mensaje_resultado(estado)` | Mensaje de éxito, o los de todas las fallas, uno por párrafo |
| `mensaje_presupuesto(estado)` | Mensaje de `presupuesto_excedido` |

**Qué clave se usa:** éxito → `exito`; `no_llega` → `delta_v_insuficiente`; `se_apaga` → `potencia_insuficiente`;
cualquier otra falla → la clave con su propio nombre; presupuesto excedido → `presupuesto_excedido`.
Los campos de las plantillas están documentados en el propio archivo. Un campo desconocido se deja tal cual
en vez de romper el juego.

**Respaldo (`MENSAJES_RESPALDO`):** borradores en inglés para `explota`, `incomunicada`, `sin_ciencia` y
`fuera_de_tiempo`, porque `mensajes.json` todavía no los trae. Si Justin los agrega, se usa su texto.

**Sin usar todavía:** `masa_excede_lanzador` y `falla_aleatoria` (eventos aleatorios, Bloque 8).

## 4. Éxito, fallas y todas las fallas a la vez

- `FALLAS_VALIDAS` ahora tiene 6 fallas: `explota`, `no_llega`, `se_apaga`, `incomunicada`, `sin_ciencia`
  y `fuera_de_tiempo`. Antes tenía 4, y por eso Harder e Insane salían como "próximamente".
- **Éxito:** ningún recurso quedó bajo su mínimo (sin cambios).
- **`simular`:** además de `falla` (la primera, por compatibilidad), devuelve `fallas`, la lista completa
  de fallas en el orden del JSON. Todas cuentan por igual.
- **`revisar`** devuelve ahora también `mensaje` (el aviso de presupuesto excedido, o `None`).

## 5. Parrilla: ahora sale de `parametros_misiones.json`

**Antes:** `cargar_misiones(progreso, ruta_misiones, ruta_parametros)` leía `misiones.json` (de Piero) y
marcaba como jugables las que tenían parámetros.

**Ahora:** `cargar_misiones(progreso, ruta_parametros)` lee solo `parametros_misiones.json`. `misiones.json`
ya no se usa. Cada fila trae únicamente `id`, `nombre`, `nivel`, `dificultad`, `destino`, `cohete`,
`presupuesto_musd`, `estado`, `mejor_puntaje` y `estrellas`, y nunca los mínimos ni óptimos.

- `nombre` viene del campo `nombre` de cada misión (en inglés). Si falta, se arma a partir del id.
- Una misión `proximamente` ya no deja bloqueada para siempre a la siguiente: el desbloqueo en orden la salta.
- **Cambio de firma:** `cargar_misiones` y `puede_jugar` ya no reciben `ruta_misiones`.
- Se eliminaron `_id_mision` y `_ids_con_parametros`.

## 6. Niveles fijos

Hay 5 niveles (`DIFICULTADES`): Easy, Normal, Hard, Harder e Insane. Cada uno tiene exactamente una misión,
la que tiene ese valor en `dificultad`.

- **`verificar_niveles(ruta)`** (nueva) avisa de: nivel sin misión, nivel con varias, nivel desconocido (se
  compara tal cual: "Hard", no "hard"), ids repetidos, y niveles que no incluyen los recursos del nivel anterior.
  También sale al correr `python nucleo.py --verificar`.
- **`cargar_misiones`** ignora las misiones de nivel desconocido y la segunda misión de un nivel ya ocupado.
  No rompe el juego; el aviso queda en la verificación.
- Cada nivel añade un recurso al anterior: 2, 3, 4, 5 y 6 recursos.

## 7. Estrellas

| Estrellas | Condición |
|---|---|
| 0 | La misión no se completó |
| 1 | Misión completada, cualquier puntaje |
| 2 | Puntaje de 70 o más |
| 3 | Puntaje de 85 o más |

**Por qué esos números:** cumplir justo los mínimos da entre 63 y 70 puntos (1 estrella), y el mejor puntaje
posible por nivel es 87–94, así que 85 exige un reparto muy cuidado pero alcanzable.

**Funciones y campos nuevos**

| Elemento | Qué hace |
|---|---|
| `ESTRELLAS_UMBRALES = (70, 85)` | Umbrales por defecto |
| `umbrales_estrellas(m)` | Umbrales de una misión; usa su campo opcional `"estrellas": [dos, tres]` |
| `estrellas_de(puntaje, umbrales, completada)` | Convierte un puntaje en estrellas |
| `puntaje_maximo(parametros)` | Estimación del mejor puntaje posible; una prueba comprueba que las 3 estrellas sigan siendo alcanzables |
| `revelar` → `estrellas`, `siguiente_estrella_pts` | Estrellas ganadas y cuánto falta para la siguiente |
| `estado["umbrales_estrellas"]` | Los umbrales de la misión en curso |
| Parrilla → `estrellas` | Estrellas según el mejor puntaje guardado |

Pasarse del óptimo sigue restando puntos, igual que quedarse corto.

## 8. Botones − y +

`paso_dinero(estado)` (nueva) da el paso de cada misión: Easy 0.5, Normal 1, Hard 5, Harder 5, Insane 4 M USD.
Elige el paso "redondo" más grande que divide el presupuesto, da al menos 25 pasos y permite comprar todos los
mínimos sin pasarse. Un paso fijo de 5 haría imposible Easy, cuyos mínimos cuestan unos 11 M USD y con ese paso
habría que gastar 15 de un presupuesto de 14.5.

## 9. Cómo queda `revelar`

```python
{'puntaje': 87, 'exito': True, 'optimo': False,
 'falla': None, 'fallas': [],                       # fallas: lista completa, cada una con su mensaje
 'mensaje': 'Mission complete! ...',
 'estrellas': 3, 'siguiente_estrella_pts': None,
 'recursos': [ {... 'minimo', 'optimo', 'puntos', 'bajo_minimo', 'cerca_optimo', 'fuente'} ]}
```

Todos los cambios al valor de retorno de las funciones son campos nuevos: nada de lo que ya usaba la
interfaz cambió de nombre.

## 10. Lo que NO cambió

- El flujo: `iniciar_mision → repartir → revisar → simular → revelar → registrar_resultado`.
- Cómo se calculan los puntos por recurso y el puntaje (promedio; 0 si la misión falló).
- Las reglas de presupuesto y los presupuestos por nivel (son de referencia y Chambi puede cambiarlos).
- El indicador `optimo` de `revelar`: en Easy y Normal no se llega a cumplir porque los óptimos cuestan más que
  el presupuesto.

## 11. Archivos que necesita

```
nucleo.py  fisica.py  potencia_costo.py
datos/parametros_misiones.json  datos/destinos.json  datos/mensajes.json
```

`datos/misiones.json` ya no hace falta. Para probar sin interfaz: `python jugar_consola.py`; para comprobar los
datos: `python nucleo.py --verificar`; para correr todas las pruebas: `python nucleo.py`.

## 12. Pendiente de otras personas

- **Justin:** agregar a `mensajes.json` las claves `explota`, `incomunicada`, `sin_ciencia` y `fuera_de_tiempo`, y
  decidir qué hacer con las pistas, que siguen en español.
- **Chambi:** conservar el campo `nombre` al regenerar `parametros_misiones.json`; si cambia los presupuestos,
  volver a correr `python nucleo.py` para comprobar que las 3 estrellas siguen siendo alcanzables.
- **Gonzalo:** tomar el `nucleo.py` y el `CONTRATO_API.md` nuevos y usar `paso_dinero`, `fallas` y `estrellas`.
