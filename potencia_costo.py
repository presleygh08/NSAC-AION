import math

S0 = 1361.0   # W/m^2 (irradiancia solar a 1 UA)

def potencia_generada(distancia_ua, area_m2, eficiencia):
    """Potencia eléctrica generada por el panel solar según la distancia al Sol.
    distancia_ua: UA | area_m2: m^2 | eficiencia: fracción entre 0 y 1
    Devuelve: potencia generada en W."""
    if distancia_ua <= 0 or area_m2 < 0 or not (0 < eficiencia <= 1):
        raise ValueError("distancia_ua > 0, area_m2 >= 0 y eficiencia entre 0 y 1")
    return (S0 / (distancia_ua ** 2)) * area_m2 * eficiencia


def balance_potencia(generada_w, consumos):
    """Diferencia entre la potencia generada y el consumo de la nave.
    generada_w: W | consumos: número total, lista o diccionario de consumos en W
    Devuelve: balance de potencia en W (positivo si alcanza, negativo si falta)."""
    if isinstance(consumos, dict):
        total_consumos = sum(consumos.values())
    elif isinstance(consumos, (list, tuple, set)):
        total_consumos = sum(consumos)
    else:
        total_consumos = consumos
    return generada_w - total_consumos


def costo_total(lanzador, nave, instrumentos):
    """Costo total de la misión.
    lanzador: M$ | nave: M$ | instrumentos: número total o lista de costos en M$
    Devuelve: costo total en millones de USD (M$)."""
    total_instrumentos = sum(instrumentos) if isinstance(instrumentos, (list, tuple, set)) else instrumentos
    if lanzador < 0 or nave < 0 or total_instrumentos < 0:
        raise ValueError("Los costos no pueden ser negativos")
    return lanzador + nave + total_instrumentos



if __name__ == "__main__":

    p_luna = potencia_generada(1.0, 2.0, 0.28)
    p_marte = potencia_generada(1.524, 2.0, 0.28)
    bal_ok = balance_potencia(p_luna, [120, 80, 150])
    c_mision = costo_total(67.0, 40.0, [12.0, 30.0])

    assert math.isclose(p_luna, 762.16, rel_tol=1e-3)
    assert math.isclose(p_marte, 328.14, rel_tol=1e-3)
    assert math.isclose(bal_ok, p_luna - 350, rel_tol=1e-6)
    assert math.isclose(c_mision, 149.0, rel_tol=1e-6)

    print(f"OK  potencia_luna={p_luna:.1f} W, potencia_marte={p_marte:.1f} W, balance={bal_ok:.1f} W, costo={c_mision:.1f} M$")
