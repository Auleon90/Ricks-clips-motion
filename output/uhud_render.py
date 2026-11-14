"""
Render: Perang Uhud — Ketika Hampir Menang, Jangan Tinggalkan Pos
Voiceover: Cartesia TTS (Galang - Indonesian male)
Format: 576x1024, 30fps, ~60 detik
"""

import os
import sys
import wave
import struct
sys.path.insert(0, "/home/user/Ricks-clips-motion")

# ─── NARASI ────────────────────────────────────────────────────────────────────
# Arc: semangat → strategi → hampir menang → tergoda → jatuh → pelajaran hidup

NARASI_FULL = """Tahun ketiga Hijriah.
Muslim baru saja menang di Badar.
Semangat membara.
Tapi kemenangan bisa jadi ujian terbesar.
Tiga ribu pasukan Quraisy datang membalas dendam.
Nabi menempatkan lima puluh pemanah di bukit Ainain.
Perintahnya jelas: Jangan turun dari pos, apapun yang terjadi.
Pertempuran dimulai.
Muslim unggul.
Musuh mulai mundur.
Lalu... rampasan perang berserakan di bawah.
Empat puluh pemanah turun meninggalkan pos.
Khalid bin Walid melihat celah itu.
Serangan dari belakang.
Situasi berbalik total.
Tujuh puluh sahabat gugur sebagai syuhada.
Nabi sendiri terluka.
Ini bukan soal kalah.
Ini soal meninggalkan prinsip di momen paling kritis.
Kamu sekarang, ketika hampir sukses, apa yang kamu tinggalkan?
Konsentrasi? Ibadah? Orang yang kamu cintai?
Uhud mengajarkan: justru saat hampir sampai, pegang posmu lebih erat.
Karena ujian terbesar datang bukan saat kamu jatuh, tapi saat kamu hampir menang."""

# ─── GENERATE VOICEOVER ────────────────────────────────────────────────────────

