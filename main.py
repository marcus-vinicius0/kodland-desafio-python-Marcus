import math
import random
from pygame import Rect
from pgzero.keyboard import keys

WIDTH = 800
HEIGHT = 600

TILE = 48
ROWS = HEIGHT // TILE
COLS = WIDTH // TILE

STATE_MENU = 0
STATE_PLAYING = 1
STATE_GAMEOVER = 2

game_state = STATE_MENU
sound_on = True

mouse_held = False
last_mouse_pos = (0, 0)

MENU_MUSIC = "bgm"
GAME_MUSIC = "bgm"

_bg_music_started = False
_last_sound_fallback = None

# Função utilitária: limita um valor ao intervalo [a, b]
def clamp(v, a, b):
    return max(a, min(b, v))

# Carrega uma sequência de frames de imagens com prefixo
def load_frames(prefix):
    frames = []
    i = 0
    while True:
        name = f"{prefix}_{i}"
        try:
            surf = getattr(images, name)
        except Exception:
            break
        frames.append(surf)
        i += 1
    return frames

class Button:
    # Construtor do botão: texto, posição e tamanho
    def __init__(self, text, x, y, w, h):
        self.text = text
        self.rect = Rect(x, y, w, h)
        self.hover = False

    # Desenha o botão na tela
    def draw(self):
        color = (200, 200, 255) if self.hover else (180, 180, 220)
        screen.draw.filled_rect(self.rect, color)
        screen.draw.rect(self.rect, (30, 30, 50))
        screen.draw.text(self.text, center=self.rect.center, color="black", fontsize=28)

    # Retorna True se a posição passada estiver sobre o botão
    def is_hover(self, pos):
        return self.rect.collidepoint(pos)

class Character:
    # Construtor base para personagens 
    def __init__(self, r, c, color=(255, 255, 255)):
        self.row = r
        self.col = c
        self.x = c * TILE + TILE // 2
        self.y = r * TILE + TILE // 2
        self.target_r = r
        self.target_c = c
        self.color = color
        self.speed = 4.0
        self.frame = 0
        self.facing = "down"
        self.alive = True

    # Define o alvo (target) em termos de célula r,c e ajusta a direção
    def set_target(self, r, c):
        r = clamp(r, 0, ROWS - 1)
        c = clamp(c, 0, COLS - 1)
        if (r, c) == (self.target_r, self.target_c):
            return
        self.target_r = r
        self.target_c = c
        dr = r - self.row
        dc = c - self.col
        if abs(dr) > abs(dc):
            self.facing = "down" if dr > 0 else "up"
        else:
            self.facing = "right" if dc > 0 else "left"

    # Retorna True se o personagem alcançou o alvo
    def at_target(self):
        target_x = self.target_c * TILE + TILE // 2
        target_y = self.target_r * TILE + TILE // 2
        return math.hypot(self.x - target_x, self.y - target_y) < 1.5

    # Atualiza a posição
    def update_position(self):
        target_x = self.target_c * TILE + TILE // 2
        target_y = self.target_r * TILE + TILE // 2
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)
        if dist <= self.speed or dist < 1:
            self.x = target_x
            self.y = target_y
            self.row = self.target_r
            self.col = self.target_c
        else:
            vx = (dx / dist) * self.speed
            vy = (dy / dist) * self.speed
            self.x += vx
            self.y += vy

    # Atualiza estado genérico do personagem (posição e frame)
    def update(self):
        self.update_position()
        self.frame = (self.frame + 1) % 10000

    # Desenha o personagem (delegando para draw_body)
    def draw(self):
        moving = not self.at_target()
        self.draw_body(screen, self.frame, moving)

    # Método placeholder para desenhar o corpo — implementado nas subclasses
    def draw_body(self, s, frame, moving):
        pass

