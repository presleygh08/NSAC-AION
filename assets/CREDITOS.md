# Asset credits

Every image, font or sound in `assets/` must be listed here with its source and license
(Space Apps rule: list everything used, even if free or open source). No NASA logos or
mission insignia, and no images of people under 18.

## Mission preview photos (`assets/misiones/`)

Downloaded from the NASA Image and Video Library (https://images.nasa.gov). NASA still images
are generally not subject to copyright in the United States (NASA Media Usage Guidelines:
https://www.nasa.gov/nasa-brand-center/images-and-media/). They must not be used to imply
NASA endorsement. Each photo was cropped around its subject and resized to 480x320; the
game pixelates it and reduces it to its 32-color palette when it is shown.
**To review (Piero):** chosen without logos, insignia or people.

| File | Title | NASA ID | Credit | Source |
|---|---|---|---|---|
| `easy_cubesat.png` | A CubeSat is ejected into Earth orbit from a small satellite orbital deployer | iss072e351959 | NASA | https://images.nasa.gov/details/iss072e351959 |
| `normal_leo.png` | A trio of CubeSats is deployed into Earth orbit outside of the International Space Station | iss074e0301636 | NASA | https://images.nasa.gov/details/iss074e0301636 |
| `hard_mro_marte.png` | Artist Concept of Mars Reconnaissance Orbiter | PIA04758 | NASA/JPL | https://images.nasa.gov/details/PIA04758 |
| `harder_perseverance.png` | Perseverance's Selfie with Ingenuity | PIA24542 | NASA/JPL-Caltech/MSSS | https://images.nasa.gov/details/PIA24542 |
| `insane_artemis1.png` | Flight Day 13: Earth, Array, and Moon (Artemis I) | art001e001822 | NASA | https://images.nasa.gov/details/art001e001822 |

## Fonts (`assets/fuentes/`)

Empty. The game uses its own 5x7 pixel font drawn in code (`interfaz/fuente_pixel.py`,
original work of the team). If a free pixel font (OFL/CC0) is added here as `*.ttf`,
the game uses it instead; list it in this file.

## Sprites

All sprites (avatar, rocket, lab, NPC, planets) are drawn in code in `interfaz/sprites.py`
(original work of the team).
