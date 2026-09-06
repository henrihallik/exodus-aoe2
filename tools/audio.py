#!/usr/bin/env python3
"""Original synthesized event sound design; no recordings or sampled voices.

Outputs 48 kHz mono PCM WAV masters and Wwise PCM WEM containers. The small
WEM format adapter follows the MIT-licensed WEMConverter layout (notice in
THIRD_PARTY.md) and is independently checked against vgmstream's Wwise reader.
Container validation does NOT certify AoE2's in-game audio-loader behavior.
"""
from array import array
from pathlib import Path
import math
import random
import struct
import sys
import wave

ROOT = Path(__file__).resolve().parents[1]
RATE = 48000
CUES = {"exodus_horn": 0.92, "exodus_wind": 7.0, "exodus_parting": 8.0,
        "exodus_warning": 4.0, "exodus_flood": 7.0, "exodus_bush": 3.5,
        "exodus_manna": 4.0}


def envelope(t, duration, attack=.04, release=.3):
    return max(0., min(1., t/attack, (duration-t)/release))


def horn(t, duration=.92, fundamental=174.61):
    # Breath, a slightly bending fundamental, open harmonics, no modern siren.
    phase = 2*math.pi*(fundamental*t - 1.6*(1-math.exp(-9*t)))
    tone = sum(math.sin(phase*n)/n**1.25 for n in range(1,7))
    return .34*envelope(t,duration,.06,.25)*tone


def synthesize(name):
    duration = CUES[name]
    rng = random.Random(610 + list(CUES).index(name))
    samples = []
    low = 0.
    mid = 0.
    for i in range(round(duration*RATE)):
        t = i/RATE
        white = rng.uniform(-1,1)
        low = .996*low + .004*white
        mid = .91*mid + .09*white
        env = envelope(t,duration,.12,.8)
        if name == "exodus_horn":
            value = horn(t) + .015*mid*env
        elif name == "exodus_warning":
            local = t % 1.25
            value = horn(local,.92,146.83) if local < .92 else 0
            value += .025*math.sin(2*math.pi*55*t)*env
        elif name == "exodus_manna":
            value = 0.
            for delay,note in [(.0,392),(.45,440),(.9,523.25),(1.35,587.33)]:
                tt=t-delay
                if tt>=0:
                    value += .12*math.exp(-2.1*tt)*math.sin(2*math.pi*note*tt)*min(1,tt/.02)
            value *= env
        elif name == "exodus_bush":
            crackle = white*.22 if rng.random() < .0015 else 0
            value = env*(.20*mid + 1.0*low + crackle + .06*math.sin(2*math.pi*220*t))
        else:
            swell = math.sin(math.pi*t/duration)**1.2
            pulse = .7 + .3*math.sin(2*math.pi*.31*t)
            value = env*swell*(1.8*low + .35*mid*pulse)
            if name in ("exodus_flood","exodus_parting"):
                value += env*.075*math.sin(2*math.pi*(43*t + 2.5*math.sin(.4*t)))
            if name == "exodus_parting":
                for note in (110,164.81,220):
                    value += env*swell*.035*math.sin(2*math.pi*note*t)
        samples.append(value)
    # Gentle paired echoes add scale, with bounded peak headroom (-6 dBFS).
    for delay,gain in [(int(.13*RATE),.20),(int(.29*RATE),.11)]:
        for i in range(len(samples)-1,delay-1,-1):
            samples[i] += samples[i-delay]*gain
    peak=max(abs(x) for x in samples) or 1.
    scale=min(1., .5/peak)
    pcm=array("h",(round(x*scale*32767) for x in samples))
    if sys.byteorder != "little":
        pcm.byteswap()
    return pcm.tobytes()


def wem_bytes(pcm):
    # Wwise PCMEX, 24-byte fmt (not a renamed ordinary WAV).
    # The packed channel config 0x4101 = mono, standard layout, front center.
    fmt=struct.pack("<HHIIHHHHI",0xFFFE,1,RATE,RATE*2,2,16,6,0,0x4101)
    chunks=b"fmt "+struct.pack("<I",len(fmt))+fmt
    chunks+=b"JUNK"+struct.pack("<I",4)+b"\0"*4
    chunks+=b"data"+struct.pack("<I",len(pcm))+pcm
    return b"RIFF"+struct.pack("<I",len(chunks)+4)+b"WAVE"+chunks


def build_audio():
    folder=ROOT/"audio"
    (folder/"converted").mkdir(parents=True,exist_ok=True)
    for name in CUES:
        pcm=synthesize(name)
        with wave.open(str(folder/(name+".wav")),"wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(RATE)
            wav.writeframes(pcm)
        (folder/"converted"/(name+".wem")).write_bytes(wem_bytes(pcm))
    print(f"Built {len(CUES)} original WAV masters and PCM WEM containers.")


if __name__ == "__main__":
    build_audio()