class Hero(Character):
    # Construtor do herói: vida, animações e parâmetros
    def __init__(self, r, c):
        super().__init__(r, c)
        self.hp = 5
        self.hurt_cooldown = 0
        self.speed = 5.5
        self.fire_cooldown = 0
        self.state = "idle"
        self.current_frame = 0
        self.frame_timer = 0
        self.anim_speed = 6
        self.idle_frames = load_frames("hero_idle")
        self.walk_frames = load_frames("hero_walk")
        self.hurt_frames = load_frames("hero_hurt")

    # Atualiza estado e animação do herói
    def update(self):
        super().update()
        moving = not self.at_target()
        if self.hurt_cooldown > 0:
            self.state = "hurt"
            self.hurt_cooldown -= 1
        elif moving:
            self.state = "walk"
        else:
            self.state = "idle"
        self.frame_timer += 1
        if self.frame_timer >= self.anim_speed:
            self.frame_timer = 0
            self.current_frame += 1
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1

    # Desenha o herói de acordo com o estado/frames carregados
    def draw_body(self, s, frame, moving):
        if self.state == "walk":
            frames = self.walk_frames
        elif self.state == "hurt":
            frames = self.hurt_frames
        else:
            frames = self.idle_frames
        idx = self.current_frame % len(frames) if len(frames) > 0 else 0
        surf = frames[idx] if len(frames) > 0 else None
        if surf:
            w, h = surf.get_width(), surf.get_height()
            draw_x = int(self.x) - w // 2
            draw_y = int(self.y) - h // 2
            s.surface.blit(surf, (draw_x, draw_y))
        else:
            screen.draw.filled_circle((int(self.x), int(self.y)), 10, (200, 200, 255))

class Enemy(Character):
    # Construtor do inimigo: vida, animações, patrulha e flag para som de morte
    def __init__(self, r, c, hp=2):
        super().__init__(r, c, (220, 70, 70))
        self.hp = hp
        self.hurt_cooldown = 0
        self.state = "appear"
        self.current_frame = 0
        self.frame_timer = 0
        self.anim_speed = 6
        self.appear_frames = load_frames("enemy_appear")
        self.walk_frames = load_frames("enemy_walk")
        self.die_frames = load_frames("enemy_die")
        self.speed = 3.2
        r0 = max(1, r - 1)
        c0 = max(1, c - 1)
        self.territory = (r0, c0, 3, 3)
        self.patrol_points = self._generate_patrol()
        self.p_index = 0
        self.set_target(r, c)
        # flag para garantir que o som de morte toque apenas uma vez
        self.death_sound_played = False

    def _generate_patrol(self):
        r0, c0, rows, cols = self.territory
        pts = [(r0, c0), (r0 + rows - 1, c0), (r0 + rows - 1, c0 + cols - 1), (r0, c0 + cols - 1)]
        return pts

    # Atualiza animações, comportamento (seguir jogador ou patrulhar) e trata morte/anim. de morte
    def update(self):
        self.frame_timer += 1
        if self.frame_timer >= self.anim_speed:
            self.frame_timer = 0
            self.current_frame += 1
        if self.state == "appear":
            if self.current_frame >= len(self.appear_frames):
                self.state = "walk"
                self.current_frame = 0
        elif self.state == "walk":
            try:
                if player and player.alive:
                    self.set_target(player.row, player.col)
            except NameError:
                if self.at_target() and self.patrol_points:
                    self.p_index = (self.p_index + 1) % len(self.patrol_points)
                    self.set_target(*self.patrol_points[self.p_index])
            super().update()
            if self.hp <= 0:
                # entra no estado de morte
                if not self.death_sound_played:
                    try:
                        if sound_on and hasattr(sounds, "enemy_die"):
                            sounds.enemy_die.play()
                        else:
                            # fallback razoável
                            if sound_on and hasattr(sounds, "ui_toggle"):
                                sounds.ui_toggle.play()
                    except Exception:
                        pass
                    self.death_sound_played = True
                self.state = "die"
                self.current_frame = 0
        elif self.state == "die":
            if self.current_frame >= len(self.die_frames):
                self.alive = False
        if self.hurt_cooldown > 0:
            self.hurt_cooldown -= 1

    # Desenha o inimigo com a animação correspondente ao estado
    def draw_body(self, s, frame, moving):
        if self.state == "appear":
            frames = self.appear_frames
        elif self.state == "walk":
            frames = self.walk_frames
        else:
            frames = self.die_frames
        idx = self.current_frame % len(frames) if len(frames) > 0 else 0
        surf = frames[idx] if len(frames) > 0 else None
        if surf:
            w = surf.get_width()
            h = surf.get_height()
            draw_x = int(self.x) - w // 2
            draw_y = int(self.y) - h // 2
            s.surface.blit(surf, (draw_x, draw_y))
        else:
            screen.draw.filled_circle((int(self.x), int(self.y)), 10, (220, 70, 70))

