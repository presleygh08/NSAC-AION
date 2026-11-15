# Game data

| File | Contents |
|---|---|
| `parametros_misiones.json` | The 5 missions: launch vehicle, destination, budget, and for each resource its unit, hidden minimum and optimum, cost per unit, failure type, source and notes. Clues in English (`pistas`) and Spanish (`pistas_es`). |
| `lanzadores.json` | Launch vehicles: capacity to LEO, Moon and Mars, and reference price. |
| `destinos.json` | Destinations: delta-v from Earth's surface and distance from the Sun (AU). |
| `mensajes.json` / `mensajes_es.json` | Result and failure explanations in English / Spanish. |
| `dialogos_en.json` | AION dialogue lines. |

Units go in the key suffix (`_kg`, `_m_s`, `_ua`, `_dias`, `_musd` = millions of USD). `null` means "no published data".
Sources and verification status of every value: [../docs/data-sources.md](../docs/data-sources.md).
