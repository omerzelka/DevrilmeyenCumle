import pygame
import random
import sys
import math
import os

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Configuration ---
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60

# Background Colors for Split Screen
BG_COLOR1 = (175, 238, 238)  # Pale Turquoise (Player 1)
BG_COLOR2 = (255, 228, 196)  # Bisque (Player 2)
SUCCESS_COLOR = (144, 238, 144) # Light Green for success flash

BOX_COLORS = [
    (255, 182, 193), # Light Pink
    (152, 251, 152), # Pale Green
    (255, 253, 150), # Pastel Yellow
    (255, 218, 185), # Peach
    (230, 230, 250), # Lavender
]
TEXT_COLOR = (50, 50, 50)
HIGHLIGHT_COLOR = (255, 69, 0) # Red-Orange for selection
GRABBED_COLOR = (255, 215, 0)  # Gold for grabbed

def load_sentences(filename):
    try:
        with open(resource_path(filename), 'r', encoding='utf-8') as f:
            sentences = [line.strip() for line in f if line.strip()]
        return sentences
    except FileNotFoundError:
        print(f"Hata: {filename} dosyası bulunamadı.")
        sys.exit()

CORRECT_COLOR = (0, 180, 0)  # Green border for correct position
LOCKED_COLOR = (100, 100, 100)  # Gray for locked/hint blocks

class WordBlock:
    def __init__(self, text, color, font):
        self.text = text
        self.color = color
        self.font = font
        self.locked = False
        text_surface = self.font.render(self.text, True, TEXT_COLOR)
        self.width = text_surface.get_width() + 24
        self.height = text_surface.get_height() + 22
        self.target_x = 0
        self.target_y = 0
        self.x = -1000
        self.y = -1000
    
    def draw(self, surface, is_selected, is_grabbed, is_locked=False, is_correct=False):
        if self.x == -1000:
            self.x = self.target_x
            self.y = self.target_y

        self.x += (self.target_x - self.x) * 0.2
        self.y += (self.target_y - self.y) * 0.2

        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        shadow_rect = pygame.Rect(self.x + 4, self.y + 4, self.width, self.height)
        pygame.draw.rect(surface, (100, 150, 180), shadow_rect, border_radius=15)
        
        # Locked blocks get a slightly muted color
        if is_locked:
            draw_color = (200, 230, 200)  # Light green-ish for hint
        else:
            draw_color = self.color
        pygame.draw.rect(surface, draw_color, rect, border_radius=15)
        
        # Draw border based on state
        if is_locked:
            pygame.draw.rect(surface, (34, 139, 34), rect, width=4, border_radius=15)
            # Draw a lock icon with shapes
            lx, ly = int(rect.right - 22), int(rect.top + 4)
            pygame.draw.rect(surface, (80, 80, 80), (lx, ly + 6, 14, 10), border_radius=2)
            pygame.draw.arc(surface, (80, 80, 80), (lx + 2, ly, 10, 12), 0, math.pi, 2)
        elif is_grabbed:
            pygame.draw.rect(surface, GRABBED_COLOR, rect, width=8, border_radius=15)
        elif is_correct:
            pygame.draw.rect(surface, CORRECT_COLOR, rect, width=5, border_radius=15)
            # Draw a checkmark with lines
            cx, cy = int(rect.right - 20), int(rect.top + 8)
            pygame.draw.lines(surface, CORRECT_COLOR, False, [(cx, cy + 6), (cx + 5, cy + 12), (cx + 14, cy)], 3)
        elif is_selected:
            pygame.draw.rect(surface, HIGHLIGHT_COLOR, rect, width=6, border_radius=15)
            
        text_surface = self.font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=rect.center)
        surface.blit(text_surface, text_rect)

