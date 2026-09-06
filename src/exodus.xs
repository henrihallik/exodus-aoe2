/* EXODUS: SEA OF SIGNS 0.2.0 — Tiny / 1v1 / standard Conquest.
   Biblical theatre, not a claim to reconstruct one historical location.
   Sea = fixed non-buildable shallows + Gaia water curtains and barriers.
   No terrain repaint API, data mod, player stat changes, or custom victory.
   Flood damage is an announced environmental hazard, not a unit-stat change.
   All simulation decisions are synchronized; audio return values are ignored.
*/

const int exGateObject = 1323; // Gaia Rock 2; ONLY this scenery type is reskinned.
const int exWaterGraphicObject = 896;
const int exWaterEffect = 1635;
const int exFire = 304;
const int exCloud = 1308;
const int exBush = 1360;
const int exWall = 117;
const int exFood = 59;
const int exPoolSize = 48;
const int exPeriod = 1080;
const int exFirstWind = 660;
const float exFloodDps = 6.0;

int exGates = -1;
int exWalls = -1;
int exQuery = -1;
int exEffects = -1;
int exExpires = -1;
int exCurtains = -1;
int exPillars = -1;
int exMannaDone = -1;
int exBushLit = -1;
int exInitialBushes = -1;
int exFoodRetries = -1;
int exPoolCursor = 0;
int exPhase = -1;
int exAttempts = 0;
int exLastTick = -1;
int exLastHorn = -1;
int exLastPillar = -1;
int exGateFailures = 0;
int exOriginalMood = 0;
bool exReady = false;
bool exJerichoFallen = false;
bool exFailure = false;
int exBushFires = -1;
int exWarningCycle = -1;
int exWarningStage = 0;
int exAmbientUntil = 0;
int exQuietUntil = 0;
int exPendingPriority = 0;
string exPendingCue;
int exAmbientPass = 0;

vector exPoint(float x = 0.0, float y = 0.0, float z = 0.0) {
    return (xsVectorSet(x, y, z));
}

int exFloor(float value = 0.0) {
    return (xsCeilToInt(floor(value)));
}

bool exOwnScenery(int id = -1, int object = -1) {
    if (xsDoesUnitExist(id) == false) { return (false); }
    return ((xsGetUnitOwner(id) == 0) && (xsGetUnitObjectId(id) == object));
}

/* Boundaries deliberately include the complete marked seabed, not beaches,
   coastal roads or towns. Map tile centers run .5 through 119.5. */
bool exInSea(vector p = vector(-1, -1, -1)) {
    float x = xsVectorGetX(p);
    float y = xsVectorGetY(p);
    return ((x >= 55.0) && (x < 65.0) && (y >= 44.0) && (y < 76.0));
}

int exGateSlot(vector p = vector(-1, -1, -1)) {
    float x = xsVectorGetX(p);
    float y = xsVectorGetY(p);
    if ((x >= 55.0) && (x < 65.0) && (y >= 58.0) && (y < 62.0)) {
        return ((exFloor(y) - 58) * 10 + exFloor(x) - 55);
    }
    return (-1);
}

/* Exact integer schedule; returning to this function after a load does not
   re-roll events. 0 flooded; 1 wind; 2 parting; 3 open; 4 warning; 5 return. */
int exSeaPhase(int now = 0) {
    if (now < exFirstWind) { return (0); }
    int t = (now - exFirstWind) % exPeriod;
    if (t < 60) { return (1); }
    if (t < 80) { return (2); }
    if (t < 330) { return (3); }
    if (t < 420) { return (4); }
    if (t < 460) { return (5); }
    return (0);
}

/* Explicit documented class queries avoid an undocumented "all units" ID.
   Class ids are query ids (900+). Includes relic monks, packed/unpacked
   siege, kings, mounted ranged units, livestock and controlled animals.
   Ships, buildings, projectiles, resources and Gaia are never damaged. */
