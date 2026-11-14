# Evidencia de Validity: misión Easy (easy_cubesat)

Fecha: 2026-11-14 · Bloque 5 (actualizado con los números de Chambi) · Estado: **con valores reales de Chambi**.

## Criterio
La mayoría de los repartos NO completa la misión, algunos sí, y el mejor
puntaje es alcanzable pero exige criterio.

## Configuración probada
- Presupuesto: 14.5 M USD · Cohete: Electron · Destino: LEO.
- Estructura: mínimo 6.0 kg, óptimo 8.5 kg, 1.0 M USD/kg.
- Propulsión (física real): mínimo 250 m/s, óptimo 400 m/s, Isp 220 s,
  masa seca 20 kg, 2.03 M USD/kg de propelente.
- Costo de los mínimos: 10.99 M USD. Costo de los óptimos: 16.77 M USD.
  Se cumple costo(mínimos) <= presupuesto < costo(óptimos).

## Resultado con el presupuesto actual (grilla de 100 pasos de 0.145 M USD)
Reproducible con `validar_mision(cargar_parametros("easy_cubesat"), pasos=100)`.

| Medida | Valor |
|---|---|
| Repartos dentro del presupuesto | 5151 |
| Completan la misión | 300 (5.8 %) |
| Repartos que gastan todo el presupuesto | 101 |
| De esos, completan | 24 (23.8 %) |
| Mejor puntaje | 87 / 100 |
| Repartos "óptimos" (todos a ±10 % del óptimo) | 0 (imposible por diseño: los óptimos cuestan más que el presupuesto) |

Mejores repartos (87 puntos): estructura 8.5 M USD + propulsión 6.0 M USD, o
estructura ~6.2 M USD + propulsión ~8.3 M USD.

## Sensibilidad al presupuesto

| Presupuesto (M USD) | Completan (todos) | Completan (gastan todo) | Mejor puntaje |
|---|---|---|---|
| 12.0 | 0.9 % | 8.9 % | 73 |
| 13.0 | 2.3 % | 14.9 % | 78 |
| 14.0 | 4.9 % | 21.8 % | 84 |
| **14.5** | **5.8 %** | **23.8 %** | **87** |
| 15.0 | 7.3 % | 26.7 % | 90 |
| 16.0 | 9.6 % | 30.7 % | 96 |

Todos son válidos (mínimos <= presupuesto < óptimos).

## Conclusión
Con 14.5 M USD se cumple el criterio: la gran mayoría de los repartos falla,
una minoría (casi uno de cada cuatro si se gasta todo) completa la misión, y el
mejor puntaje (87) es alto sin llegar a 100.

## Observación de diseño (para Justin)
Con estos números, dos repartos muy distintos empatan en 87 puntos. La
pendiente de puntos por M USD es casi igual en estructura (~11.8) y propulsión
(~11 a 11.5, según cuánto se gaste). Por eso el criterio del jugador pesa sobre
todo en NO quedar bajo el mínimo de ninguno de los dos recursos, y menos en
afinar el reparto.

## Pendiente
- Confirmar con Chambi y Justin si 14.5 M USD se queda o se ajusta.
