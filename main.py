from browser import document, window, timer, html
import math
import random

canvas = document["gameCanvas"]
ctx = canvas.getContext("2d")

intro_screen = document["intro-screen"]
intro_text = document["intro-text"]
map_screen = document["map-screen"]
map_nodes_container = document["map-nodes"]
game_ui = document["game-ui"]

hud_level_theme = document["hud-level-theme"]
hud_level = document["hud-level"]
progress_bar = document["progress-bar"]
progress_text = document["progress-text"]
hud_messages = document["hud-messages"]
canvas_bg = document["canvas-bg"]

# Levels Definition with Themes
levels = [
    {"id": 1, "theme": "Floresta Sombria", "vel": 6, "bg1": "#0B1A0B", "bg2": "#142E14", "p_color": "#44FF44", "obs_color": "#CD853F", "length": 6000},
    {"id": 2, "theme": "Ruínas do Deserto", "vel": 7, "bg1": "#2B1A04", "bg2": "#402705", "p_color": "#FFC04C", "obs_color": "#E64A19", "length": 8000},
    {"id": 3, "theme": "Oceano Profundo", "vel": 7.5, "bg1": "#001026", "bg2": "#00204A", "p_color": "#00FFFF", "obs_color": "#FF00AA", "length": 10000},
    {"id": 4, "theme": "Caverna de Lava", "vel": 8, "bg1": "#260000", "bg2": "#4A0000", "p_color": "#FF3300", "obs_color": "#FFFF00", "length": 12000},
    {"id": 5, "theme": "Cidade Cyberneo", "vel": 8.5, "bg1": "#12002B", "bg2": "#2C0052", "p_color": "#FF00FF", "obs_color": "#00FFFF", "length": 14000},
    {"id": 6, "theme": "Tundra Gelada", "vel": 9, "bg1": "#002233", "bg2": "#0A3D59", "p_color": "#E0FFFF", "obs_color": "#0055FF", "length": 16000},
    {"id": 7, "theme": "Pântano Tóxico", "vel": 9.5, "bg1": "#1A2209", "bg2": "#293A0D", "p_color": "#BFFF00", "obs_color": "#800080", "length": 18000},
    {"id": 8, "theme": "Caverna de Cristal", "vel": 10, "bg1": "#330022", "bg2": "#550033", "p_color": "#FF66B2", "obs_color": "#00FFFF", "length": 20000},
    {"id": 9, "theme": "Galáxia Sombria", "vel": 11, "bg1": "#050011", "bg2": "#110022", "p_color": "#FFFFFF", "obs_color": "#FF0000", "length": 22000},
    {"id": 10, "theme": "Núcleo Glitch", "vel": 12, "bg1": "#000000", "bg2": "#110000", "p_color": "#FF0000", "obs_color": "#FFFFFF", "length": 25000}
]

class AudioSystem:
    def __init__(self):
        self.audio = window.Audio.new()
        self.audio.loop = True
    
    def play(self, lvl_id):
        self.audio.src = f"assets/level{lvl_id}.mp3"
        try:
            self.audio.play()
        except:
            pass
    
    def stop(self):
        self.audio.pause()
        self.audio.currentTime = 0

class Particle:
    def __init__(self, x, y, color, is_bg=False):
        self.x = x
        self.y = y
        self.is_bg = is_bg
        self.size = random.uniform(1, 4) if not is_bg else random.uniform(2, 6)
        self.speed_x = random.uniform(-3, -1) if not is_bg else random.uniform(-10, -5)
        self.speed_y = random.uniform(-2, 2) if not is_bg else 0
        self.life = 100 if not is_bg else 200
        self.color = color

    def update(self):
        self.x += self.speed_x
        if not self.is_bg:
            self.y += self.speed_y
            self.life -= 2
        else:
            if self.x < -10:
                self.x = 810
                self.y = random.uniform(0, 400)

    def draw(self):
        ctx.fillStyle = self.color
        if not self.is_bg:
            ctx.globalAlpha = max(0, self.life / 100)
        ctx.beginPath()
        ctx.arc(self.x, self.y, self.size, 0, math.pi * 2)
        ctx.fill()
        ctx.globalAlpha = 1.0

