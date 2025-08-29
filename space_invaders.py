import pygame
import random
import json
import os
import time

# Leaderboard functions
def load_leaderboard():
    if os.path.exists("leaderboard.json"):
        try:
            with open("leaderboard.json", "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return [] # If file is empty/corrupt
    return [] # If no file yet
    
def save_leaderboard(leaderboard):
    with open("leaderboard.json", "w") as f:
        json.dump(leaderboard, f)
# Initialize pygame
pygame.init()

WIDTH , HEIGHT = 900, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invabers")
FPS = 60
CLOCK = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 50, 50)
GREEN = (50, 220, 90)
BLUE = (80, 120, 255)
YELLOW = (250, 210, 70)
ORANGE = (255, 140, 0)
CYAN = (0, 200, 200)
GRAY = (180, 180, 180)

# Fonts
FONT_SMALL = pygame.font.SysFont("arial", 20)
FONT_MED = pygame.font.SysFont("arial", 28)
FONT_LARGE = pygame.font.SysFont("arial", 44)
FONT_HUGE = pygame.font.SysFont("arial", 64)

# File paths
LEADERBORAD_PATH = "leaderboard_space_invaders_.json"

# Game constants
PLAYER_SPEED = 6
BULLET_SPEED = 10
ENEMY_MIN_SPEED = 2
ENEMY_MAX_SPEED = 4
ASTEROID_MIN_SPEED = 2
ASTEROID_MAX_SPEED = 5
SPAWN_COOLDOWN_BASE = 900
SPAWN_JITTER = 500
BONUS_ROUND_DURATION = 25
HIT_DAMAGE = 10
PLAYER_MAX_HEALTH = 100
LEVEL_COUNT = 10
BULLET_COOLDOWN_MS = 200

# Utility functions
def maybe_update_leaderboard(score):
    leaderboard = load_leaderboard()

    # Ensure all entries are dictionaries
    leaderboard = [{"name": entry[0], "score": entry[1]} if isinstance(entry, tuple) else entry for entry in leaderboard]

    qualifies = len(leaderboard) < 3 or score > leaderboard[-1]["score"]

    if qualifies:
        name = prompt_for_name()
        leaderboard.append({"name": name, "score": score})
        leaderboard = sorted(leaderboard, key=lambda x: x["score"], reverse=True)[:3]
        save_leaderboard(leaderboard)
        return name, leaderboard

    return None, leaderboard