bool exLandClass(int c = 0) {
    return ((c == 900) || (c == 904) || (c == 906) || (c == 912) ||
        (c == 913) || (c == 917) || (c == 918) || (c == 919) ||
        (c == 923) || (c == 924) || (c == 925) || (c == 926) ||
        (c == 928) || (c == 929) || (c == 935) || (c == 936) ||
        (c == 943) || (c == 944) || (c == 945) || (c == 946) ||
        (c == 947) || (c == 950) || (c == 951) || (c == 954) ||
        (c == 955) || (c == 956) || (c == 957) || (c == 958) ||
        (c == 959) || (c == 961));
}

void exNotice(string message = "") {
    xsChatData(message);
}

void exTimer(string message = "", int seconds = 0) {
    xsDisplayTimer(710, message, seconds);
}

bool exPublicCueSoon(int now = 0, int horizon = 8) {
    if ((now < 660) && (now + horizon >= 660)) { return (true); }
    if ((now < 1448) && (now + horizon >= 1440)) { return (true); }
    if (now >= 660) {
        int t = (now - 660) % 1080;
        for (i = 0; < 7) {
            int deadline = 1080;
            if (i == 0) { deadline = 60; }
            if (i == 1) { deadline = 80; }
            if (i == 2) { deadline = 330; }
            if (i == 3) { deadline = 390; }
            if (i == 4) { deadline = 410; }
            if (i == 5) { deadline = 420; }
            if ((t < deadline) && (t + horizon >= deadline)) { return (true); }
        }
    }
    return (false);
}

void exCue(string name = "") {
    // One global cue per tick; safety beats atmosphere. No playback return
    // value or local client information may affect this scheduler.
    int cueRank = 20;
    if (name == "exodus_wind") { cueRank = 50; }
    if (name == "exodus_parting") { cueRank = 60; }
    if (name == "exodus_horn") { cueRank = 70; }
    if (name == "exodus_jericho") { cueRank = 75; }
    if (name == "exodus_open") { cueRank = 80; }
    if (name == "exodus_warning") { cueRank = 90; }
    if (name == "exodus_final_warning") { cueRank = 95; }
    if (name == "exodus_flood") { cueRank = 100; }
    if (cueRank > exPendingPriority) {
        exPendingCue = name;
        exPendingPriority = cueRank;
    }
}

void exFlushCue(int now = 0) {
    if (exPendingPriority > 0) {
        // Suppress decorative global cues during an earlier important cue.
        if ((exPendingPriority >= 50) || ((now >= exQuietUntil) && (exPublicCueSoon(now, 8) == false))) {
            xsPlaySound(exPendingCue, -1, vector(-1, -1, -1), 0.0, -1, true);
            int hold = 8;
            if (exPendingCue == "exodus_horn") { hold = 1; }
            exQuietUntil = now + hold;
        }
    }
    exPendingPriority = 0;
    exPendingCue = "";
}

void exAmbient(int now = 0) {
    // Finite quiet 2-second clips, NOT unkillable loops. At most one paired
    // source (two voices) every 30 seconds. No unit proximity or fog queries:
    // ambience cannot disclose a hidden army or depend on client visibility.
    if ((now < exAmbientUntil) || (now < exQuietUntil) || (exPendingPriority > 0)) { return; }
    if ((exPhase != 0) && (exPhase != 3)) { return; }
    if (exPublicCueSoon(now, 2)) { return; }
    bool fires = ((exAmbientPass % 2 == 1) &&
        exOwnScenery(xsArrayGetInt(exBushFires, 0), exFire) &&
        exOwnScenery(xsArrayGetInt(exBushFires, 1), exFire));
    if (fires) {
        xsPlaySound("exodus_crackle", -1, exPoint(46.5, 35.5), 0.0, -1, false);
        xsPlaySound("exodus_crackle", -1, exPoint(73.5, 84.5), 0.0, -1, false);
    } else {
        xsPlaySound("exodus_shore", -1, exPoint(53.5, 46.5), 0.0, -1, false);
        xsPlaySound("exodus_shore", -1, exPoint(66.5, 73.5), 0.0, -1, false);
    }
    exAmbientPass = exAmbientPass + 1;
    exAmbientUntil = now + 30;
}

