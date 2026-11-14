import math
from potencia_costo import potencia_generada, balance_potencia, costo_total

# Caso 1: panel de 10 m^2, eficiencia 30 %, a 1 UA (Tierra)
p_tierra = potencia_generada(1, 10, 0.30)
assert math.isclose(p_tierra, 4083, rel_tol=0.01), p_tierra
print(f"OK  Tierra: {p_tierra:.0f} W")

# Caso 2: el mismo panel en Marte (1.524 UA): ~43 % de la potencia
p_marte = potencia_generada(1.524, 10, 0.30)
assert math.isclose(p_marte, 1758, rel_tol=0.01), p_marte
print(f"OK  Marte:  {p_marte:.0f} W")

# Caso 3: balance y costo
b = balance_potencia(p_marte, [300, 450, 200])
assert math.isclose(b, 808, rel_tol=0.02), b
c = costo_total(67, 40, 25)
assert c == 132, c
print(f"OK  balance {b:.0f} W | costo {c} M USD")