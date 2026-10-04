# Wall cling

Author: Tomás Iriarte. Date: 2025-11-19. Status: shipped in 0.10.0. Level guidance by Dev Okonkwo.

## Entry

Cling starts when all of these hold:

1. Ember is airborne.
2. Approach velocity along the wall normal is at least **240 u/s** — you have to mean it.
3. The stick is deflected toward the wall.
4. The surface is between 70° and 110° from horizontal (a true wall, not a steep slope; slopes belong to the ground rules in specs/momentum-model.md).

Entering costs nothing and grants a fresh window. Clinging to the *same* wall again within 400 ms does not refresh the window — that is the anti-abuse rule, so a single surface can't be climbed forever.

## The cling window

A fresh cling lasts at most **900 ms**. The first 500 ms are "strong": Ember holds height, pose shows grip. After 500 ms the window decays and Ember picks up a downward creep of **60 u/s²** that accumulates for the remaining 400 ms. The decay is there so the end of a cling is readable — Ember visibly starts to lose the wall instead of popping off.

## Detach

Pressing the detach button during the window applies an impulse of **520 u/s at 112° from the wall normal** — up and away, roughly over the player's shoulder. Detach ends the window immediately, gets no coyote grace (it is a deliberate act, per specs/coyote-time.md v1 and v2), and consumes the anti-abuse lock for that wall.

Letting the window expire (no input) releases Ember straight down along the wall with the accumulated creep velocity. This is the intended "bail out" and is deliberately weaker than detach.

## Normal realignment

On entry the wall normal is realigned within a ±18° cone: if the geometric normal and the velocity-implied normal disagree, we take the velocity-implied one clamped to that cone. Without this, off-angle entries on the quarry's rough beams felt like hitting a hidden trap.

## Level design guidance (Dev)

- Cling walls want an approach that naturally builds 300+ u/s — put them at the bottom of dives, not on flat runs.
- Two clings in sequence need different heights or the second one is free momentum with no read.
- The kiln's tiled shafts read as "cling allowed" because of the tile pattern; do not put clingable surfaces on rough rock, it reads as non-stick to testers.