void exRefreshTimer(int now = 0) {
    int t = (now - exFirstWind) % exPeriod;
    if (exPhase == 0) {
        int wait = exFirstWind - now;
        if (now >= exFirstWind) { wait = exPeriod - t; }
        exTimer("East wind in %d", wait);
    }
    if ((exPhase == 1) || (exPhase == 2)) { exTimer("Sea crossing opens in %d", 80 - t); }
    if (exPhase == 3) { exTimer("WATERS RETURN in %d", 420 - t); }
    if (exPhase == 4) { exTimer("EVACUATE SEABED — %d", 420 - t); }
    if (exPhase == 5) { exTimer("Waters settling in %d", 460 - t); }
}

void exSafetyWarnings(int now = 0) {
    if (exPhase != 4) { return; }
    int cycle = exFloor(1.0 * (now - exFirstWind) / exPeriod);
    if (cycle != exWarningCycle) { exWarningCycle = cycle; exWarningStage = 0; }
    int remaining = 420 - (now - exFirstWind) % exPeriod;
    // If execution resumes late, deliver only the most urgent remaining
    // warning, never a burst of obsolete 30- and 10-second notices.
    if ((remaining <= 10) && (exWarningStage < 2)) {
        exWarningStage = 2;
        exNotice("EXODUS: FINAL FLOOD WARNING — 10 SECONDS OR LESS. Leave the marked seabed NOW. Both coastal routes remain open.");
        exCue("exodus_final_warning");
    } else {
        if ((remaining <= 30) && (exWarningStage < 1)) {
            exWarningStage = 1;
            exNotice("EXODUS: FLOOD WARNING — 30 SECONDS OR LESS. Withdraw toward either bank; leave the marked seabed.");
            exCue("exodus_warning");
        }
    }
}

void exConfigureGaia() {
    // Only unused-by-this-map Gaia scenery definitions are affected.
    xsEffectAmount(cSetAttribute, exGateObject, cUnitSizeX, 0.5, 0);
    xsEffectAmount(cSetAttribute, exGateObject, cUnitSizeY, 0.5, 0);
    xsEffectAmount(cSetAttribute, exGateObject, cObstructionType, 2, 0);
    xsEffectAmount(cSetAttribute, exGateObject, cBlockageClass, 6, 0);
    xsEffectAmount(cSetAttribute, exGateObject, cSelectionEffect, 2, 0);
    float waterGraphic = xsGetObjectAttribute(0, exWaterGraphicObject, cStandingGraphic);
    if (waterGraphic >= 0.0) {
        xsEffectAmount(cSetAttribute, exGateObject, cStandingGraphic, waterGraphic, 0);
    }
    xsEffectAmount(cSetAttribute, exWaterEffect, cObstructionType, 4, 0);
    xsEffectAmount(cSetAttribute, exWaterEffect, cUnitSizeX, 0.0, 0);
    xsEffectAmount(cSetAttribute, exWaterEffect, cUnitSizeY, 0.0, 0);
    xsEffectAmount(cSetAttribute, exFire, cObstructionType, 4, 0);
    xsEffectAmount(cSetAttribute, exFire, cUnitSizeX, 0.0, 0);
    xsEffectAmount(cSetAttribute, exFire, cUnitSizeY, 0.0, 0);
    xsEffectAmount(cSetAttribute, exCloud, cObstructionType, 4, 0);
    xsEffectAmount(cSetAttribute, exCloud, cUnitSizeX, 0.0, 0);
    xsEffectAmount(cSetAttribute, exCloud, cUnitSizeY, 0.0, 0);
}

void exParticle(vector p = vector(-1, -1, -1), int now = 0, int life = 8) {
    int old = xsArrayGetInt(exEffects, exPoolCursor);
    if (exOwnScenery(old, exCloud)) { xsRemoveUnit(old); }
    int id = xsCreateUnit(exCloud, 0, p, false, false, false);
    xsArraySetInt(exEffects, exPoolCursor, id);
    xsArraySetInt(exExpires, exPoolCursor, now + life);
    exPoolCursor = (exPoolCursor + 1) % exPoolSize;
}

void exCleanParticles(int now = 0) {
    for (i = 0; < exPoolSize) {
        if (xsArrayGetInt(exExpires, i) <= now) {
            int id = xsArrayGetInt(exEffects, i);
            if (exOwnScenery(id, exCloud)) { xsRemoveUnit(id); }
            xsArraySetInt(exEffects, i, -1);
        }
    }
}

