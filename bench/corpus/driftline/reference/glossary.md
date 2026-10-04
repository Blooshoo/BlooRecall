# Team glossary — what our words mean here

Author: Rosa Lindqvist, from team interviews. Date: 2026-07-20. Purpose: new people keep asking what "the toboggan hack" is and the answers have drifted. This file is the canonical list. Add a term when a newcomer asks about it twice.

## The terms

- **Ember** — the fox, i.e., the player character's internal codename. Player-facing copy never uses it; the fox has no canon name in the game.
- **Quick Capture** — the always-running quick-save/replay-capture feature: the last 20 seconds of play, saved on a button hold, starred to keep. Not to be confused with any same-named feature of any other product; in this codebase it is always the replay thing (plans/quick-capture-v2.md, specs/quick-capture-architecture.md).
- **sparkline** — the ribbon of spark particles trailing Ember at high charge (specs/sparkline-trails.md). In this codebase it is *only* the particle trail. Someone will eventually assume it is a tiny chart; gently correct them and link this line.
- **toboggan hack** — the slope coast solver, so named by Tomás ("you sit on a toboggan and the hill decides"). The quadratic fit through the last three contact normals (specs/toboggan-hack.md). Saying "coast solver" in review comments is fine; "toboggan" is what people actually say.
- **trusted node** — a checkpoint, post-v2 policy: 60–75 s spacing, keeps 40% of entry speed on respawn (plans/checkpoint-policy-v2.md). "Checkpoint" still means the same thing; "trusted node" is the policy-v2 term of art and shows up in level files.
- **damper crate** — the high-friction crate tops that teach "landing costs speed" in the quarries. Hitting one is a choice; the seventh crate in the N8 gauntlet is the fair-punish one.
- **kiln vent** — the up-blast columns in Kiln Run, 140 u/s, the reason the descent is a fight.
- **rim snap** — the 12° cardinal-axis snap in stick handling (specs/thumbstick-deadzone.md). Testers say "it snapped" and mean this.
- **the flue** — the vertical cling-and-detach signature section, kiln nodes K-07–K-08. Capital-F Flue in level files, lowercase in speech.
- **the nightly sweep** — the retention pass over captures, run at the nightly build cut (specs/replay-format.md). "Swept" past tense = an unstarred capture that aged out.
- **the reference box** — the lab's 4-core x86 mini-PC, shelf 2. All gates close on it. "Does it hold on the box?" means the p95 frame line.
- **the toboggan ceiling** — nobody says this. Listed so nobody invents it: the 260 ms limit in specs/toboggan-hack.md has no nickname, and "the toboggan ceiling" was Tomás's rejected suggestion for it.
