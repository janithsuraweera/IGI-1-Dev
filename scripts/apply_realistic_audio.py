"""
Project I.G.I. - Ultra-Realistic Audio Synthesis & Injection Suite
Synthesizes professional, military-grade sound effects:
- Supersonic sniper cracks with sub-bass punch & echoing mountain reverb
- 7.62mm Kalashnikov gunfire loops & release tails
- Heavy magnum concussive hand-cannon blasts
- 12-gauge close-quarters shotgun blasts
- Bone-crunching visceral flesh impacts
- High-velocity steel ricochets & concrete pulverization
- Combat casualty groans & heavy body falls
- Concussive warzone explosions
"""

import io
import struct
import numpy as np
from pathlib import Path
from igipy.core.formats.res import RES
from igipy.core.formats.wav import WAV, WAVHeader

BASE_DIR = Path(__file__).resolve().parent.parent

def pcm_to_ilsf(pcm_data: np.ndarray, framerate: int = 44100, channels: int = 1) -> bytes:
    """Converts 16-bit PCM numpy array into InnerLoop ILSF WAV byte container (sound_pack=1)."""
    raw_pcm = pcm_data.tobytes()
    num_samples = len(raw_pcm) // 2
    hdr = WAVHeader(
        signature=b'ILSF',
        sound_pack=1,
        sample_width=16,
        channels=channels,
        unknown=0,
        framerate=framerate,
        sample_count=num_samples
    )
    wav_obj = WAV(header=hdr, content=raw_pcm)
    stream, _ = wav_obj.model_dump_stream()
    return stream.getvalue()

def synth_sniper(sr=44100, dur=1.8):
    """High-caliber SVD Dragunov 7.62x54mmR supersonic shot."""
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    noise = np.random.normal(0, 1, len(t))
    # 1. Supersonic crack (sharp shockwave, 0 - 20ms)
    crack = noise * np.exp(-t / 0.012) * 1.0
    # 2. Concussive sub-bass punch (75 Hz down to 38 Hz)
    freq_thump = 75.0 * np.exp(-t / 0.09) + 38.0
    thump = np.sin(2.0 * np.pi * np.cumsum(freq_thump) / sr) * np.exp(-t / 0.10) * 1.1
    # 3. Muzzle blast chamber resonance (450 Hz)
    blast = np.sin(2.0 * np.pi * 420.0 * t) * np.exp(-t / 0.04) * 0.7
    # 4. Steel bolt clack
    bolt_mask = (t >= 0.02) & (t <= 0.06)
    bolt = np.zeros_like(t)
    bolt[bolt_mask] = np.sin(2 * np.pi * 2600 * (t[bolt_mask] - 0.02)) * np.exp(-(t[bolt_mask] - 0.02) / 0.008) * 0.4
    # 5. Mountain reverberation multi-tap delay
    reverb = np.zeros_like(t)
    delays = [0.07, 0.13, 0.21, 0.34, 0.50, 0.72, 1.02, 1.40]
    amps   = [0.50, 0.38, 0.28, 0.20, 0.14, 0.09, 0.05, 0.02]
    for d, a in zip(delays, amps):
        idx = int(d * sr)
        if idx < len(t):
            sub_t = t[:len(t)-idx]
            reverb[idx:] += np.random.normal(0, 1, len(sub_t)) * np.exp(-sub_t / 0.16) * a
    mix = crack + thump + blast + bolt + reverb * 0.65
    mix = np.tanh(mix * 1.4)
    mix = mix / np.max(np.abs(mix)) * 0.96
    return (mix * 32767).astype(np.int16)

def synth_ak47_loop(sr=44100, dur=0.10):
    """Full-auto AK-47 continuous firing cycle (600 RPM)."""
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    noise = np.random.normal(0, 1, len(t))
    crack = noise * np.exp(-t / 0.008) * 1.0
    thump = np.sin(2 * np.pi * (85 * np.exp(-t / 0.05) + 45) * t) * np.exp(-t / 0.06) * 0.95
    bolt = np.sin(2 * np.pi * 1800 * t) * np.exp(-t / 0.015) * 0.5
    mix = crack + thump + bolt
    mix = np.tanh(mix * 1.3)
    mix = mix / np.max(np.abs(mix)) * 0.95
    return (mix * 32767).astype(np.int16)

