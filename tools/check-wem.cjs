// Independent optional decode check using official vgmstream r2117 WASM CLI.
// Download its release into .tools/vgmstream-wasm; no decoder ships in the map.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root=path.resolve(__dirname,'..');
const decoder=path.join(root,'.tools/vgmstream-wasm/vgmstream-cli.js');
const name=process.argv[2];
if (!/^exodus_[a-z]+(?:_[a-z]+)*$/.test(name||'')) throw Error('Supply an exodus cue basename');
const context={require,console,process:{...process,argv:['node',decoder,'-o','/decoded.wav','/'+name+'.wem']},
  __dirname:path.dirname(decoder),__filename:decoder,Buffer,TextDecoder,TextEncoder,
  setTimeout,clearTimeout,WebAssembly,performance,URL,fetch,
  Module:{preRun:[()=>context.FS.writeFile('/'+name+'.wem',fs.readFileSync(path.join(root,'audio/converted',name+'.wem')))],
    postRun:[()=>{
      const decoded=Buffer.from(context.FS.readFile('/decoded.wav'));
      const original=fs.readFileSync(path.join(root,'audio',name+'.wav'));
      function pcm(buffer){let i=12;while(i+8<=buffer.length){const n=buffer.readUInt32LE(i+4);if(buffer.toString('ascii',i,i+4)==='data')return buffer.subarray(i+8,i+8+n);i+=8+n+(n%2);}throw Error('Missing PCM');}
      if(!pcm(decoded).equals(pcm(original))) throw Error('Decoded PCM differs from master');
      console.log(name+': independently decoded PCM matches WAV master exactly');
    }]}};
vm.createContext(context);
vm.runInContext(fs.readFileSync(decoder,'utf8'),context,{filename:decoder});
