import math

G0 = 9.80665  # m/s^2

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