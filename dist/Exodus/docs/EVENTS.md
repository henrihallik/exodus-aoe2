# Event contract

All gameplay state uses synchronized XS globals, arrays and game time. No local-player checks, audio return values, real-time clocks, external files, network calls, or randomly rolled disasters influence the simulation.

## Sea cycle

| First cycle | State | Crossing / hazard |
| --- | --- | --- |
| 00:00–10:59 | Flooded | Sea road passable but hazardous (6 HP/s). Coast roads safe. |
| 11:00–11:59 | East wind | Public 80-second countdown to the safe crossing; hazard continues. Evening light; fire pillars. |
| 12:00–12:19 | Parting | Curtains withdraw. Damage continues until the SAFE signal at 12:20. |
| 12:20–16:29 | Open | Safe crossing; no flood damage or physical barriers. |
| 16:30–17:59 | Warning | Sea road still fully open. Public 90-second evacuation warning, then reminders at 17:30 and 17:50. |
| 18:00–18:39 | Return | Flood damage starts; curtains close over 40 seconds. No physical barriers spawn. |
| 18:40–28:59 | Flooded | Hazard remains active through the next parting, until SAFE at 30:20. |

From the first east wind onward, the cycle length is 1,080 game seconds. The crossing is damage-free for 340 seconds per cycle, but physically passable throughout. Tough units may survive a hazardous crossing. The hazard occupies x=55…64, y=44…75; XS tests tile-space coordinates against half-open bounds `[55,65) × [44,76)`.

Damage: six current HP per one-second rule execution, capped at zero. It ignores armor and does not award an opponent a scripted kill bounty. This is environmental damage, not a permanent maximum-HP/stat change. A duplicate rule execution within the same game second is ignored. The script does not apply a huge retrospective damage burst after a skipped tick. Death animation, monk relic drops, garrison behavior, and native combat-stat bookkeeping require engine verification.

All documented normal mobile land classes are queried explicitly, including relic-carrying monks, packed/unpacked siege, mounted ranged units, kings and livestock. Naval classes are never queried for damage. Garrisoned units are skipped, so transport passengers should be safe while aboard. Buildings, Gaia, projectiles and resources are excluded. No ordinary trainable unit definition is changed.

There are no sea barriers. Terrain remains shallow and the curtains are nonblocking. Verified HP-write failures still suspend events and declare the generation invalid; removing rocks is no longer a runtime dependency. Native damage and balance tests remain required.

## Burning bushes and guiding pillars

Bush anchors: tile (46,35) and its rotational counterpart (73,84). Either player's ungarrisoned land unit within radius five can ignite either bush. Each fires once, leaves its original plant intact, and adds native bonfire/smoke scenery. Discovery is not ownership; no resources or combat bonuses are awarded.

Two persistent cloud emitters sit at fixed, mirrored bank-side positions. At the wind, parting, warning and return phases, native fire accompanies them. The normal phase uses cloud only. Color moods blend over 10–20 seconds; the script never switches to the extreme-darkness mood or uses rapid light flashes. Native smoke lifetime/height and animation must be inspected in DE.

## Manna gardens

At 07:00 and 25:00, create three native forage bushes per bank, each reduced to 75 remaining food. Locations are fixed, mirrored, exposed and documented in `docs/layout.json`; the second wave uses a separate row. Each bank gets an opportunity to gather 225 food per wave, not a direct stockpile credit. An opponent can raid or gather there normally. Native civilization gather bonuses continue to apply.

All six bushes are staged in one call. If any placement fails, every successful new bush from that attempt is removed before the next simulation tick, leaving existing units/resources untouched. Retry at most 30 times; then cancel the wave for both banks. A player can deliberately obstruct a garden to deny both sides a wave. That denial is public, symmetric and a balance-test item, not a secret one-sided compensation.

## Jericho

There are two original 9×9 Gaia stone-wall enclosures, 32 wall pieces each. Each already contains four gold tiles and one relic. They can be attacked before the event using ordinary game mechanics. Seven original horn cues fire once each from 24:00 to 24:06. At 24:07, only stored references to surviving original Gaia wall units are removed. A converted wall or a new wall built by a player is protected by the ownership check.

The event reveals access, not previously hidden resource information: scouting the enclosures is allowed from the start. It does not kill defenders or spawn a free army. Both coast roads have paths around the sealed enclosures.

## Performance and failure handling

The simulation runs at a one-second interval. Arrays are reused: ten fixed state/effect arrays and two query arrays. Smoke uses a 48-slot ring buffer with expiry; curtains reuse 12 references; pillar fire uses two references. Two references track permanent bush fires. No trail grows indefinitely and no rule continuously spawns player units.

In 0.2.0, curtain motion uses smoothstep easing with unchanged endpoints and opening/closing times. Cloud height is reduced, and one pair of small transition mist puffs appears every six seconds outside the walkable strip, using the same bounded pool. Missing tracked Gaia fires are recreated only if their original shrub remains; player-owned scenery is never moved or removed. No resource animal migrates and no additional food or objective is introduced.

After a gap of more than two game seconds, the current countdown is recomputed from the absolute schedule, without replaying same-phase events or applying catch-up damage. A late warning uses only its most urgent remaining reminder. This is gap/re-entry logic tested in mocks, not a claim that native save/load has been verified.

Audio is scheduled separately from world effects. One highest-priority global cue is selected per tick, safety first. Quiet paired two-second ambience is rate-limited to one pair per 30 seconds, excluded during transitions/warnings and near known important cues. No local visibility, sound success or camera state controls simulation. See `AUDIO.md` for the finite-clip limits.

Runtime initialization waits for generation, validates 120×120 size, two players plus Gaia, 64 walls (or their setup markers) and two shrubs; obsolete sea rocks cause an explicit replace-both-scripts warning. It retries for ten ticks and fails visibly if the contract is not met. The opening message is part of the engine smoke test.
