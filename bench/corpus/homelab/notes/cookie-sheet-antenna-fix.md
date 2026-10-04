# The cookie-sheet antenna fix

Written 2025-10-05. Nickname is literal: there is a cookie sheet screwed
to a rafter in the attic, and it is load-bearing for television.

## The problem

The tuner PC (`marquee`'s sibling duty) pulls broadcast channels via a
UHF antenna in the attic. The antenna came with a flimsy folded-dipole
reflector that had warped in the 2024 heat wave, and reception of the
harder UHF channels degraded to a pixelated slideshow every time the
wind picked up. Buying a proper antenna was obviously the correct move,
and instead what happened is this.

## What was done

- The warped reflector was unbolted and replaced with a standard aluminum
  cookie sheet (33 × 40 cm), screwed to the rafter behind the antenna
  elements at the same standoff distance (9 cm, measured with a cork).
- The antenna's mast clamp was re-torqued and given a second hose clamp,
  because the wind event that warped the reflector had also been slowly
  rotating the whole assembly toward "mostly wall".
- The feed line got a drip loop, which it had been missing since install,
  and which is probably why the connector ends had green on them.

## Results

- The four marginal UHF channels went from "watchable with patience" to
  solid, and have stayed solid through two wind seasons.
- Signal meter readings improved 20–35 percent on the marginal channels.
- The good channels got slightly worse for one evening, which turned out
  to be the assembly being rotated 15 degrees during mounting; re-aimed
  with a helper watching the meter, and a marker line on the rafter now
  records "aligned 2025-10-05".

## Honest status

The proper antenna is on no shopping list, because the cookie sheet has
outperformed the part it replaced and there is no failure mode on the
horizon. If it ever degrades, the first suspects, in order: the drip
loop connection (green residue returns), the second hose clamp (wind
rotation), and only then the sheet itself. aluminum + rafters + dry attic
has, so far, no rust to report.

Related: this is why the 21:00 recordings job and the transcode preset
exist at all — see `runbooks/media-playback-hitches.md` and
`runbooks/media-transcode-preset.md` for how the signals get from this
attic to the main telly.
