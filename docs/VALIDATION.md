# Validation record — 0.2.2

## Curtain endpoint adjustment — curtains-02

User screenshots showed continuous-looking 18-piece curtains with staggered endpoints and short shoreline coverage. Previous y=46.5..71.5 reflected into y=48.5..73.5. New 22-piece sides both span 44.5..75.5, invariant under y -> 120-y. Spacing is 31/21 tiles; total fixed curtain count is 44. A regression checks matching sorted y positions and exact endpoints across closed, wind, opening, open, warning and flooding phases. Existing rotational/easing checks remain. These are authored shoreline tile centers, not a guarantee of exact rendered sprite-edge contact at every terrain transition. Native screenshot confirmation remains needed. Smoke-pillar graphics and the previously reported native gameplay failures are not proven resolved by this visual patch. No archive changes.

## Runtime repair candidate — runtime-01

Local verification: 38 mocked event tests cover the changes, including query-return aliasing, empty-query fallback, refused removals, refused HP writes, 36-piece symmetry and bounded failed particle cleanup. XS lint reports no errors. Loose-script encoding/declaration and source/download equality are checked. Historical ZIPs intentionally remain untouched. Primary references used: [UGC Gaia effect example](https://ugc.aoe2.rocks/general/xs/tricks/) and [XS function reference](https://ugc.aoe2.rocks/general/xs/functions/functions/). Native confirmation and performance checks remain required.

Native walls-01 testing confirmed wall creation and moving waterfall scenery, but rocks stayed through OPEN and flood phases, with later restore failure. The user also reported no villager damage. Code audit found that clearing gates discarded live references without checking removal; OPEN and fail-open announcements were unconditional. These are corrected: preserve references until disappearance, verify removals before OPEN, suspend on repeated opening failure, validate newly restored IDs/types/slots, and never claim clearance after an unsuccessful cleanup. Jericho collapse also waits for verified removal; failed particle cleanup retains references rather than spawning untracked replacements.

The player query now owns an explicitly allocated scratch array and never assigns the native function return to that array ID. A zero-return mock reproduces the potential aliasing path without corrupting gate storage. This is a plausible explanation for lost tracking, not a native trace proving the API return semantics. Query results are checked for owner/class; raw classes and +900 classes are normalized. If a player has no query results, a reference scan starting at 4096 covers land-unit effects, growing in 4096 increments when live IDs approach its edge (cap 65536). This heuristic is not a complete global enumeration guarantee, and sparse IDs beyond the scanned range remain a native-validation risk. All damage still excludes Gaia, ships, buildings and garrisoned units. HP changes are read back; failed changes suspend events. Timing/command deferral in native DE remains to be checked.

Scenery writes use documented `cGaiaSetAttribute` instead of `cSetAttribute` with player 0 (see UGC Tricks Gaia handling). This is intended to correct water appearance and nonblocking scenery; native graphics readback/appearance is not yet verified. Waterfall pool is now 36 pieces, 18 mirrored pairs spaced about 1.47 tiles apart, versus 12 pieces at 5-tile spacing. Continuous-looking coverage still needs screenshot confirmation. Startup identifies `runtime-01`. No archive is created or changed.

## Wall placement correction — walls-01

The user confirmed no visible walls around either coastal 2x2 gold pile and relic; refs-01 found zero Gaia walls. The RMS guide's Walls section documents special enclosure behavior using min/max distance, unlike ordinary point objects. Our prior zero-distance, per-tile `create_object EX_WALL` placement was therefore not a reliable method. The alpha preview explicitly does not simulate special wall placement. Root-cause inference: native wall-generation semantics, not established by an engine trace.

The new RMS substitutes nonblocking torch 499 at the same 64 authored wall anchors (land ID 511); unrelated coastal torches remain unchanged. XS scans and validates unique marker slots. If there are zero actual walls and exactly 64 valid markers, it stages 64 Gaia stone walls with collision checking at those positions. Only successful creation of both enclosures allows marker removal and events. Failed staging removes only newly created Gaia walls and preserves markers for bounded initialization retries. Partial pre-existing wall sets are never supplemented; a complete verified set is reused without duplication. Counts, ownership, slot checks, and existing resource geometry remain intact. Steady-state storage is 14 arrays. New RMS and XS must be installed together.

Local checks: 32 mocked event tests pass, including success, rollback, missing markers and partial pre-existing walls. The Python suite has 15 passing checks and one expected failure: historical ZIP/source equality, because the user explicitly requested no new ZIP. The new RMS contract test passes point-marker emission and eight total Jericho gold tiles. Both linters and script encoding/declaration checks pass. Native marker collision, wall graphics/connectivity and startup remain unverified. `--scripts-only` updates runnable files without making or changing any ZIP.

## Reference registration fix — refs-01

Native diag-02 output reported both lookup orders returning zero, while scanning reference IDs 0–4095 found 40 Gaia object-1323 barriers and 40 crossing objects. Samples were reference 1875 at (55.5,58.5) and 1876 at (64.5,61.5), both owner 0, object 1323. That establishes the barriers exist in the tested generation, not the underlying API defect or behavior for player-unit queries.

Initialization now scans the same bounded reference range, tests existence and Gaia ownership before registration, and stores references in fixed arrays. It requires 40 unique barrier tile slots, 64 unique slots on the two authored wall perimeters, and the two exact shrub tiles. Counts, duplicate slots and wrong positions fail closed. Missing landmarks outside the scan ceiling also fail closed with an explicit range warning; no replacement objects are spawned. The range is not a global enumeration guarantee and cannot detect extra objects above 4095. Scanning stops after successful initialization or ten failed attempts. Shrub-fire maintenance uses registered original shrine references and rechecks existence, ownership, type and position rather than querying Gaia again. Player-unit queries are unchanged and remain a separate native validation item.

The 29-test Node suite now defaults all Gaia queries to empty results to reproduce the observed failure. It passes registration, all existing event tests, wall/shrub count/ownership/position/duplicate rejection, no retry-array growth, and out-of-range failure without replacements. Steady-state storage is now 13 arrays, including two registered shrubs; no unbounded scan or allocation was added. XS lint, ASCII/declaration guards, source/download byte equality and diff checks pass. These are local checks, not native verification of refs-01. No ZIP or release archive was created or updated.

## Read-only lookup diagnostic — diag-02

The native screenshot shows a central rock formation while diag-01 reports zero Gaia object 1323. This does not establish its exact object IDs or query semantics. On the final barrier-count failure, diag-02 compares `xsGetPlayerUnitIds(0,1323,array)` and `(1323,0,array)` using one scratch array. It independently scans reference IDs 0–4095 with existence checks before getters, reports matching Gaia 1323 counts and barrier-footprint counts, and prints at most two footprint samples with reference ID, owner, object ID, and coordinates. Higher reference IDs are explicitly not covered. No objects/attributes are changed by the diagnostic, no automatic convention is chosen, and failed initialization remains disabled. Existing normal initialization behavior is unchanged.

The mock suite adds tests under both argument-order interpretations, checks independent identification of different object types/owners, scratch-array reuse, once-only reporting, and absence of world mutation. Native execution of these new probes remains unverified. No ZIP is created or updated.

## Diagnostic direct-download update — diag-01

The user reported another initialization failure after the player-count hotfix. The generic message cannot identify the remaining cause. This update announces `2026-09-08 diag-01` once on the first runtime tick and reports the first failing guard on the tenth/final attempt: map dimensions, non-Gaia player count, sea-barrier count, out-of-bounds barrier ID/coordinates, duplicate slot with both IDs/coordinates, wall count, or shrub count. No validation gate is relaxed and no event is enabled on failure. A standard-dataset selection is not separately detected; object checks are the actual guards.

The Node suite now has 26 mocked tests, including all diagnostic branches, actual values, final-retry-only reporting, build identification, and successful initialization without failure notices. These remain mocks, not native engine validation. Source and downloadable XS must match byte for byte. Existing ZIPs are unchanged and do not include these diagnostics.

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
