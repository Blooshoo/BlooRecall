# Network segmentation — the long version

Status: living reference, restructured 2026-06-28 when the 2026
segmentation plan (`plans/network-segmentation-2026.md`) was accepted.
The quick card lives in `reference/vlan-table.md`. This document is the
reasoning: why the network is cut the way it is, what each cut buys, what
it costs, and which mistakes are baked in forever so nobody pays for them
twice. If a future change contradicts this document, the change wins —
but it has to say so here.

## 1. Where this came from

Until September 2025 the household network was one flat layer-2: one
subnet, one DHCP server, everything trusting everything. It worked the
way a single big drawer works — fine until you need to find something,
and catastrophic the moment something in the drawer catches fire. The
fire, such as it was, arrived in August 2025: a smart plug with a
firmware bug began shouting multicast at a rate that made the printers
disappear and the TV sessions hitch, and because everything shared one
broadcast domain, there was no way to make the shouting stop without
unplugging the plug. Diagnosis took an evening that should have taken
ten minutes, because nothing about the symptoms pointed at the culprit.

The second push was quieter: the guest visiting that month asked, innocently,
"so you're telling me your laptop and your toaster are on the same
network?" — and the honest answer was yes, along with the NAS holding
every photo the family has taken since 2004, the media box, and the
work-test VM that existed only to be disposable. Nothing bad happened to
any of it. The point was that nothing *would have stopped* anything bad
from happening, and the whole design rested on the assumption that
nothing ever tries.

The decision, made 2025-09-06 and executed in stages through that
autumn, was to cut the flat network into segments along the lines the
household already understood socially: family things, work things, toys
that phone home, things guests touch, and the machinery. The rest of
this document is the design that came out of that, hardened by two years
of incidents.

## 2. Goals and non-goals

The goals, in priority order, were settled in a notebook at the kitchen
table and have not changed since:

1. **A misbehaving toy cannot take down a working thing.** The smart
   plug class of problem — chatty, badly written, unpatchable — gets its
   own airlock. Whatever happens in the gadget segment stays audible on
   the monitoring box and invisible to everything else.
2. **The machinery has no internet debts.** Storage traffic never needs
   the internet; therefore storage never gets a default route; therefore
   a compromised anything on the storage segment has nowhere to phone
   home to. This is the single highest-value rule in the whole design
   and it costs nothing.
3. **Blast radius is knowable in advance.** When something breaks, the
   segment it breaks in should be nameable from the symptom in under a
   minute. The March 2026 loop incident validated this in the negative:
   the first hour was lost precisely because a layer-2 problem looked
   like six unrelated application problems across segments.
4. **Guests get internet and hospitality, not a tour.** The cyan segment
   exists so that handing someone the wireless passphrase is a generous
   act rather than a security decision.
5. **Changes are cheap to reason about.** Any rule on the firewall must
   be explainable in one sentence to a tired person at midnight. If it
   needs a second sentence, it needs a second look before it goes in.

The non-goals matter as much. This is not an enterprise; there is no
compliance regime, no auditor, nobody to perform for. There is
deliberately no per-device micro-segmentation (the gadget segment is one
segment, not forty), because the operational cost of forty firewall
identities in a household is paid in evenings, and evenings are the
scarcest resource in the entire design. There is no intrusion-detection
appliance, no web filtering proxy, no certificate authority for internal
services — each was written up, considered, and rejected in the
appendix, and re-proposing any of them requires new evidence, not new
enthusiasm.

One more non-goal worth stating because it shaped everything downstream:
the design does not attempt to protect the household from its own
administrator. The threat model is broken toys, bad weather, leaking
roofs, and binary blunders — not the person holding the vault key. Every
rule assumes the operator is trusted, because the operator is also the
person who has to debug the rule at midnight.

A fifth goal was added by the annual review in 2026 and is recorded here
so it does not get lost: **the design must survive a weekend without
me.** The vacation checklist codified this for jobs; the network side of
the same promise means every segment must degrade to a state a
house-sitter can understand from the board. In practice this killed two
clever ideas during the 2026 planning cycle — a per-segment bandwidth
fairness scheduler and a second resolver pair — both because their
failure modes required reading logs to understand, which the board
cannot do. The scoreboard for any proposal is now: can the household
board describe its failure in one tile? If not, simplify the proposal
until it can.

