# Required engine checks before submission

The local checks do not replace any item below. Use side-swapped games and preserve the exact game build, map seed, scripts, optional audio version and recorded game.

## First generation

- Generate Tiny / two players / standard dataset. Confirm the XS opening message and timer; no failure messages.
- Inspect all terrain blending, shore shape, vegetation and 64 wall pieces. Compare the map with the authored atlas and external Age of RMS preview, allowing for each preview's documented limitations.
- Confirm both TCs, eight sheep, two boar, four deer, six berries, seven main gold, four expansion gold, five plus four stone, and five stragglers per player.
- Verify Chinese, Mayan, Lithuanian, Persian and meso starts against native expectations, plus an ordinary civilization. The script must not normalize away native civilization starting behavior.
- Confirm that every resource cluster is reachable from its outside and that lumber camps fit by the near woodlines. Check resource placement in at least 20 native seeds.
- Walk the western and eastern coastal roads before any event. Measure narrowest formation passage around each ruin and check whether native decorative mountain footprints obstruct it.
- Verify that no building (including a dock) can occupy the ten-tile sea road. If standard shallows permit a relevant exploit, adjust the design before competing; do not silently delete player buildings as a workaround.

## Water is the critical acceptance gate

- At game start, ordinary scouts cannot pass the central water barriers. Try diagonal corner cutting and large units. Ships also collide with the barrier pieces; verify access to the rest of both water basins.
- Native waterfall graphics on Gaia Rock 2 are animated and recognizable, with no remaining giant rock sprites. Verify collision is exactly one tile per piece and object data changes did not affect player-owned units.
- The shallow route is still clearly marked by shore-side torches when covered by water curtains. The show must not obscure selection or an army's escape direction.
- At 11:00 see the wind notice/timer; at 12:00 see the withdrawal; at 12:10 only outer rows disappear; at 12:20 every barrier is gone and formations can cross.
- At 16:30 see the full 90-second flood warning. No early flood damage. At 18:00 compare damage to mirrored unarmored and armored units; expect 6 current HP/second within the bounds only.
- Test a monk with a relic, a packed and unpacked trebuchet, rams with passengers, a fishing ship, transport ship with passengers, infantry, mounted ranged unit, livestock and a building outside the hazard. Relic drops and normal deaths must behave sensibly.
- Park a unit in a returning barrier cell: no forced overlapping spawn; it can retreat or die to the already-announced hazard, and the vacated barrier cell then fills. Test dense formations and invulnerable editor units to exercise the 120-second fail-open safeguard.
- Repeat at least three complete sea cycles, then leave an observer game running for two hours. Check memory, performance and the count of lingering smoke/fire/water objects.

## Other events and sound

- Either player can ignite either shrub at radius five. No duplicate ignitions or consumed bush. Flames and raised smoke look like a bush, not a destructive building fire.
- Both moving guides remain scenery, grant no shared vision and cannot be selected to command them. Night-phase fire and day-phase cloud are readable without intrusive flashing.
- At 07:00 and 25:00, confirm three 75-food bushes on each bank. Block one spawn tile; both gardens must roll back. Clear it within 30 seconds to allow a retry, or hold it to cancel both gardens.
- Attack a Jericho wall early, then at 24:00 count seven horn calls. At 24:07 verify only original Gaia walls fall. Add nearby player-built walls; these must survive. Check that the preplaced gold/relics remain intact.
- Listen to all twelve custom WEM cues in the installed game. Verify volume, timing, path lookup and no overlap clipping. Repeat without the audio files: warnings/timers and every gameplay result must remain the same.
- At 17:30 and 17:50, verify the 30- and 10-second flood reminders. The open-crossing motif must not sound like the flood or Jericho calls. Ambient water/fire should be quiet and positional, never a global combat-masking wash.
- Save/load in each sea phase, especially 17:49 and 17:59. Verify countdowns and no duplicate warnings, food, fires or audio bursts. The local tests only simulate execution gaps, not DE saves.
- Confirm lower cloud pillars and transition mist do not conceal troops. No AI-generated custom sprite should be required or installed by the normal map ZIP.

## Multiplayer and balance

- Two human peers, no AI timing assumptions. Test missing audio on one peer and identical scripts on both. Never accept an out-of-sync or a missing XS initialization as a valid match.
- Save/reload before 12:20, before 18:00 and before 24:07. Check event deadlines, effect references, duplicate manna, horn sequence and next-cycle timing. Review the recorded game with and without the audio pack.
- Play at least 12 side-swapped pairs spanning open-map aggression, cavalry, ranged units, monks, siege, meso and strong-fishing civilizations. Record crossing usage, flood losses, coast control and whether the manna denial tactic is too easy.
- Particular risks: mandatory awareness tax from the flood; sea control denying crossings; fishing snowball; walling coast bottlenecks; civilizations with faster/stronger mobile units having more evacuation latitude. Public timing and geometric symmetry do not by themselves prove balance.