class Player:
    def __init__(self):
        self.x = 100
        self.y = 370
        self.w = 30
        self.h = 30
        self.y_vel = 0
        self.gravity = 1.0
        self.jump_power = -13
        self.on_ground = True
        self.rotation = 0

    def jump(self):
        if self.on_ground:
            self.y_vel = self.jump_power
            self.on_ground = False
            
    def pad_jump(self):
        self.y_vel = -22 # Super jump impulse
        self.on_ground = False
        show_hud_message("SUPER PULO!", "#00FFFF")

    def update(self):
        self.y_vel += self.gravity
        self.y += self.y_vel

        # Floor bounds
        if self.y >= 370:
            self.y = 370
            self.y_vel = 0
            self.on_ground = True
            self.rotation = round(self.rotation / 90) * 90
        else:
            self.rotation += 6

    def draw(self, color):
        ctx.save()
        ctx.fillStyle = color
        ctx.shadowBlur = 20
        ctx.shadowColor = color
        
        ctx.translate(self.x + self.w/2, self.y + self.h/2)
        ctx.rotate(self.rotation * math.pi / 180)
        
        ctx.fillRect(-self.w/2, -self.h/2, self.w, self.h)
        ctx.restore()

class GameState:
    def __init__(self):
        self.unlocked_levels = 1
        self.current_level = 0
        self.level_data = levels[0]
        self.distance = 0
        self.checkpoint = 0
        self.is_running = False
        self.obstacles = []
        self.particles = []
        self.bg_particles = []
        self.audio = AudioSystem()
        self.speed_boost = 0
        self.speed_boost_timer = 0
        
        self.player = Player()

    def generate_obstacles(self):
        self.obstacles = []
        base_spacing = 450 - (self.level_data["vel"] * 10)
        curr_x = 800
        
        while curr_x < self.level_data["length"]:
            spacing = max(base_spacing, 180)
            
            # Decide o padrao do bloco gerado
            rand = random.random()
            
            # Forçar checkpoint a cada ~2500 px
            if int(curr_x) % 2500 < int(spacing):
                self.obstacles.append({"type": "checkpoint", "x": curr_x, "y": 320, "w": 20, "h": 20, "captured": False})
            elif rand < 0.15:
                # Pad Jump + Armadilha no alto ou no chão
                self.obstacles.append({"type": "pad_jump", "x": curr_x, "y": 385, "w": 40, "h": 15})
                # Depois que pular é obrigado a flutuar porque tem espetos no chao logo apos
                self.obstacles.append({"type": "spike", "x": curr_x + 250, "y": 370, "w": 30, "h": 30})
                self.obstacles.append({"type": "spike", "x": curr_x + 280, "y": 370, "w": 30, "h": 30})
                curr_x += 350
            elif rand < 0.25:
                # Speed Boost / Dash Plate
                self.obstacles.append({"type": "pad_speed", "x": curr_x, "y": 385, "w": 40, "h": 15})
            elif rand < 0.6:
                # Spikes triplos ou duplos
                count = random.choice([2, 3])
                for i in range(count):
                    self.obstacles.append({"type": "spike", "x": curr_x + (i * 30), "y": 370, "w": 30, "h": 30})
            else:
                # Spike simples e isolado
                self.obstacles.append({"type": "spike", "x": curr_x, "y": 370, "w": 30, "h": 30})
                
            curr_x += random.uniform(spacing, spacing * 2.2)

state = GameState()

# UI System
def show_hud_message(text, color):
    hud_messages.innerHTML = text
    hud_messages.style.color = color
    hud_messages.style.textShadow = f"0 0 20px {color}, 0 0 40px {color}"
    hud_messages.classList.add("message-active")
    timer.set_timeout(lambda: hud_messages.classList.remove("message-active"), 1000)

def init_bg_particles():
    state.bg_particles = []
    # Cria particulas decorativas
    for _ in range(30):
        state.bg_particles.append(Particle(random.uniform(0, 800), random.uniform(0, 400), state.level_data["p_color"], is_bg=True))

def draw_hud():
    prog_pct = (state.distance / state.level_data["length"]) * 100
    if prog_pct > 100: prog_pct = 100
    progress_bar.style.width = f"{prog_pct}%"
    progress_text.innerHTML = f"{int(prog_pct)}%"
    
    # Cores fixas HUD
    hud_level_theme.style.color = state.level_data["p_color"]
    hud_level.style.color = "#FFF"

# Render Drawers
def draw_spike(x, y, w, h, color):
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

def draw_pad_jump(x, y, w, h):
    ctx.fillStyle = "#00FFFF"
    ctx.shadowBlur = 20
    ctx.shadowColor = "#00FFFF"
    ctx.fillRect(x, y-h, w, h)
    ctx.fillStyle = "#FFF"
    ctx.fillRect(x+5, y-h-5, w-10, 5) # detale de impulsao
    ctx.shadowBlur = 0