class Projectile:
    # Construtor do projétil: posição, direção, velocidade, vida e dano
    def __init__(self, x, y, vx, vy, speed=12, life_frames=120, damage=1):
        self.x = x
        self.y = y
        mag = math.hypot(vx, vy)
        if mag == 0:
            self.vx = 0
            self.vy = 0
        else:
            self.vx = (vx / mag) * speed
            self.vy = (vy / mag) * speed
        self.life = life_frames
        self.damage = damage
        self.alive = True
        self.radius = 5

    # Atualiza posição do projétil e decremente sua vida
    def update(self):
        if not self.alive:
            return
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        if (self.x < -10 or self.x > WIDTH + 10 or
                self.y < -10 or self.y > HEIGHT + 10 or
                self.life <= 0):
            self.alive = False

    # Desenha o projétil
    def draw(self):
        if not self.alive:
            return
        screen.draw.filled_circle((int(self.x), int(self.y)), self.radius, (255, 240, 120))

    # Verifica colisão do projétil com um inimigo
    def collides_with_enemy(self, enemy):
        dx = self.x - enemy.x
        dy = self.y - enemy.y
        return math.hypot(dx, dy) < (self.radius + 12)

player = Hero(3, 3)
enemies = [Enemy(4, 10), Enemy(8, 6), Enemy(10, 12)]
projectiles = []

