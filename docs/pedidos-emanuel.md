# Pedidos de la interfaz para `nucleo.py` (de Gonzalo para Emanuel)

> 14 nov 2026. La interfaz ya sigue `CONTRATO_API.md`. Estas son las funciones o campos que faltan para las pantallas
> nuevas (ver `docs/especificacion-interfaz.md`). Por tiempo, Claude Code (sesión de Gonzalo) puede implementarlas directamente en
> `nucleo.py`; si lo hace, lo avisamos para que las revises y no editemos el mismo bloque a la vez. Solo se AÑADE; no cambia ningún nombre existente.

## 1. `cotizar(estado, clave, valor)` → float (M USD)  · prioridad ALTA
En cada estación el jugador escribe la **cantidad del recurso** (kg, m/s, W…), no el dinero. La interfaz necesita
saber en vivo cuánto cuesta esa cantidad para mostrarlo y luego llamar a `repartir(estado, clave, costo)`.
- Es la inversa de `convertir` (ya tienes `costo_de(recurso, valor)`): `cotizar` solo busca el recurso en el estado y la llama.
- Debe lanzar `ValueError` si `valor < 0` o la clave no existe.
- Opcional: `repartir_valor(estado, clave, valor)` que haga `repartir(estado, clave, cotizar(...))` y devuelva el costo.

## 2. Puntaje con bonus por ahorro y estrellas  · prioridad ALTA
Decisión del equipo: si la misión se completa, el puntaje premia la cercanía al óptimo **y el dinero ahorrado**,
y el resultado se muestra con **0 a 5 estrellas**.
- Agregar el bonus dentro de `puntaje(estado)` (o una función nueva) con una regla simple y documentada,
  por ejemplo: `puntaje_final = round(0.85 * puntaje_cercania + 0.15 * 100 * ahorro / presupuesto)`, con tope 100.
  Ojo: el bonus no debe premiar quedarse corto (si falla, el puntaje sigue siendo 0).
- `estrellas(estado)` → int 0–5. Propuesta: 0 si falló; 1 si completó; 2 si ≥ 40; 3 si ≥ 60; 4 si ≥ 80; 5 si `optimo` es True.
- Agregar a `revelar` los campos `estrellas`, `ahorro_musd` y `presupuesto_usado_pct`.
- Revisa con `validar_mision` que Easy siga cumpliendo el criterio de Validity con el bonus.

## 3. `faltante_pct` en las filas de `revelar`  · prioridad MEDIA
Para la pantalla de derrota: por recurso, cuánto le faltó para el mínimo en %:
`faltante_pct = max(0, (minimo - valor) / minimo * 100)` (0 si no quedó bajo el mínimo).

## 4. Revisión sin bloquear (opcional)  · prioridad BAJA
Hoy `revisar` con `ok` True pasa la fase a `simulacion` y ya no se puede repartir. Si te es fácil, un parámetro
`revisar(estado, confirmar=True)`: con `confirmar=False` solo informa, sin cambiar la fase. Si no, la interfaz se adapta.

## 5. Para Chambi / Justin (datos, no código)
- `parametros_misiones.json`: agregar por misión `descripcion` y `objetivo` **en inglés** (1–2 frases cada uno).
- `pistas` en inglés (hoy están en español).
- Claves que faltan en `datos/mensajes.json`: `explota`, `incomunicada`, `sin_ciencia`, `fuera_de_tiempo`.
