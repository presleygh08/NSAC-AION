# Validation: every mission can be won, but not by guessing

Reproduce with:
```bash
python3 nucleo.py                 # self-tests of the game core
python3 nucleo.py --validar-fino  # fine search over budget splits for the 5 missions
python3 revisar_textos.py         # test mode: no text overflows its box, in English and Spanish
```

## Method
1. Compute the cost of reaching exactly the **minimum** of each resource (with the rocket equation for propulsion and solar physics for power).
2. Split the remaining budget among the resources in small steps, trying **every** combination (including leaving money unspent, because saving money earns a bonus).
3. Score each split with the game's own rules and replay the best one with the real game functions to confirm it launches, completes the mission and earns 5 stars.

## Results (v3 data)
| Mission | Resources | Budget (M USD) | Cost of all minimums | Cost of all optimums | Splits tested | Best score | 5-star splits* |
|---|---|---|---|---|---|---|---|
| Easy – CubeSat | 2 | 18 | 10.99 | 16.77 | 20,301 | 100 | 49.0 % |
| Normal – SmallSat | 3 | 71 | 43.98 | 67.06 | 176,851 | 100 | 32.0 % |
| Hard – Mars Orbiter | 4 | 155 | 105.07 | 145.75 | 635,376 | 100 | 21.3 % |
| Harder – Mars Rover | 5 | 240 | 175.02 | 225.76 | 324,632 | 99 | 12.7 % |
| Insane – Moon Orbiter | 6 | 305 | 219.70 | 286.11 | 230,230 | 97 | 11.0 % |

\*Share of the splits that already complete the mission and also reach 5 stars.

## Guessing does not work
With a coarse "by eye" search in 10 % budget steps, most splits fail: only 15 % complete Easy, 0.1 % complete Hard
and **none** complete Insane. Players must use the clues and reason about each resource, which is the learning goal.