void exClearGates(bool outsideOnly = false) {
    for (i = 0; < 40) {
        if ((outsideOnly == false) || (i < 10) || (i >= 30)) {
            int id = xsArrayGetInt(exGates, i);
            if (exOwnScenery(id, exGateObject)) { xsRemoveUnit(id); }
            xsArraySetInt(exGates, i, -1);
        }
    }
}

bool exRestoreGates() {
    bool complete = true;
    for (i = 0; < 40) {
        int id = xsArrayGetInt(exGates, i);
        if (exOwnScenery(id, exGateObject) == false) {
            int row = exFloor(0.1 * i);
            int col = i % 10;
            // Never force an obstruction underneath a player's unit.
            int made = xsCreateUnit(exGateObject, 0,
                exPoint(55.5 + col, 58.5 + row), false, false, true);
            xsArraySetInt(exGates, i, made);
            if (made < 0) { complete = false; }
        }
    }
    return (complete);
}

void exMoveCurtains(int now = 0) {
    float opening = 0.0;
    float stageTime = (now - exFirstWind) % exPeriod;
    if ((exPhase == 3) || (exPhase == 4)) { opening = 1.0; }
    if (exPhase == 2) { opening = (stageTime - 60.0) / 20.0; }
    if (exPhase == 5) { opening = 1.0 - (stageTime - 420.0) / 40.0; }
    opening = opening * opening * (3.0 - 2.0 * opening);
    for (i = 0; < 12) {
        int side = i % 2;
        int row = exFloor(0.5 * i);
        float x = 58.5 - opening * 5.0;
        float y = 46.5 + 5.0 * row;
        if (side == 1) { x = 120.0 - x; y = 120.0 - y; }
        int id = xsArrayGetInt(exCurtains, i);
        if (exOwnScenery(id, exWaterEffect) == false) {
            id = xsCreateUnit(exWaterEffect, 0, exPoint(x, y), false, false, false);
            xsArraySetInt(exCurtains, i, id);
        } else { xsSetUnitPosition(id, exPoint(x, y), false); }
    }
}

void exSea(int now = 0) {
    int phase = exSeaPhase(now);
    if (phase != exPhase) {
        exPhase = phase;
        if (phase == 0) {
            xsSetColorMood(cColorMoodDesert, 12);
            exNotice("EXODUS: The sea is closed. The marked seabed is dangerous; both coastal roads remain open.");
            int wait = exFirstWind - now;
            if (now >= exFirstWind) { wait = exPeriod - (now - exFirstWind) % exPeriod; }
            exTimer("East wind in %d", wait);
        }
        if (phase == 1) {
            xsSetColorMood(cColorMoodEvening, 20);
            exNotice("EXODUS: THE EAST WIND. The public timer counts down to the usable crossing; wait for the OPEN signal.");
            exTimer("Sea crossing opens in %d", 80);
            exCue("exodus_wind");
        }
        if (phase == 2) {
            exNotice("EXODUS: THE WATERS DIVIDE. Watch the water curtains withdraw; wait for the OPEN signal and countdown.");
            exCue("exodus_parting");
        }
        if (phase == 3) {
            exClearGates();
            exGateFailures = 0;
            xsSetColorMood(cColorMoodDesert, 12);
            exNotice("EXODUS: THE SEA ROAD IS OPEN. Both armies may cross. The public timer shows when the waters return.");
            exTimer("WATERS RETURN in %d", 340);
            exCue("exodus_open");
        }
        if (phase == 4) {
            xsSetColorMood(cColorMoodEvening, 15);
            exNotice("EXODUS: FLOOD WARNING. Follow the evacuation countdown. Leave the marked seabed; flooded land units lose 6 HP per second.");
            exTimer("EVACUATE SEABED — %d", 90);
            exCue("exodus_warning");
        }
        if (phase == 5) {
            xsSetColorMood(cColorMoodMisty, 10);
            exNotice("EXODUS: THE WATERS RETURN. The seabed now drains 6 HP per second from land units. Retreat toward either bank; ships are exempt.");
            exTimer("Waters settling in %d", 40);
            exCue("exodus_flood");
        }
    }
    exSafetyWarnings(now);
    if (phase == 2) {
        if ((now - exFirstWind) % exPeriod >= 70) { exClearGates(true); }
    }
    if ((phase == 0) || (phase == 1) || (phase == 5)) {
        if (exRestoreGates() == false) { exGateFailures = exGateFailures + 1; }
        else { exGateFailures = 0; }
        // A broken collision implementation must not silently create a new
        // competitive ruleset. Fail open, stop all hazards, announce invalid.
        if (exGateFailures >= 120) {
            exFailure = true;
            exClearGates();
            xsClearTimer(710);
            exNotice("EXODUS: Sea barriers could not restore for 120 seconds. Events are suspended and the sea road is open. INVALID for competition; report this generation.");
        }
    }
    exMoveCurtains(now);
}