def synth_ak47_tail(sr=44100, dur=1.2):
    """AK-47 release echo / reverberation tail."""
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    noise = np.random.normal(0, 1, len(t))
    crack = noise * np.exp(-t / 0.012) * 0.9
    thump = np.sin(2 * np.pi * 60 * t) * np.exp(-t / 0.08) * 0.8
    reverb = np.zeros_like(t)
    for d, a in zip([0.06, 0.12, 0.20, 0.32, 0.50, 0.75], [0.45, 0.32, 0.22, 0.15, 0.08, 0.03]):
        idx = int(d * sr)
        if idx < len(t):
            sub_t = t[:len(t)-idx]
            reverb[idx:] += np.random.normal(0, 1, len(sub_t)) * np.exp(-sub_t / 0.14) * a
    mix = crack + thump + reverb * 0.6
    mix = np.tanh(mix * 1.3)
    mix = mix / np.max(np.abs(mix)) * 0.95
    return (mix * 32767).astype(np.int16)

def synth_handcannon(sr=44100, dur=1.3):
    """Heavy .44 Magnum / Desert Eagle concussive blast."""
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    noise = np.random.normal(0, 1, len(t))
    crack = noise * np.exp(-t / 0.01) * 1.1
    thump = np.sin(2 * np.pi * (60 * np.exp(-t / 0.1) + 35) * t) * np.exp(-t / 0.12) * 1.2
    reverb = np.zeros_like(t)
    for d, a in zip([0.08, 0.16, 0.28, 0.45, 0.70], [0.40, 0.28, 0.18, 0.10, 0.04]):
        idx = int(d * sr)
        if idx < len(t):
            sub_t = t[:len(t)-idx]
            reverb[idx:] += np.random.normal(0, 1, len(sub_t)) * np.exp(-sub_t / 0.15) * a
    mix = crack + thump + reverb * 0.5
    mix = np.tanh(mix * 1.4)
    mix = mix / np.max(np.abs(mix)) * 0.96
    return (mix * 32767).astype(np.int16)

def synth_shotgun(sr=44100, dur=1.2):
    """12-Gauge close-quarters combat shotgun blast."""
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    noise = np.random.normal(0, 1, len(t))
    blast = noise * np.exp(-t / 0.02) * 1.2
    thump = np.sin(2 * np.pi * 55 * t) * np.exp(-t / 0.09) * 1.1
    pump = np.sin(2 * np.pi * 1400 * t) * np.exp(-t / 0.025) * 0.4
    reverb = np.zeros_like(t)
    for d, a in zip([0.09, 0.18, 0.30, 0.48], [0.35, 0.24, 0.14, 0.06]):
        idx = int(d * sr)
        if idx < len(t):
            sub_t = t[:len(t)-idx]
            reverb[idx:] += np.random.normal(0, 1, len(sub_t)) * np.exp(-sub_t / 0.14) * a
    mix = blast + thump + pump + reverb * 0.5
    mix = np.tanh(mix * 1.3)
    mix = mix / np.max(np.abs(mix)) * 0.96
    return (mix * 32767).astype(np.int16)

def synth_flesh(seed: int, sr=22050, dur=0.30):
    """Visceral bone-crunching, meaty bullet flesh impact."""
    np.random.seed(seed)
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    noise = np.random.normal(0, 1, len(t))
    # Sharp supersonic entry slap
    slap = noise * np.exp(-t / 0.007) * 0.9
    # Bone crunch burst
    crunch_f = 900.0 + (seed * 80) % 300
    crunch = np.sin(2 * np.pi * crunch_f * t) * np.exp(-t / 0.02) * 0.75
    # Heavy body tissue displacement thud
    thud_f = 130.0 * np.exp(-t / 0.04) + 60.0
    thud = np.sin(2.0 * np.pi * np.cumsum(thud_f) / sr) * np.exp(-t / 0.05) * 1.1
    # Wet cavitation squelch
    squelch = np.sin(2 * np.pi * 320 * t) * np.exp(-t / 0.035) * noise * 0.4
    mix = slap + crunch + thud + squelch
    mix = np.tanh(mix * 1.5)
    mix = mix / np.max(np.abs(mix)) * 0.95
    return (mix * 32767).astype(np.int16)

