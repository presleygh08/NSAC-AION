# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

"Space Mission Design Game" for the NASA Space Apps Challenge 2026 (event: Nov 14–15, 2026). The player designs a space mission under limited resources (mass, power, cost, launcher capacity), then simulates it and sees the result explained. The UI is built with Pygame (decided Nov 12; the README still says Streamlit) and the game must work offline: all data is in `datos/`.

Everything is written in Spanish: code identifiers, docstrings, error messages, data keys, and docs. Keep new code in Spanish to match.

The repo is in an early, pre-event state. `README.md` describes a planned layout that **does not exist yet**: `fisica.py` (physics, Emanuel), `juego.py` (state/phases/events/score, Emanuel), `app.py` (Pygame UI, Gonzalo), `requirements.txt`. Sections marked **[COMPLETAR]** in the README get filled in during the event.

## Commands

No build, lint, or test framework yet. Tests are `assert`-based self-checks in each module's `if __name__ == "__main__":` block:

```bash
python3 Funciones/Funciones/potencia.py   # rocket equation + power + cost checks
python3 Funciones/fisica.py               # rocket equation checks only
```

Planned run command (once `app.py`/`requirements.txt` exist):

```bash
pip install -r requirements.txt
python3 app.py
```

## Code layout notes

- `Funciones/Funciones/potencia.py` is a **superset** of `Funciones/fisica.py`: it has the same `masa_propelente` and `delta_v` (Tsiolkovsky, `G0 = 9.80665`), plus `potencia_generada` (solar flux `S0 = 1361 W/m²` scaled by 1/d²), `balance_potencia`, and `costo_total`. Changes to the shared functions have to go into both files until they are merged into the planned top-level `fisica.py`.
- Physics functions raise `ValueError` on invalid input. Units go in the docstrings (m/s, s, kg, W, M USD).
- `Hi.py` is a scratch/hello-world file.

## Data contract (`datos/*.json`)

The README's section 4 is the authoritative spec. Key rules for code that reads the data:

- Units go in the key suffix: `_kg`, `_m_s`, `_ua`, `_km`, `_dias`, `_musd` (millions of USD). Decimal points, UTF-8 (load with `encoding="utf-8"`; names contain accents).
- **`null` means "no published data", not zero or "impossible".** Skip it in calculations and treat it as "this launcher has no figure for that destination". Every numeric field has a matching `fuente_*` field, and a `null` value has a `null` source.
- Launcher capacities are theoretical maxima under different conditions per manufacturer (often expendable configs). Costs are reference values from different years with no inflation adjustment. SLS cost is the rocket only. Don't present them as directly comparable or contractual.
- Files: `lanzadores.json` (capacity to LEO/Luna/Marte + cost per launcher), `destinos.json` (`destino`, `delta_v_m_s`, `distancia_ua`, `fuente`), `misiones.json` (3 NASA reference missions: `nombre`, `destino`, `masa_kg`, `distancia_km`, `duracion_dias`, `fuente`).
- `distancia_ua` in `destinos.json` is the input for `potencia_generada`.

Known inconsistencies to watch for when joining data:
- Destination strings must match across files (README rule), but `lanzadores.json` only has coarse `luna`/`marte` columns, while `destinos.json`/`misiones.json` use `"LEO"`, `"órbita lunar"`, `"órbita de Marte"`, `"superficie de Marte"`. Any launcher↔destination lookup needs an explicit mapping.
- The README's destination list (which includes "superficie lunar") and some of its source URLs don't match the JSON files exactly. `datos/README.md` says sources were unified under one `fuente` key, but `lanzadores.json` still uses per-field `fuente_*`. Check the JSON before trusting either README.

## Team plan
Game concept (v3: avatar, Easy–Insane grid, hidden minimum/optimal values, simulation outcomes, scoring): @docs/concepto-juego.md
Team split and definition (v4: roles and file ownership, Emanuel↔Gonzalo contract, resources per difficulty, parametros_misiones.json format, schedule): @docs/reparto-v4.md
If v3 and v4 conflict, follow v4. Both supersede older plan items (e.g. the green/yellow/red checklist) and plan-equipo-resumen.md.
Roles, screens, function/data contract and the 48 h schedule: @docs/plan-equipo-resumen.md
Official challenge statement, deliverables, judging criteria and plan-vs-challenge gaps: @docs/reto.md
All user-facing text (game UI, messages, README) must be in English per Space Apps rules; code identifiers stay in Spanish.
Team (5, roles per v4): Gonzalo (Pygame UI: app.py, interfaz/), Emanuel (game architecture: juego.py, fisica.py, potencia_costo.py), Chambi (research: datos/parametros_misiones.json), Justin (game definition, mensajes.json, textos_en.json, pitch), Piero (visual design: assets/, README, submission).

## UI rules (Pygame)
- The UI only calls functions from fisica.py / juego.py; no physics or game logic inside screens.
- Game state lives in a dict in the main loop (not st.session_state).
- Screens (v4): avatar → parrilla (Easy–Insane) → objetivo (CML1) → presupuesto y pistas (CML2) → taller de reparto (CML3) → revisión (CML4, only budget) → simulación (4 failures + success) → resultados con revelado de mínimo/óptimo. See docs/reparto-v4.md.
- Contract with juego.py (names fixed by Emanuel; until then use stubs with these names): cargar_misiones(), iniciar_mision(id), repartir(estado, recurso, dinero), presupuesto_restante(estado), revisar(estado), simular(estado), puntaje(estado), revelar(estado).
- Result texts are read from datos/mensajes.json (keys: exito, delta_v_insuficiente,
  potencia_insuficiente, masa_excede_lanzador, presupuesto_excedido, falla_aleatoria).
- Use the exact function names, JSON columns and message keys from the contract; if something doesn't fit, ask instead of inventing new names.
- Units everywhere: kg, m/s, W, millions of USD.
