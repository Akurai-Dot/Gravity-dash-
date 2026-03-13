from browser import document, window, timer
import math
import random

canvas = document["gameCanvas"]
ctx = canvas.getContext("2d")

intro_screen = document["intro-screen"]
intro_text = document["intro-text"]
game_ui = document["game-ui"]
progress_bar = document["progress-bar"]
hud_level = document["hud-level"]

levels = [
    {"id": 1, "vel": 5, "bg": "#0D0D12", "p_color": "#00D2FF", "obs_color": "#FF4B2B", "length": 5000, "music": "level1.mp3"},
    {"id": 2, "vel": 6, "bg": "#1A0020", "p_color": "#00FFC4", "obs_color": "#E50055", "length": 6500, "music": "level2.mp3"},
    {"id": 3, "vel": 7, "bg": "#051A05", "p_color": "#FF00FF", "obs_color": "#FFFF00", "length": 8000, "music": "level3.mp3"},
    {"id": 4, "vel": 8, "bg": "#2A0B00", "p_color": "#FFAA00", "obs_color": "#00D2FF", "length": 10000, "music": "level4.mp3"},
    {"id": 5, "vel": 9, "bg": "#12003B", "p_color": "#00FFFF", "obs_color": "#FF00AA", "length": 12000, "music": "level5.mp3"},
    {"id": 6, "vel": 10, "bg": "#222200", "p_color": "#FF0000", "obs_color": "#00FF00", "length": 14000, "music": "level6.mp3"},
    {"id": 7, "vel": 11, "bg": "#00202A", "p_color": "#0000FF", "obs_color": "#FFA500", "length": 16000, "music": "level7.mp3"},
    {"id": 8, "vel": 12, "bg": "#330000", "p_color": "#FFFFFF", "obs_color": "#FF0000", "length": 18000, "music": "level8.mp3"},
    {"id": 9, "vel": 13, "bg": "#1A1A1A", "p_color": "#FFFF00", "obs_color": "#FF00FF", "length": 20000, "music": "level9.mp3"},
    {"id": 10, "vel": 14, "bg": "#000000", "p_color": "#00D2FF", "obs_color": "#FFFFFF", "length": 22000, "music": "level10.mp3"}
]

class AudioSystem:
    def __init__(self):
        self.audio = window.Audio.new()
        self.audio.loop = True
    
    def play(self, src):
        self.audio.src = f"assets/{src}"
        try:
            self.audio.play()
        except:
            pass
    
    def stop(self):
        self.audio.pause()
        self.audio.currentTime = 0

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.size = random.uniform(1, 4)
        self.speed_x = random.uniform(-2, -0.5)
        self.speed_y = random.uniform(-1, 1)
        self.life = 100
        self.color = color

    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.life -= 2

    def draw(self):
        ctx.fillStyle = self.color
        ctx.globalAlpha = self.life / 100
        ctx.beginPath()
        ctx.arc(self.x, self.y, self.size, 0, math.pi * 2)
        ctx.fill()
        ctx.globalAlpha = 1.0

class GameState:
    def __init__(self):
        self.current_level = 0
        self.level_data = levels[self.current_level]
        self.distance = 0
        self.checkpoint = 0
        self.is_running = False
        self.obstacles = []
        self.particles = []
        self.audio = AudioSystem()
        self.generate_obstacles()
        
    def next_level(self):
        self.current_level += 1
        if self.current_level >= len(levels):
            # Final do jogo
            self.current_level = 0
            self.success_end()
            return
        self.reset_level_hard()

    def reset_level_hard(self):
        self.level_data = levels[self.current_level]
        self.distance = 0
        self.checkpoint = 0
        self.particles = []
        self.generate_obstacles()
        start_game_loop()

    def reset_after_death(self):
        self.distance = self.checkpoint
        self.particles = []
        player.y = 370
        player.y_vel = 0
        player.on_ground = True
        start_game_loop()

    def generate_obstacles(self):
        self.obstacles = []
        spacing = max(400 - (self.level_data["vel"] * 10), 180)
        curr_x = 800
        # Gera os obstaculos do nivel e checkpoints
        while curr_x < self.level_data["length"]:
            is_checkpoint = False
            # Coloca um checkpoint quase a cada 2000 pixels
            if int(curr_x) % 2000 < int(spacing): 
                is_checkpoint = True
                
            y_pos = 370
            count = random.choice([1, 1, 1, 2, 2, 3]) if self.level_data["vel"] > 7 else random.choice([1, 1, 2])
            
            # Adiciona Triangulos
            for i in range(count):
                self.obstacles.append({
                    "x": curr_x + (i * 30),
                    "y": y_pos,
                    "w": 30,
                    "h": 30,
                    "is_checkpoint": is_checkpoint and i == 0,
                    "captured": False
                })
            curr_x += random.uniform(spacing, spacing * 2.5)

    def success_end(self):
        self.is_running = False
        transition_screen("Fim de Jogo!\\nVocê zerou o Gravity Dash!", lambda: run_intro())

state = GameState()

class Player:
    def __init__(self):
        self.x = 100
        self.y = 370
        self.w = 30
        self.h = 30
        self.y_vel = 0
        self.gravity = 0.9
        self.jump_power = -13
        self.on_ground = True
        self.rotation = 0

    def jump(self):
        if self.on_ground:
            self.y_vel = self.jump_power
            self.on_ground = False

    def update(self):
        self.y_vel += self.gravity
        self.y += self.y_vel

        # Floor collision
        if self.y >= 370:
            self.y = 370
            self.y_vel = 0
            self.on_ground = True
            # Corrige a rotacao para 90 mutiplos
            self.rotation = round(self.rotation / 90) * 90
        else:
            self.rotation += 5

    def draw(self):
        ctx.save()
        ctx.fillStyle = state.level_data["p_color"]
        ctx.shadowBlur = 15
        ctx.shadowColor = state.level_data["p_color"]
        
        ctx.translate(self.x + self.w/2, self.y + self.h/2)
        ctx.rotate(self.rotation * math.pi / 180)
        
        ctx.fillRect(-self.w/2, -self.h/2, self.w, self.h)
        ctx.restore()