def draw_pad_speed(x, y, w, h):
    ctx.fillStyle = "#00FF00"
    ctx.shadowBlur = 20
    ctx.shadowColor = "#00FF00"
    # Forma poligonal indicando aceleracao
    ctx.beginPath()
    ctx.moveTo(x, y)
    ctx.lineTo(x+w, y)
    ctx.lineTo(x+w/2, y-h)
    ctx.fill()
    ctx.shadowBlur = 0

def draw_checkpoint(x, y, color):
    ctx.fillStyle = color
    ctx.shadowBlur = 25
    ctx.shadowColor = color
    ctx.beginPath()
    ctx.arc(x, y, 15, 0, math.pi * 2)
    ctx.fill()
    ctx.fillStyle = "#FFF"
    ctx.beginPath()
    ctx.arc(x, y, 6, 0, math.pi * 2)
    ctx.fill()
    ctx.shadowBlur = 0

# Game Engine Loop
def update(*args):
    if not state.is_running:
        return
        
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    
    # Progressão Gradativa Local (A velocidade base cresce conforme a distancia aumenta + boosts)
    vel_increase = state.distance / 2500.0  
    dynamic_vel = state.level_data["vel"] + vel_increase + state.speed_boost
    
    # Processa timer de boost
    if state.speed_boost_timer > 0:
        state.speed_boost_timer -= 1
        if state.speed_boost_timer <= 0:
            state.speed_boost = 0
    
    state.distance += dynamic_vel
    
    # Fundo Paralaxe (Particulas do Background vindo em sua direcao)
    for p in state.bg_particles:
        p.speed_x = -dynamic_vel * 1.5
        p.update()
        p.draw()
        
    # Piso Base
    ctx.fillStyle = "rgba(255,255,255,0.05)"
    ctx.fillRect(0, 370, canvas.width, 30)
    
    # Fisica e Inputs do Player
    state.player.update()
    
    # Rastro visual do Player 
    if not state.player.on_ground or state.speed_boost > 0:
        state.particles.append(Particle(state.player.x + state.player.w/2, state.player.y + state.player.h, state.level_data["p_color"]))
    
    for p in state.particles[:]:
        p.update()
        if p.life <= 0:
            state.particles.remove(p)
        else:
            p.draw()
            
    # Traçar Player final
    state.player.draw(state.level_data["p_color"])
    
    # Renderizador de Obstaculos Complexos
    for obs in state.obstacles:
        rel_x = obs["x"] - state.distance
        # Verifica visibilidade e colisao O(n) na tela
        if rel_x < 850 and rel_x > -100:
            t = obs["type"]
            y = obs["y"]
            w = obs["w"]
            h = obs["h"]
            
            p = state.player
            
            if t == "spike":
                draw_spike(rel_x, y + h, w, h, state.level_data["obs_color"])
                
                # AABB Hitbox - Reduzida nas bordas para jogo justo
                if (p.x < rel_x + w - 8 and 
                    p.x + p.w > rel_x + 8 and 
                    p.y < y + h and 
                    p.y + p.h > y + 8):
                    die()
                    return
            
            elif t == "pad_jump":
                draw_pad_jump(rel_x, y + h, w, h)
                
                # AABB Hitbox para propulsao
                if p.y + p.h >= y and p.x + p.w > rel_x and p.x < rel_x + w:
                    state.player.pad_jump()
            
            elif t == "pad_speed":
                draw_pad_speed(rel_x, y + h, w, h)
                
                if p.x + p.w > rel_x and p.x < rel_x + w and p.y + p.h >= y - h:
                    if state.speed_boost == 0:
                        state.speed_boost = 6
                        state.speed_boost_timer = 120 # Dura +- 2 segundos focado (60fps)
                        show_hud_message("DASH OVERDRIVE!", "#00FF00")
            
            elif t == "checkpoint":
                if not obs["captured"]:
                    draw_checkpoint(rel_x + w/2, y, "#00FF66")
                
                # Colisao fantasma no eixo X para ativar checkpoint
                if rel_x < p.x and not obs["captured"]:
                    state.checkpoint = obs["x"] - 250
                    obs["captured"] = True
                    show_hud_message("CHECKPOINT", "#00FF66")

    # Finaliza quadro da HUD interativa
    draw_hud()
    
    # Checar Vitoria Final
    if state.distance >= state.level_data["length"]:
        win_level()
        return

    # Loop Infinito
    window.requestAnimationFrame(update)


