# Data sources and verification

Every number in Star Forge comes from `datos/parametros_misiones.json`, `datos/lanzadores.json` and `datos/destinos.json`.
We checked them against official sources (NASA first; ESA, DLR and manufacturers when NASA does not publish the value) on Nov 15, 2026.

Legend: ✅ verified against the source · 🔶 team estimate or non-official source (used for gameplay, labeled as such)

**Game rule:** the *optimal* value of a resource is the real mission value (or a real reference with design margin) and the *minimum* is the
physical or mission requirement below which the mission fails. Minimums marked 🔶 are team estimates (usually 80–90 % of the real value).
All costs per unit (M USD per kg, per W, etc.) are **gameplay estimates**: there are no official per-unit prices.

## Physics and destinations
| Value in game | Status | Source |
|---|---|---|
| Solar irradiance at Earth: 1361 W/m² | ✅ | [NASA NSSDC Mars Fact Sheet](https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html) (Earth column) |
| Mars distance from the Sun: 1.524 AU | ✅ | NASA NSSDC Mars Fact Sheet (1.52366 AU) |
| Solar irradiance at Mars: 586 W/m² | ✅ | NASA NSSDC Mars Fact Sheet (586.2 W/m²) |
| Delta-v to LEO / lunar orbit / Mars orbit / Mars surface (9.4 / 13.4 / 14.4 / 18.5 km/s from Earth's surface) | 🔶 | Approximate values from common delta-v maps; not an official NASA table |
| Design margin of 20 % | ✅ | [ESA – Margin philosophy for science assessment studies](https://sci.esa.int/documents/34375/36249/1567260131067-Margin_philosophy_for_science_assessment_studies_1.3.pdf) |

## Launch vehicles
| Value | Status | Source |
|---|---|---|
| Electron: 300 kg to LEO | ✅ | [Rocket Lab](https://rocketlabcorp.com/news/updates/rocket-lab-increases-electron-payload-capacity-enabling-interplanetary-missions-and-reusability/) |
| Falcon 9: 22,800 kg to LEO; 4,020 kg to Mars | ✅ | SpaceX published capabilities |
| Falcon Heavy: 63,800 kg to LEO; 16,800 kg to Mars | ✅ | [SpaceX – Falcon Heavy](https://new.spacex.com/vehicles/falcon-heavy) |
| SLS Block 1: more than 95 t to LEO; more than 27 t to the Moon | ✅ | [NASA – SLS](https://www.nasa.gov/humans-in-space/space-launch-system/the-great-escape-sls-provides-power-for-missions-to-the-moon-duzxi/) |
| Launch prices (Electron 7.5, Falcon 9 67, Falcon Heavy 97, SLS 2,200 M USD) | 🔶 | Public list prices / estimates; not used in the score |

## Missions
| Mission | Value | Status | Source |
|---|---|---|---|
| Easy – CubeSat | Dry mass 20 kg (12U class), structure 25–30 % of dry mass, Isp 220 s thruster | 🔶 | Reference values from [NASA SmallSat Institute](https://www.nasa.gov/smallsat-institute/what-are-smallsats-and-cubesats/) and [NASA State-of-the-Art of Small Spacecraft Technology](https://www.nasa.gov/wp-content/uploads/2025/02/soa-2024.pdf) |
| Normal – inspired by NASA Pandora | Launched on a Falcon 9 rideshare, Jan 11, 2026 | ✅ | [NASA Small Satellites blog](https://www.nasa.gov/blogs/smallsatellites/2026/01) |
| Normal | Dry mass 140 kg, power 350–550 W | 🔶 | Generic small-satellite values (the game says "inspired by") |
| Hard – inspired by MRO | Dry mass ~1,030 kg | ✅ | [NASA/JPL MRO spacecraft](https://webarchive.library.unt.edu/web/20090813145340/http://mars.jpl.nasa.gov/mro/mission/sc.html) |
| Hard | Power optimum 1,000 W at Mars | ✅ | NSSDCA data via [Planetary Society](https://www.planetary.org/mission-spending/mro-spending) |
| Hard | Communications optimum 6 Mbps | ✅ | NSSDCA data via Planetary Society (max. data rate 6 Mbps) |
| Hard | Real launch vehicle: Atlas V 401 (game uses Falcon Heavy) | ✅ | NSSDCA via Planetary Society; shown in the mission briefing |
| Harder – inspired by Perseverance | Rover mass 1,025 kg; seven science instruments | ✅ | [NASA/JPL Mars 2020 quick facts](https://www.jpl.nasa.gov/news/press_kits/mars_2020/launch/quick_facts/) |
| Harder | Power optimum 110 W from a nuclear power source (MMRTG) | ✅ | NASA/JPL Mars 2020 |
| Harder | Science instruments 59 kg | 🔶 | [Secondary source (RocketSTEM)](https://www.rocketstem.org/2020/07/20/mars-2020-mission-overview/) |
| Harder | Real launch vehicle: Atlas V 541 (game uses Falcon Heavy) | ✅ | NASA/JPL; shown in the mission briefing |
| Insane – inspired by Artemis I | Mission duration 25.5 days | ✅ | [NASA – Artemis I splashdown](https://www.nasa.gov/?p=285100) |
| Insane | Power optimum 11,200 W (Orion European Service Module) | ✅ | [Airbus / ESA – Orion ESM](https://www.airbus.com/en/products-services/space/space-exploration/moon-missions/orion-european-service-module) |
| Insane | Science payload 98 kg (MARE: 36 kg + 62 kg phantoms) | ✅ | [DLR – MARE experiment](https://www.dlr.de/en/research-and-transfer/featured-topics/mission-moon/artemis-programme/the-mare-cosmic-radiation-experiment-on-board-artemis-i) |
| Insane | Dry mass ~10,300 kg; delta-v 4,000 m/s from LEO for "the ship" | 🔶 | Simplification: in reality the SLS upper stage (ICPS) performs the trans-lunar injection |
| All | Minimums marked as estimates; costs per unit | 🔶 | Team estimates for gameplay |
