"""
Project IGI 1 - Sinhala Modding Suite
This script handles:
1. Translating text resources (.res files) to Sinhala (Phonetic / Singlish)
2. Generating & encoding Sinhala Anya radio voice lines (ILSF WAV files)
3. Backup & restore utilities
"""

import os
import io
import struct
import subprocess
from pathlib import Path
from gtts import gTTS

from igipy.core.formats.res import RES, CSTRChunk
from igipy.core.formats.ilff import ChunkHeader
from igipy.core.formats.wav import WAV, WAVHeader
from igipy.core.formats.utils import adpcm

BASE_DIR = Path(__file__).resolve().parent.parent

def verify_res_file(file_path: Path):
    """Verify that the .res file conforms strictly to InnerLoop ILFF specification."""
    data = file_path.read_bytes()
    magic = data[:4]
    total_len = struct.unpack('<I', data[4:8])[0]
    assert magic == b'ILFF', f"Invalid magic in {file_path.name}"
    assert total_len == len(data), f"File length header mismatch in {file_path.name}: {total_len} vs {len(data)}"

    offset = 20
    chunks = []
    while offset < len(data):
        tag = data[offset:offset+4].decode('latin1')
        v1, v2, v3 = struct.unpack('<III', data[offset+4:offset+16])
        chunks.append((tag, v1, v2, v3))
        if v3 == 0:
            rem = data[offset+16:]
            assert len(rem) == v1, f"Last chunk length mismatch in {file_path.name}: {len(rem)} vs {v1}"
            break
        padded = (v1 + 3) & ~3
        assert v3 == 16 + padded, f"Chunk offset mismatch in {file_path.name}: {v3} vs {16+padded}"
        offset += v3
    print(f"  [VERIFY] {file_path.name}: Perfectly valid ({len(chunks)} chunks, {len(data)} bytes, last chunk offset=0)")

def update_res_strings(source_file: Path, dest_file: Path, translations: dict[str, str]):
    """Update string pairs in a .res file with strictly valid chunk offsets."""
    data = source_file.read_bytes()
    res_obj = RES.model_validate_stream(io.BytesIO(data))
    updated_count = 0

    new_pairs = []
    for name_chunk, cstr_chunk in res_obj.content_pairs:
        key = name_chunk.content.rstrip(b'\x00').decode('latin1', errors='replace')
        if key in translations:
            new_val = translations[key]
            content_bytes = new_val.encode('latin1', errors='replace') + b'\x00'
            padded_len = (len(content_bytes) + 3) & ~3
            new_header = ChunkHeader(
                fourcc=b'CSTR',
                length=len(content_bytes),
                alignment=4,
                offset=16 + padded_len
            )
            new_cstr = CSTRChunk(header=new_header, content=content_bytes)
            new_pairs.append((name_chunk, new_cstr))
            updated_count += 1
        else:
            new_pairs.append((name_chunk, cstr_chunk))

    res_obj.content_pairs = new_pairs

    # Collect all chunks in order
    all_chunks = []
    for chunk_a, chunk_b in res_obj.content_pairs:
        all_chunks.extend([chunk_a, chunk_b])
    if res_obj.content_paths is not None:
        all_chunks.extend(res_obj.content_paths)

    # Set exact offsets: all chunks get 16 + padded_len, and the LAST chunk gets 0
    for i, ch in enumerate(all_chunks):
        if i == len(all_chunks) - 1:
            ch.header.offset = 0
        else:
            ch.header.offset = 16 + ((ch.header.length + 3) & ~3)

    stream, _ = res_obj.model_dump_stream()
    raw = bytearray(stream.getvalue())
    struct.pack_into('<I', raw, 4, len(raw))

    dest_file.write_bytes(raw)
    print(f"[{dest_file.name}] Updated {updated_count} strings.")
    verify_res_file(dest_file)

def generate_sinhala_voice(text_si: str, out_wav_path: Path):
    """Generate Sinhala voice using gTTS, convert via ffmpeg and encode to InnerLoop ILSF."""
    temp_mp3 = out_wav_path.with_suffix('.tmp.mp3')
    temp_raw = out_wav_path.with_suffix('.tmp.raw')

    try:
        tts = gTTS(text=text_si, lang='si')
        tts.save(str(temp_mp3))

        cmd = [
            'ffmpeg', '-y', '-i', str(temp_mp3),
            '-ar', '22050', '-ac', '1', '-f', 's16le', str(temp_raw)
        ]
        subprocess.run(cmd, check=True, capture_output=True)

        pcm_data = temp_raw.read_bytes()
        encoded = adpcm.encode(pcm_data, channels=1)

        hdr = WAVHeader(
            signature=b'ILSF',
            sound_pack=2,
            sample_width=16,
            channels=1,
            unknown=0,
            framerate=22050,
            sample_count=len(pcm_data) // 2
        )
        w = WAV(header=hdr, content=encoded)
        stream, _ = w.model_dump_stream()
        out_wav_path.write_bytes(stream.getvalue())
        print(f"[VOICE] Generated Sinhala voice: {out_wav_path.name} ({len(pcm_data)//2} samples)")
    finally:
        if temp_mp3.exists():
            temp_mp3.unlink()
        if temp_raw.exists():
            temp_raw.unlink()

