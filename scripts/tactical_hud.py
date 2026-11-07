"""
Project I.G.I. - Tactical Companion Radar & Pure Sinhala Subtitle Suite v3.0
Sri Lankan Commando Special Operations Edition

Features:
- Pure Sinhala Unicode Subtitles & Mission Objectives (NO Singlish!)
- Floating On-Screen Display (OSD) Subtitle Bar overlay for in-game dialogues
- Interactive Radar Scope with Multi-Range Zoom (100m / 250m / 500m)
- 6 In-Game Active Tactical Hotkeys (F1 - F6) with Spoken Sinhala Comms
- Live Process Uplink Detection for IGI.exe
"""

import math
import time
import threading
import ctypes
import winsound
from pathlib import Path
import tkinter as tk
from tkinter import ttk

BASE_DIR = Path(__file__).resolve().parent.parent
AUDIO_DIR = BASE_DIR / "tactical_audio"
SOUNDS_DIR = BASE_DIR / "missions" / "location0" / "level1" / "sounds"

VK_F1 = 0x70
VK_F2 = 0x71
VK_F3 = 0x72
VK_F4 = 0x73
VK_F5 = 0x74
VK_F6 = 0x75

class FloatingSubtitleOSD:
    """Semi-transparent, borderless, always-on-top subtitle bar for the game screen."""
    def __init__(self, parent):
        self.win = tk.Toplevel(parent)
        self.win.title("IGI SINHALA SUBTITLE OSD")
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.90)
        self.win.configure(bg="#000000")

        # Position at bottom center of primary screen
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        w, h = 760, 65
        x = (sw - w) // 2
        y = sh - 110
        self.win.geometry(f"{w}x{h}+{x}+{y}")

        self.box = tk.Frame(self.win, bg="#051005", bd=2, relief="ridge")
        self.box.pack(fill="both", expand=True, padx=2, pady=2)

        self.speaker_lbl = tk.Label(
            self.box,
            text="ANYA // TACTICAL RADIO",
            font=("Consolas", 8, "bold"),
            fg="#ffcc00",
            bg="#051005"
        )
        self.speaker_lbl.pack(anchor="w", padx=10, pady=(4, 0))

        self.text_lbl = tk.Label(
            self.box,
            text="ඩේවිඩ්, සියලු සන්නිවේදන මාර්ග සක්‍රියයි. මෙහෙයුම ආරම්භ කරන්න.",
            font=("Nirmala UI", 11, "bold"),
            fg="#00ff66",
            bg="#051005",
            wraplength=730,
            justify="left"
        )
        self.text_lbl.pack(anchor="w", padx=10, pady=(2, 4))

        # Enable dragging the subtitle bar
        self.box.bind("<Button-1>", self.start_move)
        self.box.bind("<B1-Motion>", self.do_move)
        self.text_lbl.bind("<Button-1>", self.start_move)
        self.text_lbl.bind("<B1-Motion>", self.do_move)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        dx = event.x - self.x
        dy = event.y - self.y
        x = self.win.winfo_x() + dx
        y = self.win.winfo_y() + dy
        self.win.geometry(f"+{x}+{y}")

    def update_subtitle(self, speaker: str, text_sinhala: str, color="#00ff66"):
        self.speaker_lbl.configure(text=speaker)
        self.text_lbl.configure(text=text_sinhala, fg=color)