## 3. The hardware, honestly

The design had to work with what the rack actually contained, which is
the constraint every real network shares and no network diagram admits.

`gatehouse` is the edge router: a small fanless box running an open
router distribution, four NICs, bought in 2022 and treated since as
load-bearing infrastructure. It terminates the provider uplink, runs the
firewall and the inter-segment rules, serves DHCP for most segments, and
has survived three provider changes and one lightning-adjacent surge
(2024, the surge bar took the hit, the router kept its config, and the
config backup discipline that saved it is described in section 9).

`harbor` is the managed 8-port switch in the rack, installed 2026-06-14
per `runbooks/switch-stack-replacement.md`. Its predecessor was an
unmanaged 5-port unit under the stairs, and the gap between the two is
the difference between the March incident taking an evening and the next
one taking ten minutes: managed ports can testify. Harbor carries the
storage and media segments' interchange, which took a measurable latency
halving when it went in — traffic between the TV and the NAS no longer
hairpins through the router.

Wireless is two access points: the main unit in the hallway ceiling and
a mesh node upstairs, both consumer-grade, both on the edge of their
useful lives and neither worth replacing until one dies (the evaluation
was done in 2025; the notes concluded that a replacement pair would buy
spectrum hygiene but no new capability, and the channel pinning fix in the
February 2026 wireless notes bought back most of the pain for free).
Each AP broadcasts two SSIDs; the mapping to segments is in section 6.

Cabling is the honest weak point. The house was wired for ethernet in
two eras — the 2011 runs (office, living room wall plate) and the 2024
runs (rack to cabinet path, pulled during the first relocation attempt's
reversal). One run, the upstairs wall plate, rides a PoE injector that
browns out above 30 °C and has been blamed for two separate mysteries
before being properly convicted. Every wall plate run is labeled at both
ends as of the June migration, and the labeling convention is in
`reference/naming-conventions.md`.

The basement rack itself is a 12-unit open frame: router, switch, NAS,
media box, resolver, monitoring box, the UPS brick at the bottom, and
the evaporative intake rig that runs in summer
(`notes/basement-swamp-cooler-hack.md`). Everything in the frame is on
the same battery and the same 90-second shutdown chain, which the
segmentation design treats as a hard floor: no segment's requirements
may outlive the brick's runtime.

Two boxes in the frame deserve their own mention because the design
depends on them being boring. `dill`, the resolver, is a 2016-vintage
mini PC that idles at four watts and has one job; its hardware budget
was twelve euros of secondhand memory and an afternoon, and it has been
restarted exactly twice on purpose since 2024. The lesson recorded here
is that infrastructure should be chosen for how rarely it needs
attention, not how impressive it is — the flashiest box in the rack is
the media server, and the media server is also the box whose relocation
was reversed a year later. `weathervane`, the monitoring box, is
similarly humble and similarly deliberate: it holds the config repos,
scrapes everything, draws the board, and has no other responsibilities,
because a monitoring box that also does work has an incentive to lie
about the workload it is monitoring. Both boxes are on the UPS chain,
both are backed up in the nightly generation, and both can be rebuilt
from their repos onto any spare hardware in under an hour, a property
that was tested rather than assumed in the August 2026 drill.

## 4. Addressing and name service

Every segment is a /24. This is wasteful and deliberate: a /24 per
segment means the subnet octet is the VLAN number without exception
(VLAN 20 is 192.168.20.0/24), which means an address tells you its
segment at a glance, which means every log line in the household is
self-describing. The one exception is the lab segment on 10.20.70.0/24 —
outside the 192.168 range on purpose, so that a lab route leaking into a
client's table is instantly recognizable as foreign material rather
than quietly plausible.