def generate_voiceover(text: str, output_path: str) -> str:
    import cartesia
    client = cartesia.Cartesia(api_key=os.environ["CARTESIA_API_KEY"])

    # Galang - Indonesian male, voice for epic narration
    VOICE_ID = "04b567df-2923-4b0c-896b-4b7df0a07e1a"

    print("Generating voiceover via Cartesia (sonic-preview)...")
    result = client.tts.generate(
        model_id="sonic-preview",
        transcript=text,
        voice={"id": VOICE_ID},
        output_format={
            "container": "wav",
            "encoding": "pcm_f32le",
            "sample_rate": 44100,
        },
        language="id",
    )
    raw_audio = result.read()

    # Write WAV — pcm_f32le = 32-bit float PCM, mono
    n_channels = 1
    sampwidth  = 4      # 32-bit = 4 bytes
    framerate  = 44100

    with wave.open(output_path, "w") as wf:
        wf.setnchannels(n_channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(framerate)
        wf.writeframes(raw_audio)

    print(f"Voiceover saved: {output_path}")
    return output_path


# ─── TIMING GENERATOR ─────────────────────────────────────────────────────────

def build_tokens(words_with_times):
    """Build caption token list from (word, start, end) tuples."""
    return [{"word": w, "start": s, "end": e} for w, s, e in words_with_times]


def auto_tokens(words, t_start=0.5):
    """Auto-generate timing for a word list starting at t_start."""
    tokens = []
    t = t_start
    for word in words:
        clean = word.strip(".,!?:")
        if not clean:
            t += 0.3
            continue
        dur = 0.35 if len(clean) <= 3 else (0.70 if len(clean) >= 8 else 0.52)
        tokens.append({"word": clean, "start": round(t, 2), "end": round(t + dur, 2)})
        t += dur + 0.07
    return tokens, round(t + 0.3, 2)   # tokens, end_time


# ─── SCENE BUILDER ────────────────────────────────────────────────────────────

def build_scenes():
    from src.renderer import SceneSpec

    # Scene 1: Setup — semangat setelah Badar (8s)
    t1, end1 = auto_tokens(
        ["Tahun", "ketiga", "Hijriah", "Muslim", "baru", "menang", "di", "Badar"],
        t_start=0.5
    )
    scene1 = SceneSpec(
        duration=8.0,
        background_color=(55, 40, 20),      # epic_dawn — fajar padang pasir
        caption_tokens=t1,
        team_banners=[
            {"text": "MUSLIM",  "team": "gold", "position": (0.25, 0.08)},
            {"text": "QURAISY", "team": "red",  "position": (0.75, 0.08)},
        ],
        stat_badges=[
            {"label": "PASUKAN", "value": "700", "team": "gold", "position": (0.25, 0.9)},
            {"label": "PASUKAN", "value": "3000", "team": "red",  "position": (0.75, 0.9)},
        ],
    )

    # Scene 2: Scoreboard — Tahun ke-3 Hijriah (7s)
    t2, end2 = auto_tokens(
        ["Tiga", "ribu", "Quraisy", "datang", "membalas"],
        t_start=0.5
    )
    scene2 = SceneSpec(
        duration=7.0,
        background_color=(50, 35, 20),      # royal_gold — suasana tegang
        caption_tokens=t2,
        scoreboard={
            "label_left":  "TAHUN",
            "label_right": "HIJRIAH",
            "value":       3,
            "animated":    True,
            "start_val":   0,
            "position":    (0.5, 0.42),
        },
    )

    # Scene 3: Strategi Nabi — pemanah di bukit (9s)
    t3, end3 = auto_tokens(
        ["Nabi", "tempatkan", "50", "pemanah", "di", "bukit", "Ainain",
         "Jangan", "turun", "apapun", "yang", "terjadi"],
        t_start=0.5
    )
    scene3 = SceneSpec(
        duration=9.0,
        background_color=(30, 40, 55),      # night_tense — serius, strategis
        caption_tokens=t3,
        team_banners=[
            {"text": "STRATEGI", "team": "gold", "position": (0.5, 0.08)},
        ],
        stat_badges=[
            {"label": "PEMANAH", "value": "50 orang", "team": "gold", "position": (0.5, 0.88)},
        ],
    )

    # Scene 4: Muslim unggul → pemanah tergoda (10s)
    t4, end4 = auto_tokens(
        ["Muslim", "unggul", "Musuh", "mundur",
         "Lalu", "rampasan", "perang", "berserakan",
         "40", "pemanah", "turun", "tinggalkan", "pos"],
        t_start=0.5
    )
    scene4 = SceneSpec(
        duration=10.0,
        background_color=(45, 55, 20),      # hijau-kuning, hampir menang
        caption_tokens=t4,
        emotion_indicators=[
            {"emotion": "happy",  "position": (0.3, 0.38), "start": 0.5, "duration": 2.5},
            {"emotion": "money",  "position": (0.6, 0.35), "start": 3.5, "duration": 3.0},
            {"emotion": "shock",  "position": (0.5, 0.40), "start": 6.5, "duration": 2.5},
        ],
    )

    # Scene 5: Klimaks — serangan balik (10s)
    t5, end5 = auto_tokens(
        ["Khalid", "serang", "dari", "belakang",
         "70", "sahabat", "gugur", "sebagai", "syuhada",
         "Nabi", "sendiri", "terluka"],
        t_start=0.5
    )
    scene5 = SceneSpec(
        duration=10.0,
        background_color=(60, 15, 15),      # defeat — merah gelap
        caption_tokens=t5,
        scoreboard={
            "label_left":  "SYUHADA",
            "label_right": "UHUD",
            "value":       70,
            "animated":    True,
            "start_val":   0,
            "position":    (0.5, 0.38),
        },
        emotion_indicators=[
            {"emotion": "angry", "position": (0.7, 0.42), "start": 0.3, "duration": 4.0},
        ],
    )

    # Scene 6: Pelajaran — koneksi ke hidup modern (9s)
    t6, end6 = auto_tokens(
        ["Ini", "bukan", "soal", "kalah",
         "Ini", "soal", "meninggalkan", "prinsip",
         "di", "momen", "paling", "kritis"],
        t_start=0.5
    )
    scene6 = SceneSpec(
        duration=9.0,
        background_color=(20, 30, 50),      # spiritual — biru-ungu
        caption_tokens=t6,
        team_banners=[
            {"text": "PELAJARAN", "team": "teal", "position": (0.5, 0.08)},
        ],
    )

    # Scene 7: Call to action — refleksi diri (9s)
    t7, end7 = auto_tokens(
        ["Kamu", "hampir", "sampai",
         "Pegang", "posmu", "lebih", "erat",
         "Ujian", "terbesar", "saat", "hampir", "menang"],
        t_start=0.5
    )
    scene7 = SceneSpec(
        duration=9.0,
        background_color=(20, 55, 35),      # victory/hope — hijau gelap
        caption_tokens=t7,
        team_banners=[
            {"text": "PESAN",  "team": "gold", "position": (0.5, 0.08)},
        ],
        stat_badges=[
            {"label": "UHUD", "value": "3 H", "team": "gold", "position": (0.5, 0.88)},
        ],
    )

    return [scene1, scene2, scene3, scene4, scene5, scene6, scene7]


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    import os
    os.makedirs("/home/user/Ricks-clips-motion/output", exist_ok=True)

    # 1. Generate voiceover
    vo_path = "/home/user/Ricks-clips-motion/output/uhud_voiceover.wav"
    if not os.path.exists(vo_path):
        generate_voiceover(NARASI_FULL, vo_path)
    else:
        print(f"Voiceover already exists: {vo_path}")

    # 2. Build scenes
    print("Building scenes...")
    from src.renderer import VideoSpec, RicksClipsRenderer
    scenes = build_scenes()

    spec = VideoSpec(
        scenes=scenes,
        audio_path=vo_path,
        output_size=(576, 1024),
        output_fps=30,
        transition="zoom",
        transition_duration=0.2,
    )

    # 3. Render
    out_path = "/home/user/Ricks-clips-motion/output/perang_uhud.mp4"
    print(f"Rendering → {out_path}")
    renderer = RicksClipsRenderer(spec)
    renderer.write(out_path, verbose=True)
    print(f"\nDone! {out_path}")


if __name__ == "__main__":
    main()
