import math

G0 = 9.80665  # m/s^2
S0 = 1361.0   # W/m^2 (irradiancia solar a 1 UA)
def masa_propelente(delta_v, isp, m_seca):
    """Propelente necesario para lograr un delta-v.
    delta_v: m/s | isp: s | m_seca: kg
    Devuelve: masa de propelente en kg."""
    if isp <= 0 or m_seca <= 0 or delta_v < 0:
        raise ValueError("isp y m_seca deben ser positivos, delta_v no negativo")
    return m_seca * (math.exp(delta_v / (isp * G0)) - 1) 


def delta_v(isp, m0, mf):
    """Delta-v de la ecuación del cohete.
    isp: s | m0: masa inicial en kg | mf: masa final en kg
    Devuelve: delta-v en m/s."""
    if isp <= 0 or mf <= 0 or m0 < mf:
        raise ValueError("isp y mf deben ser positivos y m0 no puede ser menor que mf")
    return isp * G0 * math.log(m0 / mf)



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
    # (delta_v m/s, isp s, m_seca kg, propelente esperado kg)
    casos = [
        (3100, 320, 500, 843),
        (3100, 450, 500, 509),
        (6200, 320, 500, 3106),
    ]

    for dv, isp, ms, esperado in casos:
        mp = masa_propelente(dv, isp, ms)
        assert math.isclose(mp, esperado, abs_tol=1), f"Falla: {dv}, {isp}, {ms} -> {mp}"

        # Consistencia: la función inversa debe devolver el delta-v original
        dv_vuelta = delta_v(isp, ms + mp, ms)
        assert math.isclose(dv_vuelta, dv, rel_tol=1e-9), f"Inconsistente: {dv_vuelta}"

        print(f"OK  dv={dv}, isp={isp}, m_seca={ms} -> propelente {mp:.1f} kg")

    try:
        masa_propelente(3100, 0, 500)
    except ValueError as e:
        print("Error capturado:", e)


    p_luna = potencia_generada(1.0, 2.0, 0.28)
    p_marte = potencia_generada(1.524, 2.0, 0.28)
    bal_ok = balance_potencia(p_luna, [120, 80, 150])
    c_mision = costo_total(67.0, 40.0, [12.0, 30.0])

    assert math.isclose(p_luna, 762.16, rel_tol=1e-3)
    assert math.isclose(p_marte, 328.14, rel_tol=1e-3)
    assert math.isclose(bal_ok, p_luna - 350, rel_tol=1e-6)
    assert math.isclose(c_mision, 149.0, rel_tol=1e-6)

    print(f"OK  potencia_luna={p_luna:.1f} W, potencia_marte={p_marte:.1f} W, balance={bal_ok:.1f} W, costo={c_mision:.1f} M$")
