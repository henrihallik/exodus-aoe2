# Validation record — 0.2.2

## Direct-download hotfix — 2026-09-08

The user's next native test reached the scripted initialization-failure message, demonstrating execution past compilation, but not working events. The initialization guard incorrectly expected three players including Gaia. [Forgotten Empires documents that `xsGetNumPlayers` excludes Gaia](https://www.forgottenempires.net/age-of-empires-ii-definitive-edition/xs-scripting-in-age-of-empires-ii-definitive-edition); a 1v1 returns two. Both source and direct-download XS now require two. The mocked API had repeated the same mistaken assumption and is corrected, with an explicit two-player acceptance/other-count rejection regression test. The updated Node suite has 24 tests. Native initialization and subsequent events still need confirmation.

This hotfix updates loose files on `main` only, at the user's request. Existing v0.2.2 ZIPs and release assets are historical and do not contain this correction; no new ZIP is created. The validation notes below describe the earlier packaged build.

Updated: 2026-09-08. Status: implemented playtest candidate. The user's native v0.1.0 test failed XS compilation: unterminated-string/token errors at lines 235–236, followed by an `exPoint` code-generation error. Both reported string lines contain UTF-8 em dashes. This strongly implicates encoding; the `exPoint` error may be cascading, but that is not confirmed without a new native test. No successful native execution is claimed.

Version 0.2.1 replaces every non-ASCII character in XS with ASCII and validates both RMS and XS before writing runnable artifacts. Regression checks reject Unicode (including BOMs) and unsupported control bytes, and inspect the actual ZIP scripts. Earlier external lint/mock passes did not detect this native compatibility issue. The correction is packaged with the previously local v0.2.0 upgrade; the old release is preserved for traceability.

## Source and packaging checks

The user's v0.2.1 native test rejected `string exPendingCue;` at line 50 (Error 0016: initializer required). Version 0.2.2 removes global string state entirely, storing a numeric cue ID and resolving it to a literal-initialized local string only during playback. The declaration audit found no other uninitialized declarations. A build guard and regression test reject that pattern and global string state; another test round-trips all ten global cue names. This is a targeted correction, not evidence of successful native compilation or resolution of every earlier diagnostic.

- Python suite: 15 tests covering declaration guards, source/packaged script encoding, build rejection of unsafe characters, exact authored rotational symmetry, RMS coordinate reconstruction, resource counts, coastal connectivity, sea shortcut and exits, resource-cluster access, clear starts and manna gardens, package integrity, audio containers/headroom/cue coverage, and art-pack separation.
- Node suite: 23 tests, including numeric cue-ID round-trips and the authored-layout baseline check, executing the actual XS source translated into JavaScript with mocked documented APIs. Coverage includes phase boundaries, initialization failures, staged openings, repeated floods, damage exclusions, collision-safe barrier restoration, fail-open handling, bushes, paired manna rollback, original-wall-only removal, audio-independent simulation and bounded effects over 20 cycles. Checks also cover warning reminders, cue priorities, paired/rate-limited positional ambience, countdown repair, fire recovery and eased curtain endpoints. The baseline check compares every authored terrain/resource/object position against 0.1.0, excluding only the version field.
- These mocks are not an emulator: real unit classes, collision rules, graphics, deaths, pathfinding, synchronization and save/load must still be checked in DE.
- XS lint: xs-check 0.2.29. RMS lint: rms-check 0.0.4 with the existing local compatibility patch for current DE syntax. That RMS checker is not an unmodified upstream release. Optional lint tools are external to this project's normal build and are not packaged.
- Runtime scripts are approximately 205 KB RMS and 26 KB XS. Most download size is the twelve original sound cues plus their editable WAV masters, not the map logic. Deterministic ZIP construction and SHA256SUMS are provided; the AI art-study ZIP is separate from the game package.

## Age of RMS alpha preview

Used the generator and canvas renderer from [age-of-rms 0.4.1](https://github.com/aknipler/age-of-rms). Exact checkout commit, diagnostics, placement reports and generated object coordinates are retained in `docs/age-of-rms-report.json` in the source project. This is an approximate third-party alpha preview, not DE and not an XS interpreter.

The unmodified preview rounds every numeric percentage argument to a whole percent during S0 instantiation. At Tiny size, that shifts and merges fractional `land_position` anchors. Its seed-1 result therefore places only 231 objects, including 27 of 40 sea barriers. This does **not** establish that DE has the same failure: Zetnus's RMS guide explicitly documents DE support for floating-point land positions.

The optional adapter preserves only `land_position` decimal literals through S0 using a cloned argument definition. It leaves the downloaded tool sources unchanged and still records diagnostics from the original reference data. Both the uncorrected seed-1 output and this clearly labelled compatibility view are retained; the correction is not hidden as an upstream pass or a game-engine result.

With that correction, seeds **1, 7 and 42** each place all **262 authored Gaia objects at exactly their intended coordinates**, plus two town centers, two preview villagers and two scouts: 268 objects total. The adapter asserts the complete Gaia coordinate set and zero S6 placement failures. Native civilization-specific villager counts are not modeled by this preview.

The raw parser/validator reports no errors, only two informational notices about the still-supported `effect_percent` spelling. Remaining generator caveats include unseen XS includes, approximate terrain masks, unmodeled wall connectivity, shuffled rather than native deterministic object placement, and cosmetic terrain-clump growth shortfalls. Those shortfalls affect texture coverage, not missing resource placements. Automatic shoreline generation also differs from the authored atlas.

Visually inspected the generated minimap and planning atlas: both starts, forest belts, two sea basins, central crossing, both coastal routes and paired wall enclosures are visible. No burning-bush animation, moving pillar, parting curtain, flood, lighting transition or audio is visible/verified through this tool.

Reproduction: clone age-of-rms under `.tools/age-of-rms`, run its `npm ci`, supply Puppeteer and a Chrome executable using `PUPPETEER_MODULE` and `CHROME_PATH`, then run `node tools/render-age-preview.cjs`. Preview dependencies are optional and excluded from the release ZIP.

## Audio checks

All twelve generated WEM files have been independently decoded by the official vgmstream r2117 WASM CLI; decoded PCM matches the corresponding WAV master byte for byte. The decoder identifies 48 kHz mono 16-bit PCM with an Audiokinetic Wwise RIFF header. This confirms decodability, **not acceptance by DE's current audio loader**. In-game playback and positional attenuation remain pending.

## AI artwork boundary

The built-in image-generation tool produced one transparent 1254x1254 sheet. Mechanical extraction produced four 627x627 PNGs, each verified to contain both transparent and visible pixels. The source sheet was visually inspected; frame-to-frame geometry is not perfectly consistent. It is an unbound art study, not a validated seamless sprite animation. No guessed graphics IDs, sprite overrides or data mod are included. Native scenery remains the playable fallback pending game-data access and engine verification.

## Remaining release gates

Use `PLAYTEST.md`: critical items are the 40 scenery barriers' native collision/graphics, standard civilization starts, water curtains and pillar appearance, current audio loading, 6-HP flood behavior including relic carriers and transports, repeated save/load cycles and two-peer synchronization. Competitive balance requires side-swapped human matches. Do not submit as engine-tested until those checks actually pass.