Within each segment, the lower addresses are infrastructure and the
upper range is DHCP. The pattern is stable: infrastructure lives at .1
through .60 (gateway .1, resolver .53, monitoring .60), services take
.10 through .40 by assignment, and DHCP gets .100 through .199. The .200+
range is deliberately unused everywhere — it is the scratch space where
a temporary device goes when someone says "just give it an address for
tonight", and having a consistent nowhere for those keeps them from
colonizing the meaningful ranges.

Static assignments are made at the router for infrastructure and by
contract for services: `bramble` holds 192.168.30.10 and 192.168.10.10,
`marquee` holds 192.168.40.20, and these are written in the VLAN table
and in each machine's own notes rather than in one master list, because
a master list that is not where you already are at midnight is a list
that is wrong.

Name service is `dill` (192.168.10.53), the caching resolver described
in `runbooks/dns-caching-layer.md`. It answers every segment — resolver
access is deliberately the one thing every segment shares, because one
resolver with good logs beats three resolvers with three drifting
configs, and because local names are how the household's own services
stay addressable without anyone maintaining /etc/hosts files. The
resolver's cache behavior (including the stale-serving window that
absorbs the provider's evening brownouts) is documented in its runbook
and is the reason resolver restarts are scheduled like maintenance on a
bridge rather than rebooted casually.

The monitoring box (`weathervane`, 192.168.10.60) scrapes all segments
and is likewise reachable everywhere — read access to everything is the
monitoring segment's whole job, and the firewall's alias for it is
named `observer` so the rules read like sentences.

Lease discipline is the last piece of the addressing story, and it is
smaller than its incident count suggests. The router serves DHCP with a
48-hour lease everywhere except cyan, where the pool is short and the
renewal rhythm is documented in the cyan notes. Static infrastructure
never overlaps the DHCP range by construction — the .100–.199 cut —
but twice now a "temporary" device parked at .200+ has been discovered
weeks later serving some forgotten purpose, and the standing rule from
those discoveries is that anything at .200 or above gets re-found every
quarterly review or gets its lease expired on the spot. The quarterly
walk takes four minutes; the alternative is a mystery device with a
year-old lease, which happened in March 2025 and took an evening
because the mystery device turned out to be the old media box, still
plugged in behind the sofa, still answering SSH, holding an address it
had been promised in a different segmentation era.

## 5. The firewall's one philosophy

The rule base on `gatehouse` follows a single principle: **default deny
between segments, explicit allow by service, and every allow has a
comment naming why it exists.** There is no third category. Rules are
grouped by source segment, ordered by frequency of use, and the whole
base fits on roughly two hundred lines including comments, which is
small enough that it gets read in full before every change — a discipline
that has caught three would-be mistakes in two years, each of which
would have been invisible in a rule base of a thousand lines.

The allows cluster into a handful of shapes worth naming, because named
shapes are cheap to reason about. **Witness allows** let the monitoring
box see everything (scrape-only, and the segments cannot initiate back).
**Service allows** punch narrow holes for the few things that must
cross: sessions reading from storage, prints from trusted and cyan, the
board from cyan. **Airlock allows** let the gadget segment and the lab
reach the internet and the internal broker endpoint and nothing else —
the broker being the one internal service the toys legitimately need,
running on a small box in the gadget segment so that its own failure
mode stays inside the airlock with them. **Hospitality allows** are the
cyan trio (internet, board, printer) and they are the only rules in the
base marked as explicitly temporary-in-spirit: they exist for comfort
and can be revoked on a bad day without a second thought.

Everything else — inter-segment traffic of any protocol — hits the deny
and is counted. The deny counters are not decorative: they are on the
board's network tile, and the pattern of denies is the fastest diagnostic
in the household for "something is misconfigured" versus "something is
missing". A deny spike from the gadget segment at 03:00 is a toy phoning
a new endpoint, noted and forgotten; a deny spike from trusted toward
storage is someone's mount pointing at the wrong address, and worth a
look the same day.

Logging goes to `weathervane` and is kept for 90 days, which has proven
to be the right window: long enough to correlate with the monthly scrub
and the quarterly drills, short enough that the disk does not notice.
The logs that answered the March incident and the April printer-writable
mistake both came from this retention window.

