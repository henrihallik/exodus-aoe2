import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import struct
import unittest
import wave
import zipfile
from collections import Counter, deque

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("build",ROOT/"tools/build.py")
build=importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class MapContract(unittest.TestCase):
    def test_xs_declarations_require_initializers_and_avoid_global_strings(self):
        build.validate_xs_source((ROOT/'src/exodus.xs').read_text())
        for bad in ('string pending;', 'void f() { int x; }', 'string pending = "";'):
            with self.assertRaises(ValueError):
                build.validate_xs_source(bad)
        build.validate_xs_source('int cue = 0;\nvoid f() { string local = "safe"; }')

    def test_scripts_are_ascii_in_source_and_release(self):
        xs=(ROOT/'src/exodus.xs').read_bytes()
        self.assertTrue(xs.isascii())
        self.assertTrue(self.rms.isascii())
        with zipfile.ZipFile(ROOT/f'dist/Exodus-{build.VERSION}.zip') as z:
            for name in z.namelist():
                if name.endswith(('.xs','.rms')):
                    self.assertTrue(z.read(name).isascii(),name)

    def test_build_rejects_unicode_and_control_characters(self):
        for bad in ('\u2014','\u201c','\u00e9','\ufeff','\x00','\x1a'):
            with self.assertRaises(ValueError):
                build.ascii_script('void main() { /* '+bad+' */ }','test.xs')
        self.assertEqual(build.ascii_script('string s = "SAFE - %d";\r\n','test.xs'),b'string s = "SAFE - %d";\r\n')

    @classmethod
    def setUpClass(cls):
        cls.layout=build.make_layout()
        cls.grid=cls.layout["terrain"]
        cls.objects=cls.layout["objects"]
        cls.rms=(ROOT/"dist/Exodus/resources/_common/random-map-scripts/Exodus.rms").read_text()

    def distances(self,start,closed=True,forbid_sea=False):
        blocked={(o["x"],o["y"]) for o in self.objects if o["kind"] in {"gold","stone","berries","acacia","palm","wall","rock","mountain","bush"} or (closed and o["kind"]=="gate")}
        distance={start:0};queue=deque([start])
        while queue:
            x,y=queue.popleft()
            for xx,yy in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
                if not(0<=xx<120 and 0<=yy<120) or (xx,yy) in distance or (xx,yy) in blocked:
                    continue
                t=self.grid[yy][xx]
                if t in build.FORESTS or t==1 or (forbid_sea and 55<=xx<65 and 44<=yy<76):
                    continue
                distance[xx,yy]=distance[x,y]+1;queue.append((xx,yy))
        return distance

    def test_exact_rotational_symmetry_of_terrain_and_every_object(self):
        self.assertEqual(self.grid,[row[::-1] for row in self.grid[::-1]])
        objects={(o['kind'],o['x'],o['y']) for o in self.objects}
        self.assertEqual(len(objects),len(self.objects))
        for kind,x,y in objects:
            self.assertIn((kind,119-x,119-y),objects)

    def test_emitted_rms_reconstructs_every_authored_tile(self):
        grid=[[14]*120 for _ in range(120)]
        rx=r"create_land \{ terrain_type T(\d+) base_size (\d+) land_percent 0 land_position ([\d.]+) ([\d.]+)([^}]*)\}"
        count=0
        for t,r,px,py,_ in re.findall(rx,self.rms):
            t,r=int(t),int(r);x,y=math.floor(float(px)*1.2),math.floor(float(py)*1.2)
            for yy in range(y-r,y+r+1):
                for xx in range(x-r,x+r+1):
                    self.assertTrue(0<=xx<120 and 0<=yy<120)
                    grid[yy][xx]=t
            count+=1
        self.assertGreater(count,100)
        self.assertEqual(grid,self.grid)
        self.assertLess(len(self.rms.encode()),300000)

    def test_resource_counts_and_landmark_contract(self):
        c=Counter(o['kind'] for o in self.objects)
        self.assertEqual({k:c[k] for k in ['gold','stone','berries','sheep','boar','deer','relic','fish','gate','wall','bush']},
                         dict(gold=30,stone=18,berries=12,sheep=16,boar=4,deer=8,relic=4,fish=8,gate=40,wall=64,bush=2))
        gates={(o['x'],o['y']) for o in self.objects if o['kind']=='gate'}
        self.assertEqual(gates,{(x,y) for y in range(58,62) for x in range(55,65)})

    def test_both_coastal_roads_connect_without_using_any_seabed(self):
        d=self.distances(build.STARTS[0],forbid_sea=True)
        self.assertIn(build.STARTS[1],d)
        self.assertIn((3,60),d)
        self.assertIn((116,59),d)
        # Even with either side of the map removed there is another route.
        for x in (3,116):
            self.assertIn((x,50),d);self.assertIn((x,70),d)

    def test_open_sea_is_a_meaningful_shortcut_with_clear_egress(self):
        closed=self.distances(build.STARTS[0],True)
        opened=self.distances(build.STARTS[0],False)
        self.assertLess(opened[build.STARTS[1]],closed[build.STARTS[1]]-30)
        self.assertNotIn((59,59),closed)
        self.assertIn((59,59),opened)
        for x in range(55,65):
            self.assertIn((x,45),closed)
            self.assertIn((x,74),closed)

    def test_start_resources_have_accessible_perimeters_and_equal_distances(self):
        a,b=[self.distances(start) for start in build.STARTS]
        # Mines and berry groups are gathered from their outside. Requiring
        # immediate access to every buried interior tile would reject ordinary
        # compact deposits. Check every connected same-kind cluster perimeter.
        remaining={(o['kind'],o['x'],o['y']) for o in self.objects if o['role'] in {'start','expansion'} and o['y']<60}
        while remaining:
            kind,x,y=remaining.pop();cluster={(x,y)};queue=[(x,y)]
            while queue:
                xx,yy=queue.pop()
                for p in [(xx-1,yy),(xx+1,yy),(xx,yy-1),(xx,yy+1)]:
                    key=(kind,*p)
                    if key in remaining:
                        remaining.remove(key);cluster.add(p);queue.append(p)
            perimeter={p for x,y in cluster for p in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)] if p not in cluster}
            da=min(a.get(p,99999) for p in perimeter)
            db=min(b.get(build.rotate(*p),99999) for p in perimeter)
            self.assertLess(da,60,(kind,cluster,da))
            self.assertEqual(da,db,(kind,cluster))

    def test_tc_footprints_and_manna_gardens_are_clear(self):
        occupied={(o['x'],o['y']) for o in self.objects}
        for x,y in build.STARTS:
            for yy in range(y-1,y+3):
                for xx in range(x-1,x+3):
                    self.assertNotIn((xx,yy),occupied)
                    self.assertNotIn(self.grid[yy][xx],build.FORESTS|{1,4})
        for x,y in self.layout['manna']:
            for xx,yy in [(x,y),build.rotate(x,y)]:
                self.assertNotIn((xx,yy),occupied)
                self.assertNotIn(self.grid[yy][xx],build.FORESTS|{1,4})

    def test_no_hazard_outside_exact_shallows_and_no_player_modifications(self):
        for y in range(44,76):
            for x in range(55,65):
                self.assertEqual(self.grid[y][x],4)
        self.assertIn('override_map_size 120',self.rms)
        self.assertIn('create_object VILLAGER { set_place_for_every_player',self.rms)
        self.assertNotRegex(self.rms,r'create_object VILLAGER \{[^}]*number_of_objects')
        self.assertNotIn('terrain_state',self.rms)
        for line in self.rms.splitlines():
            if line.startswith(('effect_amount','effect_percent')):
                self.assertIn(' EX_GAIA_SET ',line)

    def test_archive_scripts_audio_and_documentation_match_sources(self):
        archive=ROOT/f'dist/Exodus-{build.VERSION}.zip'
        with zipfile.ZipFile(archive) as z:
            self.assertEqual(z.read('Exodus/resources/_common/xs/exodus.xs'),(ROOT/'src/exodus.xs').read_bytes())
            self.assertEqual(z.read('Exodus/resources/_common/random-map-scripts/Exodus.rms'),self.rms.encode())
            self.assertFalse(any('.reference/' in name or '.tools/' in name or '__pycache__' in name for name in z.namelist()))
            self.assertEqual(sum(name.endswith('.wem') for name in z.namelist()),12)
        expected=(ROOT/'dist/SHA256SUMS').read_text().split()[0]
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(),expected)


