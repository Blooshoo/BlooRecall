# The glyph colormap

Priya Chandrasekhar, 2026-08-12. We needed review overlays where each carrier
stays visually distinct for a full session, without color being the only cue,
and without anyone hand-tuning hues per reel.

## The glyph colormap

Eight index slots. Each slot is a hue plus a shape mark drawn inside the box
outline, so carriers remain distinguishable in grayscale printouts and in
still frames pulled out of context.

### Perceptual uniformity

Adjacent index steps should look equally far apart to the eye, otherwise
reviewers unconsciously treat some transitions as bigger events than others.
24 observers ranked 40 pairs of adjacent steps; the pass condition was set at
"fewer than 4 of 24 can reliably order the pair". Steps 3 vs 4 passed at 21 of
24 unable to order them. Steps 7 to 8 was the only pair everyone ordered
correctly — the spacing there is visibly larger and gets a nudge in the next
revision of the map.

### Red-green safety

Under the dichromat simulation the eight hues keep 92% pairwise separability,
and the shape marks carry the remainder — worst pair is slots 2 and 6 at 88%
hue separation alone, but the marks differ, so combined separability is
complete. Verified on stills from six reels across both cages.

## Decision

The map ships in review overlays from 2026-08-12. Ledger charts migrate in
autumn with the roadmap. Slot assignments are frozen until the spacing
nudge is validated; do not reorder slots for aesthetics.
