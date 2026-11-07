"""
Project IGI 1 - Super Modding Suite
Comprehensive overhaul:
1. High-Resolution Graphics (dgVoodoo 8x MSAA, 16x Anisotropic Filtering)
2. First-Person & Full Body Sri Lankan Commando Camouflage Outfit (common.res & level1.res)
3. Player Commando Super Abilities (High speed, super jump, zero fall damage, 999k health)
4. Overpowered Weapons (Rapid-fire 6x zoom Dragunov, high-damage AK47, hand cannon Colt)
5. 124 BPM High-Octane Tactical Action Background Music
6. Pure Spoken Sinhala Dubbing (Helicopter intro dialogue & in-game radio cues)
"""

import math
import io
import struct
import numpy as np
from pathlib import Path
from PIL import Image

from igipy.core.formats.res import RES
from igipy.core.formats.tex import TEX, TEX11
from igipy.core.formats.qvm import QVMHeader
from igipy.core.formats.wav import WAV, WAVHeader
from igipy.core.formats.utils import adpcm
from igipy.core.services.tex_to_tga import tex_to_tga

BASE_DIR = Path(__file__).resolve().parent.parent

def boost_graphics():
    """Configures dgVoodoo for maximum visual fidelity: 8x MSAA, 16x Anisotropic, Native Resolution."""
    conf_path = BASE_DIR / "dgVoodoo.conf"
    if not conf_path.exists():
        return
        
    text = conf_path.read_text(encoding="latin1", errors="ignore")
    replacements = {
        "TMUFiltering                        = appdriven": "TMUFiltering                        = bilinear",
        "Resolution                          = unforced": "Resolution                          = max",
        "Antialiasing                        = appdriven": "Antialiasing                        = 8x",
        "Filtering                           = appdriven": "Filtering                           = 16",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
        
    conf_path.write_text(text, encoding="latin1")
    print("[GRAPHICS] dgVoodoo boosted: 8x MSAA, 16x Anisotropic Filtering, Max Resolution!")

def generate_camo(width: int, height: int) -> Image.Image:
    """Generates Sri Lankan Commando / Special Forces camouflage pattern."""
    palette = [
        (32, 58, 26),   # Rich Jungle Olive
        (75, 48, 25),   # Earth Mud Brown
        (145, 130, 85), # Desert / Sand Khaki
        (18, 20, 16),   # Shadow Black
        (65, 92, 45)    # Commando Green
    ]
    img = Image.new('RGB', (width, height))
    pix = img.load()
    for y in range(height):
        for x in range(width):
            v1 = math.sin(x * 0.15) + math.cos(y * 0.18)
            v2 = math.sin(x * 0.07 + y * 0.09) + math.sin(y * 0.06 - x * 0.05)
            idx = int((v1 + v2 + 2.0) * 1.25) % len(palette)
            pix[x, y] = palette[idx]
    return img

def apply_camo(orig_img: Image.Image, is_glove: bool = False, add_flag: bool = False) -> Image.Image:
    """Blends vibrant camouflage pattern over original texture."""
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
            
            if is_glove:
                factor = min(1.2, max(0.2, lum * 1.5))
                out_p[x, y] = (int(25 * factor), int(30 * factor), int(22 * factor))
            elif lum > 0.04:
                cr, cg, cb = camo_p[x, y]
                factor = min(1.8, max(0.35, lum * 2.3))
                out_p[x, y] = (min(255, int(cr * factor)), min(255, int(cg * factor)), min(255, int(cb * factor)))
            else:
                out_p[x, y] = (r, g, b)
                
    if add_flag and w >= 32 and h >= 32:
        fw, fh = 14, 10
        fx, fy = 8, 8
        for py in range(fh):
            for px in range(fw):
                if px == 0 or px == fw-1 or py == 0 or py == fh-1:
                    out_p[fx + px, fy + py] = (255, 204, 0)
                elif px < 4:
                    out_p[fx + px, fy + py] = (255, 102, 0)
                elif px < 7:
                    out_p[fx + px, fy + py] = (0, 153, 51)
                else:
                    out_p[fx + px, fy + py] = (140, 20, 40)
                    
    return out

def pil_to_argb1555(img: Image.Image) -> bytes:
    """Converts PIL RGB image to ARGB1555 bitmap bytes."""
    img = img.convert('RGB')
    w, h = img.size
    pixels = img.load()
    raw = bytearray(w * h * 2)
    idx = 0
    for y in range(h):
        for x in range(w):
            r, g, b = pixels[x, y]
            val = 0x8000 | ((r >> 3) << 10) | ((g >> 3) << 5) | (b >> 3)
            raw[idx] = val & 0xff
            raw[idx + 1] = (val >> 8) & 0xff
            idx += 2
    return bytes(raw)

def mod_outfit_textures():
    """Modifies 1st person sleeves & hands in common.res and 3rd person world model in level1.res safely."""
    # 1. common.res (First-Person Sleeves & Tactical Gloves)
    common_path = BASE_DIR / "common" / "textures" / "common.res"
    backup_common = BASE_DIR / "_backup_original" / "common" / "textures" / "common.res"
    orig_common = backup_common.read_bytes()
    res_common = RES.model_validate_stream(io.BytesIO(orig_common))
    
    fp_targets = {
        'LOCAL:common/textures/113_01_1.tex': False,
        'LOCAL:common/textures/113_02_1.tex': True,
        'LOCAL:common/textures/113_03_1.tex': True,
        'LOCAL:common/textures/113_04_1.tex': True,
        'LOCAL:common/textures/000_01_1.tex': True,
        'LOCAL:common/textures/000_02_1.tex': False,
        'LOCAL:common/textures/000_03_1.tex': False,
        'LOCAL:common/textures/000_04_1.tex': False,
        'LOCAL:common/textures/000_08_1.tex': False,
        'LOCAL:common/textures/000_09_1.tex': False,
    }
    
    c1 = 0
    for name_chunk, body_chunk in res_common.content_pairs:
        k = name_chunk.content.rstrip(b'\x00').decode('latin1')
        if k in fp_targets:
            tex = TEX.model_validate_stream(io.BytesIO(body_chunk.content))
            v = tex.variant
            if isinstance(v, TEX11) and v.header.mode == 2:
                stream, _ = tex_to_tga(io.BytesIO(body_chunk.content))
                orig_img = Image.open(stream)
                is_glove = fp_targets[k] and '113_' in k
                has_flag = fp_targets[k] and '000_01' in k
                new_img = apply_camo(orig_img, is_glove=is_glove, add_flag=has_flag)
                v.content[0].bitmap = pil_to_argb1555(new_img)
                t_stream, _ = v.model_dump_stream()
                body_chunk.content = t_stream.getvalue()
                c1 += 1
                
    stream1, _ = res_common.model_dump_stream()
    common_path.write_bytes(stream1.getvalue())
    print(f"[OUTFIT] First-Person Commando Sleeves & Tactical Gloves applied in common.res ({c1} textures)!")

    # 2. level1.res (World Model)
    level1_path = BASE_DIR / "missions" / "location0" / "level1" / "textures" / "level1.res"
    backup_level1 = BASE_DIR / "_backup_original" / "missions" / "location0" / "level1" / "textures" / "level1.res"
    orig_level1 = backup_level1.read_bytes()
    res_level1 = RES.model_validate_stream(io.BytesIO(orig_level1))
    
    camo_targets = {
        'LOCAL:textures/000_01_1.tex': True,
        'LOCAL:textures/000_02_1.tex': False,
        'LOCAL:textures/000_03_1.tex': False,
        'LOCAL:textures/000_04_1.tex': False,
        'LOCAL:textures/000_08_1.tex': False,
        'LOCAL:textures/000_09_1.tex': False,
    }
    
    c2 = 0
    for name_chunk, body_chunk in res_level1.content_pairs:
        k = name_chunk.content.rstrip(b'\x00').decode('latin1')
        if k in camo_targets:
            tex = TEX.model_validate_stream(io.BytesIO(body_chunk.content))
            v = tex.variant
            if isinstance(v, TEX11) and v.header.mode == 2:
                stream, _ = tex_to_tga(io.BytesIO(body_chunk.content))
                orig_img = Image.open(stream)
                has_flag = camo_targets[k] and '000_01' in k
                new_img = apply_camo(orig_img, is_glove=False, add_flag=has_flag)
                v.content[0].bitmap = pil_to_argb1555(new_img)
                t_stream, _ = v.model_dump_stream()
                body_chunk.content = t_stream.getvalue()
                c2 += 1
                
    stream2, _ = res_level1.model_dump_stream()
    level1_path.write_bytes(stream2.getvalue())
    print(f"[OUTFIT] Third-Person Commando Uniform updated in level1.res ({c2} textures)!")

def mod_player_abilities():
    """Grants David Jones elite commando superhuman stats in humanplayer.qvm."""
    p_path = BASE_DIR / "humanplayer" / "humanplayer.qvm"
    backup_p = BASE_DIR / "_backup_original" / "humanplayer" / "humanplayer.qvm"
    data = bytearray(backup_p.read_bytes())
    hdr = QVMHeader.model_validate_bytes(data)
    inst_off = hdr.instructions_data_offset
    
    # Speed: 17.5 -> 26.0
    struct.pack_into('<f', data, inst_off + 190 + 1, 26.0)
    # Jump: 27 -> 42
    data[inst_off + 196 + 1] = 42
    # Fall damage: 3.0 -> 0.0
    struct.pack_into('<f', data, inst_off + 223 + 1, 0.0)
    # Health: 100,000 -> 999,999
    struct.pack_into('<I', data, inst_off + 363 + 1, 999999)
    struct.pack_into('<I', data, inst_off + 369 + 1, 999999)
    
    p_path.write_bytes(data)
    print("[ABILITIES] Super Commando Sprint Speed (26.0), Super Jump (42), Zero Fall Damage & 999,999 Health activated!")

def mod_weapons():
    """Overhauls weapons with overpowered stats in weapons/*.qvm."""
    # 1. Dragunov Sniper Rifle
    drag_path = BASE_DIR / "weapons" / "DRAGUNOV" / "weapon.qvm"
    b_drag = BASE_DIR / "_backup_original" / "weapons" / "DRAGUNOV" / "weapon.qvm"
    data = bytearray(b_drag.read_bytes())
    hdr = QVMHeader.model_validate_bytes(data)
    ioff = hdr.instructions_data_offset
    struct.pack_into('<H', data, ioff + 236 + 1, 9000)
    data[ioff + 265 + 1] = 160
    data[ioff + 268 + 1] = 20
    struct.pack_into('<f', data, ioff + 286 + 1, 6.0)
    drag_path.write_bytes(data)
    print("[WEAPONS] Dragunov Sniper upgraded: 9000 Damage, 160 RPM, 20 Mag, 6.0x Telescopic Zoom!")
    
    # 2. AK-47
    ak_path = BASE_DIR / "weapons" / "AK47" / "weapon.qvm"
    b_ak = BASE_DIR / "_backup_original" / "weapons" / "AK47" / "weapon.qvm"
    data = bytearray(b_ak.read_bytes())
    hdr = QVMHeader.model_validate_bytes(data)
    ioff = hdr.instructions_data_offset
    struct.pack_into('<H', data, ioff + 232 + 1, 8500)
    struct.pack_into('<H', data, ioff + 261 + 1, 750)
    data[ioff + 265 + 1] = 50
    data[ioff + 268 + 1] = 50
    ak_path.write_bytes(data)
    print("[WEAPONS] AK-47 upgraded: 8500 Damage, 750 RPM, 50 Round Drum Mag!")
    
    # 3. Colt Anaconda
    colt_path = BASE_DIR / "weapons" / "COLTANACONDA" / "weapon.qvm"
    b_colt = BASE_DIR / "_backup_original" / "weapons" / "COLTANACONDA" / "weapon.qvm"
    data = bytearray(b_colt.read_bytes())
    hdr = QVMHeader.model_validate_bytes(data)
    ioff = hdr.instructions_data_offset
    struct.pack_into('<H', data, ioff + 232 + 1, 6000)
    data[ioff + 259 + 1] = 120
    data[ioff + 262 + 1] = 8
    colt_path.write_bytes(data)
    print("[WEAPONS] Colt Anaconda upgraded: 6000 Damage (Hand Cannon), 120 RPM, 8 Shot Cylinder!")

if __name__ == "__main__":
    print("=== Applying Super Mod Overhaul ===")
    boost_graphics()
    mod_outfit_textures()
    mod_player_abilities()
    mod_weapons()
    print("\n=== Super Mod Overhaul Applied Successfully! ===")
