# The melting GPU week

Marco Deluca, written 2026-01-16, the week it happened. Postmortem minutes are
separate (meeting of 2026-01-19); this is the saga as it unfolded.

## Monday 2026-01-12

Exhaust probes read 47 °C in the farm room at midday. By the night shift the
dies were touching 91 °C and the clocks had sagged to 610 MHz — about half of
rated. Farm throughput fell 38% and stayed there. The night operator's log
entry reads, in full: "farm is very warm and very slow, will check tomorrow."

## Tuesday 2026-01-13

Ran the fans to 100%. Made it worse. Hot air was recirculating through row 2's
intake path instead of being exhausted, so we were cooling the room by warming
its supply. Backed the fans off and opened the case fronts to smell-test the
airflow. Row 2's filters were grey with felt dust.

## Wednesday 2026-01-14

Root cause split three ways, none sufficient alone:

1. The building heating loop overshot overnight — facilities confirmed their
   valve controller had been stuck since the weekend.
2. Row 2's filters had not been swapped since before the project kickoff;
   they were packed.
3. A poster of the cage layout (mine) was blocking renderlet-17's front
   intake. This contributed maybe 2 °C on one node and 100% of the comedy.

## Thursday 2026-01-15

Filters swapped, heating loop retuned, poster relocated to the corridor.
Dies back under 83 °C by the evening shift and clocks recovered to rated.

## Friday 2026-01-16

Fan curve v3 shipped: keyed to the exhaust probe rather than die temperature,
so it reacts to the room instead of chasing the die in circles. Throughput
recovered to 97% of baseline; the last 3% is the kindled pool drawing its 8
processes through the night roll, which we accept.

Priya named it the melting GPU week on Tuesday and the name went into the
ledger that afternoon, so the postmortem could point here instead of
re-telling it. Filter rotation is now quarterly, in Bram's hands, on the wall
calendar next to the drift audit.