class TacticalHUD:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("IGI TACTICAL COMPANION HUD v3.0 - PURE SINHALA EDITION")
        self.root.geometry("520x820")
        self.root.resizable(False, False)
        self.root.configure(bg="#050a05")
        self.root.attributes("-topmost", True)

        self.radar_angle = 0.0
        self.radar_range_m = 250
        self.last_pressed = {}
        self.game_running = False
        self.osd = None

        self.raw_targets = [
            {"name": "COMM HQ", "rx": 65, "ry": -110, "color": "#ff3333"},
            {"name": "CONVOY", "rx": -85, "ry": 60, "color": "#ffaa00"},
            {"name": "SNIPER 1", "rx": 40, "ry": 80, "color": "#ff4444"},
            {"name": "SNIPER 2", "rx": -70, "ry": -65, "color": "#ff4444"},
            {"name": "SAM SITE", "rx": 90, "ry": 15, "color": "#ff7700"},
            {"name": "ARMORY", "rx": -25, "ry": 120, "color": "#ffff33"},
        ]

        self.radio_dialogues = [
            ("ANYA (01)", "ඩේවිඩ්, ප්‍රධාන දොරටුව අසල ඇති ට්‍රක් රථය පැහැරගෙන පලා යන්න.", SOUNDS_DIR / "m01_ing_01.wav"),
            ("ANYA (02)", "ආරක්ෂක CCTV කැමරා වලට හසු නොවන්න, ජෝන්ස්.", SOUNDS_DIR / "m01_ing_02.wav"),
            ("ANYA (03)", "අනතුරු ඇඟවීමේ සීනුව (Alarm) ක්‍රියාත්මක වීමට ඉඩ නොදෙන්න!", SOUNDS_DIR / "m01_ing_03.wav"),
            ("ANYA (04)", "ට්‍රක් රථය තිබෙන්නේ කඳවුරේ අනෙක් පස ඇති garage එක තුළයි.", SOUNDS_DIR / "m01_ing_04.wav"),
            ("ANYA (05)", "අවවාදයයි: කඳවුරේ සීනුව නාද විය! ආරක්ෂක සෙබළුන්ගෙන් ප්‍රවේශම් වන්න!", SOUNDS_DIR / "m01_ing_05.wav"),
            ("CUTSCENE", "ඉලක්කය ජොසෙෆ් ප්‍රිබෝයි. න්‍යෂ්ටික අවි තොරතුරු ලබාගැනීමට ඔහුව මුදවාගන්න.", SOUNDS_DIR / "_cut01_01.wav"),
        ]

        self.setup_ui()
        self.start_radar()
        self.start_hotkey_listener()
        self.start_process_monitor()

    def setup_ui(self):
        # Header banner
        header = tk.Frame(self.root, bg="#0a190a", bd=1, relief="ridge", pady=6)
        header.pack(fill="x", padx=10, pady=(8, 4))

        top_row = tk.Frame(header, bg="#0a190a")
        top_row.pack(fill="x", padx=6)

        title_lbl = tk.Label(
            top_row,
            text="PROJECT I.G.I. // TACTICAL OPS HUD v3.0",
            font=("Consolas", 12, "bold"),
            fg="#00ff66",
            bg="#0a190a"
        )
        title_lbl.pack(side="left")

        self.status_lbl = tk.Label(
            top_row,
            text="● STANDBY",
            font=("Consolas", 8, "bold"),
            fg="#ffaa00",
            bg="#0a190a"
        )
        self.status_lbl.pack(side="right")

        sub_lbl = tk.Label(
            header,
            text="පිරිසිදු සිංහල භාෂා උපසිරැසි සහ කොමාන්ඩෝ පාලන මැදිරිය (PURE SINHALA)",
            font=("Nirmala UI", 8),
            fg="#88cc88",
            bg="#0a190a"
        )
        sub_lbl.pack(anchor="w", padx=6, pady=(2, 0))

        # Top Control Row: OSD Toggle Button
        ctrl_bar = tk.Frame(self.root, bg="#050a05")
        ctrl_bar.pack(fill="x", padx=10, pady=2)

        self.osd_btn = tk.Button(
            ctrl_bar,
            text="🖥️ පාවෙන සිංහල උපසිරැසි තිරය (Floating Screen OSD) සක්‍රිය කරන්න",
            font=("Nirmala UI", 8, "bold"),
            bg="#113311",
            fg="#00ff66",
            activebackground="#00ff66",
            activeforeground="#000000",
            bd=1,
            relief="raised",
            command=self.toggle_osd
        )
        self.osd_btn.pack(fill="x", pady=2)

        # Radar Scope Display Frame
        radar_outer = tk.Frame(self.root, bg="#081408", bd=2, relief="sunken")
        radar_outer.pack(padx=10, pady=2)

        range_bar = tk.Frame(radar_outer, bg="#081408")
        range_bar.pack(fill="x", padx=6, pady=(3, 1))

        tk.Label(
            range_bar,
            text="RADAR RANGE:",
            font=("Consolas", 7, "bold"),
            fg="#66aa66",
            bg="#081408"
        ).pack(side="left", padx=4)

        self.range_btns = {}
        for r_val in [100, 250, 500]:
            btn = tk.Button(
                range_bar,
                text=f"{r_val}M",
                font=("Consolas", 7, "bold"),
                bg="#00ff66" if r_val == 250 else "#112b11",
                fg="#000000" if r_val == 250 else "#88ff88",
                activebackground="#00ff66",
                bd=1,
                padx=6,
                command=lambda rv=r_val: self.set_radar_range(rv)
            )
            btn.pack(side="left", padx=2)
            self.range_btns[r_val] = btn

        self.canvas_size = 200
        self.center = self.canvas_size // 2
        self.radius = 90

        self.canvas = tk.Canvas(
            radar_outer,
            width=self.canvas_size,
            height=self.canvas_size,
            bg="#020602",
            highlightthickness=0
        )
        self.canvas.pack(pady=2)

        # Tactical Support Hotkeys Frame
        hotkey_box = tk.LabelFrame(
            self.root,
            text=" TACTICAL SUPPORT HOTKEYS (F1 - F6) ",
            font=("Consolas", 8, "bold"),
            fg="#ffcc00",
            bg="#050a05",
            bd=1,
            relief="groove"
        )
        hotkey_box.pack(fill="x", padx=10, pady=2)

        self.btn_f1 = self.create_grid_btn(hotkey_box, "F1", "සැටලයිට් ඔත්තු බැලීම", "Satellite Recon", 0, 0, lambda: self.trigger_action("F1"))
        self.btn_f2 = self.create_grid_btn(hotkey_box, "F2", "ගුවන් ප්‍රහාරක සහය", "Airstrike Support", 0, 1, lambda: self.trigger_action("F2"))
        self.btn_f3 = self.create_grid_btn(hotkey_box, "F3", "හදිසි ආයුධ සැපයුම", "Tactical Ammo Drop", 1, 0, lambda: self.trigger_action("F3"))
        self.btn_f4 = self.create_grid_btn(hotkey_box, "F4", "හෙලිකොප්ටර් ගලවා ගැනීම", "Extraction Chopper", 1, 1, lambda: self.trigger_action("F4"))
        self.btn_f5 = self.create_grid_btn(hotkey_box, "F5", "තාප සංවේදී සංවේදක", "Thermal / Sonar Ping", 2, 0, lambda: self.trigger_action("F5"))
        self.btn_f6 = self.create_grid_btn(hotkey_box, "F6", "රේඩාර් ජෑමර් සහ EMP", "Radar & Comms Jammer", 2, 1, lambda: self.trigger_action("F6"))

        # Mission Objectives & Dialogue Bar (Pure Sinhala)
        sub_box = tk.LabelFrame(
            self.root,
            text=" සජීවී සිංහල උපසිරැසි සහ මෙහෙයුම් ඉලක්ක (LIVE SUBTITLES) ",
            font=("Nirmala UI", 8, "bold"),
            fg="#00ff66",
            bg="#050a05",
            bd=1,
            relief="groove"
        )
        sub_box.pack(fill="both", expand=True, padx=10, pady=3)

        # Active Objectives List
        obj_text = (
            "🎯 [මෙහෙයුම 01: දුම්රිය අංගනයට ඇතුළුවීම]\n"
            "  [✓] ප්‍රධාන දොරටුව අසල ඇති ට්‍රක් රථය පැහැරගෙන පලා යන්න.\n"
            "  [✓] ආරක්ෂක මූලස්ථානයේ (Security HQ) පරිගණක දත්ත බාගත කරන්න.\n"
            "  [✓] සන්නිවේදන කුලුන (Comm Tower) අක්‍රිය කරන්න."
        )
        obj_lbl = tk.Label(
            sub_box,
            text=obj_text,
            font=("Nirmala UI", 8),
            fg="#aaddaa",
            bg="#071207",
            justify="left",
            anchor="w",
            padx=8,
            pady=4,
            relief="sunken",
            bd=1
        )
        obj_lbl.pack(fill="x", padx=6, pady=(4, 2))

        # Live Radio Subtitle Display
        sub_disp_frame = tk.Frame(sub_box, bg="#030803", bd=1, relief="sunken")
        sub_disp_frame.pack(fill="both", expand=True, padx=6, pady=3)

        self.sub_speaker = tk.Label(
            sub_disp_frame,
            text="ANYA // RADIO COMM",
            font=("Consolas", 7, "bold"),
            fg="#ffcc00",
            bg="#030803"
        )
        self.sub_speaker.pack(anchor="w", padx=6, pady=(3, 0))

        self.sub_content = tk.Label(
            sub_disp_frame,
            text="ඩේවිඩ්, ප්‍රධාන දොරටුව අසල ඇති ට්‍රක් රථය පැහැරගෙන පලා යන්න.",
            font=("Nirmala UI", 9, "bold"),
            fg="#00ff66",
            bg="#030803",
            wraplength=460,
            justify="left"
        )
        self.sub_content.pack(anchor="w", padx=6, pady=(1, 4))

        # Quick Dialogue Buttons
        btn_bar = tk.Frame(sub_box, bg="#050a05")
        btn_bar.pack(fill="x", padx=6, pady=(0, 4))

        for idx, (spk, si_txt, wav) in enumerate(self.radio_dialogues[:5]):
            b = tk.Button(
                btn_bar,
                text=f"හඬ {idx+1}",
                font=("Nirmala UI", 7),
                bg="#0d1f0d",
                fg="#aaffaa",
                bd=1,
                padx=4,
                command=lambda s=spk, t=si_txt, w=wav: self.play_radio_cue(s, t, w)
            )
            b.pack(side="left", padx=2, expand=True, fill="x")

    def toggle_osd(self):
        if self.osd is None or not self.osd.win.winfo_exists():
            self.osd = FloatingSubtitleOSD(self.root)
            self.osd_btn.configure(text="🖥️ පාවෙන සිංහල උපසිරැසි තිරය (Floating OSD) සක්‍රියයි ✓", bg="#00aa44", fg="#ffffff")
        else:
            self.osd.win.destroy()
            self.osd = None
            self.osd_btn.configure(text="🖥️ පාවෙන සිංහල උපසිරැසි තිරය (Floating Screen OSD) සක්‍රිය කරන්න", bg="#113311", fg="#00ff66")

    def play_radio_cue(self, speaker: str, text_si: str, wav_path: Path):
        self.sub_speaker.configure(text=speaker)
        self.sub_content.configure(text=text_si)
        if self.osd and self.osd.win.winfo_exists():
            self.osd.update_subtitle(speaker, text_si)
        if wav_path.exists():
            winsound.PlaySound(str(wav_path), winsound.SND_FILENAME | winsound.SND_ASYNC)

    def create_grid_btn(self, parent, key_tag, title_si, sub_en, r, c, cmd):
        frame = tk.Frame(parent, bg="#0d1f0d", bd=1, relief="raised", cursor="hand2")
        frame.grid(row=r, column=c, padx=3, pady=2, sticky="nsew")
        parent.grid_columnconfigure(c, weight=1)

        frame.bind("<Button-1>", lambda e: cmd())

        top = tk.Label(
            frame,
            text=f"[{key_tag}] {title_si}",
            font=("Nirmala UI", 8, "bold"),
            fg="#ffdd44",
            bg="#0d1f0d",
            anchor="w"
        )
        top.pack(fill="x", padx=4, pady=(2, 0))
        top.bind("<Button-1>", lambda e: cmd())

        bot = tk.Label(
            frame,
            text=sub_en,
            font=("Consolas", 7),
            fg="#88bb88",
            bg="#0d1f0d",
            anchor="w"
        )
        bot.pack(fill="x", padx=4, pady=(0, 2))
        bot.bind("<Button-1>", lambda e: cmd())

        frame.widget_container = frame
        return frame

    def set_radar_range(self, r_val):
        self.radar_range_m = r_val
        for val, btn in self.range_btns.items():
            if val == r_val:
                btn.configure(bg="#00ff66", fg="#000000")
            else:
                btn.configure(bg="#112b11", fg="#88ff88")

    def draw_radar_base(self):
        self.canvas.delete("all")
        cx, cy, r = self.center, self.center, self.radius

        # Outer Scope Rings
        self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline="#00bb44", width=2)
        self.canvas.create_oval(cx - int(r*0.66), cy - int(r*0.66), cx + int(r*0.66), cy + int(r*0.66), outline="#004422", width=1, dash=(2, 4))
        self.canvas.create_oval(cx - int(r*0.33), cy - int(r*0.33), cx + int(r*0.33), cy + int(r*0.33), outline="#004422", width=1, dash=(2, 4))

        # Crosshairs
        self.canvas.create_line(cx - r, cy, cx + r, cy, fill="#003318", width=1)
        self.canvas.create_line(cx, cy - r, cx, cy + r, fill="#003318", width=1)

        # Player Center Marker
        self.canvas.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill="#00ff66", outline="#ffffff", width=1)
        self.canvas.create_text(cx, cy + 9, text="JONES", font=("Consolas", 6, "bold"), fill="#00ff66")

        # Rotating Sweep Line
        rad = math.radians(self.radar_angle)
        sx = cx + r * math.cos(rad)
        sy = cy + r * math.sin(rad)
        self.canvas.create_line(cx, cy, sx, sy, fill="#33ff88", width=2)

        # Fading Phosphor Sweep Trail
        for deg in range(1, 15, 3):
            t_rad = math.radians(self.radar_angle - deg)
            self.canvas.create_line(cx, cy, cx + r * math.cos(t_rad), cy + r * math.sin(t_rad), fill="#072b14", width=1)

        # Dynamic Scale Blips
        scale = r / float(self.radar_range_m)
        for t in self.raw_targets:
            bx = cx + int(t["rx"] * scale)
            by = cy + int(t["ry"] * scale)
            dist_m = int(math.hypot(t["rx"], t["ry"]))

            if math.hypot(bx - cx, by - cy) <= r:
                dx = bx - cx
                dy = by - cy
                angle = math.degrees(math.atan2(dy, dx)) % 360
                diff = (self.radar_angle - angle) % 360

                glow = "#ffffff" if diff < 50 else t["color"]
                size = 4 if diff < 50 else 3

                self.canvas.create_oval(bx - size, by - size, bx + size, by + size, fill=glow, outline=t["color"])
                self.canvas.create_text(bx, by - 7, text=f"{t['name']} {dist_m}m", font=("Consolas", 5, "bold"), fill="#aaffaa")

        # Compass Points
        self.canvas.create_text(cx, cy - r + 8, text="N", font=("Consolas", 7, "bold"), fill="#ffaa00")
        self.canvas.create_text(cx, cy + r - 8, text="S", font=("Consolas", 7, "bold"), fill="#00aa44")
        self.canvas.create_text(cx + r - 8, cy, text="E", font=("Consolas", 7, "bold"), fill="#00aa44")
        self.canvas.create_text(cx - r + 8, cy, text="W", font=("Consolas", 7, "bold"), fill="#00aa44")

    def start_radar(self):
        def loop():
            self.radar_angle = (self.radar_angle + 3.2) % 360
            self.draw_radar_base()
            self.root.after(40, loop)
        loop()

    def flash_button(self, btn):
        orig = "#0d1f0d"
        flash = "#1e441e"
        btn.configure(bg=flash)
        for c in btn.winfo_children():
            try:
                c.configure(bg=flash)
            except Exception:
                pass

        def reset():
            btn.configure(bg=orig)
            for c in btn.winfo_children():
                try:
                    c.configure(bg=orig)
                except Exception:
                    pass

        self.root.after(250, reset)

    def trigger_action(self, action_key: str):
        now = time.time()
        if now - self.last_pressed.get(action_key, 0) < 1.0:
            return
        self.last_pressed[action_key] = now

        actions = {
            "F1": (self.btn_f1, "ANYA (F1)", "චන්ද්‍රිකා ඔත්තු බැලීමේ දත්ත සම්ප්‍රේෂණය වෙමින් පවතී!", AUDIO_DIR / "f1_intel.wav"),
            "F2": (self.btn_f2, "COMMAND (F2)", "ගුවන් ප්‍රහාරක ජෙට් යානා ඉලක්කයට එල්ල වේ! පහත් වන්න!", AUDIO_DIR / "f2_airstrike.wav"),
            "F3": (self.btn_f3, "ANYA (F3)", "හදිසි උණ්ඩ සහ වෛද්‍ය ආධාර පැරෂුට් මගින් මුදා හැරේ!", AUDIO_DIR / "f3_supply.wav"),
            "F4": (self.btn_f4, "EXTRACTION (F4)", "ගලවා ගැනීමේ හෙලිකොප්ටරය පිටත් විය! මිනිත්තු 2කින් පැමිණේ!", AUDIO_DIR / "f4_evac.wav"),
            "F5": (self.btn_f5, "ANYA (F5)", "තාප සංවේදී සංවේදක සක්‍රියයි! සතුරු සෙබළුන් හඳුනා ගැනුණා!", AUDIO_DIR / "f5_thermal.wav"),
            "F6": (self.btn_f6, "SYSTEM (F6)", "රේඩාර් ජෑමර් ක්‍රියාත්මකයි! සතුරු සන්නිවේදන අක්‍රියයි!", AUDIO_DIR / "f6_jammer.wav"),
        }

        if action_key in actions:
            btn, spk, text_si, wav_path = actions[action_key]
            self.flash_button(btn)
            self.sub_speaker.configure(text=spk)
            self.sub_content.configure(text=text_si)
            if self.osd and self.osd.win.winfo_exists():
                self.osd.update_subtitle(spk, text_si)
            if wav_path.exists():
                winsound.PlaySound(str(wav_path), winsound.SND_FILENAME | winsound.SND_ASYNC)

    def start_hotkey_listener(self):
        user32 = ctypes.windll.user32
        key_map = {
            VK_F1: "F1",
            VK_F2: "F2",
            VK_F3: "F3",
            VK_F4: "F4",
            VK_F5: "F5",
            VK_F6: "F6"
        }
        held = {k: False for k in key_map}

        def listen():
            while True:
                for vk, name in key_map.items():
                    state = user32.GetAsyncKeyState(vk)
                    down = bool(state & 0x8000)
                    if down and not held[vk]:
                        held[vk] = True
                        self.root.after(0, lambda n=name: self.trigger_action(n))
                    elif not down and held[vk]:
                        held[vk] = False
                time.sleep(0.04)

        t = threading.Thread(target=listen, daemon=True)
        t.start()

    def start_process_monitor(self):
        import subprocess

        def monitor():
            while True:
                try:
                    res = subprocess.run(["tasklist"], capture_output=True, text=True)
                    out = res.stdout.lower()
                    active = ("igi.exe" in out or "project-igi.exe" in out)
                    if active != self.game_running:
                        self.game_running = active
                        if active:
                            self.status_lbl.configure(text="● IGI LINK: ACTIVE", fg="#00ff66")
                        else:
                            self.status_lbl.configure(text="○ STANDBY", fg="#ffaa00")
                except Exception:
                    pass
                time.sleep(2.5)

        t = threading.Thread(target=monitor, daemon=True)
        t.start()

def main():
    root = tk.Tk()
    app = TacticalHUD(root)
    root.mainloop()

if __name__ == "__main__":
    main()
