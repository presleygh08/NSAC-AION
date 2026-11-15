# Evidencia de Validity: las 5 misiones tienen solución

Fecha: 2026-11-15 (actualizada para la **v2**, decisión D2) · Datos: `datos/parametros_misiones.json` con los presupuestos nuevos y el recurso datos en kg (D8) · Complementa a `evidencia_validacion_easy.md`.

## Cómo se reproduce
```bash
python3 nucleo.py --validar-fino   # tabla de abajo (≈ 3 s)
python3 nucleo.py                  # prueba 25: cada misión completable, con margen y 5 estrellas
```
Función: `validar_mision_fina(parametros)` en `nucleo.py`.

## Método
`validar_mision` (la de antes) prueba repartos en escalones del 10 % del presupuesto. Es demasiado gruesa:
en Harder e Insane **ningún** reparto de esa grilla completa la misión, aunque sí existen repartos que lo hacen.
La validación fina hace esto:

1. Calcula cuánto cuesta llegar exactamente al **mínimo** de cada recurso (`costo_de`, con la física real
   para propulsión y potencia).
2. El **sobrante** = presupuesto − Σ costos de los mínimos se reparte entre los recursos en escalones
   pequeños (2 recursos: 200 escalones; 3: 100; 4: 60; 5: 30; 6: 20), probando **todas** las combinaciones,
   incluso las que dejan dinero sin gastar (por el bonus por ahorro).
3. Para cada combinación calcula el puntaje del juego (cercanía al óptimo + bonus por ahorro).
4. El mejor reparto se **vuelve a jugar con las funciones reales** (`iniciar_mision` → `repartir` → `revisar` →
   `simular` → `revelar`) para confirmar que pasa la revisión, completa la misión y da ese puntaje y estrellas.

**Margen razonable** (v2): sobrante ≥ 10 % del presupuesto, Σ mínimos ≤ P ≤ 1.10 × Σ óptimos y 5 estrellas
alcanzables (puntaje ≥ 86 o diseño óptimo).

**Cambio de la v2 (D2):** antes se exigía P < Σ óptimos (el óptimo nunca cabía) y las 5 estrellas eran casi
imposibles. Ahora `presupuesto_sugerido(parametros)` da el menor valor redondo (múltiplo de 0.5 si P < 50,
de 1 si P < 100, de 5 si es mayor) ≥ **1.05 × Σ costo(óptimos)** con al menos 25 pasos de `paso_dinero`.
El reto sigue: el jugador no ve cuánto lleva gastado (solo un indicador verde/rojo, D1), gastar de más en
un recurso deja menos para otro y el bonus premia ahorrar.

## Presupuestos nuevos (D2)

| Misión | Σ óptimos | 1.05 × Σ óptimos | P antes | **P v2** | Paso − / + |
|---|---|---|---|---|---|
| easy_cubesat | 16.77 | 17.61 | 14.5 | **18** | 0.5 |
| normal_leo | 67.06 | 70.41 | 57 | **71** | 1 |
| hard_mro_marte | 145.73 | 153.02 | 125 | **155** | 5 |
| harder_perseverance | 225.80 | 237.09 | 195 | **240** | 5 |
| insane_artemis1 | 286.09 | 300.40 | 256 | **305** | 5 (antes 4) |

## Resultados (`python3 nucleo.py --validar-fino`)

| Misión | Recursos | P (M USD) | Σ mínimos | Σ óptimos | Sobrante | Repartos probados | Mejor puntaje | Estrellas | Repartos con 5★ | Margen |
|---|---|---|---|---|---|---|---|---|---|---|
| easy_cubesat | 2 | 18 | 10.99 | 16.77 | 39.0 % | 20 301 | 100 | 5 | 49.0 % | OK |
| normal_leo | 3 | 71 | 43.98 | 67.06 | 38.1 % | 176 851 | 100 | 5 | 32.0 % | OK |
| hard_mro_marte | 4 | 155 | 97.72 | 145.73 | 37.0 % | 635 376 | 100 | 5 | 16.7 % | OK |
| harder_perseverance | 5 | 240 | 166.42 | 225.80 | 30.7 % | 324 632 | 100 | 5 | 10.3 % | OK |
| insane_artemis1 | 6 | 305 | 215.49 | 286.09 | 29.3 % | 230 230 | 97 | 5 | 9.2 % | OK |

"Repartos con 5★" = porcentaje de los repartos que ya completan la misión (todos parten de los mínimos) que
además llegan a 5 estrellas: las misiones difíciles siguen exigiendo un reparto más cuidado.

### Grilla gruesa de `validar_mision` (escalones del 10 %), como referencia
| Misión | Repartos | Completan | Mejor puntaje |
|---|---|---|---|
| easy_cubesat | 66 | 10 (15.2 %) | 93 |
| normal_leo | 286 | 20 (7.0 %) | 92 |
| hard_mro_marte | 1 001 | 5 (0.5 %) | 80 |
| harder_perseverance | 3 003 | 6 (0.2 %) | 95 |
| insane_artemis1 | 8 008 | 0 | — |

Lectura: la mayoría de los repartos "a ojo" sigue SIN completar la misión, pero con criterio siempre hay solución.
En Insane ningún reparto en escalones del 10 % la completa: hay que repartir con cuidado los 6 recursos.

## Mejores repartos encontrados

| Misión | Dinero por recurso (M USD) | Cantidades que el jugador escribe en cada estación |
|---|---|---|
| easy_cubesat | estructura 8.24 · propulsión 8.25 | 8.2 kg · 399 m/s |
| normal_leo | estructura 17.51 · propulsión 26.79 · potencia 21.83 | 43.8 kg · 644.1 m/s · 545.9 W |
| hard_mro_marte | estructura 22.57 · propulsión 58.00 · potencia 39.93 · comunicaciones 23.05 | 451.4 kg · 5457.6 m/s · 798 W · 230.5 kbps |
| harder_perseverance | estructura 24.91 · propulsión 108.44 · potencia 42.26 · comunicaciones 23.62 · instrumentos 26.06 | 996.2 kg · 9770.9 m/s · 845.3 W · 236.2 kbps · 57.9 kg |
| insane_artemis1 | estructura 46.98 · propulsión 84.94 · potencia 53.44 · comunicaciones 27.38 · instrumentos 40.95 · tiempo 24.48 | 4697.5 kg · 4299.4 m/s · 1068.5 W · 547.5 kbps · 102.4 kg · 24.5 días |

Con la v2 el mejor reparto queda cerca del óptimo en todo (diseño "óptimo" = 5 estrellas directas) y deja algo
de dinero sin gastar para el bonus.

## Conclusión
Las 5 misiones tienen solución, con sobrante ≥ 29 % y 5 estrellas alcanzables. Si Chambi cambia mínimos u
óptimos, recalcular con `presupuesto_sugerido(cargar_parametros(id))` y repetir `python3 nucleo.py --validar-fino`.
