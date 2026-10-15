import pygame
from sys import exit
import random
import json   # [BARU]
import math   # [BARU]
import os     # [BARU]
import array  # [BARU]

# game variables
GAME_WIDTH = 360
GAME_HEIGHT = 640
GAME_DIR = os.path.dirname(os.path.abspath(__file__))

bird_x = GAME_WIDTH / 8
bird_y = GAME_HEIGHT / 2
brid_width = 34
bird_height = 24

class Bird(pygame.Rect):
    def __init__(self, img):
        pygame.Rect.__init__(self, bird_x, bird_y, brid_width, bird_height)
        self.image = img

#pipes class
pipe_x = GAME_WIDTH
pipe_y = 0
pipe_width = 64
pipe_height = 512

class Pipe(pygame.Rect):
    def __init__(self, img, counts_for_score=False):
        pygame.Rect.__init__(self, pipe_x, pipe_y, pipe_width, pipe_height)
        self.image = img
        self.passed = False
        self.counts_for_score = counts_for_score

#Game images 
background_imaege = pygame.image.load(os.path.join(GAME_DIR, "flappybirdbg.png"))
bird_image = pygame.image.load(os.path.join(GAME_DIR, "flappybird.png"))
bird_image = pygame.transform.scale(bird_image, (brid_width, bird_height))
top_pipe_image = pygame.image.load(os.path.join(GAME_DIR, "toppipe.png"))
top_pipe_image = pygame.transform.scale(top_pipe_image, (pipe_width, pipe_height))
bottom_pipe_image = pygame.image.load(os.path.join(GAME_DIR, "bottompipe.png"))
bottom_pipe_image = pygame.transform.scale(bottom_pipe_image, (pipe_width, pipe_height))

#Game logic
bird = Bird(bird_image)
pipes = []
velocity_x = -2
velocity_y = 0
gravity = 0.4
score = 0
game_over = False

def draw():
    window.blit(background_imaege, (0, 0))
    draw_bird()   # [UBAH] dulu: window.blit(bird.image, bird) -> sekarang + efek skill

    for pipe in pipes:
        window.blit(pipe.image, pipe)

    text_str = str(int(score))
    # [UBAH] tulisan "Game Over: ..." dan "Press Space to restart" dipindah ke
    # layar game over yang baru (draw_game_over), jadi dihapus dari sini.

    text_font = pygame.font.Font(None, 45)
    text_render = text_font.render(text_str, True, "white")
    window.blit(text_render, (5, 0))

def move():
    global velocity_y, score, game_over 
    velocity_y += gravity
    bird.y += velocity_y
    bird.y = max(bird.y, 0)

    if bird.y > GAME_HEIGHT:
        game_over = True
        return

    for pipe in pipes:
        pipe.x += velocity_x

        if pipe.counts_for_score and not pipe.passed and bird.x > pipe.x + pipe.width:
            score += 1
            pipe.passed = True

        if bird.colliderect(pipe) and not absorb_hit():   # [UBAH] skill bisa nahan tabrakan
            game_over = True
            return

    while len(pipes) > 0 and pipes[0].x + pipes[0].width < 0:
        pipes.pop(0)

def create_pipe():
    random_pipe_y = pipe_y - pipe_height/4 - random.random() * (pipe_height/2)
    opening_space = GAME_HEIGHT / 4


    top_pipe = Pipe(top_pipe_image, counts_for_score=True)
    top_pipe.y = random_pipe_y
    pipes.append(top_pipe)

    bottom_pipe = Pipe(bottom_pipe_image)
    bottom_pipe.y = top_pipe.y + top_pipe.height + opening_space
    pipes.append(bottom_pipe)

def restart_game():
    global bird, velocity_y, score, game_over
    bird = Bird(bird_image)
    pipes.clear()
    velocity_y = 0
    score = 0
    game_over = False

pygame.init()
window = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
pygame.display.set_caption("Flappy Bird")
Clock = pygame.time.Clock()

create_pipes_timer = pygame.USEREVENT + 0
pygame.time.set_timer(create_pipes_timer, 1500)


# =====================================================================
# [BARU] MAIN MENU, GET READY, DAN GAME OVER
# Alur: menu -> ready -> playing -> gameover -> (OK = menu / PLAY = ready)
# =====================================================================
INK = (84, 56, 71)
WHITE = (255, 255, 255)
ORANGE = (232, 97, 1)
GREEN = (115, 191, 46)
SAND = (222, 216, 149)
TITLE_COLOR = (248, 163, 14)
SAVE_FILE = os.path.join(GAME_DIR, "highscore.json")

def load_save():
    """Baca skor terbaik + total koin dari highscore.json."""
    try:
        with open(SAVE_FILE) as f:
            d = json.load(f)
            return int(d.get("best", 0)), int(d.get("coins", 0))
    except (OSError, ValueError, TypeError):
        return 0, 0

