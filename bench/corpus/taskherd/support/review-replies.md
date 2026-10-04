# Review reply examples (reference set)

- Owner: Tomas Lindgren
- Date: 2026-06-01
- Purpose: worked examples for the store-review response program (`plans/store-review-response.md`). These are the tone reference; the program doc is the rules reference.

## Example 1 — the battery complaint (2 stars)

Review (2026-05-28): "Battery died by 3pm since the last update. Uninstalling until this is fixed."

Reply we shipped: "That is not the trade we want you making. The 2.8 train had a regression in background sync scheduling that a subset of devices hit; it was fixed in the update two weeks later. If the device still runs hot on the latest version, write to support and we will pull the battery trace from your account with your permission — the fix should not cost you an afternoon of charge."

Why it works: names the real regression, gives the ship date, offers a concrete next step, no defensiveness. The reviewer updated to 4 stars on 2026-06-19, which is the single best outcome the program has produced.

## Example 2 — the sync worry (3 stars)

Review (2026-06-04): "Love the shared lists but twice now my partner's edits showed up hours late on my phone."

Reply we shipped: "Late-arriving edits usually mean the local queue was draining in the background — oldest changes first, so a big backlog can reorder itself over a few minutes. If it is happening on a stable connection with a small backlog, that is a bug and support can read the sync trace. The reconciliation page in our docs explains the whole path."

Why it works: explains the normal case honestly (it is usually not a bug), and gives the abnormal case a route. No "works on our machine."

## Example 3 — the advocacy reply (5 stars)

Review (2026-06-10): "This app runs our household. The whole family is finally on the same page."

Reply we shipped: "This made the whole team's week — thank you. If you have not tried it yet: swipe down anywhere to add a task in about two seconds. Household chores are what that gesture was built for."

Why it works: pure thanks plus one concrete tip, no asks. The program's rule: advocacy replies never request ratings or shares; the measured effect of asks was negative and they are banned.

## Anti-examples (what we do not send)

- "Thanks for the feedback!" with nothing else — the empty calorie reply, banned by the program rules.
- Any reply that argues with the reviewer's experience, even when the trace says the device was fine. State the facts once, offer the route, stop.
- Any reply promising a version or date. "Next update" is the ceiling, and only if the fix has already merged.
