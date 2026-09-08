/* Execute actual XS with mocked documented APIs. NOT an AoE2 emulator. */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'../src/exodus.xs'),'utf8');
const layout=JSON.parse(fs.readFileSync(path.join(__dirname,'../docs/layout.json'),'utf8'));
const kinds={gold:66,stone:102,berries:59,sheep:594,boar:48,deer:65,acacia:1063,
  bush:1360,gate:1323,torch:499,wall:117,relic:285,fish:458,mountain:1048,rock:623,flowers:334};

test('presentation upgrade preserves the complete 0.1.0 authored gameplay layout',()=>{
  const copy=structuredClone(layout);delete copy.version;
  const digest=require('node:crypto').createHash('sha256').update(JSON.stringify(copy)).digest('hex');
  assert.equal(digest,'4fa292471633552f4724a26d53ea2ec14ebf45a98cc89bf904b89eca65385342');
});

test('numeric cue IDs preserve every global audio filename and reset after flush',()=>{
  for(const name of ['bush','manna','wind','parting','horn','jericho','open','warning','final_warning','flood']) {
    const w=world();w.value(`exCue("exodus_${name}"); exFlushCue(100);`);
    assert.equal(w.sounds.at(-1).name,`exodus_${name}`);
    assert.equal(w.value('exPendingCue'),0);assert.equal(w.value('exPendingPriority'),0);
  }
});