Rule ordering deserves its paragraph because it is the part of firewall
craft that documentation always skips. The base reads top-down: witness
allows first (they match constantly and must never be shadowed), then
service allows grouped by source segment, then the airlock and
hospitality blocks, then the deny with its counters. Each rule carries
a comment in the same shape — *what, for whom, since when* — and a rule
whose comment cannot name a date is treated as suspect during the
quarterly review, because undated rules are how rule bases grow
archaeology layers. Aliases are named for roles, not addresses:
`observer`, `printers`, `board`, `the-toys`. The test for an alias name
is whether a rule containing it can be read aloud to the household
without embarrassment; `alias_17_final_new` fails that test, and every
rule that ever carried such a name was hiding the fact that nobody
remembered why it existed. The 2026 alias cleanup removed nine such
rules, and nothing in the household noticed, which is the quietest
possible proof they were dead weight.

What the firewall deliberately does not do: deep packet inspection,
content filtering, per-device identity, or any form of the word
"parental". Those were each considered and rejected in the appendix
with reasons, and the one-sentence version is that every one of them
converts a midnight-debuggable rule base into an appliance whose
behavior has to be believed rather than read.

## 6. Wireless mapping

Two SSIDs per access point, four SSIDs total, and the mapping to
segments is fixed and uninteresting, which is the goal.

**Amber** is the trusted wireless, tagging VLAN 20. Family laptops,
handsets, tablets. Full internal access, the works. Passphrase rotates
yearly, lives in the vault under `homelab/core`.

**Cyan** is the visitors' wireless, tagging VLAN 60. Passphrase rotates
with the seasons and lives in the vault under `homelab/cyan`; the
fridge-magnet problem this creates is documented in the cyan notes
(`notes/guest-network-quirks.md`) and accepted as the cost of rotation.

The gadget SSID (tagging VLAN 50 since the 2026 segmentation plan) is
hidden, not for security — SSID hiding is a vibration, not a wall — but
to keep the toys from being the first thing a visiting teenager tries to
join. Its credentials live in the vault and in the note on the inside of
the rack door, which is where they are needed when a new plug cannot
pair.

Band behavior: 2.4 GHz exists for the toys and the far corners; 5 GHz is
preferred for everything else and both APs steer by legacy-rate
exclusion rather than advertising tricks (the February 2026 wireless
notes record why: the steering knobs that ship with consumer APs made
the problem worse by negotiation flapping, and simply disabling old
modulations plus pinning channels did the actual work). Roaming between
the hallway and upstairs units is adequate, not excellent; the one
persistent dead spot behind the bookcases in the front room is a known
and accepted tax of the wall's construction, revisited and re-accepted
in every annual review since 2024.

One more wireless note belongs here because it interacts with the
segmentation directly: the two APs are managed as a pair, never
individually. Channel plans, transmit power, and the legacy-rate
exclusion are set identically on both, from one note card taped inside
the rack door, because the February 2026 congestion incident
(`notes/wireless-clients-roaming.md`) was caused by exactly the kind of
per-unit drift this rule prevents — one unit auto-negotiated its way
onto the other's channel and the evening band quietly fell over. When
the eventual AP replacement happens, both units go at once or the
config-drift rule gets a new paragraph; mixing generations of consumer
APs in one roaming group was evaluated in 2025 and produced a client
that ping-ponged between them on every handoff, which is the empirical
answer to "can we replace just one".

## 7. The table itself

This is the load-bearing center of the whole document: the segment table
as it stands since the 2026 plan. The quick-card version lives in
`reference/vlan-table.md` and must never drift from this section — when
they disagree, the live config on `gatehouse` is the referee and one of
the two documents gets fixed the same day.