class Player:
    def __init__(self, p_id, rect, bg_color, sentences, font, score_font, inst_font):
        self.p_id = p_id
        self.rect = rect
        self.bg_color = bg_color
        self.sentences = sentences[:]
        random.shuffle(self.sentences) # Independent sequence
        self.font = font
        self.score_font = score_font
        self.inst_font = inst_font
        
        self.score = 0
        self.current_sentence_index = 0
        self.blocks = []
        self.words = []
        self.selected_index = 0
        self.grabbed = False
        self.success_timer = 0
        
        self.setup_new_sentence()
        
    def setup_new_sentence(self):
        if not self.sentences:
            return
            
        original_sentence = self.sentences[self.current_sentence_index]
        self.words = original_sentence.split()
        
        # Shuffle all words (no first-word lock)
        shuffled_words = self.words[:]
        if len(self.words) > 1:
            while shuffled_words == self.words:
                random.shuffle(shuffled_words)
                
        self.blocks = []
        for i, word in enumerate(shuffled_words):
            color = random.choice(BOX_COLORS)
            block = WordBlock(word, color, self.font)
            self.blocks.append(block)
            
        self.selected_index = 0
        self.grabbed = False
        self.update_block_positions()
        
    def update_block_positions(self):
        padding = 10
        start_x = self.rect.x + 20
        start_y = self.rect.y + 140
        current_x = start_x
        current_y = start_y
        
        for i, block in enumerate(self.blocks):
            if current_x + block.width > self.rect.right - 20:
                # Wrap to next line
                current_x = start_x
                current_y += block.height + padding
                
            block.target_x = current_x
            block.target_y = current_y
            
            current_x += block.width + padding

    def move_selection(self, direction):
        if self.success_timer > 0:
            return
            
        if self.grabbed:
            new_index = self.selected_index + direction
            if 0 <= new_index < len(self.blocks):
                # Don't swap into a locked position
                #if self.blocks[new_index].locked:
                #    return
                self.blocks[self.selected_index], self.blocks[new_index] = self.blocks[new_index], self.blocks[self.selected_index]
                self.selected_index = new_index
                self.update_block_positions()
                if self.check_win():
                    self.on_success()
        else:
            # Skip locked blocks when navigating
            new_index = self.selected_index
            for _ in range(len(self.blocks)):
                new_index = (new_index + direction) % len(self.blocks)
                if not self.blocks[new_index].locked:
                    break
            self.selected_index = new_index

    def toggle_grab(self):
        if self.success_timer > 0:
            return
            
        self.grabbed = not self.grabbed
        if not self.grabbed:
            if self.check_win():
                self.on_success()

    def check_win(self):
        current_sequence = [b.text for b in self.blocks]
        return current_sequence == self.words

    def on_success(self):
        self.score += 1  # Simple star scoring
        self.success_timer = pygame.time.get_ticks()
        self.grabbed = False
        for b in self.blocks:
            b.target_y -= 15

    def update(self):
        if self.success_timer > 0:
            if pygame.time.get_ticks() - self.success_timer > 800: # 0.8 sec flash
                self.success_timer = 0
                self.current_sentence_index = (self.current_sentence_index + 1) % len(self.sentences)
                self.setup_new_sentence()
    
    def _draw_star(self, surface, x, y, size, color):
        """Draw a 5-pointed star at (x, y)."""
        points = []
        for i in range(10):
            angle = math.radians(i * 36 - 90)
            r = size if i % 2 == 0 else size * 0.4
            points.append((x + r * math.cos(angle), y + r * math.sin(angle)))
        pygame.draw.polygon(surface, color, points)

    def _make_hand_surf(self, skin, outline):
        w, h = 42, 62
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        cx = w // 2
        # knuckle bumps
        for kx in [cx - 11, cx, cx + 11]:
            pygame.draw.circle(surf, outline, (kx, 19), 2)
        # --- Index finger ---
        pygame.draw.rect(surf, skin,    (cx - 7, 32, 14, 26), border_radius=7)
        pygame.draw.rect(surf, outline, (cx - 7, 32, 14, 26), 2, border_radius=7)
        # finger crease
        pygame.draw.line(surf, outline, (cx - 5, 39), (cx + 5, 39), 1)
        # fingernail
        pygame.draw.ellipse(surf, (255, 238, 215), (cx - 5, 49, 10, 7))
        pygame.draw.ellipse(surf, outline,          (cx - 5, 49, 10, 7), 1)
        return surf

    def draw(self, surface):
        if self.success_timer > 0:
            s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            s.fill((*SUCCESS_COLOR, 200))
            surface.blit(s, (self.rect.x, self.rect.y))
        else:
            s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            s.fill((*self.bg_color, 150))
            surface.blit(s, (self.rect.x, self.rect.y))
            
        # Draw Title
        p_label = self.score_font.render(f"Oyuncu {self.p_id}", True, (255, 255, 255))
        shadow_p = self.score_font.render(f"Oyuncu {self.p_id}", True, (100, 150, 180))
        surface.blit(shadow_p, (self.rect.x + 142, 22))
        surface.blit(p_label, (self.rect.x + 140, 20))
        
        # Draw Score text at top (compact, no inline stars)
        score_text = f"- Puan:{self.score}"
        score_label = self.score_font.render(score_text, True, (255, 255, 255))
        shadow_score = self.score_font.render(f"- Puan {self.score}", True, (100, 150, 180))
        surface.blit(shadow_score, (self.rect.right - score_label.get_width() - 167, 22))
        surface.blit(score_label, (self.rect.right - score_label.get_width() - 169, 20))

        # Draw Instructions at very bottom
        if self.p_id == 1:
            inst_text = "A-D | BOŞLUK ile tut/bırak"
        else:
            inst_text = "Yön Tuşları | ENTER ile tut/bırak"
        inst_surf = self.inst_font.render(inst_text, True, (80, 80, 80))
        inst_rect = inst_surf.get_rect(center=(self.rect.centerx, self.rect.bottom - 16))
        surface.blit(inst_surf, inst_rect)

        # --- Notebook star scoreboard ---
        nb_x = self.rect.x + 64
        nb_y = self.rect.y + 325
        nb_w = self.rect.width - 136
        nb_h = 136

        # Drop shadow
        pygame.draw.rect(surface, (155, 135, 80), (nb_x + 5, nb_y + 5, nb_w, nb_h), border_radius=8)
        # Cream page background
        pygame.draw.rect(surface, (255, 252, 218), (nb_x, nb_y, nb_w, nb_h), border_radius=8)
        # Border
        pygame.draw.rect(surface, (175, 148, 72), (nb_x, nb_y, nb_w, nb_h), 3, border_radius=8)
        # Horizontal ruled lines
        for ly in range(nb_y + 48, nb_y + nb_h - 8, 26):
            pygame.draw.line(surface, (160, 195, 228), (nb_x + 74, ly), (nb_x + nb_w - 14, ly), 1)
        # Red margin line
        pygame.draw.line(surface, (210, 75, 75), (nb_x + 72, nb_y + 20), (nb_x + 72, nb_y + nb_h - 10), 2)
        # Spiral binding rings at top
        for bx in range(nb_x + 20, nb_x + nb_w - 8, 30):
            pygame.draw.circle(surface, (130, 130, 130), (bx, nb_y), 7, 2)
            pygame.draw.arc(surface, (195, 195, 195), (bx - 6, nb_y - 6, 12, 12), 0, math.pi, 2)
        # "Yıldız:" label in left margin
        nb_label = self.inst_font.render(" Yıldız:", True, (120, 88, 28))
        surface.blit(nb_label, (nb_x + 3, nb_y + 14))
        # Draw stars on ruled lines
        star_cols = max(1, (nb_w - 60) // 28)
        for s_i in range(self.score):
            col = s_i % star_cols
            row = s_i // star_cols
            sx = nb_x + 78 + col * 28 + 14
            sy = nb_y + 22 + row * 30 + 9
            if sy > nb_y + nb_h - 14:
                break  # don't overflow notebook
            self._draw_star(surface, sx, sy, 11, (195, 140, 0))  # dark outline star
            self._draw_star(surface, sx, sy, 9,  (255, 215, 0))  # gold fill star

        # Draw Words with correct-position highlighting
        for i, block in enumerate(self.blocks):
            is_selected = (i == self.selected_index)
            # Check if this block is in the correct position
            is_correct = (block.text == self.words[i]) if i < len(self.words) else False
            block.draw(surface, is_selected, self.grabbed and is_selected, block.locked, is_correct)

        # Draw animated arrow pointer above selected block
        if 0 <= self.selected_index < len(self.blocks):
            sel = self.blocks[self.selected_index]
            t = pygame.time.get_ticks()
            bob = int(math.sin(t * 0.007) * 6)
            hx = int(sel.x + sel.width // 2)
            hy = int(sel.y) - 8 + bob
            # Colors: orange normally, gold when grabbed
            fill_col    = (255, 215, 0)   if self.grabbed else (255, 100, 30)
            outline_col = (160, 120,  0)  if self.grabbed else (160,  50,  0)
            # Downward-pointing solid triangle
            arrow_pts = [(hx, hy), (hx - 12, hy - 20), (hx + 12, hy - 20)]
            pygame.draw.polygon(surface, fill_col,    arrow_pts)
            pygame.draw.polygon(surface, outline_col, arrow_pts, 2)
            # Small dot at tip for polish
            #pygame.draw.circle(surface, outline_col, (hx, hy), 3)

class Game:
    def __init__(self):
        pygame.init()
        self.fullscreen = False  # Starts in fullscreen
        if self.fullscreen:
            info = pygame.display.Info()
            self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.render_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Cümle Kurma Yarışı (2 Oyuncu)")
        self.clock = pygame.time.Clock()
        
        # Fonts
        try:
            self.font = pygame.font.SysFont("comicsansms", 30, bold=True)
            self.score_font = pygame.font.SysFont("comicsansms", 36, bold=True)
            self.timer_font = pygame.font.SysFont("comicsansms", 26, bold=True)
            self.win_font = pygame.font.SysFont("comicsansms", 84, bold=True)
            self.inst_font = pygame.font.SysFont("comicsansms", 20)
        except:
            self.font = pygame.font.Font(None, 36)
            self.score_font = pygame.font.Font(None, 44)
            self.timer_font = pygame.font.Font(None, 80)
            self.win_font = pygame.font.Font(None, 100)
            self.inst_font = pygame.font.Font(None, 26)
            
        self.sentences = load_sentences("sentences.txt")
        if not self.sentences:
            self.sentences = ["Dosya boş."]
            
        # Setup Players (Split Screen)
        self.player1 = Player(1, pygame.Rect(0, 0, 640, 720), BG_COLOR1, self.sentences, self.font, self.score_font, self.inst_font)
        self.player2 = Player(2, pygame.Rect(640, 0, 640, 720), BG_COLOR2, self.sentences, self.font, self.score_font, self.inst_font)
        
        # Joystick Setup
        self.joystick = None
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            
        self.axis_moved = False
        
        self.state = "MENU" # MENU, PLAYING, GAME_OVER
        try:
            self.bg_image = pygame.image.load(resource_path("background.png")).convert_alpha()
            self.bg_image = pygame.transform.scale(self.bg_image, (WINDOW_WIDTH, WINDOW_HEIGHT))
        except:
            self.bg_image = None
            
        self.start_ticks = 0
        self.time_left = 90  # More time for young players
        
        # Create smaller pencil surface (classic yellow)
        pw, ph = 28, 210
        self.pencil_height = ph
        self.pencil_width = pw
        self.pencil_surf = pygame.Surface((pw, ph * 2), pygame.SRCALPHA)
        # Eraser – hot pink
        pygame.draw.rect(self.pencil_surf, (255, 105, 180), (2, 0, pw-4, 20), border_radius=7)
        pygame.draw.rect(self.pencil_surf, (200, 60, 140), (2, 0, pw-4, 20), 2, border_radius=7)
        # Metal band
        pygame.draw.rect(self.pencil_surf, (192, 192, 192), (2, 20, pw-4, 12))
        pygame.draw.line(self.pencil_surf, (240, 240, 240), (2, 22), (pw-2, 22), 2)
        pygame.draw.rect(self.pencil_surf, (130, 130, 130), (2, 20, pw-4, 12), 1)
        # Yellow body
        pygame.draw.rect(self.pencil_surf, (255, 215, 0), (2, 32, pw-4, 120))
        pygame.draw.rect(self.pencil_surf, (200, 160, 0), (2, 32, pw-4, 120), 1)
        pygame.draw.line(self.pencil_surf, (255, 230, 80), (8, 32), (8, 152), 2)   # shine
        # Wood tip
        body_end = 152
        pygame.draw.polygon(self.pencil_surf, (210, 170, 115), [(2, body_end), (pw-2, body_end), (pw//2, body_end+44)])
        pygame.draw.polygon(self.pencil_surf, (160, 120, 70), [(2, body_end), (pw-2, body_end), (pw//2, body_end+44)], 1)
        # Graphite tip
        ty = body_end + 33
        pygame.draw.polygon(self.pencil_surf, (50, 50, 60), [(pw//2-4, ty), (pw//2+4, ty), (pw//2, body_end+44)])
        # Text "DEVRİLMEZ" on yellow body
        try:
            pen_font = pygame.font.SysFont("comicsansms", 13, bold=True)
        except:
            pen_font = pygame.font.Font(None, 15)
        step = 118 // len("DEVRİLMEZ")
        for i, char in enumerate("DEVRİLMEZ"):
            cy = 38 + i * step
            sh_s = pen_font.render(char, True, (100, 80, 0))
            ch_s = pen_font.render(char, True, (60, 40, 0))
            self.pencil_surf.blit(sh_s, sh_s.get_rect(center=(pw//2+1, cy+1)))
            self.pencil_surf.blit(ch_s, ch_s.get_rect(center=(pw//2, cy)))

        self.current_pencil_angle = 0
        self.target_pencil_angle = 0


    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            info = pygame.display.Info()
            self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            
            # F11 toggles fullscreen in any state
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                self.toggle_fullscreen()
                continue
                
            if self.state == "MENU":
                if event.type == pygame.KEYDOWN and event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                    self.restart_game()
                if event.type == pygame.JOYBUTTONDOWN and event.button == 0:
                    self.restart_game()
                continue
                
            if self.state == "GAME_OVER":
                # Handle restart
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    self.state = "MENU"
                if event.type == pygame.JOYBUTTONDOWN and event.button == 0:
                    self.state = "MENU"
                continue
                
            # Keyboard Inputs
            if event.type == pygame.KEYDOWN:
                # Player 1
                if event.key == pygame.K_a:
                    self.player1.move_selection(-1)
                elif event.key == pygame.K_d:
                    self.player1.move_selection(1)
                elif event.key == pygame.K_SPACE:
                    self.player1.toggle_grab()
                    
                # Player 2
                elif event.key == pygame.K_LEFT:
                    self.player2.move_selection(-1)
                elif event.key == pygame.K_RIGHT:
                    self.player2.move_selection(1)
                elif event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                    self.player2.toggle_grab()
                    
            # Joystick Inputs for Player 2
            if event.type == pygame.JOYHATMOTION:
                dx, dy = event.value
                if dx == -1:
                    self.player2.move_selection(-1)
                elif dx == 1:
                    self.player2.move_selection(1)
                    
            if event.type == pygame.JOYAXISMOTION:
                if event.axis == 0:
                    if event.value < -0.5:
                        if not self.axis_moved:
                            self.player2.move_selection(-1)
                            self.axis_moved = True
                    elif event.value > 0.5:
                        if not self.axis_moved:
                            self.player2.move_selection(1)
                            self.axis_moved = True
                    else:
                        if abs(event.value) < 0.2: 
                            self.axis_moved = False
                            
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0: # Usually 'A' or 'Cross'
                    self.player2.toggle_grab()

    def restart_game(self):
        self.player1.score = 0
        self.player2.score = 0
        self.player1.current_sentence_index = 0
        self.player2.current_sentence_index = 0
        random.shuffle(self.player1.sentences)
        random.shuffle(self.player2.sentences)
        self.player1.setup_new_sentence()
        self.player2.setup_new_sentence()
        self.start_ticks = pygame.time.get_ticks()
        self.time_left = 120
        self.state = "PLAYING"

    def update(self):
        if self.state == "PLAYING":
            elapsed_sec = (pygame.time.get_ticks() - self.start_ticks) // 1000
            self.time_left = max(0, 120 - elapsed_sec)
            if self.time_left == 0:
                self.state = "GAME_OVER"
            
            self.player1.update()
            self.player2.update()
            
            score_diff = self.player1.score - self.player2.score
            self.target_pencil_angle = score_diff * 8  # Adjusted for 1-point scoring
            self.target_pencil_angle = max(-45, min(45, self.target_pencil_angle))
            
        elif self.state == "GAME_OVER":
            if self.player1.score > self.player2.score:
                self.target_pencil_angle = 80
            elif self.player2.score > self.player1.score:
                self.target_pencil_angle = -80
            else:
                self.target_pencil_angle = 0
        else:
            self.target_pencil_angle = 0
            
        self.current_pencil_angle += (self.target_pencil_angle - self.current_pencil_angle) * 0.05

    def draw(self):
        surf = self.render_surface

        if self.bg_image:
            surf.blit(self.bg_image, (0, 0))
        else:
            surf.fill((135, 206, 235))
            
        if self.state == "MENU":
            # Draw Menu Overlay
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            surf.blit(overlay, (0,0))
            
            title_surf = self.win_font.render("Cümle Kurma Yarışı", True, (255, 215, 0))
            title_rect = title_surf.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 60))
            shadow = self.win_font.render("Cümle Kurma Yarışı", True, (50, 50, 50))
            surf.blit(shadow, (title_rect.x + 6, title_rect.y + 6))
            surf.blit(title_surf, title_rect)
            
            start_surf = self.score_font.render("Başlamak için BOŞLUK veya ENTER'a basın", True, (255, 255, 255))
            start_rect = start_surf.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 50))
            surf.blit(start_surf, start_rect)

            # F11 hint
            fs_surf = self.inst_font.render("Tam ekran: F11", True, (200, 200, 200))
            fs_rect = fs_surf.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 110))
            surf.blit(fs_surf, fs_rect)
            
            # Scale and display
            scaled = pygame.transform.smoothscale(surf, self.screen.get_size())
            self.screen.blit(scaled, (0, 0))
            pygame.display.flip()
            return
            
        # Draw players on their respective halves
        self.player1.draw(surf)
        self.player2.draw(surf)
        
        # Draw dotted center divider
        for y in range(0, WINDOW_HEIGHT, 40):
            pygame.draw.line(surf, (255, 255, 255, 100), (WINDOW_WIDTH//2, y), (WINDOW_WIDTH//2, y+20), 4)
            
        # Draw the tilted pencil
        rotated_pencil = pygame.transform.rotate(self.pencil_surf, self.current_pencil_angle)
        pencil_rect = rotated_pencil.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT - 35))
        surf.blit(rotated_pencil, pencil_rect.topleft)
        
        # Draw Center Timer
        timer_color = (255, 50, 50) if self.time_left <= 10 else (255, 255, 255)
        timer_text = str(self.time_left)
        timer_surf = self.timer_font.render(timer_text, True, timer_color)
        
        timer_width = 60
        timer_height = 40
        timer_bg = pygame.Rect(WINDOW_WIDTH//2 - timer_width//2, 20, timer_width, timer_height)
        pygame.draw.rect(surf, (30, 30, 30), timer_bg, border_radius=15)
        pygame.draw.rect(surf, (255, 255, 255), timer_bg, width=4, border_radius=15)
        
        timer_rect = timer_surf.get_rect(center=timer_bg.center)
        surf.blit(timer_surf, timer_rect)
        
        # Draw Game Over Screen
        if self.state == "GAME_OVER":
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 210))
            surf.blit(overlay, (0,0))
            
            if self.player1.score > self.player2.score:
                win_text = "Oyuncu 1 Kazandı!"
                color = (135, 206, 250)
            elif self.player2.score > self.player1.score:
                win_text = "Oyuncu 2 Kazandı!"
                color = (255, 218, 185)
            else:
                win_text = "Büyük Beraberlik!"
                color = (255, 255, 255)
                
            y_offset = math.sin(pygame.time.get_ticks() * 0.005) * 15
            win_surf = self.win_font.render(win_text, True, color)
            win_rect = win_surf.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 40 + y_offset))
            
            # Draw shadow
            shadow_surf = self.win_font.render(win_text, True, (50, 50, 50))
            surf.blit(shadow_surf, (win_rect.x + 6, win_rect.y + 6))
            surf.blit(win_surf, win_rect)
            
            # Restart instructions
            rst_surf = self.score_font.render("Menüye Dönmek için 'R' Tuşuna Basın", True, (200, 200, 200))
            rst_rect = rst_surf.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 70))
            surf.blit(rst_surf, rst_rect)

        # Scale render surface to actual screen size and display
        scaled = pygame.transform.smoothscale(surf, self.screen.get_size())
        self.screen.blit(scaled, (0, 0))
        pygame.display.flip()

    def run(self):
        while True:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()