def write_save():
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump({"best": best_score, "coins": total_coins}, f)
    except OSError:
        pass

# ---------------------------------------------------------------------
# SUARA: dibuat lewat kode, jadi nggak butuh file audio.
# Mau pakai suara sendiri? Taruh file di folder yang sama dengan nama:
# sfx_flap, sfx_point, sfx_coin, sfx_powerup, sfx_block, sfx_hit, sfx_die,
# sfx_click (format .wav atau .ogg). Otomatis dipakai kalau ada.
# Tekan M di keyboard untuk mute / unmute.
# ---------------------------------------------------------------------
audio_ok = True
SAMPLE_RATE, CHANNELS = 44100, 1
try:
    pygame.mixer.quit()
    pygame.mixer.init(44100, -16, 1, 512)        # buffer kecil = suara nggak telat
    _init = pygame.mixer.get_init()
    if not _init or _init[1] != -16 or _init[2] > 2:
        audio_ok = False
    else:
        SAMPLE_RATE, _, CHANNELS = _init
except pygame.error:
    audio_ok = False                              # nggak ada perangkat audio -> game tetap jalan tanpa suara

def synth(parts):
    """parts = [(frekuensi_awal, frekuensi_akhir, durasi_detik, volume, 'sine'/'square'/'noise'), ...]"""
    buf = array.array("h")
    for f0, f1, dur, vol, wave in parts:
        n = int(SAMPLE_RATE * dur)
        phase = 0.0
        for i in range(n):
            k = i / n
            phase += 2 * math.pi * (f0 + (f1 - f0) * k) / SAMPLE_RATE
            if wave == "sine":
                v = math.sin(phase)
            elif wave == "square":
                v = 1.0 if math.sin(phase) >= 0 else -1.0
            else:
                v = random.uniform(-1, 1)
            env = min(1.0, i / 150) * (1 - k) ** 1.4          # naik cepat, lalu meredup
            buf.append(int(max(-1.0, min(1.0, v * env * vol)) * 32767))
    return buf

def make_sound(*layers):
    bufs = [synth(layer) for layer in layers]
    n = max(len(b) for b in bufs)
    mix = array.array("h")
    for i in range(n):
        v = max(-32767, min(32767, sum(b[i] for b in bufs if i < len(b))))
        mix.append(v)
        if CHANNELS == 2:
            mix.append(v)
    return pygame.mixer.Sound(buffer=mix.tobytes())

SFX_DEF = {
    "flap":    [[(380, 720, 0.09, 0.30, "sine")]],
    "point":   [[(988, 988, 0.07, 0.25, "square"), (1319, 1319, 0.16, 0.25, "square")]],
    "coin":    [[(1568, 1568, 0.05, 0.22, "square"), (2093, 2093, 0.14, 0.22, "square")]],
    "powerup": [[(523, 523, 0.06, 0.22, "square"), (659, 659, 0.06, 0.22, "square"),
                 (784, 784, 0.06, 0.22, "square"), (1047, 1047, 0.16, 0.22, "square")]],
    "block":   [[(0, 0, 0.14, 0.35, "noise")], [(300, 120, 0.18, 0.30, "sine")]],
    "hit":     [[(0, 0, 0.12, 0.45, "noise")], [(320, 70, 0.16, 0.40, "sine")]],
    "die":     [[(700, 140, 0.40, 0.30, "sine")]],
    "click":   [[(660, 660, 0.04, 0.20, "square")]],
}

def load_sfx(name):
    for ext in (".wav", ".ogg"):
        path = os.path.join(GAME_DIR, "sfx_" + name + ext)
        if os.path.exists(path):
            try:
                return pygame.mixer.Sound(path)
            except pygame.error:
                pass
    return make_sound(*SFX_DEF[name])

sounds = {}
if audio_ok:
    for _n in SFX_DEF:
        sounds[_n] = load_sfx(_n)
muted = False
die_played = True

def play(name):
    snd = sounds.get(name)
    if snd is not None and not muted:
        snd.play()