player = Player()

def on_keydown(ev):
    if ev.code == "Space":
        ev.preventDefault()
        player.jump()

def on_mousedown(ev):
    player.jump()

document.bind("keydown", on_keydown)
canvas.bind("mousedown", on_mousedown)

def draw_triangle(x, y, w, h, color):
    # Triangulo base a baixo, ponta a cima
    ctx.fillStyle = color
    ctx.shadowBlur = 15
    ctx.shadowColor = color
    ctx.beginPath()
    ctx.moveTo(x + w/2, y - h)
    ctx.lineTo(x + w, y)
    ctx.lineTo(x, y)
    ctx.closePath()
    ctx.fill()
    ctx.shadowBlur = 0
    
def draw_checkpoint(x, y, color):
    # Ponto de salvamento (Halo/Estrela verde)
    ctx.fillStyle = "#00FF66"
    ctx.shadowBlur = 25
    ctx.shadowColor = "#00FF66"
    ctx.beginPath()
    ctx.arc(x + 15, y - 50, 8, 0, math.pi * 2)
    ctx.fill()
    ctx.shadowBlur = 0

def update(*args):
    if not state.is_running:
        return
        
    # Bg clear
    ctx.fillStyle = state.level_data["bg"]
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    
    # Progress
    state.distance += state.level_data["vel"]
    prog_pct = (state.distance / state.level_data["length"]) * 100
    if prog_pct > 100: prog_pct = 100
    progress_bar.style.width = f"{prog_pct}%"
    
    # Floor
    ctx.fillStyle = "#111"
    ctx.fillRect(0, 400, canvas.width, 10)
    
    # Particles trail
    if not player.on_ground:
        state.particles.append(Particle(player.x + player.w/2, player.y + player.h, state.level_data["p_color"]))
    
    for p in state.particles[:]:
        p.update()
        if p.life <= 0:
            state.particles.remove(p)
        else:
            p.draw()
            
    # Update Player
    player.update()
    player.draw()
    
    # Update Obstacles
    for obs in state.obstacles:
        rel_x = obs["x"] - state.distance
        if rel_x < 850 and rel_x > -100:
            if obs["is_checkpoint"] and not obs["captured"]:
                draw_checkpoint(rel_x, obs["y"], state.level_data["obs_color"])
                
            draw_triangle(rel_x, obs["y"] + obs["h"], obs["w"], obs["h"], state.level_data["obs_color"])
            
            # Hitbox AABB: Reduzimos a hitbox do triangulo para ser menos punitivo
            if (player.x < rel_x + obs["w"] - 8 and
                player.x + player.w > rel_x + 8 and
                player.y < obs["y"] + obs["h"] and
                player.y + player.h > obs["y"] + 8):
                die()
                return
            
            # Checkpoint capture (Player past the checkpoint location)
            if obs["is_checkpoint"] and rel_x < player.x and not obs["captured"]:
                # Save just a bit before the checkpoint so we have reaction time
                state.checkpoint = obs["x"] - 200 
                obs["captured"] = True
                
    # Win Level Check
    if state.distance >= state.level_data["length"] + 800: # Padding beyond line
        win_level()
        return

    window.requestAnimationFrame(update)

def die():
    state.is_running = False
    state.audio.stop()
    # Efeito de Morte rápido
    canvas.style.opacity = "0.5"
    timer.set_timeout(lambda: restart_from_checkpoint(), 500)

def restart_from_checkpoint():
    canvas.style.opacity = "1"
    state.reset_after_death()

def win_level():
    state.is_running = False
    state.audio.stop()
    transition_screen(f"Nível {state.current_level + 1} Concluído!", state.next_level)

def start_game_loop():
    canvas.style.opacity = "1"
    state.audio.play(state.level_data["music"])
    hud_level.textContent = f"Level: {state.current_level + 1}"
    state.is_running = True
    window.requestAnimationFrame(update)

def transition_screen(text, callback):
    canvas.style.display = "none"
    game_ui.style.display = "none"
    intro_screen.style.display = "flex"
    intro_screen.style.opacity = "1"
    intro_text.innerHTML = text
    
    def fade_out_intro():
        intro_screen.style.opacity = "0"
        def finish_transition():
            intro_screen.style.display = "none"
            canvas.style.display = "block"
            game_ui.style.display = "flex"
            callback()
        timer.set_timeout(finish_transition, 1000)
        
    timer.set_timeout(fade_out_intro, 2000)

intro_step = 0
intro_sentences = [
    "Eric productions\napresenta...",
    "Gravity Dash",
    "Projeto escolar\nEtec MSA"
]

def run_intro():
    global intro_step
    intro_step = 0
    
    def show_sentence():
        global intro_step
        if intro_step >= len(intro_sentences):
            intro_text.innerHTML = "Clique para Começar"
            intro_text.style.cursor = "pointer"
            def begin(ev):
                intro_text.unbind("click", begin)
                transition_screen("Prepare-se...", start_game_loop)
            intro_text.bind("click", begin)
            return
            
        intro_text.innerHTML = intro_sentences[intro_step]
        intro_screen.style.opacity = "1"
        
        def fade():
            intro_screen.style.opacity = "0"
            global intro_step
            intro_step += 1
            timer.set_timeout(show_sentence, 1000)
            
        timer.set_timeout(fade, 2500)

    show_sentence()

# Inicia script
run_intro()
