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
Team (5, roles per v4): Gonzalo (Pygame UI: app.py, interfaz/), Emanuel (game architecture: nucleo.py, fisica.py, potencia_costo.py), Chambi (research: datos/parametros_misiones.json), Justin (game definition, mensajes.json, textos_en.json, pitch), Piero (visual design: assets/, README, submission).

## UI rules (Pygame)
- UI spec (screens, 16-bit style, lab with CML phases, simulation, results, priorities): @docs/especificacion-interfaz.md — follow it for everything visual.
- Game logic API: @CONTRATO_API.md — the UI only calls functions of nucleo.py listed there (nucleo.py replaced juego.py, now juego_v1.py). During allocation never read estado["recursos"]; use recursos_visibles. Missing functions (cotizar, estrellas, faltante_pct, bonus por ahorro) are added directly to nucleo.py following docs/pedidos-emanuel.md.
- You may edit ANY file in the repo (nucleo.py, fisica.py, potencia_costo.py, datos/, docs, README) when needed to meet the spec or fix a bug. Rules: keep existing function names and data keys used by CONTRATO_API.md (only add), update CONTRATO_API.md when adding functions, rerun the module self-tests/pruebas.py and validar_mision after touching game logic, never invent NASA numbers (mark estimates as such), and list in your final summary which teammates' files you changed.
- Game state lives in a dict in the main loop of app.py.
- Files that stop being used are renamed with a _v1 suffix (not deleted).
- Run with: python3.12 app.py (the Anaconda python3 has no pygame).
- Units: kg, m/s, W, kbps, days, millions of USD.
