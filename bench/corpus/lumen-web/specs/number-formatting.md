# Number formatting rules

Author: Cece Marlow, 2026-01-25. Status: current.

## Abbreviation

- At 10,000 and above: `10.0k`. At 1,000,000 and above: `1.0M`. At 1,000,000,000 and above: `1.2B`. Exactly one decimal, always.
- Under 10,000 renders with grouping separators and no decimals.

## Percent versus ratio

Percentages render with the % sign and no space (`42.1%`). Ratios keep their unit suffix: the cache hit rate renders as a percentage, but drift renders as `1840 ppm`, never as a converted percent — the ppm figure is what the drift checker logs, and translating it invited arguments.

## Currency

Currency renders as a unit suffix (`12.4k EUR`), never a leading glyph. The leading glyph collides with negative values at small sizes; we tried it in beta and reverted within a sprint.

## Small containers

Tiles narrower than 160 px drop grouping separators and keep the abbreviation. The tooltip always carries the full value with grouping.

## Alignment

All numeric columns and stat tiles use tabular numerals. Decimal points align within a tile row even when magnitudes differ; this cost us a custom font-feature setting and it was worth it.