def prompt_for_name():
    """Simple on screen text input to capture the player's name"""
    input_str = ""
    prompt = "New High Score! Enter your name: "
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return input_str.strip() or "Player"
                elif event.key == pygame.K_BACKSPACE:
                    input_str = input_str[:-1]
                else:
                    if len(input_str) < 16:
                        input_str += event.unicode

        WIN.fill(BLACK)
        draw_centered_text(FONT_MED, prompt, WHITE, HEIGHT // 2 - 40)
        draw_centered_text(FONT_LARGE, input_str + "_", GREEN, HEIGHT // 2 +10)
        pygame.display.flip()
        CLOCK.tick(FPS)

def draw_centered_text(font, text, color, y):
    """Draw text centered horizontally at y"""
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(WIDTH // 2, y))
    WIN.blit(surf, rect)

def get_advancement_threshold(level):
    """Return the points needed to advance from this level"""
    if 1 <= level <= 3:
        return 350
    elif 4 <= level <= 6:
        return 550
    else:
        return 650
    
def cumulative_required_up_to(level):
    """Return cumulative total points required to have reached next level from level 1 up to level
       ex: to advance from level 1 - 2 you need 350 total, 2 - 3 you need 350+350=700 total, etc"""
    total = 0
    for L in range(1, level + 1):
        total += get_advancement_threshold(L)
    return total

def level_has_bonus_after(level):
    """True if a bonus round comes after finishing this level(3, 6, 9)"""
    return level % 3 == 0 and level < LEVEL_COUNT

# Sprites
class Player(pygame.sprite.Sprite):
    """Player ship sprite"""
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((50, 35), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, BLUE, [(0, 35), (25, 0), (50, 35)])
        self.rect = self.image.get_rect(midbottom=(WIDTH // 2, HEIGHT - 20))
        self.speed = PLAYER_SPEED
        self.health = PLAYER_MAX_HEALTH
        self.last_shot = 0

    def update(self, keys):
        """Move based on key input and clamp to screen"""
        dx = 0
        dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += self.speed
        self.rect.x = max(0, min(WIDTH - self.rect.width, self.rect.x + dx))
        self.rect.y = max(0, min(HEIGHT - self.rect.height, self.rect.y + dy))

    def can_shoot(self):
        """Check bullet cooldown"""
        return pygame.time.get_ticks() - self.last_shot >= BULLET_COOLDOWN_MS
    
    def shoot(self, bullets_group):
        """Spawn a bullet if cooldown allows"""
        if self.can_shoot():
            bullet = Bullet(self.rect.centerx, self.rect.top)
            bullets_group.add(bullet)
            self.last_shot = pygame.time.get_ticks()

class Bullet(pygame.sprite.Sprite):
    """Upward traveling bullet"""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((5, 12), pygame.SRCALPHA)
        pygame.draw.rect(self.image, CYAN, (0, 0, 5, 12))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = -BULLET_SPEED

    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()

class Enemy(pygame.sprite.Sprite):
    """Falling ememy ship"""
    def __init__(self):
        super().__init__()
        w, h = random.randint(30, 50), random.randint(20, 35)
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(self.image, YELLOW, (0, 0, w, h), border_radius=6)
        self.rect = self.image.get_rect(midtop=(random.randint(20, WIDTH - 20), -h))
        self.speed = random.uniform(ENEMY_MIN_SPEED, ENEMY_MAX_SPEED)

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.kill()

class Asteroid(pygame.sprite.Sprite):
    """Falling asteroid target"""
    def __init__(self):
        super().__init__()
        r = random.randint(12, 28)
        self.image = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, ORANGE, (r, r), r)
        self.rect = self.image.get_rect(midtop=(random.randint(20, WIDTH - 20), -r * 2))
        self.speed = random.uniform(ASTEROID_MIN_SPEED, ASTEROID_MAX_SPEED)

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.kill()

# Game State Containers
all_sprites = pygame.sprite.Group() # Everything (player for now)
enemy_group = pygame.sprite.Group() 
asteroid_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()

# Spawning Control
def spawn_entities(level, is_bonus=False):
    """Spawn enemies/asteroids, bonus round spawns asteroids only"""
    if is_bonus:
        asteroid_group.add(Asteroid()) # Bonus is asteriods only
    else:
        # Slightly increase asteroid chance with level
        if random.random() < 0.15 + 0.02 * level:
            asteroid_group.add(Asteroid())
        else:
            enemy_group.add(Enemy())

def spawn_interval_ms(level):
    """Time between spawn in milliseconds, decreasing with higher levels"""
    base = max(250, SPAWN_COOLDOWN_BASE - (level - 1) * 80) # Reduce with level
    jitter = random.randint(-SPAWN_JITTER, SPAWN_JITTER) # Randomize cadence
    return max(180, base + jitter) # Clamp lower bound

# Drawing HUD
def draw_hud(score, bonus_score, health, level, in_bonus, bonus_time_left):
    """Draw score (left/green), Health (right/red), Level (center), Bonus tracker (bottom left) """
    score_text = FONT_MED.render(f"Score: {score}", True, GREEN)
    WIN.blit(score_text, (10, 10))

    health_text = FONT_MED.render(f"Health: {health}%", True, RED)
    WIN.blit(health_text, (WIDTH - health_text.get_width() - 10, 10))

    level_label = f"Level {level}" if not in_bonus else f"BONUS ROUND - {int(bonus_time_left)}s"
    level_text = FONT_MED.render(level_label, True, WHITE)
    WIN.blit(level_text, (WIDTH // 2 - level_text.get_width() // 2, 10))

    bonus_text = FONT_SMALL.render(f"Bonus Points: {bonus_score}", True, GRAY)
    WIN.blit(bonus_text, (10, HEIGHT - 30))

# Menu Screens
def start_menu():
    """Start menu with start, high scores, quit """
    selected = 0
    options = ["Start", "High Scores", "Quit"]
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    selected = (selected - 1) % len(options)
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    selected = (selected + 1) % len(options)
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    choice = options[selected]
                    if choice == "Start":
                        return "start"
                    elif choice == "High Scores":
                        show_high_scores()
                    else:
                        pygame.quit()
                        raise SystemExit
                    
        WIN.fill(BLACK)
        draw_centered_text(FONT_HUGE, "SPACE INVADERS", WHITE, 160)
        draw_centered_text(FONT_MED, "Arrow/WASD to move | SPACE to shoot | ESC to pause", GRAY, 220)
        draw_centered_text(FONT_MED, "Advance: L1-3 +350 | L4-6 +550 | L7-10 +650", GRAY, 250)
        draw_centered_text(FONT_MED, "Bonus Round every 3 levels (25s) - Bonus points don't advance levels", GRAY, 280)

        for i, opt in enumerate(options):
            color = GREEN if i == selected else WHITE
            draw_centered_text(FONT_LARGE, opt, color, 360 + i * 60)

        pygame.display.flip()
        CLOCK.tick(FPS)

def show_high_scores():
    """Display top 3 high scores"""
    lb = load_leaderboard()
    lb_sorted = sorted(lb, key=lambda e: e.get("score", 0), reverse=True)[:3]
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                waiting = False

        WIN.fill(BLACK)
        draw_centered_text(FONT_HUGE, "HIGH SCORE", WHITE, 140)
        if not lb_sorted:
            draw_centered_text(FONT_MED, "No score yet. Be the first!", GRAY, 220)
        else:
            for i, entry in enumerate(lb_sorted, start=1):
                line = f"{i}. {entry.get('name', 'Player')} - {entry.get('score', 0)}"
                draw_centered_text(FONT_LARGE, line, GREEN, 200 + i * 60)

        draw_centered_text(FONT_MED, "Press any key to return", GRAY, 520)
        pygame.display.flip()
        CLOCK.tick(FPS)

def game_over_screen(score):
    """Show Game Over, update leaderboard if needed, and ask to replay/menu/quit"""
    name, top3 = maybe_update_leaderboard(score)
    selected = 0
    options = ["Play Again", "Main Menu", "Quit"]

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    selected = (selected - 1) % len(options)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    selected = (selected + 1) % len(options)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    choice = options[selected]
                    if choice == "Play Again":
                        return "replay"
                    elif choice == "Main Menu":
                        return "menu"
                    else:
                        pygame.quit()
                        raise SystemExit

        # Draw screen
        WIN.fill(BLACK)
        draw_centered_text(FONT_HUGE, "GAME OVER", WHITE, 120)
        draw_centered_text(FONT_LARGE, f"Your Score: {score}", GREEN, 180)

        draw_centered_text(FONT_MED, "Top 3 High Scores:", GRAY, 240)
        if top3:
            for i, entry in enumerate(top3, start=1):
                line = f"{i}. {entry.get('name', 'Player')} - {entry.get('score', 0)}"
                draw_centered_text(FONT_MED, line, WHITE, 260 + i * 30)
        else:
            draw_centered_text(FONT_MED, "No scores yet", GRAY, 280)

        for i, opt in enumerate(options):
            color = GREEN if i == selected else WHITE
            draw_centered_text(FONT_LARGE, opt, color, 400 + i * 50)

        pygame.display.flip()
        CLOCK.tick(FPS)

# Game loop 
def play_game():
    """Play a full session (levels + bonus rounds) until Game over or victory"""
    # Reset sprite groups
    all_sprites.empty()
    enemy_group.empty()
    asteroid_group.empty()
    bullet_group.empty()

    # Create player 
    player = Player()
    all_sprites.add(player)

    # State variables
    running = True
    paused = False
    level = 1
    score = 0
    bonus_score = 0
    in_bonus = False
    bonus_end_time = 0
    last_spawn_time = pygame.time.get_ticks()
    last_bonus_spawn = pygame.time.get_ticks()

    # Health refill milestone helper
    def maybe_refill_health(current_level):
        if current_level in (4, 6):
            player.health = PLAYER_MAX_HEALTH

    # Main loop
    while running:
        # Events 
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    paused = not paused
                if not paused:
                    if event.key == pygame.K_SPACE:
                        player.shoot(bullet_group)

        # Pause
        if paused:
            WIN.fill(BLACK)
            draw_centered_text(FONT_HUGE, "PAUSED", WHITE, HEIGHT // 2 - 20)
            draw_centered_text(FONT_MED, "Press Esc to resume", GRAY, HEIGHT // 2 + 30)
            pygame.display.flip()
            CLOCK.tick(FPS)
            continue

        # Bonus round trigger, enter bonus after finishing level 3, 6 or 9. Finishing a level here means total score >= cumulative_required_up_to(level)
        if (not in_bonus and level_has_bonus_after(level) and score >= cumulative_required_up_to(level)):
            in_bonus = True
            bonus_end_time = time.time() + BONUS_ROUND_DURATION
            # Clear enemies so bonus focuses on asteroids
            for e in enemy_group.sprites():
                e.kill()
            last_bonus_spawn = pygame.time.get_ticks()

        # Spawning
        now = pygame.time.get_ticks()
        if in_bonus:
            # Faster asteroid spawns during bonus
            if now - last_bonus_spawn > 300:
                spawn_entities(level, is_bonus=True)
                last_bonus_spawn = now

        else:
            if now - last_spawn_time > spawn_interval_ms(level):
                spawn_entities(level, is_bonus=False)
                last_spawn_time = now

        # Updates
        keys = pygame.key.get_pressed()
        player.update(keys)
        bullet_group.update()
        enemy_group.update()
        asteroid_group.update()

        # Collisions: bullets vs enemies/asteroids
        hits_enemies = pygame.sprite.groupcollide(enemy_group, bullet_group, True, True)
        if hits_enemies:
            gained = 10 * len(hits_enemies)
            if in_bonus:
                bonus_score += gained
            else:
                score += gained

        hits_asteroids = pygame.sprite.groupcollide(asteroid_group, bullet_group, True, True)
        if hits_asteroids:
            gained = 15 * len(hits_asteroids)
            if in_bonus:
                bonus_score += gained
            else:
                score += gained

        # Collisions: emenies/asteroids vs player (no damage during bonus)
        if not in_bonus:
            if pygame.sprite.spritecollide(player, enemy_group, True):
                player.health = max(0, player.health - HIT_DAMAGE)
            if pygame.sprite.spritecollide(player, asteroid_group, True):
                player.health = max(0, player.health - HIT_DAMAGE)

        # Game Over
        if player.health <= 0:
            return "gameover", score
        
        # Level Advancement (normal play only)
        if not in_bonus:
            # If total score reached the cumulative requirement for current level, advance
            if score >= cumulative_required_up_to(level):
                level += 1
                maybe_refill_health(level)
                if level > LEVEL_COUNT:
                    # Treat finishing level 10 as win, end session and go to game over screen
                    return "gameover", score
                
        # Bonus round end
        if in_bonus:
            remaining = bonus_end_time - time.time()
            if remaining <= 0: 
                in_bonus = False # Exit bonus
                level += 1 # Proceed to next level after bonus
                maybe_refill_health(level)
                if level > LEVEL_COUNT:
                    return "gameover", score
                
        # Draw
        WIN.fill((10, 10, 18))
        all_sprites.draw(WIN)
        enemy_group.draw(WIN)
        asteroid_group.draw(WIN)
        bullet_group.draw(WIN)

        bonus_time_left = max(0, (bonus_end_time - time.time())) if in_bonus else 0
        draw_hud(score, bonus_score, player.health, level, in_bonus, bonus_time_left)

        pygame.display.flip()
        CLOCK.tick(FPS)

# Main app loop
def main():
    """Entry point: menu loop -> game -> game over choices"""
    while True:
        action = start_menu()
        if action == "start":
            result, score = play_game()
            if result == "gameover":
                post = game_over_screen(score)
                if post == "replay":
                    continue
                elif post == "menu":
                    continue
                else:
                    break
        else:
            break

# Run the game
if __name__ == "__main__":
    try: 
        main()
    finally:
        pygame.quit()