function translate(xs) {
  return xs.replace(/\/\*[\s\S]*?\*\//g,'').replace(/\/\/[^\n]*/g,'')
    .replace(/rule\s+(\w+)\s+active\s+minInterval\s+\d+\s+maxInterval\s+\d+\s*\{/g,'function $1() {')
    .replace(/\b(?:void|int|float|bool|vector|string)\s+(\w+)\s*\(/g,'function $1(')
    .replace(/([,(]\s*)(?:int|float|bool|vector|string)\s+(\w+)/g,'$1$2')
    .replace(/\bconst\s+(?:int|float|bool|vector|string)\s+/g,'const ')
    .replace(/\b(?:int|float|bool|vector|string)\s+(\w+)/g,'let $1')
    .replace(/for\s*\(\s*(\w+)\s*=\s*([^;]+);\s*<\s*([^)]*)\)/g,'for (let $1 = $2; $1 < $3; $1++)');
}

// Native xsGetNumPlayers excludes Gaia; a standard 1v1 returns 2.
function world({spawn=true,sound=true,players=2,width=120,height=120,objectFirst=false,gaiaQueryEmpty=true}={}) {
  const arrays=new Map(),units=new Map(),messages=[],sounds=[],removed=[],damage=[],effects=[],moods=[],timers=[];
  let nextArray=0,nextUnit=1,now=0,disabled=false,scans=0,deny=()=>false;
  function add(object,x,y,owner=0,klass=911,hp=100,garrison=-1) {
    const id=nextUnit++;units.set(id,{id,object,x,y,z:0,owner,klass,hp,garrison,food:object===59?125:0});return id;
  }
  function landmarks(){for(const o of layout.objects)add(kinds[o.kind],o.x+.5,o.y+.5);}
  if(spawn)landmarks();
  function createArray(n,v){const id=nextArray++;arrays.set(id,Array(n).fill(v));return id;}
  const api={
    cSetAttribute:0,cUnitSizeX:3,cUnitSizeY:4,cObstructionType:78,cBlockageClass:79,
    cSelectionEffect:80,cStandingGraphic:71,cColorMoodDefault:0,cColorMoodDesert:4,
    cColorMoodEvening:6,cColorMoodMisty:13,
    floor:Math.floor,xsCeilToInt:Math.ceil,
    vector:(x,y,z)=>({x,y,z}),xsVectorSet:(x,y,z)=>({x,y,z}),
    xsVectorGetX:p=>p.x,xsVectorGetY:p=>p.y,
    xsArrayCreateInt:createArray,
    xsArrayGetInt:(id,i)=>{assert.ok(arrays.has(id));assert.ok(i>=0&&i<arrays.get(id).length);return arrays.get(id)[i];},
    xsArraySetInt:(id,i,v)=>{assert.ok(arrays.has(id));assert.ok(Number.isInteger(i)&&i>=0&&i<arrays.get(id).length);arrays.get(id)[i]=v;},
    xsArrayGetSize:id=>{assert.ok(arrays.has(id));return arrays.get(id).length;},
    xsGetPlayerUnitIds:(owner,kind,id=-1)=>{
      if(objectFirst)[owner,kind]=[kind,owner];
      scans++;if(!arrays.has(id))id=nextArray++;
      arrays.set(id,[...units.values()].filter(u=>!(gaiaQueryEmpty&&owner===0)&&u.owner===owner&&(u.object===kind||u.klass===kind)).map(u=>u.id));return id;
    },
    xsGetGameTime:()=>now,xsGetMapWidth:()=>width,xsGetMapHeight:()=>height,xsGetNumPlayers:()=>players,
    xsDoesUnitExist:id=>units.has(id),xsGetUnitOwner:id=>units.get(id).owner,xsGetUnitObjectId:id=>units.get(id).object,
    xsGetUnitPosition:id=>{const u=units.get(id);assert.ok(u);return {x:u.x,y:u.y,z:u.z};},
    xsGetUnitHitpoints:id=>units.get(id).hp,xsGetGarrisonedInUnitId:id=>units.get(id).garrison,
    xsSetUnitHitpoints:(id,hp)=>{const u=units.get(id);assert.ok(u.owner===1||u.owner===2);damage.push({id,before:u.hp,hp,time:now});u.hp=hp;if(hp<=0)units.delete(id);return true;},
    xsSetUnitAttributeHeld:(id,food)=>{assert.equal(units.get(id).owner,0);units.get(id).food=food;return true;},
    xsCreateUnit:(object,owner,p,foundation=true,play=true,collision=true)=>{
      assert.equal(owner,0,'events must never create player units');
      if(deny({object,owner,p,collision,now}))return -1;
      if(collision&&[...units.values()].some(u=>Math.abs(u.x-p.x)<.8&&Math.abs(u.y-p.y)<.8))return -1;
      const made=add(object,p.x,p.y,owner);units.get(made).z=p.z;return made;
    },
    xsRemoveUnit:id=>{assert.equal(units.get(id).owner,0,'only tracked Gaia scenery/new manna may be removed');removed.push(id);return units.delete(id);},
    xsSetUnitPosition:(id,p)=>{assert.equal(units.get(id).owner,0);Object.assign(units.get(id),p);return true;},
    xsGetObjectAttribute:()=>12345,
    xsEffectAmount:(effect,object,attribute,value,player)=>{assert.equal(player,0);assert.ok([1323,1635,304,1308].includes(object));effects.push({effect,object,attribute,value,player});},
    xsGetColorMood:()=>4,xsSetColorMood:(mood,seconds)=>{moods.push({mood,seconds,time:now});return true;},
    xsChatData:message=>messages.push({message,time:now}),
    xsPlaySound:(name,player,position,angle,unit,global)=>{sounds.push({name,time:now,player,position,angle,unit,global});return sound;},
    xsDisplayTimer:(id,message,seconds)=>{timers.push({id,message,seconds,time:now});return true;},
    xsClearTimer:id=>{timers.push({id,clear:true,time:now});},
    xsDisableSelf:()=>{disabled=true;}
  };
  const context=vm.createContext(api);vm.runInContext(translate(source),context);vm.runInContext('main()',context);
  return {units,arrays,messages,sounds,removed,damage,effects,moods,timers,add,landmarks,
    tick(t){now=t;if(!disabled)vm.runInContext('exTick()',context);},
    run(a,b){for(let t=a;t<=b;t++)this.tick(t);},
    value:code=>vm.runInContext(code,context),
    block(fn){deny=fn;},get disabled(){return disabled;},get scans(){return scans;},
    count(object){return [...units.values()].filter(u=>u.object===object&&u.owner===0).length;}
  };
}

test('phase boundaries and repeating schedule are exact for ten cycles',()=>{
  const w=world();
  for(let c=0;c<10;c++)for(const [offset,phase] of [[0,1],[59,1],[60,2],[79,2],[80,3],[329,3],[330,4],[419,4],[420,5],[459,5],[460,0],[1079,0]])
    assert.equal(w.value(`exSeaPhase(${660+c*1080+offset})`),phase);
  assert.equal(w.value('exSeaPhase(659)'),0);
});

test('initialization accepts two non-Gaia players and rejects other player counts',()=>{
  const duel=world({players:2});duel.tick(1);
  assert.equal(duel.value('exReady'),true);
  for(const players of [0,1,3,4,5,6,7,8]) {
    const invalid=world({players});invalid.run(1,10);
    assert.equal(invalid.value('exReady'),false);
    assert.equal(invalid.disabled,true);
  }
  assert.equal(fs.readFileSync(path.join(__dirname,'../dist/Exodus/resources/_common/xs/exodus.xs'),'utf8'),source);
});

test('initialization waits; missing, duplicate, or wrong-player landmarks fail visibly',()=>{
  const late=world({spawn:false});late.tick(1);assert.equal(late.value('exReady'),false);late.landmarks();late.tick(2);assert.equal(late.value('exReady'),true);
  const missing=world();const id=[...missing.units.values()].find(u=>u.object===1323).id;missing.units.delete(id);missing.run(1,10);assert.equal(missing.disabled,true);assert.match(missing.messages.at(-1).message,/INITIALIZATION FAILED/);
  const dup=world();const gates=[...dup.units.values()].filter(u=>u.object===1323);gates[1].x=gates[0].x;gates[1].y=gates[0].y;dup.run(1,10);assert.equal(dup.disabled,true);
  const wrong=world({players:5});wrong.run(1,10);assert.equal(wrong.disabled,true);
});

test('diagnostic build reports every initialization rejection with actual values, only at final retry',()=>{
  const cases=[
    [world({width:144}),/Map=144x120; expected 120x120/],
    [world({height:144}),/Map=120x144; expected 120x120/],
    [world({players:3}),/Players=3; expected 2 excluding Gaia/]
  ];
  for(const [object,pattern] of [[1323,/sea barriers \(1323\)=39; expected 40/],[117,/walls \(117\)=63; expected 64/],[1360,/shrubs \(1360\)=1; expected 2/]]) {
    const w=world();w.units.delete([...w.units.values()].find(u=>u.object===object).id);cases.push([w,pattern]);
  }
  const misplaced=world();const gate=[...misplaced.units.values()].find(u=>u.object===1323);gate.x=54.5;
  cases.push([misplaced,/Landmark object=1323; ref=\d+; x=54.5; y=.*outside authored slots/]);
  const duplicate=world();const gates=[...duplicate.units.values()].filter(u=>u.object===1323);
  gates[1].x=gates[0].x;gates[1].y=gates[0].y;
  cases.push([duplicate,/Duplicate landmark object=1323; slot=\d+; refs=\d+,\d+/]);
  for(const [w,pattern] of cases) {
    w.run(1,9);
    assert.equal(w.messages.length,1);
    assert.match(w.messages[0].message,/EXODUS XS BUILD: 2026-09-08 refs-01/);
    w.run(10,20);
    assert.equal(w.messages.filter(m=>m.message.includes('INITIALIZATION FAILED')).length,1);assert.equal(w.disabled,true);
    assert.match(w.messages.at(-1).message,/INITIALIZATION FAILED \[refs-01\]/);
    assert.match(w.messages.at(-1).message,pattern);
    assert.equal(w.value('exReady'),false);
    assert.equal(w.sounds.length,0);assert.equal(w.damage.length,0);
  }
});

test('reference registration succeeds when all Gaia queries are empty; allocates no retry arrays',()=>{
  const w=world();const arrays=w.arrays.size;w.tick(1);
  assert.equal(w.value('exReady'),true);
  assert.match(w.messages[1].message,/Registered 40 sea barriers, 64 walls and 2 shrubs/);
  for(const [name,object,size] of [['exGates',1323,40],['exWalls',117,64],['exShrubs',1360,2]]) {
    const ids=w.arrays.get(w.value(name));assert.equal(ids.length,size);assert.equal(new Set(ids).size,size);
    for(const id of ids){assert.equal(w.units.get(id).owner,0);assert.equal(w.units.get(id).object,object);}
  }
  // The one additional allocation is the normal player-unit query, not a Gaia query.
  assert.equal(w.arrays.size,arrays+1);
});

test('landmark scans reject moved, duplicated, missing and non-Gaia walls/shrubs',()=>{
  for(const object of [117,1360])for(const mode of ['moved','duplicate','owned','extra']) {
    const w=world();const list=[...w.units.values()].filter(u=>u.object===object);
    if(mode==='moved'){list[0].x=30.5;list[0].y=20.5;}
    if(mode==='duplicate'){list[1].x=list[0].x;list[1].y=list[0].y;}
    if(mode==='owned')list[0].owner=1;
    if(mode==='extra')w.add(object,30.5,20.5);
    const before=JSON.stringify([...w.units]);const arrays=w.arrays.size;
    w.run(1,20);
    assert.equal(w.disabled,true);assert.equal(w.value('exReady'),false);
    assert.equal(w.arrays.size,arrays);assert.equal(JSON.stringify([...w.units]),before);
  }
});

test('reference ceiling fails visibly for out-of-range landmarks without creating replacements',()=>{
  const w=world();const gate=[...w.units.values()].find(u=>u.object===1323);
  w.units.delete(gate.id);gate.id=5000;w.units.set(gate.id,gate);
  const before=JSON.stringify([...w.units]);w.run(1,20);
  assert.equal(w.disabled,true);assert.match(w.messages.at(-1).message,/barriers \(1323\)=39.*higher refs not checked/);
  assert.equal(JSON.stringify([...w.units]),before);
});

test('successful initialization emits build identifier once without failure diagnostics',()=>{
  const w=world();w.run(1,20);
  assert.equal(w.messages.filter(m=>m.message.includes('XS BUILD:')).length,1);
  assert.equal(w.messages.filter(m=>m.message.includes('INITIALIZATION FAILED')).length,0);
  assert.equal(w.value('exReady'),true);
});

test('sea parts in mirrored stages, opens at 12:20, warns 90s, restores at 18:00',()=>{
  const w=world();w.tick(1);assert.equal(w.count(1323),40);
  w.tick(660);assert.equal(w.timers.at(-1).seconds,80);
  w.tick(720);assert.equal(w.count(1323),40);w.tick(729);assert.equal(w.count(1323),40);
  w.tick(730);assert.equal(w.count(1323),20);w.tick(739);assert.equal(w.count(1323),20);
  w.tick(740);assert.equal(w.count(1323),0);w.tick(990);assert.equal(w.timers.at(-1).seconds,90);
  w.tick(1079);assert.equal(w.count(1323),0);w.tick(1080);assert.equal(w.count(1323),40);
  w.tick(1820);assert.equal(w.count(1323),0);
});

test('flood is precisely bounded; same damage for both players, never Gaia, ships, buildings or garrisoned units',()=>{
  const w=world();w.tick(1);w.tick(740);
  const a=w.add(83,57.5,50.5,1,904,100),b=w.add(83,62.5,69.5,2,904,100);
  const protectedIds=[w.add(83,54.999,50,1,904),w.add(83,65,50,1,904),w.add(83,60,43.999,1,904),w.add(83,60,76,2,904),
    w.add(13,60,50,1,921),w.add(539,60,51,2,922),w.add(545,60,52,1,920),w.add(17,60,53,2,902),
    w.add(70,60,54,1,903),w.add(83,60,55,0,904),w.add(83,60,56,1,904,100,999)];
  w.tick(990);w.tick(1079);assert.equal(w.damage.length,0);
  w.tick(1080);assert.equal(w.units.get(a).hp,94);assert.equal(w.units.get(b).hp,94);
  w.tick(1081);assert.equal(w.units.get(a).hp,88);assert.equal(w.units.get(b).hp,88);
  for(const id of protectedIds)assert.equal(w.units.get(id).hp,100);
});

test('relic monks and packed/unpacked siege are not immune to the flood',()=>{
  const w=world();w.tick(1);
  const ids=[943,951,954,955,947,923,924,936,958].map((c,i)=>w.add(200+i,60,48+i,1,c,100));
  w.tick(2);for(const id of ids)assert.equal(w.units.get(id).hp,94);
});

test('duplicate rule execution cannot double damage, rewards, or notifications',()=>{
  const w=world();w.tick(1);const id=w.add(83,57.5,50.5,1,904,100);w.tick(2);
  const snapshot=[w.units.get(id).hp,w.messages.length,w.scans,w.sounds.length];w.tick(2);
  assert.deepEqual([w.units.get(id).hp,w.messages.length,w.scans,w.sounds.length],snapshot);
});

test('occupied barrier cells are not forcibly filled; retreat leaves a cell that safely restores',()=>{
  const w=world();w.tick(1);w.tick(740);const id=w.add(83,55.5,58.5,1,904,100);
  w.tick(1080);assert.equal(w.count(1323),39);assert.equal(w.units.get(id).hp,94);
  w.units.get(id).y=43.5;w.tick(1081);assert.equal(w.count(1323),40);assert.equal(w.units.get(id).hp,94);
});

test('persistent barrier creation failure fails open and suspends damage, not silently asymmetric',()=>{
  const w=world();w.tick(1);w.tick(740);w.block(({object})=>object===1323);w.run(1080,1199);
  assert.equal(w.value('exFailure'),true);assert.equal(w.count(1323),0);assert.match(w.messages.at(-1).message,/INVALID/);
  const id=w.add(83,60,50,1,904,100);w.tick(1200);assert.equal(w.units.get(id).hp,100);
});

test('either player can ignite either bush once, without consuming it or granting stats',()=>{
  const w=world();w.tick(1);w.add(448,46.5,35.5,2,947);w.tick(2);
  assert.equal(w.value('xsArrayGetInt(exBushLit,0)'),1);assert.equal(w.count(1360),2);assert.equal(w.count(304),1);
  w.run(3,12);assert.equal(w.count(304),1);assert.equal(w.messages.filter(m=>m.message.includes('BUSH BURNS')).length,1);
  w.add(83,73.5,84.5,1,904);w.tick(13);assert.equal(w.count(304),2);
});

test('manna stages and commits equal 225-food gardens twice, without touching existing food',()=>{
  const w=world();w.tick(1);const original=[...w.units.values()].filter(u=>u.object===59).map(u=>u.id);
  w.tick(420);assert.equal(w.count(59),18);let added=[...w.units.values()].filter(u=>u.object===59&&!original.includes(u.id));
  assert.equal(added.length,6);assert.equal(added.filter(u=>u.y<60).reduce((n,u)=>n+u.food,0),225);
  assert.equal(added.filter(u=>u.y>60).reduce((n,u)=>n+u.food,0),225);
  w.tick(421);assert.equal(w.count(59),18);w.tick(1500);assert.equal(w.count(59),24);w.tick(1501);assert.equal(w.count(59),24);
  for(const id of original)assert.equal(w.units.get(id).food,125);
});

test('a blocked manna garden rolls BOTH banks back, retries, then cancels with no net food',()=>{
  const w=world();w.tick(1);w.block(({object,p})=>object===59&&p.y>60);
  w.run(420,449);assert.equal(w.count(59),12);assert.equal(w.value('xsArrayGetInt(exMannaDone,0)'),-1);
  assert.match(w.messages.at(-1).message,/cancelled for BOTH/);
  w.block(()=>false);w.tick(450);assert.equal(w.count(59),12);
});

test('seven horns, then only original Gaia Jericho walls fall; player walls survive',()=>{
  const w=world();w.tick(1);const playerWall=w.add(117,8.5,56.5,1,927),unrelated=w.add(117,30.5,20.5,0,927);
  w.run(1440,1446);assert.equal(w.sounds.filter(s=>s.name==='exodus_horn').length,7);assert.equal(w.count(117),65);
  w.tick(1447);assert.equal(w.count(117),1);assert.ok(w.units.has(playerWall));assert.ok(w.units.has(unrelated));
  w.tick(1450);assert.equal(w.sounds.filter(s=>s.name==='exodus_horn').length,7);
});

test('audio availability never changes simulation; particle arrays remain bounded over multiple cycles',()=>{
  const a=world({sound:true}),b=world({sound:false});a.run(1,2300);b.run(1,2300);
  assert.equal(a.arrays.size,13);assert.equal(b.arrays.size,13);assert.ok(a.count(1308)<=48);
  assert.equal(a.count(1635),12);assert.ok(a.count(304)<=4);
  assert.deepEqual([...a.units.values()],[...b.units.values()]);assert.deepEqual(a.messages,b.messages);
});

test('long-running cycles recreate no duplicate sea gates or runaway effects',()=>{
  const w=world();w.tick(1);for(let c=0;c<20;c++)for(const offset of [660,720,730,740,990,1080,1120])w.tick(offset+c*1080);
  assert.equal(w.count(1323),40);assert.equal(w.count(1635),12);assert.ok(w.count(1308)<=48);
  assert.equal(w.arrays.size,13);assert.equal(w.value('exFailure'),false);
});

test('30s and 10s safety reminders fire once per cycle; late resume emits only urgent reminder',()=>{
  const w=world();w.tick(1);w.run(990,1080);
  assert.equal(w.messages.filter(m=>m.message.includes('30 SECONDS OR LESS')).length,1);
  assert.equal(w.messages.filter(m=>m.message.includes('10 SECONDS OR LESS')).length,1);
  assert.equal(w.sounds.filter(s=>s.name==='exodus_final_warning').length,1);
  w.run(2070,2160);
  assert.equal(w.messages.filter(m=>m.message.includes('10 SECONDS OR LESS')).length,2);
  const late=world();late.tick(1);late.tick(1075);
  assert.equal(late.messages.filter(m=>m.message.includes('30 SECONDS OR LESS')).length,0);
  assert.equal(late.sounds.filter(s=>s.global).at(-1).name,'exodus_final_warning');
  assert.equal(late.timers.at(-1).seconds,5);
});

test('warning audio takes precedence over same-tick discoveries and has a unique open motif',()=>{
  const w=world();w.tick(1);w.add(83,46.5,35.5,1,904);w.tick(990);
  const played=w.sounds.filter(s=>s.time===990&&s.global);
  assert.equal(played.length,1);assert.equal(played[0].name,'exodus_warning');
  assert.equal(w.value('xsArrayGetInt(exBushLit,0)'),1);
  const opened=world();opened.tick(1);opened.tick(740);
  assert.equal(opened.sounds.filter(s=>s.global).at(-1).name,'exodus_open');
  assert.equal(opened.sounds.filter(s=>s.name==='exodus_horn').length,0);
});

test('positional ambience is paired, bounded, absent during warnings and never client-dependent',()=>{
  const w=world();w.run(1,1150);
  const local=w.sounds.filter(s=>!s.global);
  assert.ok(local.length>0);
  for(let i=0;i<local.length;i+=2){
    const a=local[i],b=local[i+1];assert.equal(a.time,b.time);assert.equal(a.player,-1);
    assert.equal(a.position.x+b.position.x,120);assert.equal(a.position.y+b.position.y,120);
    if(i>=2)assert.ok(a.time-local[i-2].time>=30);
    assert.ok(a.time<660||(a.time>=740&&a.time<990)||a.time>=1120);
  }
  for(let t=990;t<=1080;t++)assert.equal(local.filter(s=>s.time===t).length,0);
});

test('decorative discovery cannot mask an imminent public cue; fire ambience needs both sources',()=>{
  const w=world();w.tick(1);w.add(83,46.5,35.5,1,904);w.tick(655);
  assert.equal(w.sounds.filter(s=>s.time===655&&s.global).length,0);
  w.run(656,740);assert.equal(w.sounds.filter(s=>s.name==='exodus_crackle').length,0);
  w.add(83,73.5,84.5,2,904);w.run(741,850);
  assert.ok(w.sounds.some(s=>s.name==='exodus_crackle'));
});

test('same-phase resume repairs countdown without replaying opening, reward or horn',()=>{
  const w=world();w.tick(1);w.tick(740);const before=w.sounds.filter(s=>s.global).length;
  w.tick(900);assert.equal(w.timers.at(-1).seconds,180);
  assert.equal(w.sounds.filter(s=>s.global).length,before);
  assert.equal(w.count(59),18);w.tick(901);assert.equal(w.count(59),18);
});

test('missing cosmetic fire is repaired once; player-owned fire is never moved or deleted',()=>{
  const w=world();w.tick(1);w.add(83,46.5,35.5,1,904);w.tick(2);
  const original=w.value('xsArrayGetInt(exBushFires,0)');w.units.delete(original);w.tick(3);
  const repaired=w.value('xsArrayGetInt(exBushFires,0)');assert.notEqual(repaired,original);
  w.tick(4);assert.equal(w.value('xsArrayGetInt(exBushFires,0)'),repaired);
  w.units.get(repaired).owner=1;w.tick(5);assert.ok(w.units.has(repaired));
  assert.equal(w.messages.filter(m=>m.message.includes('BUSH BURNS')).length,1);
});

test('curtain easing preserves endpoints and rotational pairing; transition mist stays outside seabed',()=>{
  const w=world();w.tick(1);w.tick(720);
  const first=[...w.units.values()].filter(u=>u.object===1635)[0];assert.equal(first.x,58.5);
  w.tick(730);assert.equal(first.x,56);w.tick(740);assert.equal(first.x,53.5);
  for(let i=0;i<12;i+=2){const a=w.units.get(w.value(`xsArrayGetInt(exCurtains,${i})`));
    const b=w.units.get(w.value(`xsArrayGetInt(exCurtains,${i+1})`));assert.equal(a.x+b.x,120);assert.equal(a.y+b.y,120);}
  w.tick(1080);
  const low=[...w.units.values()].filter(u=>u.object===1308&&u.z===.5);assert.equal(low.length,2);
  for(const u of low)assert.ok(u.x<55||u.x>=65);
});
