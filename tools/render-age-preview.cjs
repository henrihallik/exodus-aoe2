// Optional developer check. Requires age-of-rms checkout + npm ci under .tools,
// Puppeteer (PUPPETEER_MODULE), and Chrome (CHROME_PATH).
const fs = require('node:fs');
const path = require('node:path');
const {execFileSync} = require('node:child_process');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const age = path.join(root, '.tools/age-of-rms');
const puppeteer = require(process.env.PUPPETEER_MODULE || 'puppeteer');
(async () => {
  execFileSync(path.join(age,'node_modules/.bin/esbuild'), [path.join(__dirname,'age-preview.ts'), '--bundle', '--platform=browser', '--outfile='+path.join(root,'.tools/age-preview.js')]);
  const browser = await puppeteer.launch({headless: 'shell', executablePath: process.env.CHROME_PATH, args:['--no-sandbox']});
  try {
    const page = await browser.newPage();
    await page.setViewport({width:1100,height:700,deviceScaleFactor:1});
    await page.setContent('<body style="margin:0;background:#14161a;color:#e9deca;font:16px sans-serif"><div style="padding:16px 24px">EXODUS / Age of RMS 0.4.1 · approximate initial layout · XS effects not rendered</div><canvas width="1100" height="630"></canvas></body>');
    await page.addScriptTag({path:path.join(root,'.tools/age-preview.js')});
    const source=fs.readFileSync(path.join(root,'dist/Exodus/resources/_common/random-map-scripts/Exodus.rms'),'utf8');
    const language=JSON.parse(fs.readFileSync(path.join(age,'reference/data/language.json')));
    const constants=JSON.parse(fs.readFileSync(path.join(age,'reference/data/game-constants.json')));
    const layout=JSON.parse(fs.readFileSync(path.join(root,'docs/layout.json')));
    const raw=await page.evaluate((...args)=>window.renderMap(...args),source,language,constants,1,false);
    await page.screenshot({path:path.join(root,'docs/age-of-rms-uncorrected.png')});
    await page.$eval('div', el=>el.textContent='EXODUS / Age of RMS 0.4.1 · DE decimal-position correction · approximate · no XS effects');
    const runs=[];
    for (const seed of [1,7,42]) {
      const result=await page.evaluate((...args)=>window.renderMap(...args),source,language,constants,seed,true);
      const actual=result.objects.filter(o=>o.objectRef.startsWith('EX_'))
        .map(o=>`${o.objectRef.toLowerCase().slice(3)}:${o.x}:${o.y}`).sort();
      const expected=layout.objects.map(o=>`${o.kind}:${o.x}:${o.y}`).sort();
      assert.deepEqual(actual,expected,'Every authored Gaia object must survive generation at its exact tile');
      assert.equal(result.reports.filter(r=>r.stage==='S6'&&r.failures.length).length,0);
      assert.equal(result.diagnostics.filter(d=>d.severity==='error').length,0);
      await page.screenshot({path:path.join(root,`docs/age-of-rms-seed-${seed}.png`)});
      runs.push(result);
      console.log(JSON.stringify({seed,dim:result.dim,players:result.players,objects:result.objects.length,diagnostics:result.diagnostics,failedReports:result.reports.filter(r=>r.failures.length)}));
    }
    fs.writeFileSync(path.join(root,'docs/age-of-rms-report.json'),JSON.stringify({tool:'age-of-rms',version:'0.4.1',commit:execFileSync('git',['rev-parse','HEAD'],{cwd:age,encoding:'utf8'}).trim(),raw,runs},null,2)+'\n');
    await page.goto('file://'+path.join(root,'docs/atlas.svg'));
    await page.setViewport({width:1200,height:1010,deviceScaleFactor:1});
    await page.screenshot({path:path.join(root,'docs/atlas.png')});
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});
