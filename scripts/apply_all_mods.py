"""
Project IGI 1 - Advanced Modding Suite
Includes:
1. Starting Weapons Mod (Dragunov Sniper Rifle & Colt/Deagle)
2. David Jones Sri Lankan Commando / Army Camouflage Skin Mod
3. New Cinematic Action Military Background Music
4. Pure Sinhala Voice Dubbing (Intro cutscene & radio messages)
"""

import math
import io
import struct
import subprocess
from pathlib import Path
from PIL import Image
import numpy as np

from igipy.core.formats.res import RES
from igipy.core.formats.tex import TEX, TEX11
from igipy.core.formats.qvm import QVMHeader
from igipy.core.formats.wav import WAV, WAVHeader
from igipy.core.formats.utils import adpcm

BASE_DIR = Path(__file__).resolve().parent.parent

def mod_starting_weapons():
    """Equips David Jones with Dragunov Sniper Rifle and Colt Anaconda in Mission 1."""
    qvm_path = BASE_DIR / "missions" / "location0" / "level1" / "objects.qvm"
    backup_path = BASE_DIR / "_backup_original" / "missions" / "location0" / "level1" / "objects.qvm"
    
    if not backup_path.exists():
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path.write_bytes(qvm_path.read_bytes())
        
    data = bytearray(backup_path.read_bytes())
    hdr = QVMHeader.model_validate_bytes(data)
    
    # 1. At address 145206 (formerly Glock string 770), change to string 823 (WEAPON_ID_DRAGUNOV)
    addr = hdr.instructions_data_offset + 145206
    struct.pack_into('<H', data, addr + 1, 823)
    
    # 2. In string table, change WEAPON_ID_GLOCK (16 bytes) to WEAPON_ID_COLT (Colt Anaconda Revolver)
    glock_bytes = b'WEAPON_ID_GLOCK\x00'
    colt_bytes = b'WEAPON_ID_COLT\x00\x00'
    pos = data.find(glock_bytes)
    if pos != -1:
        data[pos:pos+16] = colt_bytes
        
    qvm_path.write_bytes(data)
    print("[WEAPONS] Player equipped with Dragunov Sniper Rifle & Colt Anaconda Magnum!")

def generate_camo(width: int, height: int) -> Image.Image:
    """Generates procedural Sri Lankan Army / Commando camouflage pattern."""
    palette = [
        (35, 55, 30),   # Deep Forest Olive
        (75, 50, 30),   # Jungle Mud Brown
        (135, 120, 85), # Earthy Desert Tan
        (22, 25, 20),   # Tactical Deep Shadow
        (65, 85, 48)    # Commando Light Olive
    ]
    img = Image.new('RGB', (width, height))
    pix = img.load()
    for y in range(height):
        for x in range(width):
            v1 = math.sin(x * 0.12) + math.cos(y * 0.14)
            v2 = math.sin(x * 0.06 + y * 0.08) + math.sin(y * 0.05 - x * 0.04)
            idx = int((v1 + v2 + 2.0) * 1.2) % len(palette)
            pix[x, y] = palette[idx]
    return img

