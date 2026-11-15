# jugar_consola.py
# Runner de consola para probar TODO el flujo del núcleo sin interfaz gráfica.
# Sirve también como ejemplo de uso para Gonzalo: solo llama a funciones de nucleo.
#
# Uso:  python jugar_consola.py

import nucleo

ETIQUETA = {"completada": "COMPLETADA", "disponible": "disponible", "bloqueada": "bloqueada",
            "proximamente": "próximamente"}


def elegir_mision(progreso):
    parrilla = nucleo.cargar_misiones(progreso)
    print("\n=== MISIONES ===")
    for i, f in enumerate(parrilla, 1):
        pts = (f" (mejor: {f['mejor_puntaje']}  {'★' * f['estrellas']}{'☆' * (5 - f['estrellas'])})"
               if f["mejor_puntaje"] is not None else "")
        print(f"{i}. [{f['dificultad']}] {f['nombre']} -> {f['destino']}, {f['cohete']}  "
              f"- {ETIQUETA[f['estado']]}{pts}")
    while True:
        op = input("Elige una misión (número, o 'q' para salir): ").strip().lower()
        if op == "q":
            return None
        if op.isdigit() and 1 <= int(op) <= len(parrilla):
            fila = parrilla[int(op) - 1]
            if nucleo.puede_jugar(progreso, fila["id"]):
                return fila["id"]
            print("Esa misión no está disponible todavía.")


def jugar(mision_id, progreso):
    estado = nucleo.iniciar_mision(nucleo.cargar_parametros(mision_id))
    print(f"\nMisión: {estado['mision']} -> {estado['destino']} con {estado['cohete']}")
    print(f"Presupuesto: {estado['presupuesto_musd']} M USD")
    for pista in estado["pistas"]:
        print("  Pista:", pista)
    while True:
        print()
        for r in nucleo.recursos_visibles(estado):
            print(f"  {r['clave']:<15} {r['dinero_musd']:>7.2f} M USD  ->  {r['valor']:.1f} {r['unidad']}")
        print(f"  Restante: {nucleo.presupuesto_restante(estado):.2f} M USD")
        clave = input("Recurso a financiar (Enter = lanzar): ").strip()
        if clave == "":
            rev = nucleo.revisar(estado)
            if rev["ok"]:
                break
            print(rev["mensaje"])
            continue
        try:
            nucleo.repartir(estado, clave, float(input("  M USD: ")))
        except ValueError as ex:
            print("  ->", ex)
    nucleo.simular(estado)
    info = nucleo.revelar(estado)
    print("\n=== RESULTADO ===")
    if info["exito"]:
        print(info["mensaje"])
    else:
        for f in info["fallas"]:                # todas las fallas, con el mismo peso
            print(f"- [{f['clave']} -> {f['falla']}] {f['mensaje']}\n")
    print(f"Puntaje: {info['puntaje']}   {'★' * info['estrellas']}{'☆' * (5 - info['estrellas'])}")
    if info["siguiente_estrella_pts"]:
        print(f"Para la siguiente estrella: {info['siguiente_estrella_pts']} puntos")
    for f in info["recursos"]:
        marca = "BAJO EL MÍNIMO" if f["bajo_minimo"] else ("cerca del óptimo" if f["cerca_optimo"] else "")
        print(f"  {f['clave']:<15} {f['valor']:>9.1f} {f['unidad']:<6} mín {f['minimo']:<7} "
              f"ópt {f['optimo']:<7} {f['puntos']:>3} pts  {marca}")
    nucleo.registrar_resultado(progreso, estado)


if __name__ == "__main__":
    progreso = nucleo.nuevo_progreso()
    while True:
        mision = elegir_mision(progreso)
        if mision is None:
            break
        jugar(mision, progreso)
