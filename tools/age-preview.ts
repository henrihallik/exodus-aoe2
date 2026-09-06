// Optional preview adapter: uses an unmodified age-of-rms checkout in .tools.
import { parseRms } from '../.tools/age-of-rms/src/parser/parser';
import { buildLanguageIndex } from '../.tools/age-of-rms/src/parser/language';
import { validate } from '../.tools/age-of-rms/src/parser/validate';
import { generatePreview } from '../.tools/age-of-rms/src/preview/generator';
import { createTerrainPalette } from '../.tools/age-of-rms/src/preview/render/palette';
import { buildTerrainBitmap } from '../.tools/age-of-rms/src/preview/render/terrainBitmap';
import { createBitmapCanvas, drawPreview } from '../.tools/age-of-rms/src/preview/render/drawPreview';
import { fitViewport } from '../.tools/age-of-rms/src/preview/render/projection';

(window as any).renderMap = (source: string, language: any, gameConstants: any, seed: number, preserveDecimalPositions = false) => {
  const parse = parseRms(source, language);
  const diagnostics = [...parse.diagnostics, ...validate(parse, { language, gameConstants })];
  // 0.4.1 rounds percent arguments to whole percentages during S0, even
  // though DE land_position accepts floats. Keep raw diagnostics; for the
  // explicitly labelled compatibility run, bypass ONLY that coercion via
  // a cloned reference definition. Original tool sources remain untouched.
  const previewLanguage = structuredClone(language);
  if (preserveDecimalPositions) {
    previewLanguage.attributes.find((a: any) => a.name === 'land_position').arguments
      .forEach((a: any) => { a.type = 'string'; });
  }
  const result = generatePreview(parseRms(source, previewLanguage), {
    language: buildLanguageIndex(previewLanguage), constants: gameConstants.constants,
  }, { playerCount: 2, mapSize: 'Tiny', teams: [0,0,0,0,0,0,0,0] },
  { seed, collectSnapshots: true });
  const snapshot = result.snapshots!.at(-1)!;
  const terrain = createBitmapCanvas(buildTerrainBitmap(snapshot, createTerrainPalette(gameConstants.constants, 'game')));
  const canvas = document.querySelector('canvas')!;
  drawPreview(canvas.getContext('2d')!, fitViewport(result.dim, canvas.width, canvas.height, 24),
    { base: {result, snapshot, terrain}, highlight: null, selection: null });
  return { seed, preserveDecimalPositions, dim: result.dim, diagnostics, notes: result.notes,
    failureMarks: result.failureMarks, reports: result.reports,
    players: result.players, objects: result.objects, resourceTotals: result.resourceTotals };
};