# ---- font piksel 5x7 buatan sendiri (nggak butuh file .ttf) ----
# tiap huruf = 7 baris, "#" = piksel nyala. Dipakai lewat pixel_text() / outlined_text().
_GLYPHS = {}
for _line in """
A:.###.|#...#|#...#|#####|#...#|#...#|#...#
B:####.|#...#|#...#|####.|#...#|#...#|####.
C:.###.|#...#|#....|#....|#....|#...#|.###.
D:####.|#...#|#...#|#...#|#...#|#...#|####.
E:#####|#....|#....|####.|#....|#....|#####
F:#####|#....|#....|####.|#....|#....|#....
G:.###.|#...#|#....|#.###|#...#|#...#|.###.
H:#...#|#...#|#...#|#####|#...#|#...#|#...#
I:.###.|..#..|..#..|..#..|..#..|..#..|.###.
J:..###|...#.|...#.|...#.|...#.|#..#.|.##..
K:#...#|#..#.|#.#..|##...|#.#..|#..#.|#...#
L:#....|#....|#....|#....|#....|#....|#####
M:#...#|##.##|#.#.#|#.#.#|#...#|#...#|#...#
N:#...#|##..#|#.#.#|#..##|#...#|#...#|#...#
O:.###.|#...#|#...#|#...#|#...#|#...#|.###.
P:####.|#...#|#...#|####.|#....|#....|#....
Q:.###.|#...#|#...#|#...#|#.#.#|#..#.|.##.#
R:####.|#...#|#...#|####.|#.#..|#..#.|#...#
S:.####|#....|#....|.###.|....#|....#|####.
T:#####|..#..|..#..|..#..|..#..|..#..|..#..
U:#...#|#...#|#...#|#...#|#...#|#...#|.###.
V:#...#|#...#|#...#|#...#|#...#|.#.#.|..#..
W:#...#|#...#|#...#|#.#.#|#.#.#|##.##|#...#
X:#...#|#...#|.#.#.|..#..|.#.#.|#...#|#...#
Y:#...#|#...#|.#.#.|..#..|..#..|..#..|..#..
Z:#####|....#|...#.|..#..|.#...|#....|#####
0:.###.|#...#|#..##|#.#.#|##..#|#...#|.###.
1:..#..|.##..|..#..|..#..|..#..|..#..|.###.
2:.###.|#...#|....#|...#.|..#..|.#...|#####
3:.###.|#...#|....#|..##.|....#|#...#|.###.
4:...#.|..##.|.#.#.|#..#.|#####|...#.|...#.
5:#####|#....|####.|....#|....#|#...#|.###.
6:.###.|#....|#....|####.|#...#|#...#|.###.
7:#####|....#|...#.|..#..|.#...|.#...|.#...
8:.###.|#...#|#...#|.###.|#...#|#...#|.###.
9:.###.|#...#|#...#|.####|....#|....#|.###.
!:..#..|..#..|..#..|..#..|..#..|.....|..#..
.:.....|.....|.....|.....|.....|.....|..#..
-:.....|.....|.....|.###.|.....|.....|.....
/:....#|....#|...#.|..#..|.#...|#....|#....
 :.....|.....|.....|.....|.....|.....|.....
""".strip().splitlines():
    _ch, _rows = _line.split(":", 1)
    _GLYPHS[_ch] = _rows.split("|")

_text_cache = {}

def pixel_text(text, px, color):
    """Render teks piksel. px = ukuran 1 piksel font di layar."""
    key = (text, px, color)
    if key not in _text_cache:
        t_up = text.upper()
        surf = pygame.Surface(((len(t_up) * 6 - 1) * px, 7 * px), pygame.SRCALPHA)
        for i, ch in enumerate(t_up):
            for y, row in enumerate(_GLYPHS.get(ch, _GLYPHS[" "])):
                for x, c in enumerate(row):
                    if c == "#":
                        surf.fill(color, ((i * 6 + x) * px, y * px, px, px))
        _text_cache[key] = surf
    return _text_cache[key]

# ukuran piksel font (makin besar = makin chunky)
title_font = 5
msg_font = 4
num_font = 4
label_font = 2
btn_font = 3
small_font = 2

big_bird = pygame.transform.scale(bird_image, (brid_width * 2, bird_height * 2))

def outlined_text(text, size, color, pos, anchor="center", thick=2, shadow=2, outline=INK):
    """Teks piksel dengan outline gelap + bayangan bawah. Outline/bayangan
    selalu kelipatan 1 piksel font supaya tetap rapi di grid piksel."""
    n = max(1, round(thick / size)) if thick > 0 else 0
    s = max(1, round(shadow / size)) if shadow > 0 else 0
    dark = pixel_text(text, size, outline)
    light = pixel_text(text, size, color)
    r = light.get_rect(**{anchor: pos})
    for dx in range(-n, n + 1):
        for dy in range(-n, n + s + 1):
            window.blit(dark, (r.x + dx * size, r.y + dy * size))
    window.blit(light, r)

