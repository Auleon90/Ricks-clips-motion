# motion-graphics

Skill ini memberi Claude kemampuan membuat motion graphics video bertema apapun
dalam gaya Rick's Clips — narasi berbasis fakta, dua kubu, stickman characters,
vertical 9:16, word-by-word captions.

---

## Kapan diaktifkan

Aktifkan skill ini saat user meminta:
- "Buat video tentang X"
- "Render motion graphics X vs Y"
- "Ceritakan kisah X dalam format video"
- Apapun yang menghasilkan file MP4 motion graphics

---

## Proses berpikir Claude saat menerima permintaan

### Langkah 1 — Pahami narasinya

Ekstrak dari tema yang diberikan:
- **Siapa dua kubu?** (tim A vs tim B, atau satu tokoh menghadapi tantangan)
- **Angka dramatis apa?** (jumlah tentara, tahun, rasio, skor)
- **Arc narasinya bagaimana?** setup → konflik → klimaks → resolusi
- **Tone-nya?** serius / epik / lucu / inspiratif

Contoh untuk "Perang Badar":
```
Kubu A : Muslim (313 orang)
Kubu B : Quraisy (1000 orang)
Angka  : 313 vs 1000, 2 tahun hijrah, 70 tawanan
Arc    : terdesak → doa → kemenangan tak terduga
Tone   : epik, spiritual
```

---

### Langkah 2 — Susun scene structure

Setiap video terdiri dari **4–6 scene** dengan total durasi 30–60 detik.
Gunakan pola ini sebagai panduan, bukan aturan kaku:

| Scene | Nama | Durasi | Isi |
|-------|------|--------|-----|
| 1 | Setup | 6–10s | Perkenalkan kubu, konteks, suasana |
| 2 | Angka dramatik | 5–8s | Scoreboard / counter reveal |
| 3 | Formasi / skala | 8–12s | Tunjukkan kekuatan/perbandingan |
| 4 | Klimaks | 8–12s | Titik balik / konfrontasi |
| 5 | Resolusi | 5–8s | Hasil akhir, pelajaran |

Untuk tema non-perang (ilmu, sains, bisnis), ganti nama scene sesuai arc cerita.

---

### Langkah 3 — Pilih warna kubu

Dua kubu selalu punya warna kontras. Panduan pemilihan:

```python
# Gunakan nilai hex ini sebagai basis, sesuaikan dengan konteks tema
PALETTES = {
    # Konflik fisik / perang
    "battle":    {"a": "red",  "b": "teal"},

    # Islam / spiritual
    "islamic":   {"a": "gold", "b": "teal"},   # hijau/emas adalah warna islami

    # Teknologi / modern
    "tech":      {"a": "teal", "b": "red"},

    # Alam / lingkungan
    "nature":    {"a": "#2E7D32", "b": "#1565C0"},  # hijau vs biru

    # Ekonomi / bisnis
    "business":  {"a": "gold", "b": "red"},
}
```

Warna tersedia di renderer: `"red"`, `"teal"`, `"gold"`.
Untuk warna custom, gunakan hex string langsung di `background_color`.

---

### Langkah 4 — Tulis narasi & caption tokens

Caption harus:
- **1–3 kata per token** (bukan kalimat penuh)
- Timing natural seperti orang berbicara (0.3–0.8 detik per kata)
- Kata kunci penting diberi durasi lebih panjang (0.6–1.0s)
- Jeda antar kalimat = gap 0.3–0.5s

Rumus timing cepat:
```python
# Estimasi: rata-rata 0.5s per kata, kata pendek 0.3s, kata panjang 0.7s
tokens = []
t = 0.5  # mulai setelah 0.5s (bukan dari 0 agar tidak terpotong)
for word in narration_words:
    dur = 0.35 if len(word) <= 3 else (0.65 if len(word) >= 8 else 0.5)
    tokens.append({"word": word, "start": round(t, 2), "end": round(t + dur, 2)})
    t += dur + 0.05  # gap antar kata
```

---

### Langkah 5 — Susun SceneSpec & render

Gunakan renderer yang sudah ada:

```python
import sys
sys.path.insert(0, "/home/user/Ricks-clips-motion")

from src.renderer import SceneSpec, VideoSpec, RicksClipsRenderer

scenes = [
    SceneSpec(
        duration=8.0,
        background_color=(30, 40, 55),      # dark blue-ish untuk setup
        caption_tokens=tokens_scene1,
        team_banners=[
            {"text": "NAMA_KUBU_A", "team": "gold",  "position": (0.25, 0.08)},
            {"text": "NAMA_KUBU_B", "team": "teal",  "position": (0.75, 0.08)},
        ],
    ),
    SceneSpec(
        duration=7.0,
        background_color=(50, 35, 20),      # warm brown untuk scoreboard
        caption_tokens=tokens_scene2,
        scoreboard={
            "label_left":  "LABEL_KIRI",
            "label_right": "LABEL_KANAN",
            "value":       313,             # angka dramatik
            "animated":    True,
            "start_val":   0,
            "position":    (0.5, 0.42),
        },
    ),
    # ... scene berikutnya
]

spec    = VideoSpec(scenes=scenes, transition="zoom", transition_duration=0.2)
renderer = RicksClipsRenderer(spec)
renderer.write("output.mp4", verbose=True)
```

