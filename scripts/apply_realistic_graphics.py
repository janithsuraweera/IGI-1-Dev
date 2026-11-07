"""
Project I.G.I. - Ultra-Realistic Graphics Overhaul Suite
Enhances all textures across:
- missions/location0/level1/textures/level1.res (Terrain, buildings, props, guards)
- common/textures/common.res (First-person weapons, tactical sleeves, gloves)
- missions/location0/common/textures/location0.res (World models, shared vehicles)

Applies:
- Micro-surface detail unsharp masking (brings out crisp concrete grain, snow crystals, metallic wear, rivets)
- High Dynamic Range local contrast & depth boost (eliminates washed-out retro haze)
- Enhanced color vibrancy & rich military tones
- dgVoodoo 2 DirectX optimization for maximum 8x MSAA, 16x Anisotropic, True 32-bit Color
"""

import io
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
from igipy.core.formats.res import RES
from igipy.core.formats.tex import TEX, TEX11
from igipy.core.services.tex_to_tga import tex_to_tga

BASE_DIR = Path(__file__).resolve().parent.parent

def pil_to_argb1555(img: Image.Image) -> bytes:
    """Converts PIL image to 16-bit ARGB1555 bitmap bytes."""
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

def enhance_image(im: Image.Image) -> Image.Image:
    """Enhance texture with micro-contrast, crisp unsharp mask, and rich depth."""
    # 1. Unsharp mask for micro-texture definition (stone grain, metal scratches, fabric weave)
    out = im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=135, threshold=2))
    # 2. Local contrast enhancement to deepen ambient occlusion and specular pop
    out = ImageEnhance.Contrast(out).enhance(1.16)
    # 3. Micro sharpness boost
    out = ImageEnhance.Sharpness(out).enhance(1.22)
    # 4. Subtle color richness
    out = ImageEnhance.Color(out).enhance(1.06)
    return out

def enhance_res_textures(res_path: Path):
    """Processes all textures in a .res archive safely preserving chunk headers."""
    orig_data = res_path.read_bytes()
    res_obj = RES.model_validate_stream(io.BytesIO(orig_data))
    count = 0

    for name_chunk, body_chunk in res_obj.content_pairs:
        try:
            tex = TEX.model_validate_stream(io.BytesIO(body_chunk.content))
            v = tex.variant
            if isinstance(v, TEX11) and hasattr(v.header, 'mode'):
                stream, _ = tex_to_tga(io.BytesIO(body_chunk.content))
                orig_img = Image.open(stream)
                new_img = enhance_image(orig_img)
                
                if v.header.mode == 2:
                    v.content[0].bitmap = pil_to_argb1555(new_img)
                elif v.header.mode == 67:
                    v.content[0].bitmap = new_img.convert('RGBA').tobytes()
                else:
                    continue
                    
                t_stream, _ = v.model_dump_stream()
                body_chunk.content = t_stream.getvalue()
                count += 1
        except Exception:
            continue

    stream, _ = res_obj.model_dump_stream()
    new_data = stream.getvalue()
    assert len(orig_data) == len(new_data), f"Length mismatch in {res_path.name}: {len(orig_data)} vs {len(new_data)}"
    res_path.write_bytes(new_data)
    print(f"[{res_path.name}] Enhanced {count} textures to ultra-realistic visual fidelity.")

def configure_dgvoodoo_realism():
    """Tunes dgVoodoo.conf for optimal modern realism: contrast, 8x MSAA, 16x Anisotropic, True 32-bit."""
    conf_path = BASE_DIR / "dgVoodoo.conf"
    if not conf_path.exists():
        return
        
    text = conf_path.read_text(encoding="latin1", errors="ignore")
    replacements = {
        "Contrast                             = 100": "Contrast                             = 112",
        "Color                                = 100": "Color                                = 106",
        "Brightness                           = 100": "Brightness                           = 100",
        "TMUFiltering                        = appdriven": "TMUFiltering                        = bilinear",
        "Resolution                          = unforced": "Resolution                          = max",
        "Antialiasing                        = appdriven": "Antialiasing                        = 8x",
        "Filtering                           = appdriven": "Filtering                           = 16",
        "DitheringEffect                     = high_quality": "DitheringEffect                     = pure32bit",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
        
    conf_path.write_text(text, encoding="latin1")
    print("[GRAPHICS] dgVoodoo configuration tuned: 112% Contrast, 106% Color, Pure 32-bit, 16x Anisotropic!")

def main():
    print("=== Applying Ultra-Realistic Graphics Overhaul ===")
    configure_dgvoodoo_realism()
    
    # 1. Level 1 textures (393 textures: terrain, buildings, vehicles, guards)
    enhance_res_textures(BASE_DIR / "missions" / "location0" / "level1" / "textures" / "level1.res")
    
    # 2. Common textures (First person weapons, hands, sleeves)
    enhance_res_textures(BASE_DIR / "common" / "textures" / "common.res")
    
    # 3. Location0 textures (World weapon models, shared environment)
    enhance_res_textures(BASE_DIR / "missions" / "location0" / "common" / "textures" / "location0.res")
    
    print("\n=== Ultra-Realistic Graphics Overhaul Completed Successfully! ===")

if __name__ == "__main__":
    main()