| VLAN | Name | Subnet | Gateway | Purpose | Internet | Key allows |
|---|---|---|---|---|---|---|
| 10 | mgmt | 192.168.10.0/24 | 192.168.10.1 | Management interfaces; `gatehouse`, `dill` (.53), `weathervane` (.60), `harbor` (.7) | yes | Trusted reaches mgmt for admin panels |
| 20 | trusted | 192.168.20.0/24 | 192.168.20.1 | Family laptops and handsets on amber | yes | Full internal read; storage via services |
| 30 | storage | 192.168.30.0/24 | none, on purpose | `bramble` (.10), cold dock | **no default route** | Witness only, plus service write-backs from bramble itself |
| 40 | media | 192.168.40.0/24 | 192.168.40.1 | `marquee` (.20), TV, dongle, projector, tuner PC | yes | Read from storage; nothing writes to trusted |
| 50 | gadgets | 192.168.50.0/24 | 192.168.50.1 | Smart plugs, displays, apps-first devices | yes, airlocked | Broker endpoint in-segment only |
| 60 | cyan | 192.168.60.0/24 | 192.168.60.1 | Visitors | yes, capped 20/5 | Board + printer only |
| 70 | lab | 10.20.70.0/24 | 10.20.70.1 | Test resolver, disposable VM host | yes | Default-deny to house; one allow per resident, each logged in the plan |
| 99 | transfer | 192.168.99.0/24 | 192.168.99.1 | Uplink/transfer lane router-to-cabinet | n/a | No clients, no DHCP, ever |

Three rows deserve their paragraph. **Storage without a default route**
is the keystone: nothing on VLAN 30 can initiate anything toward the
internet, which converts the most valuable segment into the least
useful target. **The lab segment's allows are a budget**: each one is a
line in the segmentation plan with a date, and the quarterly review
walks the list — an allow that cannot justify itself gets removed, and
in the four quarters so far the list has only ever shrunk. **The
transfer lane** exists because the router-cabinet link carried tagged
traffic for all segments over one trunk, and giving that physical hop
its own unnumbered-feeling lane made the March-style loops easier to
localize: a storm on the lane is a cable problem, not a six-segment
mystery.

## 8. Services and what may talk to what

The household runs five services that matter, and their reachability is
the practical output of the whole design.

`bramble` (the NAS) serves files over the storage segment and answers
management on the management segment. Clients never mount the storage
segment directly — sessions, shares, and syncs go through the services
`bramble` itself publishes, which keeps the write path auditable and is
why the media segment is read-only toward storage at the network layer.
The one exception is the cold dock, which joins storage when plugged in
and is otherwise the most secure device in the house: unplugged.

`marquee` (the media box) lives on the media segment, reads from
storage, serves the television, the dongle, and the projector, and
talks to nothing else. Its relocation history (2025 into the cabinet,
2026 back to the rack) is recorded in the two relocation plans and is
worth reading as a case study in a plan being wrong cheaply.

`dill` (the resolver) answers everyone, as covered in section 4.

`weathervane` (monitoring) scrapes everyone, alerts onto the household
board, and hosts the small config repos (resolver config, cron card,
firewall base) that make the "no hand edits on the box" discipline
possible. It is the only machine with credentials to every segment, and
it is on the battery chain with a documented shutdown order.

The print server is the humblest and the most-asked-about: reachable
from trusted and cyan only, because those are the only segments with
hands attached. The April 2026 incident where the printer briefly
became reachable from the visitors' segment via a copy-pasted rule block
is the canonical example of why the rules now live in named aliases —
the fix was not closing the hole, it was making the rule base read like
prose so the hole could not silently reopen.

## 9. Operations: how changes actually happen

Changes to the network follow the same loop as everything else in these
notes, and the loop is short: propose in a plan document, wait out the
household veto period (48 hours, a real institution after the living
room cable incident of 2024), execute in the documented rollout order,
verify with the standard checks, and update the two documents that must
not drift (`reference/vlan-table.md` and this document). The 2026
segmentation plan is the most recent full-cycle example and shows the
loop working, including the one sulking smart plug that was budgeted as
an expected cost.

Router config is backed before every change: export from `gatehouse`
to `weathervane`'s backup store, timestamped. The discipline dates from
the 2024 surge, after which the router came up with a two-week-old
config and the household discovered which rules had been added by hand
in the interim — all three, it turned out, and all three got comments
and a place in the base afterwards. The export ritual takes two minutes
and has never once been regretted.