# Handlers & Callbacks Principais
def die():
    state.is_running = False
    state.audio.stop()
    canvas.style.opacity = "0.2"
    show_hud_message("DESTRUÍDO", "#FF0000")
    
    def recover():
        restart_from_checkpoint()
    timer.set_timeout(recover, 800)

def restart_from_checkpoint():
    canvas.style.opacity = "1"
    state.distance = state.checkpoint
    state.particles = []
    state.player.y = 370
    state.player.y_vel = 0
    state.player.on_ground = True
    start_level(state.current_level, resume=True)

def win_level():
    state.is_running = False
    state.audio.stop()
    show_hud_message("ESTÁGIO COMPLETO!", "#FFF")
    
    # Desbloqueia prox fase no mapa
    if state.current_level + 2 > state.unlocked_levels:
        state.unlocked_levels = min(state.current_level + 2, len(levels))
        
    timer.set_timeout(open_map_screen, 2500)

def start_level(idx, resume=False):
    state.current_level = idx
    state.level_data = levels[idx]
    
    # Configura Dados da HUD
    hud_level.innerHTML = f"Fase {state.level_data['id']}"
    hud_level_theme.innerHTML = f"» {state.level_data['theme']} «"
    
    # Troca de Tema Dinâmica no Fundo! 
    bg_gradient = f"linear-gradient(135deg, {state.level_data['bg1']} 0%, {state.level_data['bg2']} 100%)"
    canvas_bg.style.background = bg_gradient
    
    if not resume:
        # Reseta variaveis da tentativa
        state.distance = 0
        state.checkpoint = 0
        state.speed_boost = 0
        state.speed_boost_timer = 0
        state.particles = []
        state.generate_obstacles()
        init_bg_particles()
        
    canvas.style.opacity = "1"
    
    # Transicao de UI DOM Web
    map_screen.style.display = "none"
    intro_screen.style.display = "none"
    canvas.style.display = "block"
    game_ui.style.display = "flex"
    
    state.audio.play(state.level_data["id"])
    state.is_running = True
    window.requestAnimationFrame(update)

# Interface de Seleção de Mapas (Mapa Mundi Node)
def open_map_screen():
    # Hide Others
    game_ui.style.display = "none"
    canvas.style.display = "none"
    
    # Show Map
    map_screen.style.display = "flex"
    map_screen.style.opacity = "0"
    
    # Popula Arvore de Níveis
    map_nodes_container.innerHTML = ""
    
    for i in range(len(levels)):
        lvl = levels[i]
        node = html.DIV(str(lvl["id"]), Class="map-node")
        
        # O Brython precisa capturar a variavel lexical atual no for loop, e closures nativas do Python funcionam dif:
        def bind_click(level_idx):
            def on_click(ev):
                start_level(level_idx)
            return on_click

        if i < state.unlocked_levels:
            node.classList.add("unlocked")
            node.bind("click", bind_click(i))
            node.title = lvl["theme"]
        else:
            node.classList.add("locked")
            node.title = "Acesso Negado (Bloqueado)"
            
        map_nodes_container <= node
        
    def fade_in():
        map_screen.style.opacity = "1"
    timer.set_timeout(fade_in, 50)


# Apresentação Inicial (Intro)
intro_step = 0
intro_sentences = [
    "Bem-vindo à Nova Era",
    "Gravity Dash Thematic",
    "Prepare-se para o Maior Desafio..."
]

def run_intro():
    global intro_step
    intro_step = 0
    intro_screen.style.opacity = "1"
    
    def show_sentence():
        global intro_step
        if intro_step >= len(intro_sentences):
            intro_screen.style.opacity = "0"
            timer.set_timeout(open_map_screen, 1000)
            return
            
        intro_text.innerHTML = intro_sentences[intro_step]
        intro_screen.style.opacity = "1"
        
        def fade():
            intro_screen.style.opacity = "0"
            global intro_step
            intro_step += 1
            timer.set_timeout(show_sentence, 800)
            
        timer.set_timeout(fade, 2200)

    show_sentence()

# Sistema de Entradas / Captura Teclado
def on_keydown(ev):
    if state.is_running and ev.code == "Space":
        ev.preventDefault()
        state.player.jump()

def on_mousedown(ev):
    if state.is_running:
        state.player.jump()

document.bind("keydown", on_keydown)
canvas.bind("mousedown", on_mousedown)

# Botar pra Rolar a Engine
run_intro()
