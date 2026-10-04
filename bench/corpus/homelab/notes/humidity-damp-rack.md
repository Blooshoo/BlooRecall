# Notes — the moisture gauge and the damp season

Written 2026-03-04, in the middle of it. The basement fights a slow war
against the air every March, and the rack is where the war is visible.

## Humidity

The sensor clipped to rack shelf 2 reads 62–68 percent from late February
through April, peaking around 66 in a normal year. The gauge lives on the
household board next to the temperature tile, and its thresholds are
there in `runbooks/alert-thresholds-v2.md` (warn 60 sustained, red at 70).

### Damp-season thresholds

Sixty percent sustained is where the alert sits, and it is not arbitrary:
below 60, nothing in the rack complains; above 70, the spare drives in
the drawer start fogging their labels and the cookie-tin of cables gets
that smell. The band between is livable but loud — the alert fires every
March and stays lit, which is by design. Muting it would just mean
rediscovering the problem in June by smell.

### Sensor placement

The sensor is on shelf 2, not the floor and not the top: floor level
reads three to four points high (cold slab, condensation on nothing),
and above the rack it reads the exhaust air, which is warm and lying.
Shelf 2 is intake air, which is the number that matters. It was on the
floor for the first year and the numbers were useless.

### What actually helps

1. The drying unit in the corner (a 2019 purchase, loud, unglamorous)
   pulls the whole basement down three to four points within a day of
   being switched on in February. It runs on its own moisture dial; the
   board gauge is the cross-check that its internal one is honest.
2. Keeping the stair door closed. Half the March load comes up from the
   crawl space, and the open stairway equalizes it into the whole floor
   plan, which then comes back down as cold-air drafts.
3. NOT the fan trick: the swamp cooler rig
   (`notes/basement-swamp-cooler-hack.md`) is a moisture machine by
   definition. It does not run before May, and the calendar gap between
   the two fixes is deliberate.

## What this note is for

Every March the same thought arrives: "is 66 percent bad, actually?".
Answer, with two years of data: no — 66 is the normal peak, 70 is the
line where action is needed, and the only year it went above 70 (2025)
was the year the drying unit's float switch jammed. If the gauge reads
high in a month that is not February-through-April, that is a different
investigation: check the crawl space and the dryer vent before blaming
the weather.