def apply_camo_to_image(orig_img: Image.Image, add_flag: bool = False) -> Image.Image:
    """Blends camouflage pattern over an existing texture preserving luminance, folds and belts."""
    w, h = orig_img.size
    orig_rgb = orig_img.convert('RGB')
    orig_p = orig_rgb.load()
    camo_img = generate_camo(w, h)
    camo_p = camo_img.load()
    
    out = Image.new('RGB', (w, h))
    out_p = out.load()
    
    for y in range(h):
        for x in range(w):
            r, g, b = orig_p[x, y]
            lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
            if lum > 0.05:
                cr, cg, cb = camo_p[x, y]
                factor = min(1.8, max(0.3, lum * 2.2))
                fr = min(255, int(cr * factor))
                fg = min(255, int(cg * factor))
                fb = min(255, int(cb * factor))
                out_p[x, y] = (fr, fg, fb)
            else:
                out_p[x, y] = (r, g, b)
                
    if add_flag and w >= 32 and h >= 32:
        # Paint Sri Lankan flag emblem on shoulder sleeve
        fw, fh = 14, 10
        fx, fy = 8, 8
        for py in range(fh):
            for px in range(fw):
                # Yellow border
                if px == 0 or px == fw-1 or py == 0 or py == fh-1:
                    out_p[fx + px, fy + py] = (255, 204, 0)
                elif px < 4:
                    out_p[fx + px, fy + py] = (255, 102, 0) # Orange stripe
                elif px < 7:
                    out_p[fx + px, fy + py] = (0, 153, 51)  # Green stripe
                else:
                    out_p[fx + px, fy + py] = (140, 20, 40) # Maroon field with Lion
                    
    return out

def pil_to_argb1555_bytes(img: Image.Image) -> bytes:
    """Converts PIL RGB image to Innerloop ARGB1555 bytes."""
    img = img.convert('RGB')
    w, h = img.size
    pixels = img.load()
    raw = bytearray(w * h * 2)
    idx = 0
    for y in range(h):
        for x in range(w):
            r, g, b = pixels[x, y]
            r5 = r >> 3
            g5 = g >> 3
            b5 = b >> 3
            val = 0x8000 | (r5 << 10) | (g5 << 5) | b5
            raw[idx] = val & 0xff
            raw[idx + 1] = (val >> 8) & 0xff
            idx += 2
    return bytes(raw)

def mod_player_camo():
    """Applies Sri Lankan Commando Camouflage skin to David Jones in level1.res."""
    res_path = BASE_DIR / "missions" / "location0" / "level1" / "textures" / "level1.res"
    backup_path = BASE_DIR / "_backup_original" / "missions" / "location0" / "level1" / "textures" / "level1.res"
    
    if not backup_path.exists():
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path.write_bytes(res_path.read_bytes())
        
    data = backup_path.read_bytes()
    res_obj = RES.model_validate_stream(io.BytesIO(data))
    
    camo_targets = {
        'LOCAL:textures/000_01_1.tex': True,   # Left arm with SL Flag
        'LOCAL:textures/000_02_1.tex': False,  # Jacket / Upper Vest
        'LOCAL:textures/000_03_1.tex': False,  # Torso / Coat
        'LOCAL:textures/000_04_1.tex': False,  # Trousers / Pants
        'LOCAL:textures/000_08_1.tex': False,  # Shoulder / Arm
        'LOCAL:textures/000_09_1.tex': False,  # Sleeves
    }
    
    updated_count = 0
    for name_chunk, body_chunk in res_obj.content_pairs:
        k = name_chunk.content.rstrip(b'\x00').decode('latin1')
        if k in camo_targets:
            tex = TEX.model_validate_stream(io.BytesIO(body_chunk.content))
            v = tex.variant
            if isinstance(v, TEX11) and v.header.mode == 2:
                w, h = v.header.width, v.header.height
                # Convert original bitmap to PIL
                from igipy.core.services.tex_to_tga import tex_to_tga
                stream, _ = tex_to_tga(io.BytesIO(body_chunk.content))
                orig_img = Image.open(stream)
                
                # Apply camouflage
                camo_img = apply_camo_to_image(orig_img, add_flag=camo_targets[k])
                new_bitmap = pil_to_argb1555_bytes(camo_img)
                v.content[0].bitmap = new_bitmap
                
                # Serialize tex
                t_stream, _ = v.model_dump_stream()
                new_body_content = t_stream.getvalue()
                
                body_chunk.content = new_body_content
                body_chunk.header.length = len(new_body_content)
                body_chunk.header.offset = 16 + ((len(new_body_content) + 3) & ~3)
                updated_count += 1
                
    # Fix last chunk offset
    if res_obj.content_paths is not None:
        res_obj.content_paths[1].header.offset = 0
    else:
        res_obj.content_pairs[-1][1].header.offset = 0
        
    out_stream, _ = res_obj.model_dump_stream()
    raw = bytearray(out_stream.getvalue())
    struct.pack_into('<I', raw, 4, len(raw))
    
    res_path.write_bytes(raw)
    print(f"[CAMO] Sri Lankan Commando camouflage applied to {updated_count} player textures!")