def synth_ricochet(seed: int, sr=22050, dur=0.45):
    """Supersonic whistling metallic ricochet."""
    np.random.seed(seed)
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    # Pitch slides rapidly downwards
    f_start = 3800.0 + (seed * 300) % 800
    f_end = 900.0 + (seed * 150) % 400
    freq = f_start * np.exp(-t / 0.12) + f_end
    # Flutter modulation
    flutter = np.sin(2 * np.pi * 45 * t) * 150.0
    phase = 2.0 * np.pi * np.cumsum(freq + flutter) / sr
    whine = np.sin(phase) * np.exp(-t / 0.20) * 0.85
    # Initial slap
    noise = np.random.normal(0, 1, len(t))
    slap = noise * np.exp(-t / 0.005) * 0.6
    mix = whine + slap
    mix = np.tanh(mix * 1.2)
    mix = mix / np.max(np.abs(mix)) * 0.95
    return (mix * 32767).astype(np.int16)

def synth_concrete(seed: int, sr=22050, dur=0.35):
    """Sharp pulverized concrete impact crack."""
    np.random.seed(seed)
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    noise = np.random.normal(0, 1, len(t))
    crack = noise * np.exp(-t / 0.008) * 1.0
    grit = np.sin(2 * np.pi * 1200 * t) * np.exp(-t / 0.03) * noise * 0.6
    thump = np.sin(2 * np.pi * 110 * t) * np.exp(-t / 0.04) * 0.7
    mix = crack + grit + thump
    mix = np.tanh(mix * 1.3)
    mix = mix / np.max(np.abs(mix)) * 0.95
    return (mix * 32767).astype(np.int16)

def synth_bodyfall(seed: int, sr=22050, dur=0.45):
    """Heavy tactical body drop onto terrain."""
    np.random.seed(seed)
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    noise = np.random.normal(0, 1, len(t))
    thud = np.sin(2 * np.pi * 65 * t) * np.exp(-t / 0.08) * 1.1
    rustle = noise * np.exp(-t / 0.12) * 0.5
    mix = thud + rustle
    mix = np.tanh(mix * 1.3)
    mix = mix / np.max(np.abs(mix)) * 0.95
    return (mix * 32767).astype(np.int16)

def synth_pain_grunt(seed: int, sr=22050, dur=0.38):
    """Combat casualty sharp intake of breath / pain grunt."""
    np.random.seed(seed)
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    f = 160.0 + (seed * 35) % 80
    vocal = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.14)
    vocal += np.sin(2 * np.pi * (f * 2) * t) * 0.5 * np.exp(-t / 0.12)
    noise = np.random.normal(0, 1, len(t)) * 0.3 * np.exp(-t / 0.10)
    mix = vocal + noise
    mix = np.tanh(mix * 1.4)
    mix = mix / np.max(np.abs(mix)) * 0.95
    return (mix * 32767).astype(np.int16)

def synth_explosion(seed: int, sr=22050, dur=1.8):
    """Massive concussive explosion with sub-bass seismic shockwave."""
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    noise = np.random.normal(0, 1, len(t))
    det = noise * np.exp(-t / 0.03) * 1.2
    sub_f = 40.0 * np.exp(-t / 0.3) + 25.0
    sub = np.sin(2.0 * np.pi * np.cumsum(sub_f) / sr) * np.exp(-t / 0.45) * 1.3
    rumble = noise * np.exp(-t / 0.8) * 0.7
    mix = det + sub + rumble
    mix = np.tanh(mix * 1.5)
    mix = mix / np.max(np.abs(mix)) * 0.97
    return (mix * 32767).astype(np.int16)

