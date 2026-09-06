# Burning-bush AI art study

Created using the built-in image-generation tool, not Blender or a local model. The original transparent PNG is `assets/source/burning-bush-ai-v1.png` in the source checkout. Four mechanically extracted cells and an alpha/content manifest are in `assets/frames/`; `tools/extract-sprite.cjs` reproduces extraction using the existing optional browser tooling. No painted alterations or frame interpolation were added by that script.

**Status: artwork study, not an installed/game-ready sprite.** Visual inspection shows an appropriate small living thorn bush with restrained flames, but some branches and silhouette details vary between frames. Native sprite conversion, palette/format selection, anchors, timing, standing-graphic mapping and engine testing remain pending. We do not claim a seamless loop. This art is deliberately excluded from the playable map's graphics folder; native bush/fire scenery remains the fallback.

The separate `Exodus-Art-Study-0.2.0.zip` preserves the source, frames and this prompt for future work. No custom ordinary unit, civilization or gameplay data is included.

## Generation prompt (built-in tool)

Use case: stylized-concept. Asset type: production source sprite sheet for an isometric historical RTS decorative burning bush. Generate one 1024x1024 PNG with genuine transparent background, not a checkerboard drawing. Exactly 2 by 2 equal 512px cells, no borders, no labels. In each cell the SAME small rounded living desert thorn bush, olive green leaves, fine brown branches, viewed from an elevated isometric camera (30 degrees down), warm light from upper left, grounded at the same position with identical silhouette and branches. Sparse golden amber flames interwoven among living leaves: four consecutive subtle loop frames, flames gently change between cells while bush remains fixed; no smoke plume or large glow, no ground tile, no scenery, no people. Each bush fits inside the central 300x300 of its cell, with root ground contact at cell x256 y390; ample fully transparent margins. Detailed painterly realism for Age of Empires II DE-like scenery, crisp small-scale silhouette, restrained saturated fire, no blue, no text, no watermark. Original asset, not copied game art. This is a sprite sheet for actual conversion, not a presentation mockup.

Actual output dimensions, unlike the requested dimensions, are recorded by the extraction manifest. The original output is preserved unchanged.
