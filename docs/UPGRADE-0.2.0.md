# Competitive presentation upgrade — 0.2.0

## Implemented

- Evacuation reminders at 30 and 10 seconds remaining, repeated each sea cycle, with late-entry and duplicate guards.
- Recomputed countdowns after execution gaps; no obsolete countdown message or burst of catch-up damage.
- Priority-based global cue scheduling; safety outranks decoration. Distinct opening, final warning and Jericho collapse audio.
- Quiet positional shoreline and paired shrine-fire ambience, finite two-second clips with 30-second rate limit; no narration, continuous soundtrack or unstoppable loops.
- Smooth curtain easing, lower cloud pillars and bounded bank-side transition mist.
- Missing tracked decorative fire recovery without touching player objects, duplicating discovery events or recreating resources.
- AI-generated transparent burning-bush sheet, preserved as a separate art study with mechanically extracted PNG frames. No Blender installation or local image model.

## Intentionally unchanged

The authored 120x120 terrain, both coastal routes, every resource and starting animal, 40 barrier cells, 64 original walls, manna quantities, 18-minute cycle, flood footprint and 6 HP/s damage. No standard trainable unit/civilization stat edits, new objectives, capturable rewards, random disasters or moving food animals.

## Deferred rather than guessed

Custom sprite binding and game-ready animation are pending current DE graphics mappings and native testing. AI frames have subtle branch/silhouette differences and are not a validated seamless loop. New cloud and water artwork is deferred until the burning-bush pipeline works. The standard playable package uses native graphics; source art is in a separate ZIP and is not a required mod.

The user may be unable to access a current DAT file through their cloud-gaming setup. No data mod, unverified graphics filename, new graphics ID or overwritten game asset is shipped to work around that missing input. Organizer acceptance of optional asset packs is also unconfirmed.

## Verification

See `VALIDATION.md`. Mocked XS execution is not an engine test. Native pathfinding, sprite size/occlusion, audio attenuation, saved games and multiplayer synchronization remain playtest gates.
