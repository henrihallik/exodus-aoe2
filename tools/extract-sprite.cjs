// Mechanical 2x2 frame extraction only; no new painted/generated content.
// Uses existing optional preview browser tooling; does not install Blender.
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const puppeteer=require(process.env.PUPPETEER_MODULE||'puppeteer');
(async()=>{
  const browser=await puppeteer.launch({headless:'shell',executablePath:process.env.CHROME_PATH,args:['--no-sandbox']});
  try {
    const page=await browser.newPage();
    const data='data:image/png;base64,'+fs.readFileSync(path.join(root,'assets/source/burning-bush-ai-v1.png')).toString('base64');
    const frames=await page.evaluate(async data=>{
      const img=new Image();img.src=data;await img.decode();
      const w=img.width/2,h=img.height/2;if(!Number.isInteger(w)||!Number.isInteger(h))throw Error('Expected 2x2 grid');
      return Array.from({length:4},(_,i)=>{
        const canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;
        const ctx=canvas.getContext('2d');ctx.drawImage(img,(i%2)*w,Math.floor(i/2)*h,w,h,0,0,w,h);
        const pixels=ctx.getImageData(0,0,w,h).data;let empty=0,visible=0;
        for(let j=3;j<pixels.length;j+=4){if(pixels[j]===0)empty++;else visible++;}
        if(!empty||!visible)throw Error('Invalid alpha/content');
        return {i,w,h,empty,visible,png:canvas.toDataURL('image/png').split(',')[1]};
      });
    },data);
    fs.mkdirSync(path.join(root,'assets/frames'),{recursive:true});
    for(const {png,...meta} of frames){fs.writeFileSync(path.join(root,`assets/frames/bush-${meta.i}.png`),Buffer.from(png,'base64'));console.log(meta);}
    fs.writeFileSync(path.join(root,'assets/frames/manifest.json'),JSON.stringify({status:'unbound AI frame study; not a game-ready sprite',frames:frames.map(({png,...m})=>m)},null,2)+'\n');
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