---

## Komponen yang tersedia

### SceneSpec — properti lengkap

```python
SceneSpec(
    duration          = 8.0,                # detik (wajib)
    background_color  = (30, 40, 55),       # RGB fallback jika tidak ada video clip
    background_clip   = None,               # MoviePy clip (opsional)
    caption_tokens    = [...],              # list dict {word, start, end}
    scoreboard        = {                   # opsional
        "label_left":  "TEKS KIRI",         # maks ~8 karakter
        "label_right": "TEKS KANAN",
        "value":       99,                  # angka ditampilkan (0–999)
        "animated":    True,                # True = count up dari start_val
        "start_val":   0,
        "position":    (0.5, 0.40),         # (cx, cy) relatif 0.0–1.0
    },
    team_banners      = [                   # list, opsional
        {"text": "NAMA", "team": "red", "position": (0.25, 0.08)},
    ],
    stat_badges       = [                   # list, opsional
        {"label": "JUMLAH", "value": "× 313", "team": "gold", "position": (0.3, 0.9)},
    ],
    emotion_indicators = [                  # list, opsional
        {"emotion": "sweat", "position": (0.3, 0.35), "start": 1.0, "duration": 2.0},
    ],
)
```

### Emotion yang tersedia
`"sweat"` `"shock"` `"happy"` `"angry"` `"money"`

### Transition yang tersedia
`"zoom"` (punch-in, Rick's Clips default) · `"fade"` · `"slide"` · `"cut"`

---

## Panduan background color per mood

```python
MOODS = {
    "epic_dawn":     (55, 40, 20),   # orange-brown, pagi pertempuran
    "night_tense":   (15, 15, 30),   # biru gelap, malam sebelum perang
    "desert_hot":    (80, 55, 20),   # kuning-coklat, padang pasir
    "victory":       (20, 55, 35),   # hijau gelap, kemenangan
    "defeat":        (50, 15, 15),   # merah gelap, kekalahan
    "spiritual":     (20, 30, 50),   # biru-ungu, suasana doa/renungan
    "modern_clean":  (25, 25, 35),   # abu gelap, tema modern
    "royal_gold":    (45, 35, 10),   # coklat-emas, kerajaan/dinasti
}
```

---

## Contoh output: Perang Badar

```python
# Claude generate ini secara dinamis dari tema "Perang Badar"
scenes = [
    SceneSpec(
        duration=8.0,
        background_color=(55, 40, 20),   # epic_dawn
        caption_tokens=[
            {"word": "313",      "start": 0.5, "end": 1.1},
            {"word": "Muslim",   "start": 1.1, "end": 1.7},
            {"word": "melawan",  "start": 1.7, "end": 2.2},
            {"word": "1000",     "start": 2.2, "end": 2.9},
            {"word": "Quraisy",  "start": 2.9, "end": 3.6},
        ],
        team_banners=[
            {"text": "MUSLIM",  "team": "gold", "position": (0.25, 0.08)},
            {"text": "QURAISY", "team": "red",  "position": (0.75, 0.08)},
        ],
    ),
    SceneSpec(
        duration=7.0,
        background_color=(50, 35, 20),
        scoreboard={
            "label_left": "MUSLIM", "label_right": "QURAISY",
            "value": 313, "animated": True, "start_val": 0,
        },
        caption_tokens=[
            {"word": "Hanya",   "start": 0.4, "end": 0.8},
            {"word": "313",     "start": 0.8, "end": 1.4},
            {"word": "orang",   "start": 1.4, "end": 1.8},
        ],
    ),
    # ... lanjut scene formasi, klimaks, resolusi
]
```

---

## Checklist sebelum render

- [ ] Setiap scene ada `duration` dan minimal `background_color`
- [ ] Caption tokens tidak overlap antar scene (offset sudah disesuaikan ke local time)
- [ ] Scoreboard `value` antara 0–999
- [ ] Banner text maksimal 10 karakter agar tidak terpotong
- [ ] Total durasi semua scene = 30–60 detik (sweet spot untuk short-form)
- [ ] Output path sudah ditentukan

---

## File output

Simpan di project root atau folder yang diminta user:
```python
renderer.write("output/nama_video.mp4", verbose=True)
```

Format: H.264, AAC, 30fps, 576×1024.
