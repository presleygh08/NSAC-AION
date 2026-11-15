# Evidencia de Validity: las 5 misiones tienen solución

Fecha: 2026-11-15 · Datos: `datos/parametros_misiones.json` (sin cambios) · Complementa a `evidencia_validacion_easy.md`.

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

**Margen razonable** (criterio del equipo de interfaz): sobrante ≥ 10 % del presupuesto, Σ mínimos ≤ P < Σ óptimos
(hay trade-off: no se puede llegar al óptimo en todo) y 5 estrellas alcanzables (puntaje ≥ 86).

## Resultados

| Misión | Recursos | P (M USD) | Σ mínimos | Σ óptimos | Sobrante | Repartos probados | Mejor puntaje | Estrellas | Repartos con 5★ | Margen |
|---|---|---|---|---|---|---|---|---|---|---|
| easy_cubesat | 2 | 14.5 | 10.99 | 16.77 | 24.2 % | 20 301 | 87 | 5 | 12.8 % | OK |
| normal_leo | 3 | 57.0 | 43.98 | 67.06 | 22.8 % | 176 851 | 88 | 5 | 6.8 % | OK |
| hard_mro_marte | 4 | 125.0 | 97.72 | 145.73 | 21.8 % | 635 376 | 91 | 5 | 3.8 % | OK |
| harder_perseverance | 5 | 195.0 | 163.27 | 227.75 | 16.3 % | 324 632 | 91 | 5 | 3.3 % | OK |
| insane_artemis1 | 6 | 256.0 | 211.49 | 284.89 | 17.4 % | 230 230 | 93 | 5 | 11.6 % | OK |

"Repartos con 5★" = porcentaje de los repartos que ya completan la misión (todos parten de los mínimos) que
además llegan a 5 estrellas: las misiones difíciles exigen un reparto más cuidado.

### Grilla gruesa de `validar_mision` (escalones del 10 %), como referencia
| Misión | Repartos | Completan | Mejor puntaje |
|---|---|---|---|
| easy_cubesat | 66 | 3 (4.5 %) | 87 |
| normal_leo | 286 | 4 (1.4 %) | 86 |
| hard_mro_marte | 1 001 | 1 (0.1 %) | 84 |
| harder_perseverance | 3 003 | 0 | — |
| insane_artemis1 | 8 008 | 0 | — |

Lectura: la mayoría de los repartos "a ojo" NO completan la misión (criterio de la sección 7.2 del bosquejo v4),
pero con criterio siempre hay solución. En Harder e Insane el margen entre "falla" y "completa" es fino.

## Mejores repartos encontrados

| Misión | Dinero por recurso (M USD) | Cantidades que el jugador escribe en cada estación |
|---|---|---|
| easy_cubesat | estructura 6.21 · propulsión 8.27 | 6.2 kg · 400 m/s |
| normal_leo | estructura 16.73 · propulsión 18.33 · potencia 21.94 | 41.8 kg · 454.6 m/s · 548.5 W |
| hard_mro_marte | estructura 21.93 · propulsión 48.45 · potencia 31.61 · comunicaciones 23.00 | 438.6 kg · 5000 m/s · 631.8 W · 230 kbps |
| harder_perseverance | estructura 22.12 · propulsión 91.27 · potencia 30.00 · comunicaciones 23.04 · datos 28.58 | 884.6 kg · 9100 m/s · 600 W · 230.4 kbps · 95.3 pts |
| insane_artemis1 | estructura 42.50 · propulsión 75.98 · potencia 48.91 · comunicaciones 25.03 · datos 36.90 · tiempo 26.68 | 4250 kg · 4000 m/s · 978 W · 500.5 kbps · 92.3 pts · 26.7 días |

Observación para Chambi/Justin: en Hard, Harder e Insane el mejor reparto deja la **propulsión justo en su
mínimo** (el delta-v del destino): es el recurso más caro por punto, así que conviene no pasarse. Es coherente con
la física (Tsiolkovsky), pero vale explicarlo en las pistas.

## Conclusión
Las 5 misiones tienen al menos un reparto que las completa, con sobrante ≥ 16 % y 5 estrellas alcanzables.
**No hace falta ajustar `presupuesto_musd`.**