class Button:
    def __init__(self, label, center, color, width=120, height=46):
        self.label, self.color = label, color
        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.center = center
        self.down = False

    def draw(self):
        r = self.rect.move(0, 3 if self.down else 0)
        pygame.draw.rect(window, INK, r.inflate(8, 8))
        pygame.draw.rect(window, WHITE, r.inflate(4, 4))
        pygame.draw.rect(window, self.color, r)
        dark = tuple(max(c - 60, 0) for c in self.color)
        light = tuple(min(c + 50, 255) for c in self.color)
        pygame.draw.rect(window, dark, (r.x, r.bottom - 6, r.w, 6))
        pygame.draw.rect(window, light, (r.x, r.y, r.w, 3))
        outlined_text(self.label, btn_font, WHITE, r.center, thick=1, shadow=1)

    def handle(self, e):
        """True kalau tombol diklik (tekan + lepas di atas tombol)."""
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.rect.collidepoint(e.pos):
            self.down = True
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            hit = self.down and self.rect.collidepoint(e.pos)
            self.down = False
            return hit
        return False

start_btn = Button("START", (GAME_WIDTH // 2 - 75, 400), GREEN)
score_btn = Button("SCORE", (GAME_WIDTH // 2 + 75, 400), ORANGE)
ok_btn = Button("OK", (GAME_WIDTH // 2 - 75, 500), ORANGE)
play_btn = Button("PLAY", (GAME_WIDTH // 2 + 75, 500), GREEN)
back_btn = Button("OK", (GAME_WIDTH // 2, 500), ORANGE)

state = "menu"          # menu | ready | playing | gameover | score
best_score, total_coins = load_save()
last_score = 0
new_best = False
flash = 0.0             # kilatan putih saat mati
panel_t = 0.0           # timer animasi layar game over

def medal_color(s):
    if s >= 40: return (225, 232, 235)   # platinum
    if s >= 30: return (255, 205, 40)    # emas
    if s >= 20: return (200, 204, 210)   # perak
    if s >= 10: return (205, 127, 50)    # perunggu
    return None

# ---------------------------------------------------------------------
# KOIN: muncul di celah antar pipa, berputar, +1 tiap diambil.
# Total koin disimpan di highscore.json bareng skor terbaik.
# ---------------------------------------------------------------------
COIN_CHANCE = 0.7     # peluang koin muncul di tiap pasang pipa (0.0 - 1.0)
COIN_HIT = 26         # ukuran hitbox koin (piksel)
COIN_ART = [
    "..oooooo..",
    ".oyyyyyyo.",
    "oyllyyyyyo",
    "oylyddyyyo",
    "oyyyddyyyo",
    "oyyyddyyyo",
    "oyyyddyyyo",
    "oyyyyyyyyo",
    ".oyyyyyyo.",
    "..oooooo..",
]
COIN_COLORS = {"o": INK, "y": (255, 205, 40), "l": (255, 245, 160), "d": (214, 150, 20)}

def make_coin_frames(px=3):
    """Koin piksel 10x10, dipencet lebarnya buat efek berputar."""
    base = pygame.Surface((10, 10), pygame.SRCALPHA)
    for y, row in enumerate(COIN_ART):
        for x, c in enumerate(row):
            if c in COIN_COLORS:
                base.set_at((x, y), COIN_COLORS[c])
    return [pygame.transform.scale(base, (w * px, 10 * px)) for w in (10, 8, 5, 2, 5, 8)]

coin_frames = make_coin_frames()
coins = []
popups = []        # efek "+1" yang naik pelan
run_coins = 0      # koin yang diambil di ronde ini

class Coin(pygame.Rect):
    def __init__(self, cx, cy):
        pygame.Rect.__init__(self, 0, 0, COIN_HIT, COIN_HIT)
        self.center = (int(cx), int(cy))
        self.taken = False

def spawn_coin():
    """Dipanggil tepat setelah create_pipe(): taruh koin di tengah celah pipa."""
    if random.random() > COIN_CHANCE:
        return
    top, bottom = pipes[-2], pipes[-1]
    gap_mid = (top.bottom + bottom.top) / 2
    coins.append(Coin(top.x + pipe_width / 2, gap_mid + random.randint(-40, 40)))

def update_coins():
    global run_coins, total_coins
    magnet = skill_time["magnet"] > 0
    for c in coins:
        c.x += velocity_x
        if magnet:                                    # koin ketarik ke burung
            dx, dy = bird.centerx - c.centerx, bird.centery - c.centery
            d = math.hypot(dx, dy)
            if 0 < d < MAGNET_RADIUS:
                step = min(7, d)
                c.centerx += round(dx / d * step)
                c.centery += round(dy / d * step)
        if not c.taken and bird.colliderect(c):
            c.taken = True
            run_coins += 1
            total_coins += 1
            popups.append([c.centerx, c.centery, 0, "+1"])
            play("coin")
    coins[:] = [c for c in coins if not c.taken and c.right > 0]
    for p in popups:
        p[0] += velocity_x
        p[1] -= 1
        p[2] += 1
    popups[:] = [p for p in popups if p[2] < 30]

def draw_coins(t):
    img = coin_frames[int(t * 8) % len(coin_frames)]
    for c in coins:
        window.blit(img, img.get_rect(center=c.center))
    for p in popups:
        outlined_text(p[3], small_font, (255, 230, 90), (int(p[0]), int(p[1])), thick=1, shadow=0)

def draw_coin_hud(n):
    """Ikon koin + angka di pojok kanan atas."""
    ir = coin_frames[0].get_rect(center=(GAME_WIDTH - 26, 26))
    window.blit(coin_frames[0], ir)
    outlined_text(str(n), btn_font, WHITE, (ir.left - 8, 26), "midright", thick=3, shadow=3)

# ---------------------------------------------------------------------
# SKILL: MAGNET (koin ketarik), SHIELD (nahan 1x tabrakan), INVISIBLE (tembus pipa)
# Item muncul di antara dua pipa; begitu diambil, skill langsung aktif.
# Ikon: taruh PNG sendiri di folder yang sama dengan file ini, namanya
# skill_magnet.png, skill_shield.png, skill_invisible.png (otomatis dipakai).
# Ukuran ideal: sekitar 30-34 piksel dan sudah tajam (kalau lebih besar akan dikecilkan).
# Kalau file nggak ada, dipakai gambar bawaan buatan kode.
# ---------------------------------------------------------------------
ITEM_SIZE = 28                                          # ukuran ikon item di jalur (burung = 34x24)
HUD_SIZE = 18                                           # ukuran ikon di pojok kanan atas
SKILL_GAP_MIN = 9                                       # jeda antar item skill: acak 9-13 pasang pipa
SKILL_GAP_MAX = 13                                      # (1 pasang pipa = 1,5 detik -> sekitar 13-20 detik)
MAGNET_RADIUS = 130                                     # jangkauan tarikan magnet (piksel)
SKILL_TIME = {"magnet": 8 * 60, "invisible": 5 * 60}    # durasi dalam frame (60 = 1 detik)
GRACE_TIME = 60                                         # kebal 1 detik setelah shield pecah
SKILL_NAME = {"magnet": "MAGNET", "shield": "SHIELD", "invisible": "INVISIBLE"}
SKILL_BAR = {"magnet": (220, 50, 50), "shield": (60, 140, 230), "invisible": (245, 245, 245)}
SKILL_COLORS = {"o": INK, "r": (220, 50, 50), "w": (245, 245, 245),
                "b": (60, 140, 230), "l": (170, 215, 255)}
SKILL_ART = {
    "magnet": [
        "oooo..oooo", "owwo..owwo", "owwo..owwo", "orro..orro", "orro..orro",
        "orro..orro", "orrroorrro", ".orrrrrro.", "..orrrro..", "...oooo...",
    ],
    "shield": [
        "oooooooooo", "obllbbbbbo", "oblbbbbbbo", "obbbbbbbbo", "obbbbbbbbo",
        ".obbbbbbo.", ".obbbbbbo.", "..obbbbo..", "...obbo...", "....oo....",
    ],
    "invisible": [
        "...oooo...", "..owwwwo..", ".owwwwwwo.", ".owowwowo.", ".owwwwwwo.",
        ".owwwwwwo.", ".owwwwwwo.", ".owwwwwwo.", ".owowwowo.", "..o.oo.o..",
    ],
}

def fit_icon(img, size):
    """Skala gambar ke kotak size x size, rasio dijaga, ditaruh di tengah."""
    w, h = img.get_size()
    if w > size or h > size:                      # kegedean -> kecilkan (rasio dijaga)
        k = min(size / w, size / h)
        img = pygame.transform.smoothscale(img, (max(1, round(w * k)), max(1, round(h * k))))
        w, h = img.get_size()
    out = pygame.Surface((size, size), pygame.SRCALPHA)   # kalau udah muat, dipakai apa adanya (tetap tajam)
    out.blit(img, ((size - w) // 2, (size - h) // 2))
    return out

def make_skill_icon(kind):
    """Pakai skill_<nama>.png kalau ada di folder game; kalau nggak ada, pakai gambar bawaan."""
    path = os.path.join(GAME_DIR, "skill_" + kind + ".png")
    try:
        img = pygame.image.load(path).convert_alpha()
    except (pygame.error, OSError):
        img = pygame.Surface((10, 10), pygame.SRCALPHA)
        for y, row in enumerate(SKILL_ART[kind]):
            for x, c in enumerate(row):
                if c in SKILL_COLORS:
                    img.set_at((x, y), SKILL_COLORS[c])
        img = pygame.transform.scale(img, (24, 24))
    return fit_icon(img, ITEM_SIZE), fit_icon(img, HUD_SIZE)   # (ikon item di jalur, ikon HUD)

skill_big, skill_small = {}, {}
for _k in SKILL_ART:
    skill_big[_k], skill_small[_k] = make_skill_icon(_k)

# efek visual (dibuat sekali)
BUBBLE = pygame.Surface((36, 36), pygame.SRCALPHA)
pygame.draw.circle(BUBBLE, (255, 255, 255, 80), (18, 18), 17)
pygame.draw.circle(BUBBLE, (255, 255, 255, 180), (18, 18), 17, 2)
SHIELD_FX = pygame.Surface((60, 60), pygame.SRCALPHA)
pygame.draw.circle(SHIELD_FX, (90, 170, 255, 70), (30, 30), 28)
pygame.draw.circle(SHIELD_FX, (170, 215, 255, 230), (30, 30), 28, 2)
MAGNET_FX = pygame.Surface((MAGNET_RADIUS * 2, MAGNET_RADIUS * 2), pygame.SRCALPHA)
pygame.draw.circle(MAGNET_FX, (255, 255, 255, 45), (MAGNET_RADIUS, MAGNET_RADIUS), MAGNET_RADIUS, 2)

skill_time = {"magnet": 0, "invisible": 0}
shield_on = False
grace = 0
items = []
skill_cooldown = SKILL_GAP_MIN // 2   # sisa pasang pipa sebelum item skill boleh muncul lagi

class SkillItem(pygame.Rect):
    def __init__(self, kind, cx, cy):
        pygame.Rect.__init__(self, 0, 0, 26, 26)
        self.center = (int(cx), int(cy))
        self.kind = kind
        self.taken = False

def skill_busy():
    """True kalau masih ada skill aktif atau item skill yang belum diambil/lewat."""
    return (skill_time["magnet"] > 0 or skill_time["invisible"] > 0
            or shield_on or grace > 0 or len(items) > 0)

def spawn_skill():
    """Dipanggil setelah create_pipe(). Aturan biar skill nggak berdempetan:
    1) setelah item muncul ATAU diambil, ada jeda 9-13 pasang pipa,
    2) item baru nggak muncul selama masih ada skill aktif (termasuk shield yang belum pecah)
       atau item skill lain yang masih ada di layar."""
    global skill_cooldown
    if skill_cooldown > 0:
        skill_cooldown -= 1
        return
    if skill_busy():
        return
    top, bottom = pipes[-2], pipes[-1]
    gap_mid = (top.bottom + bottom.top) / 2
    items.append(SkillItem(random.choice(list(SKILL_ART)), top.x + pipe_width / 2 + 90, gap_mid))
    skill_cooldown = random.randint(SKILL_GAP_MIN, SKILL_GAP_MAX)

def absorb_hit():
    """Dipanggil move() saat burung nabrak pipa. True = tabrakan diabaikan."""
    global shield_on, grace
    if skill_time["invisible"] > 0 or grace > 0:
        return True
    if shield_on:
        shield_on = False
        grace = GRACE_TIME
        popups.append([bird.centerx, bird.y, 0, "BLOCK!"])
        play("block")
        return True
    return False

def update_skills():
    global shield_on, grace, skill_cooldown
    for k in skill_time:
        if skill_time[k] > 0:
            skill_time[k] -= 1
    if grace > 0:
        grace -= 1
    for it in items:
        it.x += velocity_x
        if not it.taken and bird.colliderect(it):
            it.taken = True
            skill_cooldown = max(skill_cooldown, SKILL_GAP_MIN)   # jeda dihitung ulang dari saat diambil
            if it.kind == "shield":
                shield_on = True
            else:
                skill_time[it.kind] = SKILL_TIME[it.kind]
            popups.append([it.centerx, it.centery, 0, SKILL_NAME[it.kind]])
            play("powerup")
    items[:] = [i for i in items if not i.taken and i.right > 0]

def reset_skills():
    global shield_on, grace, skill_cooldown
    skill_cooldown = SKILL_GAP_MIN // 2
    skill_time["magnet"] = skill_time["invisible"] = 0
    shield_on = False
    grace = 0
    items.clear()

def draw_bird():
    img = bird.image
    inv = skill_time["invisible"]
    if inv > 0:
        img = img.copy()
        img.set_alpha(80 if (inv > 90 or (inv // 6) % 2 == 0) else 200)   # berkedip mau habis
    elif grace > 0 and (grace // 4) % 2 == 0:
        img = img.copy()
        img.set_alpha(70)                                                  # kedip setelah shield pecah
    if skill_time["magnet"] > 0:
        window.blit(MAGNET_FX, MAGNET_FX.get_rect(center=bird.center))
    window.blit(img, bird)
    if shield_on:
        window.blit(SHIELD_FX, SHIELD_FX.get_rect(center=bird.center))

def draw_items(t):
    bob = round(math.sin(t * 4) * 3)
    for it in items:
        c = (it.centerx, it.centery + bob)
        window.blit(BUBBLE, BUBBLE.get_rect(center=c))
        window.blit(skill_big[it.kind], skill_big[it.kind].get_rect(center=c))

def draw_skill_hud():
    """Ikon + bar sisa waktu, di bawah hitungan koin."""
    y = 62
    for kind in ("magnet", "invisible", "shield"):
        if kind == "shield":
            if not shield_on:
                continue
            frac = 1.0
        else:
            if skill_time[kind] <= 0:
                continue
            frac = skill_time[kind] / SKILL_TIME[kind]
        ic = skill_small[kind].get_rect(center=(GAME_WIDTH - 26, y))
        window.blit(skill_small[kind], ic)
        bar = pygame.Rect(ic.left - 62, y - 4, 54, 8)
        pygame.draw.rect(window, INK, bar.inflate(4, 4))
        pygame.draw.rect(window, (40, 40, 50), bar)
        pygame.draw.rect(window, SKILL_BAR[kind], (bar.x, bar.y, int(bar.w * frac), bar.h))
        y += 28

def draw_panel(center_y, shown_score, shown_best, is_new):
    panel = pygame.Rect(0, 0, 290, 150)
    panel.center = (GAME_WIDTH // 2, center_y)
    pygame.draw.rect(window, WHITE, panel.inflate(10, 10))
    pygame.draw.rect(window, INK, panel.inflate(6, 6))
    pygame.draw.rect(window, SAND, panel.inflate(-2, -2))
    pygame.draw.rect(window, (210, 176, 76), (panel.x + 1, panel.bottom - 6, panel.w - 2, 5))

    # medali (kiri)
    mx, my = panel.x + 60, panel.y + 88
    outlined_text("MEDAL", label_font, ORANGE, (mx, panel.y + 28), thick=1, shadow=0, outline=WHITE)
    col = medal_color(shown_score)
    pygame.draw.circle(window, INK, (mx, my), 31)
    if col:
        pygame.draw.circle(window, col, (mx, my), 28)
        pygame.draw.circle(window, tuple(max(c - 45, 0) for c in col), (mx, my), 20)
        pygame.draw.circle(window, col, (mx, my), 17)
    else:
        pygame.draw.circle(window, (170, 150, 90), (mx, my), 28)

    # skor (kanan)
    rx = panel.right - 22
    outlined_text("SCORE", label_font, ORANGE, (rx, panel.y + 24), "midright", thick=1, shadow=0, outline=WHITE)
    outlined_text(str(shown_score), num_font, WHITE, (rx, panel.y + 52), "midright", thick=2, shadow=1)
    outlined_text("BEST", label_font, ORANGE, (rx, panel.y + 90), "midright", thick=1, shadow=0, outline=WHITE)
    outlined_text(str(shown_best), num_font, WHITE, (rx, panel.y + 118), "midright", thick=2, shadow=1)
    if is_new:
        tag = pygame.Rect(0, 0, 44, 20)
        tag.midright = (rx - 62, panel.y + 90)
        pygame.draw.rect(window, INK, tag.inflate(4, 4))
        pygame.draw.rect(window, (232, 60, 40), tag)
        new_s = pixel_text("NEW", small_font, WHITE)
        window.blit(new_s, new_s.get_rect(center=tag.center))

def draw_menu(t):
    window.blit(background_imaege, (0, 0))
    outlined_text("Flappy Bird", title_font, TITLE_COLOR, (GAME_WIDTH // 2, 130), thick=4, shadow=4)
    by = 262 + round(math.sin(t * 5) * 3) * 2        # gerak naik-turun per 2 piksel
    window.blit(big_bird, big_bird.get_rect(center=(GAME_WIDTH // 2, by)))
    start_btn.draw()
    score_btn.draw()
    outlined_text("KLIK ATAU SPACE", small_font, WHITE, (GAME_WIDTH // 2, 470), thick=1, shadow=1)
    draw_coin_hud(total_coins)
    label = ("M: SUARA " + ("OFF" if muted else "ON")) if audio_ok else "SUARA TIDAK TERSEDIA"
    outlined_text(label, small_font, WHITE, (GAME_WIDTH // 2, 494), thick=1, shadow=1)

def draw_ready(t):
    window.blit(background_imaege, (0, 0))
    outlined_text("Get Ready!", msg_font, (252, 160, 70), (GAME_WIDTH // 2, 150), thick=3, shadow=3)
    window.blit(bird.image, (bird.x, bird.y + math.sin(t * 5) * 6))
    r = 16 + int(abs(math.sin(t * 4)) * 4)
    cx, cy = GAME_WIDTH // 2, 400
    pygame.draw.circle(window, INK, (cx, cy), r + 3)
    pygame.draw.circle(window, WHITE, (cx, cy), r)
    outlined_text("TAP", label_font, WHITE, (cx, cy + 46), thick=1, shadow=1)

def draw_game_over():
    k = min(panel_t / 0.5, 1.0)
    ease = 1 - (1 - k) ** 3
    outlined_text("Game Over", msg_font, (252, 160, 70),
                  (GAME_WIDTH // 2, 120 + ease * 60), thick=3, shadow=3)
    draw_panel(int(GAME_HEIGHT + 100 - ease * (GAME_HEIGHT + 100 - 330)), last_score, best_score, new_best)
    if panel_t > 0.7:
        icon = coin_frames[0]
        ir = icon.get_rect(center=(GAME_WIDTH // 2 - 100, 440))
        window.blit(icon, ir)
        outlined_text("+" + str(run_coins), btn_font, WHITE, (ir.right + 8, 440), "midleft", thick=3, shadow=3)
        outlined_text("TOTAL " + str(total_coins), label_font, WHITE, (GAME_WIDTH // 2 + 140, 440),
                      "midright", thick=1, shadow=1)
        ok_btn.draw()
        play_btn.draw()

def draw_flash():
    if flash > 0:
        overlay = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        overlay.fill(WHITE)
        overlay.set_alpha(int(255 * flash))
        window.blit(overlay, (0, 0))

def go_ready():
    global state, run_coins
    restart_game()
    coins.clear()
    popups.clear()
    run_coins = 0
    reset_skills()
    state = "ready"

def start_playing():
    global state, velocity_y
    state = "playing"
    velocity_y = -6
    play("flap")
    pygame.time.set_timer(create_pipes_timer, 1500)   # pipa pertama muncul 1,5 detik setelah tap

def on_death():
    global state, best_score, new_best, last_score, flash, panel_t, die_played
    last_score = int(score)
    new_best = last_score > best_score
    if new_best:
        best_score = last_score
    write_save()          # simpan skor terbaik + total koin
    reset_skills()
    flash = 1.0
    panel_t = 0.0
    die_played = False
    play("hit")
    state = "gameover"


t = 0.0
dt = 0.0
while True: #Game loop
    t += dt
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

        if event.type == create_pipes_timer and state == "playing" and not game_over:
            create_pipe()
            spawn_coin()
            spawn_skill()

        key_tap = event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_RETURN)
        mouse_tap = (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                     and state in ("ready", "playing"))
        tap = key_tap or mouse_tap

        if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
            muted = not muted                         # M = mute / unmute

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and state != "playing":
            state = "menu"

        if state == "menu":
            hit_start = start_btn.handle(event)
            hit_score = score_btn.handle(event)
            if hit_start or key_tap:
                play("click")
                go_ready()
            elif hit_score:
                play("click")
                state = "score"
        elif state == "ready":
            if tap:
                start_playing()
        elif state == "playing":
            if tap and not game_over:
                velocity_y = -6
                play("flap")
        elif state == "gameover":
            if panel_t > 0.7:
                hit_ok = ok_btn.handle(event)
                hit_play = play_btn.handle(event)
                if hit_ok:
                    play("click")
                    state = "menu"
                elif hit_play or key_tap:
                    play("click")
                    go_ready()
        elif state == "score":
            if back_btn.handle(event) or key_tap:
                play("click")
                state = "menu"

    # ---- update ----
    if state == "playing":
        if not game_over:
            s_before = int(score)
            move()
            if int(score) > s_before:
                play("point")
            update_coins()
            update_skills()
        if game_over:
            on_death()
    elif state == "gameover":
        panel_t += dt
        flash = max(0.0, flash - dt * 3)
        if not die_played and panel_t > 0.2:        # suara jatuh menyusul setelah benturan
            play("die")
            die_played = True
        if bird.y < GAME_HEIGHT - bird_height:      # burung jatuh setelah mati
            velocity_y += gravity
            bird.y += velocity_y
            bird.y = min(bird.y, GAME_HEIGHT - bird_height)

    # ---- gambar ----
    if state == "menu":
        draw_menu(t)
    elif state == "ready":
        draw_ready(t)
    elif state == "playing":
        draw()
        draw_coins(t)
        draw_items(t)
        draw_coin_hud(run_coins)
        draw_skill_hud()
    elif state == "gameover":
        draw()
        draw_coins(t)
        draw_game_over()
        draw_flash()
    elif state == "score":
        window.blit(background_imaege, (0, 0))
        outlined_text("Score", msg_font, (252, 160, 70), (GAME_WIDTH // 2, 150), thick=3, shadow=3)
        draw_panel(320, last_score, best_score, False)
        draw_coin_hud(total_coins)
        back_btn.draw()

    pygame.display.update()
    dt = Clock.tick(60) / 1000