def apply_sinhala_translations():
    lang_dir = BASE_DIR / "language" / "english"
    backup_dir = BASE_DIR / "_backup_original" / "language" / "english"

    # 1. Menusystem translations
    menu_trans = {
        "LOCAL:english/Main Menu": "Pradhana Puvatha (Main Menu)",
        "LOCAL:english/Single Player": "Project IGI Sellam Karanna",
        "LOCAL:english/Start New Game": "Aluth Tharagayak Patanganna",
        "LOCAL:english/Load Game": "Save Kala Game Thoranna",
        "LOCAL:english/Select Mission": "Meheyuma Thoranna",
        "LOCAL:english/Configuration": "Settings (Sakasum)",
        "LOCAL:english/Quit": "Iwath Wenna (Quit)",
        "LOCAL:english/Sound Configuration": "Shabdha Sakasum (Sound Settings)",
        "LOCAL:english/Sound": "Shabdha (Sound)",
        "LOCAL:english/Graphics Configuration": "Ruupa Sakasum (Graphics Settings)",
        "LOCAL:english/Graphics": "Ruupa (Graphics)",
        "LOCAL:english/Controls": "Paalanayan (Controls)",
        "LOCAL:english/Controls Configuration": "Paalana Sakasum (Controls Settings)",
        "LOCAL:english/Invert Mouse": "Mouse Invert Karanna",
        "LOCAL:english/Mouse Sensitivity": "Mouse Sanwedi Thawaya",
        "LOCAL:english/Reset to Default": "Mulika Thatthwayata Pathkaranna",
        "LOCAL:english/Select a key or button": "Key ekak ho button ekak obanna",
        "LOCAL:english/Select Mission to play": "Sellam kireemata Meheyuma thoranna",
        "LOCAL:english/Press ESC to abort": "Iwath weemata ESC obanna",
        "LOCAL:english/Difficulty": "Amāru Mattama (Difficulty)",
        "LOCAL:english/Easy": "Pahasu (Easy)",
        "LOCAL:english/Medium": "Madhyastha (Medium)",
        "LOCAL:english/Hard": "Amāru (Hard)",
    }
    update_res_strings(backup_dir / "menusystem.res", lang_dir / "menusystem.res", menu_trans)

    # 2. Computer text translations
    comp_trans = {
        "MAP": "Sithiyama (Map)",
        "OBJECTIVES": "Meheyum Ilakka",
        "LOG": "Warthawa (Log)",
        "INITIALIZING": "ARAMBHA WEMIN PAVATHI...",
        "CONNECTING": "SAMBANDHA WEMIN PAVATHI...",
        "DOWNLOADING": "DATA BAGA GANIMIN PAVATHI...",
    }
    update_res_strings(backup_dir / "computer.res", lang_dir / "computer.res", comp_trans)

    # 3. Mission Names and Descriptions (All 14 Levels)
    missions_trans = {
        "LOCAL:english/Mission 1 Name": "Meheyuma 01: Trainyard",
        "LOCAL:english/Mission 1 Desc": "Josef Priboi soya ganna. Dumriya anganaye athi truck eka horaagena pala yanna.",
        "LOCAL:english/Mission 2 Name": "Meheyuma 02: SAM Base",
        "LOCAL:english/Mission 2 Desc": "Guwan arakshaka SAM ksipanisa vinasa kara extract point ekata yanna.",
        "LOCAL:english/Mission 3 Name": "Meheyuma 03: Military Airbase",
        "LOCAL:english/Mission 3 Desc": "Josef Priboi beragena, jet yanyayakin pala yanna.",
        "LOCAL:english/Mission 4 Name": "Meheyuma 04: GOD (Village)",
        "LOCAL:english/Mission 4 Desc": "Gammanaya araksha kara Priboi wa mudawaganeemata sahaya wenna.",
        "LOCAL:english/Mission 5 Name": "Meheyuma 05: Radar Base",
        "LOCAL:english/Mission 5 Desc": "Radar dome piganata virus eka athul karanna.",
        "LOCAL:english/Mission 6 Name": "Meheyuma 06: Get Priboi",
        "LOCAL:english/Mission 6 Desc": "Priboi ge gabadawa thula thiyena sakshi soya ganna.",
        "LOCAL:english/Mission 7 Name": "Meheyuma 07: Border Crossing",
        "LOCAL:english/Mission 7 Desc": "Simawa haraha yana truck rathayata nagina thuru alarm eka wadinna ida thiyanna epa.",
        "LOCAL:english/Mission 8 Name": "Meheyuma 08: Re-Supply",
        "LOCAL:english/Mission 8 Desc": "Camp eken bera vi homing beacon eka sam sawikara pala yanna.",
        "LOCAL:english/Mission 9 Name": "Meheyuma 09: Missile Trainyard",
        "LOCAL:english/Mission 9 Desc": "Arakshaka vyuhaya binda gena dumriyata godawenna.",
        "LOCAL:english/Mission 10 Name": "Meheyuma 10: Defend Priboi",
        "LOCAL:english/Mission 10 Desc": "Abandoned gammanaye usama godanagillata vi Priboi araksha karanna.",
        "LOCAL:english/Mission 11 Name": "Meheyuma 11: Eagle's Nest 1",
        "LOCAL:english/Mission 11 Desc": "Sniper rifle eka soya cable car eka pawanwanna.",
        "LOCAL:english/Mission 12 Name": "Meheyuma 12: Eagle's Nest 2",
        "LOCAL:english/Mission 12 Desc": "Ekk soya maranna saha paramaanu boma akriyakaranna.",
        "LOCAL:english/Mission 13 Name": "Meheyuma 13: Nuclear Facility",
        "LOCAL:english/Mission 13 Desc": "Paramaanu arakshaka seemawa binda gena factory eka thulin athul wenna.",
        "LOCAL:english/Mission 14 Name": "Meheyuma 14: The Final Reckoning",
        "LOCAL:english/Mission 14 Desc": "Ekk maranna saha paramaanu bomaya samupurna washayen nathi karanna.",
    }
    update_res_strings(backup_dir / "missions.res", lang_dir / "missions.res", missions_trans)

    # 4. Objectives (All Levels)
    obj_trans = {
        "OBJECTIVE": "MEHEYUM ILAKKAYA",
        "COMPLETE": "SAMPURNAI",
        "INCOMPLETE": "ASAMPURNAI",
        "FAILED": "PARAJITHAI!",
        "OBJ_1_COMPLETE": "1 wana Ilakkaya Sampurnai.",
        "OBJ_2_COMPLETE": "2 wana Ilakkaya Sampurnai.",
        "OBJ_3_COMPLETE": "3 wana Ilakkaya Sampurnai.",
        "OBJ_4_COMPLETE": "4 wana Ilakkaya Sampurnai.",
        "OBJ_5_COMPLETE": "5 wana Ilakkaya Sampurnai.",
        "OBJ_6_COMPLETE": "6 wana Ilakkaya Sampurnai.",
        "OBJ_7_COMPLETE": "7 wana Ilakkaya Sampurnai.",
        "OBJ_8_COMPLETE": "8 wana Ilakkaya Sampurnai.",
        "OBJ_9_COMPLETE": "9 wana Ilakkaya Sampurnai.",
        "OBJ_1_FAILED": "1 wana Ilakkaya Asarthakai!",
        "OBJ_2_FAILED": "2 wana Ilakkaya Asarthakai!",
        "OBJ_3_FAILED": "3 wana Ilakkaya Asarthakai!",
        "OBJ_1_INCOMPLETE": "1 wana Ilakkaya Asampurnai.",
        "OBJ_2_INCOMPLETE": "2 wana Ilakkaya Asampurnai.",
        "OBJ_3_INCOMPLETE": "3 wana Ilakkaya Asampurnai.",

        "M1_OBJ1": "Pradhana dwaraya langa athi truck rathaya horaagena pala yanna.",
        "M2_OBJ1": "Gabadawen C4 boma soya ganna.",
        "M2_OBJ2": "SAM launchers matha C4 boma sawikaranna.",
        "M2_OBJ3": "Extraction point ekata gaman karanna.",
        "M3_OBJ1": "Arakshaka godanagilla thulin Josef Priboi soya beraganna.",
        "M3_OBJ2": "Josef Priboi extraction point ekata arakshithawa aragena yanna.",
        "M3_OBJ3": "Flight logs pariksha kara Josef ge aluth sthanaya soya ganna.",
        "M3_OBJ4": "Jet yanyaya pähära gena pala yanna.",
        "M4_OBJ1": "Gammanaya araksha kara water tower ekata naginna.",
        "M4_OBJ2": "Josef nidahas karaganna thuru mituru kandayamata arakshawa sapayanna.",
        "M5_OBJ1": "Radar dome keycard eka soya ganna.",
        "M5_OBJ2": "Radar terminal ekata virus eka athul karanna.",
        "M5_OBJ3": "Extraction kalapaya araksha karanna.",
        "M6_OBJ1": "Main gabadawen wedibheth soya ganna.",
        "M6_OBJ2": "Electric fence eka nawathweemata generator eka off karanna.",
        "M6_OBJ3": "Fuel dump ekata wedibheth sawikaranna.",
        "M6_OBJ4": "Filing cabinets pariksha kara sakshi soya ganna.",
        "M7_OBJ1": "Simawa thulin athul wenna.",
        "M7_OBJ2": "Truck rathayata nagina thuru alarm eka wadinna nodenna.",
        "M7_OBJ3": "Security checkpoint eken bera yanna.",
        "M7_OBJ4": "Simawa binda athul wenna.",
        "M7_OBJ5": "Welaawa iwara weemata pera simawa pasukara yanna.",
        "M8_OBJ1": "Camp eken bera yanna.",
        "M8_OBJ2": "Tank maintenance yard ekata athul vi ammo godanagillata yanna.",
        "M8_OBJ3": "Map computer saha homing beacon soya ganna.",
        "M8_OBJ4": "Airstrike eka sadaha SAM launcher matha homing beacon sawikaranna.",
        "M8_OBJ5": "Listening post saha radar kootayata yanna.",
        "M8_OBJ6": "Extraction vehicle wetha yanna.",
        "M9_OBJ1": "Base ekata athul vi arakshaka viuhaya akriya karanna.",
        "M9_OBJ2": "Dumriyata godawenna.",
        "M9_OBJ3": "Siyalu sathuran winasha karanna.",
        "M10_OBJ1": "Gabadawen proximity mines soya ganna.",
        "M10_OBJ2": "Gammanaye usama godanagillata vi evacuation ekata sudanam wenna.",
        "M11_OBJ1": "Sniper rifle eka soya ganna.",
        "M11_OBJ2": "Generator eka on kara cable car eka sawikaranna.",
        "M11_OBJ3": "Cable car eka kriyathmaka karanna.",
        "M12_OBJ1": "Paramaanu bomaya akriya karanna, Ekk soya maranna.",
        "M13_OBJ1": "Arakshaka seemawa binda athul wenna.",
        "M13_OBJ2": "Anya saha mituru senawata kalapaya araksha karaganna.",
        "M13_OBJ3": "Generator eka on karanna.",
        "M13_OBJ4": "Storage building eke transformer eka on karanna.",
        "M13_OBJ5": "Weapons factory eke dhora arinna.",
        "M13_OBJ6": "Weapons factory eka haraha yanna.",
        "M13_OBJ7": "Alarm eka wadinne nathuwa cooling tower kotasata yanna.",
        "M13_OBJ8": "Underground complex ekata athul wenna.",
        "M14_OBJ1": "Ekk soya maranna.",
        "M14_OBJ2": "Paramaanu bomaya akriya karanna.",
    }
    update_res_strings(backup_dir / "objectives.res", lang_dir / "objectives.res", obj_trans)

    # 5. Messages (Level 1 in-game radio cues and cutscenes)
    msg_trans = {
        "M1_MSG_1": "ANYA: Pradhana dwaraya langa athi truck rathaya horaaganna.",
        "M1_MSG_2": "ANYA: Arakshaka CCTV camera walata ahuwenna epaa, Jones.",
        "M1_MSG_3": "ANYA: Alarm eka wadinna thiyanna epaa, Jones.",
        "M1_MSG_4": "ANYA: Truck eka thiyenne camp eke anith paththe garage eka athule.",
        "M1_MSG_5": "ANYA: Alarm eka wäduanaa! Arakshaka kandayam walin parissamin!",
        "M1_MSG_6": "ANYA: Mema gettuwa wahalaa aththe. Athul weemata wena margayak soyaaganna.",
        "M1_MSG_7": "ANYA: Obata weta udin anith kotasata pana gatha haka bawa penenawa.",

        "M1_CUT_01": "ANYA: Mehata ikmanin apu eka hondai. Me meheyuma godak wadagath. Target eka Josef Priboi. Oyata thiyenne eyawa beragena debriefing ekata genna ganna. Priboi thama paramaanu bomaya gana thiyena ekama sakshiya.",
        "M1_CUT_02": "JONES: Hari hari. Mata eka deyai danaganna oona, eyawa thiyenne koheda?",
        "M1_CUT_03": "ANYA: Josef wa thiyaganna inne military airbase ekaka. Ehi darunu guwan arakshawa thiyenawa. E defences disarm karanna kalin oyawa base eken poddak durin bahanna wenawa.",
        "M1_CUT_04": "JONES: Mokakda? Transport ready da mata yanna?",
        "M1_CUT_05": "ANYA: Na, oyata ethaninma transport ekak hoyaganna wenawa.",
        "M1_CUT_06": "JONES: E kiyanne mama monawa hari horakam karanna ooneda?",
        "M1_CUT_07": "ANYA: Ow hariyatama. Dumriya anganayata gihin transport ekak hoyaganna. Meka simple stages 3k:",
        "M1_CUT_08": "ANYA: 1 - Transport ekak hoyaganna. 2 - Air defences disarm karanna. 3 - Josef Priboi wa mudawa ganna.",
        "M1_CUT_09": "JONES: Mama wage kenekutath therenawa - mama karannam.",
        "M1_CUT_10": "ANYA: Danata apita thiyena hondama plan eka mekai.",
        "M1_CUT_11": "JONES: Anya, Josef wa hoyagaththe kohomada?",
        "M1_CUT_12": "ANYA: Apita Josef ge call ekak trace una. E apartment eke photos saha mobile number eka thibba.",
        "M1_CUT_13": "ANYA: E number ekata call karala location eka hoyagaththa. Airfield eka thama target eka.",
        "M1_CUT_14": "JONES: Niyamai - eya ethanama hitiyoth.",
        "M1_CUT_15": "ANYA: Oyata dumriya anganaya haraha truck ekata yanna wenawa. CCTV walata ahuwenna epa - ahu unoth camp eke okkoma oyawa wata karanawa.",
        "M1_CUT_16": "ANYA: Truck eka gawaata yanna. Eka thama oyage objective eka. Sadha nathuwa wade karanna. Dan wadata bahinna Jones!",

        "weapons/strings/Medipack": "Prathama Adhara Pettiya (Medipack)",
        "weapons/strings/Hand Grenade": "Atha Boma (Hand Grenade)",
        "weapons/strings/Proximitymine": "Bhibhumi Boma (Proximity Mine)",
        "weapons/strings/FlashBang": "Andhakara Boma (FlashBang)",
    }
    update_res_strings(backup_dir / "messages.res", lang_dir / "messages.res", msg_trans)