class AudioContract(unittest.TestCase):
    def test_ambient_and_event_headroom_and_xs_cue_coverage(self):
        xs=(ROOT/'src/exodus.xs').read_text()
        used=set(re.findall(r'"(exodus_[a-z_]+)"',xs))
        packaged={p.stem for p in (ROOT/'audio/converted').glob('*.wem')}
        self.assertEqual(used,packaged)
        for p in (ROOT/'audio').glob('*.wav'):
            with wave.open(str(p),'rb') as wav:
                pcm=wav.readframes(wav.getnframes())
                if p.stem in ('exodus_shore','exodus_crackle'):
                    self.assertEqual(wav.getnframes(),96000)
            samples=struct.unpack('<'+'h'*(len(pcm)//2),pcm)
            ceiling=.08 if p.stem in ('exodus_shore','exodus_crackle') else .35
            self.assertLessEqual(max(abs(s) for s in samples),math.ceil(ceiling*32767))

    def test_art_study_is_separate_and_no_graphics_override_ships(self):
        with zipfile.ZipFile(ROOT/f'dist/Exodus-{build.VERSION}.zip') as game:
            self.assertFalse(any('/graphics/' in n or n.endswith(('.dat','.smx','.sld')) for n in game.namelist()))
        with zipfile.ZipFile(ROOT/f'dist/Exodus-Art-Study-{build.VERSION}.zip') as art:
            self.assertEqual(sum(n.endswith('.png') for n in art.namelist()),5)
            self.assertFalse(any('/resources/' in n for n in art.namelist()))
        manifest=json.loads((ROOT/'assets/frames/manifest.json').read_text())
        self.assertEqual(len(manifest['frames']),4)
        for f in manifest['frames']:
            self.assertGreater(f['empty'],0);self.assertGreater(f['visible'],0)

    def test_wem_chunks_decode_to_exact_wav_pcm_with_headroom(self):
        files=list((ROOT/'audio').glob('*.wav'));self.assertEqual(len(files),12)
        for f in files:
            with wave.open(str(f),'rb') as wav:
                self.assertEqual((wav.getnchannels(),wav.getsampwidth(),wav.getframerate()),(1,2,48000))
                pcm=wav.readframes(wav.getnframes())
            wem=(ROOT/'audio/converted'/f.with_suffix('.wem').name).read_bytes()
            self.assertEqual(wem[:4],b'RIFF');self.assertEqual(wem[8:12],b'WAVE')
            self.assertEqual(struct.unpack_from('<I',wem,4)[0],len(wem)-8)
            chunks={};pos=12
            while pos<len(wem):
                size=struct.unpack_from('<I',wem,pos+4)[0]
                chunks[wem[pos:pos+4]]=wem[pos+8:pos+8+size]
                pos+=8+size+(size%2)
            self.assertEqual(pos,len(wem));self.assertEqual(chunks[b'data'],pcm)
            self.assertEqual(struct.unpack('<HHIIHHHHI',chunks[b'fmt ']),(0xFFFE,1,48000,96000,2,16,6,0,0x4101))
            samples=struct.unpack('<'+'h'*(len(pcm)//2),pcm)
            self.assertLessEqual(max(abs(s) for s in samples),16384)
            self.assertGreater(max(abs(s) for s in samples),1000)


if __name__=='__main__':
    unittest.main()