def apply_all_realistic_audio():
    res_path = BASE_DIR / "common" / "sounds" / "sounds.res"
    backup_path = BASE_DIR / "_backup_original" / "common" / "sounds" / "sounds.res"
    orig_data = backup_path.read_bytes()
    res_obj = RES.model_validate_stream(io.BytesIO(orig_data))

    sound_map = {
        'LOCAL:common/sounds/svddrag_shot_1.wav': pcm_to_ilsf(synth_sniper(), 44100),
        'LOCAL:common/sounds/ak47_loop.wav': pcm_to_ilsf(synth_ak47_loop(), 44100),
        'LOCAL:common/sounds/ak47_loop_e.wav': pcm_to_ilsf(synth_ak47_tail(), 44100),
        'LOCAL:common/sounds/colt_shot_1.wav': pcm_to_ilsf(synth_handcannon(), 44100),
        'LOCAL:common/sounds/deagle_shot_1.wav': pcm_to_ilsf(synth_handcannon(), 44100),
        'LOCAL:common/sounds/spas12_shot_1.wav': pcm_to_ilsf(synth_shotgun(), 44100),
        'LOCAL:common/sounds/bul_flesh_1.wav': pcm_to_ilsf(synth_flesh(1), 22050),
        'LOCAL:common/sounds/bul_flesh_2.wav': pcm_to_ilsf(synth_flesh(2), 22050),
        'LOCAL:common/sounds/bul_flesh_3.wav': pcm_to_ilsf(synth_flesh(3), 22050),
        'LOCAL:common/sounds/bul_flesh_4.wav': pcm_to_ilsf(synth_flesh(4), 22050),
        'LOCAL:common/sounds/bul_flesh_5.wav': pcm_to_ilsf(synth_flesh(5), 22050),
        'LOCAL:common/sounds/bul_concrete_1.wav': pcm_to_ilsf(synth_concrete(1), 22050),
        'LOCAL:common/sounds/bul_concrete_2.wav': pcm_to_ilsf(synth_concrete(2), 22050),
        'LOCAL:common/sounds/bul_metal_hrd_1.wav': pcm_to_ilsf(synth_ricochet(10), 22050),
        'LOCAL:common/sounds/bul_metal_hrd_2.wav': pcm_to_ilsf(synth_ricochet(20), 22050),
        'LOCAL:common/sounds/bul_metal_hrd_3.wav': pcm_to_ilsf(synth_ricochet(30), 22050),
        'LOCAL:common/sounds/riccochet_1.wav': pcm_to_ilsf(synth_ricochet(1), 22050),
        'LOCAL:common/sounds/riccochet_2.wav': pcm_to_ilsf(synth_ricochet(2), 22050),
        'LOCAL:common/sounds/riccochet_3.wav': pcm_to_ilsf(synth_ricochet(3), 22050),
        'LOCAL:common/sounds/riccochet_4.wav': pcm_to_ilsf(synth_ricochet(4), 22050),
        'LOCAL:common/sounds/riccochet_5.wav': pcm_to_ilsf(synth_ricochet(5), 22050),
        'LOCAL:common/sounds/ai_hit_01.wav': pcm_to_ilsf(synth_pain_grunt(1), 22050),
        'LOCAL:common/sounds/ai_hit_02.wav': pcm_to_ilsf(synth_pain_grunt(2), 22050),
        'LOCAL:common/sounds/ai_hit_03.wav': pcm_to_ilsf(synth_pain_grunt(3), 22050),
        'LOCAL:common/sounds/bodyfall_1.wav': pcm_to_ilsf(synth_bodyfall(1), 22050),
        'LOCAL:common/sounds/bodyfall_2.wav': pcm_to_ilsf(synth_bodyfall(2), 22050),
        'LOCAL:common/sounds/bodyfall_3.wav': pcm_to_ilsf(synth_bodyfall(3), 22050),
        'LOCAL:common/sounds/explo_01_s.wav': pcm_to_ilsf(synth_explosion(1), 22050),
        'LOCAL:common/sounds/explo_02_m.wav': pcm_to_ilsf(synth_explosion(2), 22050),
        'LOCAL:common/sounds/explo_03_l.wav': pcm_to_ilsf(synth_explosion(3), 22050),
        'LOCAL:common/sounds/explo_04_xl.wav': pcm_to_ilsf(synth_explosion(4), 22050),
    }

    updated = 0
    for name_chunk, body_chunk in res_obj.content_pairs:
        k = name_chunk.content.rstrip(b'\x00').decode('latin1')
        if k in sound_map:
            body_chunk.content = sound_map[k]
            body_chunk.header.length = len(body_chunk.content)
            body_chunk.header.offset = 16 + ((len(body_chunk.content) + 3) & ~3)
            updated += 1

    # Recalculate all chunk offsets strictly conforming to ILFF specification
    all_chunks = []
    for ca, cb in res_obj.content_pairs:
        all_chunks.extend([ca, cb])
    if res_obj.content_paths is not None:
        all_chunks.extend(res_obj.content_paths)

    for i, ch in enumerate(all_chunks):
        if i == len(all_chunks) - 1:
            ch.header.offset = 0
        else:
            ch.header.offset = 16 + ((ch.header.length + 3) & ~3)

    stream, _ = res_obj.model_dump_stream()
    raw = bytearray(stream.getvalue())
    struct.pack_into('<I', raw, 4, len(raw))

    res_path.write_bytes(raw)
    print(f"[AUDIO OVERHAUL] Successfully injected {updated} realistic military sounds into sounds.res!")
    print(f"Total archive size: {len(raw)} bytes.")

if __name__ == "__main__":
    apply_all_realistic_audio()