void exSurveyLandUnits(int now = 0) {
    bool dangerous = ((exPhase == 0) || (exPhase == 1) || (exPhase == 5));
    for (player = 1; < 3) {
        for (c = 900; < 966) {
            if (exLandClass(c)) {
                exQuery = xsGetPlayerUnitIds(player, c, exQuery);
                int count = xsArrayGetSize(exQuery);
                for (i = 0; < count) {
                    int id = xsArrayGetInt(exQuery, i);
                    if (xsDoesUnitExist(id)) {
                        if (xsGetGarrisonedInUnitId(id) < 0) {
                            vector p = xsGetUnitPosition(id);
                            if (dangerous && exInSea(p)) {
                                float hp = xsGetUnitHitpoints(id) - exFloodDps;
                                if (hp < 0.0) { hp = 0.0; }
                                xsSetUnitHitpoints(id, hp);
                            }
                            // Either player can discover either bush; neither
                            // receives an economic or combat buff from it.
                            for (b = 0; < 2) {
                                if (xsArrayGetInt(exBushLit, b) == 0) {
                                    float bx = 46.5;
                                    float by = 35.5;
                                    if (b == 1) { bx = 120.0 - bx; by = 120.0 - by; }
                                    float dx = xsVectorGetX(p) - bx;
                                    float dy = xsVectorGetY(p) - by;
                                    if (dx * dx + dy * dy <= 25.0) {
                                        xsArraySetInt(exBushLit, b, 1);
                                        int fireId = xsCreateUnit(exFire, 0, exPoint(bx, by), false, false, false);
                                        xsArraySetInt(exBushFires, b, fireId);
                                        exParticle(exPoint(bx, by, 1.0), now, 8);
                                        exNotice("EXODUS: A BUSH BURNS, YET IS NOT CONSUMED. A sign only: no player receives a hidden bonus.");
                                        exCue("exodus_bush");
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

void exPillar(int now = 0) {
    int mode = 0;
    if ((exPhase == 1) || (exPhase == 2) || (exPhase == 4) || (exPhase == 5)) { mode = 1; }
    // Two mirrored guides move along the bank, never reveal enemy territory.
    int step = exFloor(1.0 * now / 3.0) % 24;
    if (step > 12) { step = 24 - step; }
    for (side = 0; < 2) {
        float x = 52.5 + 0.5 * step;
        float y = 37.5;
        if (side == 1) { x = 120.0 - x; y = 120.0 - y; }
        int id = xsArrayGetInt(exPillars, side);
        if (mode == 1) {
            if (exOwnScenery(id, exFire) == false) {
                id = xsCreateUnit(exFire, 0, exPoint(x, y), false, false, false);
                xsArraySetInt(exPillars, side, id);
            } else { xsSetUnitPosition(id, exPoint(x, y), false); }
        } else {
            if (exOwnScenery(id, exFire)) { xsRemoveUnit(id); }
            xsArraySetInt(exPillars, side, -1);
        }
        if (now % 3 == 0) {
            exParticle(exPoint(x, y, 1.0), now, 8);
            exParticle(exPoint(x, y, 1.8), now, 8);
        }
    }
    if (mode != exLastPillar) {
        if (mode == 1) { exNotice("EXODUS: THE PILLARS OF FIRE GUIDE THE BANKS."); }
        else { exNotice("EXODUS: THE PILLARS OF CLOUD GUIDE THE BANKS."); }
        exLastPillar = mode;
    }
}

void exSceneryMaintenance(int now = 0) {
    // Reconcile only tracked, nonblocking decorative fires. Never touch a
    // resource, restore a destroyed shrine, or replay its discovery reward.
    for (b = 0; < 2) {
        if (xsArrayGetInt(exBushLit, b) == 1) {
            int id = xsArrayGetInt(exBushFires, b);
            if (exOwnScenery(id, exFire) == false) {
                float x = 46.5;
                float y = 35.5;
                if (b == 1) { x = 73.5; y = 84.5; }
                // The shrine must still exist at its original position.
                bool present = false;
                exQuery = xsGetPlayerUnitIds(0, exBush, exQuery);
                int shrubs = xsArrayGetSize(exQuery);
                for (j = 0; < shrubs) {
                    vector p = xsGetUnitPosition(xsArrayGetInt(exQuery, j));
                    if ((exFloor(xsVectorGetX(p)) == exFloor(x)) && (exFloor(xsVectorGetY(p)) == exFloor(y))) { present = true; }
                }
                if (present) {
                    id = xsCreateUnit(exFire, 0, exPoint(x, y), false, false, false);
                    xsArraySetInt(exBushFires, b, id);
                }
            }
        }
    }
    // Small paired mist puffs OUTSIDE the walkable strip during transitions;
    // the existing 48-slot TTL pool bounds all mist, cloud and collapse dust.
    if (((exPhase == 2) || (exPhase == 5)) && (now % 6 == 0)) {
        exParticle(exPoint(53.5, 46.5, 0.5), now, 5);
        exParticle(exPoint(66.5, 73.5, 0.5), now, 5);
    }
}

void exManna(int wave = 0, int now = 0) {
    if (xsArrayGetInt(exMannaDone, wave) != 0) { return; }
    // Transactional paired creation: a blocked garden cannot award only one
    // bank food. Stage all six bushes, roll back exactly those new IDs if any
    // creation fails, and retry at most 30 times without consuming resources.
    int staged = exInitialBushes;
    bool ok = true;
    for (i = 0; < 6) {
        int side = exFloor(1.0 * i / 3.0);
        int col = i % 3;
        float x = 73.5 + col;
        float y = 35.5 + 3.0 * wave;
        if (side == 1) { x = 120.0 - x; y = 120.0 - y; }
        int id = xsCreateUnit(exFood, 0, exPoint(x, y), false, false, true);
        xsArraySetInt(staged, i, id);
        if (id < 0) { ok = false; }
        else { xsSetUnitAttributeHeld(id, 75.0); }
    }
    if (ok == false) {
        for (i = 0; < 6) {
            int rollbackId = xsArrayGetInt(staged, i);
            if (exOwnScenery(rollbackId, exFood)) { xsRemoveUnit(rollbackId); }
        }
        int retries = xsArrayGetInt(exFoodRetries, wave) + 1;
        xsArraySetInt(exFoodRetries, wave, retries);
        if (retries >= 30) {
            xsArraySetInt(exMannaDone, wave, -1);
            exNotice("EXODUS: Both manna gardens must be clear. This wave is cancelled for BOTH banks; no food was awarded.");
        }
    } else {
        xsArraySetInt(exMannaDone, wave, 1);
        exNotice("EXODUS: MANNA IN THE WILDERNESS. Three new 75-food bushes blossom on EACH bank. Gather normally; either player may claim them.");
        exCue("exodus_manna");
        exParticle(exPoint(74.5, 35.5 + 3.0 * wave), now, 10);
        exParticle(exPoint(45.5, 84.5 - 3.0 * wave), now, 10);
    }
}

void exJericho(int now = 0) {
    if (exJerichoFallen) { return; }
    if ((now >= 1440) && (now < 1447)) {
        int horn = now - 1440;
        if (horn > exLastHorn) {
            exLastHorn = horn;
            exCue("exodus_horn");
            if (horn == 0) { exNotice("EXODUS: SEVEN TRUMPETS. Both ancient enclosures fall after the seventh call."); }
        }
    }
    if (now >= 1447) {
        int count = xsArrayGetSize(exWalls);
        for (i = 0; < count) {
            int id = xsArrayGetInt(exWalls, i);
            if (exOwnScenery(id, exWall)) { xsRemoveUnit(id); }
        }
        exJerichoFallen = true;
        exNotice("EXODUS: THE WALLS OF JERICHO FALL. Both neutral enclosures are open. Player-built walls are untouched.");
        exCue("exodus_jericho");
        for (i = 0; < 6) {
            exParticle(exPoint(7.5 + i, 56.5), now, 12);
            exParticle(exPoint(112.5 - i, 63.5), now, 12);
        }
    }
}

bool exInitialize() {
    if ((xsGetMapWidth() != 120) || (xsGetMapHeight() != 120) || (xsGetNumPlayers() != 3)) {
        return (false);
    }
    exQuery = xsGetPlayerUnitIds(0, exGateObject, exQuery);
    int count = xsArrayGetSize(exQuery);
    if (count != 40) { return (false); }
    for (i = 0; < 40) { xsArraySetInt(exGates, i, -1); }
    for (i = 0; < count) {
        int id = xsArrayGetInt(exQuery, i);
        int slot = exGateSlot(xsGetUnitPosition(id));
        if (slot < 0) { return (false); }
        if (xsArrayGetInt(exGates, slot) >= 0) { return (false); }
        xsArraySetInt(exGates, slot, id);
    }
    exWalls = xsGetPlayerUnitIds(0, exWall, exWalls);
    if (xsArrayGetSize(exWalls) != 64) { return (false); }
    exQuery = xsGetPlayerUnitIds(0, exBush, exQuery);
    if (xsArrayGetSize(exQuery) != 2) { return (false); }
    exOriginalMood = xsGetColorMood();
    exConfigureGaia();
    exNotice("EXODUS: SEA OF SIGNS. Tiny 1v1 Conquest. First sea crossing 12:20; flood 18:00; repeats every 18 minutes. Coastal roads NEVER close. Flooded seabed: 6 HP/second to land units.");
    return (true);
}

rule exTick
active
minInterval 1
maxInterval 1
{
    int now = xsGetGameTime();
    if (now == exLastTick) { return; }
    bool refresh = (now > exLastTick + 2);
    exLastTick = now;
    if (exReady == false) {
        exAttempts = exAttempts + 1;
        exReady = exInitialize();
        if ((exReady == false) && (exAttempts >= 10)) {
            exNotice("EXODUS: INITIALIZATION FAILED. Requires Tiny, two players, standard dataset, and all authored landmarks. Do not count this generation; report the seed.");
            xsDisableSelf();
        }
        if (exReady == false) { return; }
    }
    exCleanParticles(now);
    if (exFailure) { return; }
    exSea(now);
    if (exFailure) { xsSetColorMood(exOriginalMood, 10); return; }
    if (refresh) { exRefreshTimer(now); }
    exSurveyLandUnits(now);
    exPillar(now);
    exSceneryMaintenance(now);
    if ((now >= 420) && (xsArrayGetInt(exMannaDone, 0) == 0)) { exManna(0, now); }
    if ((now >= 1500) && (xsArrayGetInt(exMannaDone, 1) == 0)) { exManna(1, now); }
    exJericho(now);
    exAmbient(now);
    exFlushCue(now);
}

void main() {
    exPendingCue = "";
    exGates = xsArrayCreateInt(40, -1, "exGates");
    exEffects = xsArrayCreateInt(exPoolSize, -1, "exEffects");
    exExpires = xsArrayCreateInt(exPoolSize, 0, "exExpires");
    exCurtains = xsArrayCreateInt(12, -1, "exCurtains");
    exPillars = xsArrayCreateInt(2, -1, "exPillars");
    exMannaDone = xsArrayCreateInt(2, 0, "exMannaDone");
    exBushLit = xsArrayCreateInt(2, 0, "exBushLit");
    exInitialBushes = xsArrayCreateInt(6, -1, "exStagedFood");
    exFoodRetries = xsArrayCreateInt(2, 0, "exFoodRetries");
    exBushFires = xsArrayCreateInt(2, -1, "exBushFires");
    // Configure before RMS objects are placed AND again in the runtime init.
    exConfigureGaia();
}
