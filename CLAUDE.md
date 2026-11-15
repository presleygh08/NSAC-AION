# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

"Space Mission Design Game" for the NASA Space Apps Challenge 2026 (event: Nov 14–15, 2026). The player designs a space mission under limited resources (mass, power, cost, launcher capacity), then simulates it and sees the result explained. The UI is built with Pygame (decided Nov 12; the README still says Streamlit) and the game must work offline: all data is in `datos/`.

Everything is written in Spanish: code identifiers, docstrings, error messages, data keys, and docs. Keep new code in Spanish to match.

Main files: `nucleo.py` (game logic: missions, allocation, review, simulation, score; Emanuel; it replaced `juego.py`, now `juego_v1.py`), `fisica.py` and `potencia_costo.py` (physics), `app.py` + `interfaz/` (Pygame UI, Gonzalo), `jugar_consola.py` (plays the whole flow in the terminal, no UI). `README.md` may still describe an older layout; sections marked **[COMPLETAR]** get filled in during the event.

## Commands

No build, lint, or test framework yet. Tests are `assert`-based self-checks in each module's `if __name__ == "__main__":` block:

```bash
python3 nucleo.py              # game logic self-tests (also validates Easy and Normal)
python3 nucleo.py --verificar  # checks datos/parametros_misiones.json
python3 nucleo.py --validar-fino  # finer search: every mission solvable, best score (docs/evidencia_validacion_misiones.md)
python3 fisica.py              # rocket equation checks
python3 potencia_costo.py      # power + cost checks
python3 jugar_consola.py       # play the flow in the terminal
python3.12 revisar_textos.py   # v3 test mode: every screen in EN and ES, warns if a text leaves its box (--capturas saves PNGs)
```

Run the game (needs pygame, which is installed for python3.12, not for the Anaconda python3):

```bash
python3.12 app.py
```

## Code layout notes

- Physics functions raise `ValueError` on invalid input. Units go in the docstrings (m/s, s, kg, W, M USD).

## Data contract (`datos/*.json`)

The README's section 4 is the authoritative spec. Key rules for code that reads the data:

- Units go in the key suffix: `_kg`, `_m_s`, `_ua`, `_km`, `_dias`, `_musd` (millions of USD). Decimal points, UTF-8 (load with `encoding="utf-8"`; names contain accents).
- **`null` means "no published data", not zero or "impossible".** Skip it in calculations and treat it as "this launcher has no figure for that destination". Every numeric field has a matching `fuente_*` field, and a `null` value has a `null` source.
- Launcher capacities are theoretical maxima under different conditions per manufacturer (often expendable configs). Costs are reference values from different years with no inflation adjustment. SLS cost is the rocket only. Don't present them as directly comparable or contractual.
- Files: `lanzadores.json` (capacity to LEO/Luna/Marte + cost per launcher), `destinos.json` (`destino`, `delta_v_m_s`, `distancia_ua`, `fuente`), `parametros_misiones.json` (one mission per difficulty: id in `mision`, `dificultad`, `destino`, `cohete`, `presupuesto_musd`, `recursos` with hidden `minimo`/`optimo`, `pistas`; the mission grid comes from here), `mensajes.json` (result texts). `misiones_v1.json` is no longer used.
- `distancia_ua` in `destinos.json` is the input for `potencia_generada`.

Known inconsistencies to watch for when joining data:
- Destination strings must match across files (README rule), but `lanzadores.json` only has coarse `luna`/`marte` columns, while `destinos.json`/`misiones.json` use `"LEO"`, `"órbita lunar"`, `"órbita de Marte"`, `"superficie de Marte"`. Any launcher↔destination lookup needs an explicit mapping.
- The README's destination list (which includes "superficie lunar") and some of its source URLs don't match the JSON files exactly. `datos/README.md` says sources were unified under one `fuente` key, but `lanzadores.json` still uses per-field `fuente_*`. Check the JSON before trusting either README.

## Team plan
Read these only when the task needs them (not loaded automatically):
- `docs/team-notes/reparto-v4.md` — team split and definition (v4: roles and file ownership, Emanuel↔Gonzalo contract, resources per difficulty, parametros_misiones.json format, schedule).
- `docs/team-notes/concepto-juego.md` — game concept (v3). If v3 and v4 conflict, follow v4. Both supersede older plan items (e.g. the green/yellow/red checklist) and `docs/team-notes/plan-equipo-resumen.md` (old roles and 48 h schedule).
- `docs/team-notes/reto.md` — official challenge statement, deliverables, judging criteria and plan-vs-challenge gaps. Read it for README, demo, pitch or submission tasks.
All user-facing text (game UI, messages, README) must be in English per Space Apps rules; code identifiers stay in Spanish.
Team (5, roles per v4): Gonzalo (Pygame UI: app.py, interfaz/), Emanuel (game architecture: nucleo.py, fisica.py, potencia_costo.py), Chambi (research: datos/parametros_misiones.json), Justin (game definition, mensajes.json, textos_en.json, pitch), Piero (visual design: assets/, README, submission).

## UI rules (Pygame)
- VERSION 3 decisions (override v2 and the spec where they conflict): @docs/team-notes/v3-cambios.md — verified data and sources: docs/team-notes/auditoria-datos.md.
- VERSION 2 decisions (override the spec where they conflict): @docs/team-notes/v2-cambios.md — English content for new screens is in interfaz/guia_misiones_en.json.
- UI spec (screens, 16-bit style, lab with CML phases, simulation, results, priorities): @docs/team-notes/especificacion-interfaz.md — follow it for everything visual.
- Game logic API: @docs/team-notes/CONTRATO_API.md — the UI only calls functions of nucleo.py listed there (nucleo.py replaced juego.py, now juego_v1.py). During allocation never read estado["recursos"]; use recursos_visibles. Missing functions (cotizar, estrellas, faltante_pct, bonus por ahorro) are added directly to nucleo.py following docs/team-notes/pedidos-emanuel.md.
- Use `paso_dinero` for the − / + buttons, never a fixed step.
- You may edit ANY file in the repo (nucleo.py, fisica.py, potencia_costo.py, datos/, docs, README) when needed to meet the spec or fix a bug. Rules: keep existing function names and data keys used by CONTRATO_API.md (only add), update CONTRATO_API.md when adding functions, rerun the module self-tests/pruebas.py and validar_mision after touching game logic, never invent NASA numbers (mark estimates as such), and list in your final summary which teammates' files you changed.
- Files that stop being used are renamed with a _v1 suffix (not deleted).
- Units: kg, m/s, W, kbps, days, millions of USD.