btn_start = Button("Start", WIDTH // 2 - 100, 160, 200, 56)
btn_toggle = Button("Sound: ON", WIDTH // 2 - 100, 240, 200, 56)
btn_exit = Button("Exit", WIDTH // 2 - 100, 320, 200, 56)

spawn_timer = 0
spawn_interval = 180
spawn_interval_min = 40
spawn_interval_decrease = 0.5
spawn_safe_distance = 6

level = 1
kills = 0
kills_to_next_level = 10
spawn_batch = 1

# Incrementa o nível e ajusta parâmetros de spawn
def level_up():
    global level, spawn_batch, spawn_interval, kills_to_next_level
    level += 1
    spawn_batch += 1
    spawn_interval = max(spawn_interval_min, spawn_interval - 10)
    kills_to_next_level = int(kills_to_next_level * 1.5)

# Tenta criar um inimigo em posição aleatória longe do jogador
def spawn_enemy_near_edge_or_random():
    MAX_TRIES = 40
    for _ in range(MAX_TRIES):
        rr = random.randint(0, ROWS - 1)
        cc = random.randint(0, COLS - 1)
        if math.hypot(rr - player.row, cc - player.col) >= spawn_safe_distance:
            return Enemy(rr, cc, hp=2)
    edges = []
    for i in range(COLS):
        edges.append((0, i)); edges.append((ROWS - 1, i))
    for j in range(ROWS):
        edges.append((j, 0)); edges.append((j, COLS - 1))
    random.shuffle(edges)
    for rr, cc in edges:
        if math.hypot(rr - player.row, cc - player.col) >= spawn_safe_distance:
            return Enemy(rr, cc, hp=2)
    rr = random.randint(0, ROWS - 1)
    cc = random.randint(0, COLS - 1)
    return Enemy(rr, cc, hp=2)

# Tenta tocar música de fundo
def try_play_bgm(track_name=MENU_MUSIC, volume=0.6):
    global sound_on, _last_sound_fallback
    if not sound_on:
        return
    try:
        music.play(track_name)
        music.set_volume(volume)
        _last_sound_fallback = None
        return
    except Exception:
        pass
    try:
        if hasattr(sounds, track_name):
            s = getattr(sounds, track_name)
            s.play()
            _last_sound_fallback = track_name
            return
    except Exception:
        pass
    try:
        if hasattr(sounds, "ui_toggle"):
            sounds.ui_toggle.play()
            _last_sound_fallback = "ui_toggle"
    except Exception:
        pass

# Alterna o som on/off e para/retoma músicas 
def toggle_sound():
    global sound_on, _last_sound_fallback
    sound_on = not sound_on
    if sound_on:
        try_play_bgm(MENU_MUSIC)
    else:
        try:
            music.stop()
        except Exception:
            pass
        try:
            if _last_sound_fallback and hasattr(sounds, _last_sound_fallback):
                s = getattr(sounds, _last_sound_fallback)
                try:
                    s.stop()
                except Exception:
                    pass
            _last_sound_fallback = None
        except Exception:
            _last_sound_fallback = None

# Função principal de atualização do jogo (lógica, movimentação, colisões, spawn)
def update():
    global game_state, enemies, projectiles, spawn_timer, spawn_interval, kills, mouse_held, last_mouse_pos
    if game_state == STATE_MENU:
        return
    if game_state == STATE_PLAYING:
        if player.at_target():
            try:
                if keyboard[keys.UP] or keyboard[keys.W]:
                    player.set_target(player.row - 1, player.col)
                elif keyboard[keys.DOWN] or keyboard[keys.S]:
                    player.set_target(player.row + 1, player.col)
                elif keyboard[keys.LEFT] or keyboard[keys.A]:
                    player.set_target(player.row, player.col - 1)
                elif keyboard[keys.RIGHT] or keyboard[keys.D]:
                    player.set_target(player.row, player.col + 1)
            except Exception:
                pass
        player.update()
        if mouse_held and player.fire_cooldown == 0:
            mx, my = last_mouse_pos
            sx = player.x; sy = player.y
            vx = mx - sx; vy = my - sy
            proj = Projectile(sx, sy, vx, vy, speed=12, life_frames=120, damage=1)
            projectiles.append(proj)
            player.fire_cooldown = 8
            try:
                if sound_on:
                    sounds.ui_toggle.play()
            except Exception:
                pass
        spawn_timer += 1
        if spawn_timer >= int(spawn_interval):
            spawn_timer = 0
            for _ in range(spawn_batch):
                enemies.append(spawn_enemy_near_edge_or_random())
            spawn_interval = max(spawn_interval_min, spawn_interval - spawn_interval_decrease)
        for e in enemies:
            e.update()
        for p in projectiles:
            p.update()

        died_now = []

        for p in projectiles:
            if not p.alive:
                continue
            for e in enemies:
                if not e.alive:
                    continue
                if getattr(e, "state", None) == "die":
                    continue
                if p.collides_with_enemy(e):
                    e.hp -= p.damage
                    e.hurt_cooldown = 12
                    p.alive = False
                    try:
                        if sound_on:
                            sounds.hit.play()
                    except Exception:
                        pass
                    if e.hp <= 0:
                        # se inimigo tiver animação de morte, colocamos no estado "die"
                        if getattr(e, "die_frames", None):
                            # toca som de morte uma vez (se ainda não tocou)
                            if not getattr(e, "death_sound_played", False):
                                try:
                                    if sound_on and hasattr(sounds, "enemy_die"):
                                        sounds.enemy_die.play()
                                    else:
                                        if sound_on and hasattr(sounds, "ui_toggle"):
                                            sounds.ui_toggle.play()
                                except Exception:
                                    pass
                                e.death_sound_played = True
                            e.state = "die"
                            e.current_frame = 0
                        else:
                            try:
                                if sound_on and hasattr(sounds, "enemy_die"):
                                    sounds.enemy_die.play()
                                else:
                                    if sound_on and hasattr(sounds, "ui_toggle"):
                                        sounds.ui_toggle.play()
                            except Exception:
                                pass
                            e.alive = False
                    break

        # remove inimigos mortos e atualiza kills
        prev_count = len(enemies)
        enemies[:] = [e for e in enemies if e.alive]
        removed = prev_count - len(enemies)
        if removed > 0:
            kills += removed

        projectiles[:] = [p for p in projectiles if p.alive]
        while kills >= kills_to_next_level:
            level_up()
        for e in enemies:
            if player.hurt_cooldown == 0:
                dx = player.x - e.x
                dy = player.y - e.y
                if math.hypot(dx, dy) < 22:
                    player.hp -= 1
                    player.hurt_cooldown = 40
                    try:
                        if sound_on:
                            sounds.hit.play()
                    except Exception:
                        pass
                    if player.hp <= 0:
                        game_state = STATE_GAMEOVER
                        break

# Desenha tudo na tela conforme o estado do jogo (menu, jogando, game over)
def draw():
    global _bg_music_started
    screen.clear()
    if game_state == STATE_MENU:
        if not _bg_music_started:
            _bg_music_started = True
            try_play_bgm(MENU_MUSIC)
        draw_menu()
    elif game_state == STATE_PLAYING:
        for r in range(0, HEIGHT, TILE):
            for c in range(0, WIDTH, TILE):
                color = (25, 60, 25) if ((r // TILE + c // TILE) % 2 == 0) else (20, 50, 20)
                screen.draw.filled_rect(Rect(c, r, TILE, TILE), color)
        for p in projectiles:
            p.draw()
        for e in enemies:
            e.draw()
        player.draw()
        screen.draw.text(f"HP: {player.hp}", (10, 6), fontsize=24, color="white")
        screen.draw.text(f"Level: {level}", (10, 34), fontsize=24, color="white")
        screen.draw.text(f"Kills: {kills}", (10, 56), fontsize=24, color="white")
        screen.draw.text(f"Kills to next: {kills_to_next_level - kills}", (10, 76), fontsize=24, color="white")
        screen.draw.text(f"Enemies: {len(enemies)}", (10, 96), fontsize=24, color="white")
    elif game_state == STATE_GAMEOVER:
        screen.fill((0, 0, 0))
        screen.draw.text("GAME OVER", center=(WIDTH // 2, HEIGHT // 2 - 20), fontsize=72, color="red")
        screen.draw.text("Click to return to menu", center=(WIDTH // 2, HEIGHT // 2 + 40), fontsize=28, color="white")

# Desenha o menu principal (título e botões)
def draw_menu():
    screen.fill((30, 30, 40))
    screen.draw.text("Ataque de Zumbis", center=(WIDTH // 2, 80), fontsize=34, color="white")
    btn_start.draw()
    btn_toggle.text = "Sound: ON" if sound_on else "Sound: OFF"
    btn_toggle.draw()
    btn_exit.draw()

# Evento: movimento do mouse — atualiza posição e hover dos botões
def on_mouse_move(pos):
    global last_mouse_pos
    last_mouse_pos = pos
    for b in (btn_start, btn_toggle, btn_exit):
        b.hover = b.is_hover(pos)

# Evento: pressionamento do mouse — trata cliques no menu e ações em jogo
def on_mouse_down(pos):
    global game_state, player, enemies, projectiles
    global spawn_timer, spawn_interval, spawn_batch
    global level, kills, kills_to_next_level
    global mouse_held, last_mouse_pos, _last_sound_fallback, _bg_music_started

    mx, my = pos
    last_mouse_pos = pos
    mouse_held = True

    if game_state == STATE_MENU:
        if btn_start.is_hover(pos):
            player = Hero(3, 3)
            enemies = [Enemy(4, 10), Enemy(8, 6), Enemy(10, 12)]
            projectiles = []
            spawn_timer = 0
            spawn_interval = 180
            spawn_batch = 1
            level = 1
            kills = 0
            kills_to_next_level = 10
            try:
                music.stop()
            except Exception:
                pass
            try:
                if _last_sound_fallback and hasattr(sounds, _last_sound_fallback):
                    s = getattr(sounds, _last_sound_fallback)
                    try:
                        s.stop()
                    except Exception:
                        pass
                _last_sound_fallback = None
            except Exception:
                _last_sound_fallback = None
            try:
                if sound_on:
                    try_play_bgm(GAME_MUSIC)
            except Exception:
                pass
            _bg_music_started = False
            game_state = STATE_PLAYING
        elif btn_toggle.is_hover(pos):
            toggle_sound()
        elif btn_exit.is_hover(pos):
            exit()
    elif game_state == STATE_PLAYING:
        try:
            if player.fire_cooldown == 0:
                sx = player.x; sy = player.y
                vx = mx - sx; vy = my - sy
                proj = Projectile(sx, sy, vx, vy, speed=12, life_frames=120, damage=1)
                projectiles.append(proj)
                player.fire_cooldown = 8
                try:
                    if sound_on:
                        sounds.ui_toggle.play()
                except Exception:
                    pass
        except Exception:
            tr = my // TILE
            tc = mx // TILE
            player.set_target(tr, tc)
    elif game_state == STATE_GAMEOVER:
        game_state = STATE_MENU
        try:
            music.stop()
        except Exception:
            pass
        try:
            if _last_sound_fallback and hasattr(sounds, _last_sound_fallback):
                s = getattr(sounds, _last_sound_fallback)
                try:
                    s.stop()
                except Exception:
                    pass
            _last_sound_fallback = None
        except Exception:
            _last_sound_fallback = None
        if sound_on:
            try:
                try_play_bgm(MENU_MUSIC)
                _bg_music_started = True
            except Exception:
                pass

# Evento: soltar o botão do mouse — para o disparo contínuo
def on_mouse_up(pos):
    global mouse_held, last_mouse_pos
    mouse_held = False
    last_mouse_pos = pos

# Evento: tecla pressionada
def on_key_down(key):
    if game_state != STATE_PLAYING:
        return
    if key == keys.SPACE:
        if player.facing == "up":
            player.set_target(player.row - 2, player.col)
        elif player.facing == "down":
            player.set_target(player.row + 2, player.col)
        elif player.facing == "left":
            player.set_target(player.row, player.col - 2)
        elif player.facing == "right":
            player.set_target(player.row, player.col + 2)
