# Theme token catalog (wave 1)

Author: Cece Marlow, 2026-03-28. Status: current. Wave 2 lands with the 4.3 palette refresh.

## Rules

- Components never hardcode hex; they read tokens.
- Text tokens keep a 4.5:1 contrast floor; chart strokes hold 3:1.
- The accent family stays out of the catalog until the wave-2 refresh — the March accent regression taught us to migrate it last, behind the screenshot-diff gate.

## Wave-1 tokens

- `--lumen-axis-stroke` — chart axis lines, `#8A93A6` at rest, 1 px. Dims to 40% alpha on boards in focus mode.
- `--lumen-grid-line` — plot gridlines, `#E3E7EE`, 1 px, never dashed. Dashing reads as a threshold boundary, which gridlines are not.
- `--lumen-surface-raised` — slide-overs and popovers, `#FFFFFF` at 97% opacity with the standard shadow ramp.
- `--lumen-tooltip-bg` — `#1C2430`; tooltip text inverts to the light ramp.

## Migration notes

Wave 1 replaced 41 hardcoded hex values across 17 components (PR batch 2026-03-25 through 2026-03-27). The diff gate compares 14 reference boards on every palette-affecting PR; a red diff blocks merge with no overrides.