def apply_sinhala_voices():
    level1_sounds = BASE_DIR / "missions" / "location0" / "level1" / "sounds"
    backup_sounds = BASE_DIR / "_backup_original" / "missions" / "location0" / "level1" / "sounds"
    backup_sounds.mkdir(parents=True, exist_ok=True)

    voice_lines = {
        "m01_ing_01.wav": "ජෝන්ස්, ප්‍රධාන දොරටුව ළඟ තියෙන ට්‍රක් රථය හොරාගන්න.",
        "m01_ing_02.wav": "ආරක්ෂක කැමරා ගැන පරිස්සමෙන් ඉන්න, ජෝන්ස්.",
        "m01_ing_03.wav": "අනතුරු ඇඟවීමේ සීනුව නාද වෙන්න තියන්න එපා, ජෝන්ස්.",
        "m01_ing_04.wav": "ට්‍රක් රථය තියෙන්නේ කඳවුරේ අනික් පැත්තේ ගැරාජ් එක ඇතුළේ.",
        "m01_ing_05.wav": "අනතුරු ඇඟවීමේ සීනුව නාද වුණා! ආරක්ෂක කණ්ඩායම් වලින් පරිස්සම් වෙන්න!",
    }

    for fname, text_si in voice_lines.items():
        sound_path = level1_sounds / fname
        if sound_path.exists():
            backup_file = backup_sounds / fname
            if not backup_file.exists():
                backup_file.write_bytes(sound_path.read_bytes())
        generate_sinhala_voice(text_si, sound_path)

if __name__ == "__main__":
    print("=== Applying Sinhala Translations ===")
    apply_sinhala_translations()
    print("\n=== Applying Sinhala Anya Voices ===")
    apply_sinhala_voices()
    print("\n=== Sinhala Mod applied and verified successfully! ===")