Firewall edits are made in the config repo on `weathervane`, reviewed
against the two-hundred-line readability budget, and deployed by script.
The script is trivial; the discipline is the point. Hand edits on the
router itself are permitted in an active incident and must be back-
ported to the repo within 24 hours — the printer incident's copy-paste
block survived precisely as long as it did because it predates this
rule.

The quarterly review walks four lists: the lab segment's allow budget,
the firmware inventory, the threshold sheets, and the deny-counter
highlights from the board. It is scheduled like the scrub (a recurring
entry on the job card) and takes about an hour with the notebook. The
review has killed more rules than it has written, which is the correct
direction of travel for a household network's complexity.

## 10. Testing

Segmentation that is never tested from the wrong side is decoration, so
the checks are concrete and cheap. From a gadget: printers unreachable,
internet reachable, broker reachable. From cyan: board and printer
reachable, nothing else answers, cap holds under a speed test (the cap
is the one rule guests can actually feel, and it is tested with a real
speed test from a real guest device once a quarter, with permission and
often with commentary). From the lab: default-deny confirmed by trying
to reach `bramble` and watching the deny counter increment instead of
the connection succeed. From trusted: everything works, which is the
test most likely to be skipped and the one whose failure is most
expensive, so it goes first.

The checks are written as a laminated card, not as a script, on
purpose. A script that runs the checks unattended would test the
network as it existed when the script was written; the card forces a
human to look at each result, and the looking has caught two things the
checks themselves were not asking: the printer's IPv6 answers leaking
past the alias rules in July 2026 (the card said "printer unreachable",
nobody had said anything about v6, and the board's deny counters are
v4-only), and a lab VM that had quietly acquired a second allow rule
during a late-night experiment. Both are fixed; both are why the card
gets a fresh read every quarter rather than being trusted from memory.

The bigger test is the deliberate fault drill, done yearly alongside
the restore drill: pull a link on purpose (the cabinet trunk, in
September 2026's drill) and time how long the board takes to say which
segment died. The target is under a minute of human confusion; the
September drill took forty seconds and is the current record to beat.
The drill exists because the March incident's real cost was not the
downtime, it was the hour of looking in the wrong places, and hour-long
searches are a trained behavior that only drills untrain.

## 11. Appendix: decisions recorded so they stay made

**Rejected: per-device micro-segmentation for the gadgets.** Forty
identities, forty rules, zero additional safety in the actual threat
model. The airlock shape gives up nothing that matters and costs one
segment instead of forty. Revisited only if a single toy becomes a
known problem, in which case the toy gets retired, not a new segment.

**Rejected: an intrusion-detection appliance.** The alert volume for a
household of this size is noise with a power cord. The monitoring box
already answers the actual question ("what changed, and is it wrong?")
with deny counters and scrape coverage. The IDS evaluation from
2025-10 is summarized in one line in the notebook: "it found the smart
plug problem four days after the board did."

**Rejected: internal certificate authority.** Everything internal that
needs a lock icon gets it from a public ACME issuer with DNS
validation; the household runs no CA because a CA is a root of trust
that must never be lost, and the household's actual root of trust is
the vault, which already holds enough.

**Rejected: renumbering the segments "properly" with bigger subnets and
a cleaner plan.** The current scheme is legible at a glance, deployed,
documented twice, and understood by everyone who touches it. The
cleanup would cost a weekend and buy a cleaner diagram. Both are real
currencies; the weekend is scarcer.

**Kept, deliberately: the 90-second shutdown chain outranking every
segmentation concern.** If a proposed rule makes the shutdown chain
slower or the battery budget bigger, it is declined regardless of its
other merits. The chain is the one mechanism in the household that has
worked perfectly, every time, including the March incident, and it
outranks theory.

**Open, revisited at every annual review: a segment for visiting
consoles.** Deferred because cyan covers the need with one rule and the
decade scheme has no natural home for a one-device segment. The day a
guest console needs more than internet-plus-board, the 70s decade has a
neighbor waiting.