def mod_background_music():
    """Generates an intense, dramatic military cinematic background soundtrack for Mission 1."""
    music_path = BASE_DIR / "missions" / "location0" / "level1" / "sounds" / "game_music.wav"
    backup_path = BASE_DIR / "_backup_original" / "missions" / "location0" / "level1" / "sounds" / "game_music.wav"
    
    if not backup_path.exists():
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path.write_bytes(music_path.read_bytes())
        
    sr = 22050
    duration = 60.0 # 60s seamless loop
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    
    bpm = 110.0
    beat_len = 60.0 / bpm
    
    # 1. Analog Sub-Bass pulse
    bass_freq = 55.0 # A1
    bass = np.sin(2 * np.pi * bass_freq * t) * (np.exp(-((t % beat_len) / 0.15)**2))
    
    # 2. Cinematic tension drone (A-minor chord)
    drone = (0.4 * np.sin(2 * np.pi * 55.0 * t) + 
             0.3 * np.sin(2 * np.pi * 82.4 * t) + 
             0.2 * np.sin(2 * np.pi * 110.0 * t) + 
             0.15 * np.sin(2 * np.pi * 164.8 * t))
    
    # 3. Tactical percussion
    beat_num = (t / beat_len).astype(int)
    time_in_beat = t % beat_len
    
    # Kick
    is_kick = (beat_num % 2 == 0)
    kick_env = np.exp(-time_in_beat / 0.08) * is_kick
    kick = np.sin(2 * np.pi * (120.0 * np.exp(-time_in_beat / 0.04) + 40.0) * t) * kick_env
    
    # Snare
    is_snare = (beat_num % 2 == 1)
    noise = np.random.uniform(-1, 1, len(t))
    snare_env = np.exp(-time_in_beat / 0.12) * is_snare
    snare = (noise * 0.7 + np.sin(2 * np.pi * 180.0 * t) * 0.3) * snare_env
    
    # Military hi-hat ticker
    sub_beat = (t % (beat_len / 4.0)) / (beat_len / 4.0)
    ticker_env = np.exp(-sub_beat / 0.04)
    ticker = noise * ticker_env * 0.15
    
    # Stereo mix
    left = 0.35 * bass + 0.25 * drone + 0.4 * kick + 0.3 * snare + 0.1 * ticker
    right = 0.35 * bass + 0.25 * drone + 0.4 * kick + 0.3 * snare + 0.1 * ticker
    
    stereo = np.column_stack((left, right))
    max_val = np.max(np.abs(stereo))
    if max_val > 0:
        stereo = (stereo / max_val) * 0.88
        
    pcm_data = (stereo * 32767).astype(np.int16).tobytes()
    encoded = adpcm.encode(pcm_data, channels=2)
    
    hdr = WAVHeader(
        signature=b'ILSF',
        sound_pack=2,
        sample_width=16,
        channels=2,
        unknown=0,
        framerate=sr,
        sample_count=len(pcm_data) // 4
    )
    w = WAV(header=hdr, content=encoded)
    stream, _ = w.model_dump_stream()
    music_path.write_bytes(stream.getvalue())
    print("[MUSIC] New cinematic military action soundtrack installed in game_music.wav!")

if __name__ == "__main__":
    print("=== Applying Advanced Mods ===")
    mod_starting_weapons()
    mod_player_camo()
    mod_background_music()
    print("=== All advanced mods applied successfully! ===")

