import pygame
import sys
import random
import math
from pygame.locals import *
import os

# Set SDL audio driver to a fallback before initializing
os.environ['SDL_AUDIODRIVER'] = 'dummy'  # This uses a dummy audio driver

# Initialize pygame
pygame.init()

# Try initializing audio with fallback options
try:
    pygame.mixer.init()
except pygame.error:
    print("Warning: Audio could not be initialized, game will run without sound")

# Game constants
WIDTH = 800
HEIGHT = 900
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)

# Create the game window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Fighter")
clock = pygame.time.Clock()

# Load game assets
def load_image(name, scale=1):
    try:
        image = pygame.image.load(name).convert_alpha()
        size = image.get_size()
        scaled_image = pygame.transform.scale(image, (int(size[0] * scale), int(size[1] * scale)))
        return scaled_image
    except pygame.error:
        # Create a default image if the file is not found
        surf = pygame.Surface((50, 50), pygame.SRCALPHA)
        pygame.draw.rect(surf, BLUE, (0, 0, 50, 50))
        pygame.draw.line(surf, RED, (0, 0), (50, 50), 3)
        pygame.draw.line(surf, RED, (50, 0), (0, 50), 3)
        return surf

# Create resource folders
if not os.path.exists("assets"):
    os.makedirs("assets")

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((50, 40), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, BLUE, [(0, 40), (25, 0), (50, 40)])
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.bottom = HEIGHT - 20
        self.speedx = 0
        self.speedy = 0
        self.health = 150
        self.max_health = 150
        self.energy = 100
        self.max_energy = 100
        self.energy_regen = 0.5
        self.shield_active = False
        self.shield_strength = 50
        self.shoot_delay = 200
        self.last_shot = 0
        self.special_delay = 2000
        self.last_special = 0
        self.hyper_dash_active = False
        self.hyper_dash_duration = 500
        self.hyper_dash_start = 0
        self.invincible = False
        self.invincible_duration = 1000
        self.invincible_start = 0
        self.weapon_level = 1
        self.weapon_type = "normal"  # normal, spread, laser, homing
        self.drones = 0
        self.max_drones = 2
        self.drone_list = []

    def update(self):
        # Movement
        self.speedx = 0
        self.speedy = 0
        keystate = pygame.key.get_pressed()
        
        # Regular movement
        speed_factor = 2.5 if self.hyper_dash_active else 1
        base_speed = 8
        
        if keystate[K_LEFT] or keystate[K_a]:
            self.speedx = -base_speed * speed_factor
        if keystate[K_RIGHT] or keystate[K_d]:
            self.speedx = base_speed * speed_factor
        if keystate[K_UP] or keystate[K_w]:
            self.speedy = -base_speed * speed_factor
        if keystate[K_DOWN] or keystate[K_s]:
            self.speedy = base_speed * speed_factor
            
        # Update position
        self.rect.x += self.speedx
        self.rect.y += self.speedy
        
        # Keep player on screen
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > HEIGHT:
            self.rect.bottom = HEIGHT
            
        # Automatically shoot
        now = pygame.time.get_ticks()
        if keystate[K_SPACE] and now - self.last_shot > self.shoot_delay:
            self.shoot()
            self.last_shot = now
            
        # Energy shield
        if keystate[K_LSHIFT] and self.energy > 0:
            self.shield_active = True
            self.energy -= 1
        else:
            self.shield_active = False
            
        # Energy regeneration
        if not self.shield_active and self.energy < self.max_energy:
            self.energy += self.energy_regen
            
        # Check hyper dash status
        if self.hyper_dash_active:
            if now - self.hyper_dash_start > self.hyper_dash_duration:
                self.hyper_dash_active = False
                
        # Check invincibility status
        if self.invincible:
            if now - self.invincible_start > self.invincible_duration:
                self.invincible = False
                
    def shoot(self):
        if self.weapon_type == "normal":
            bullet = Bullet(self.rect.centerx, self.rect.top)
            all_sprites.add(bullet)
            bullets.add(bullet)
            
            # Add additional bullets based on weapon level
            if self.weapon_level >= 2:
                bullet1 = Bullet(self.rect.left + 10, self.rect.top + 10)
                bullet2 = Bullet(self.rect.right - 10, self.rect.top + 10)
                all_sprites.add(bullet1, bullet2)
                bullets.add(bullet1, bullet2)
                
            if self.weapon_level >= 3:
                bullet3 = Bullet(self.rect.left + 5, self.rect.top + 20)
                bullet4 = Bullet(self.rect.right - 5, self.rect.top + 20)
                all_sprites.add(bullet3, bullet4)
                bullets.add(bullet3, bullet4)
                
        elif self.weapon_type == "spread":
            for angle in range(-30, 31, 30):
                bullet = SpreadBullet(self.rect.centerx, self.rect.top, angle)
                all_sprites.add(bullet)
                bullets.add(bullet)
                
        elif self.weapon_type == "laser":
            laser = Laser(self.rect.centerx, self.rect.top, self.weapon_level)
            all_sprites.add(laser)
            bullets.add(laser)

    def hyper_dash(self):
        now = pygame.time.get_ticks()
        if now - self.last_special > self.special_delay:
            self.hyper_dash_active = True
            self.invincible = True
            self.hyper_dash_start = now
            self.invincible_start = now
            self.last_special = now
            
    def add_drone(self):
        if len(self.drone_list) < self.max_drones:
            drone = Drone(self, len(self.drone_list))
            self.drone_list.append(drone)
            all_sprites.add(drone)
            
    def hit(self, damage):
        if not self.invincible:
            if self.shield_active:
                # Shield absorbs damage
                return
            else:
                self.health -= damage
                if self.health <= 0:
                    self.kill()
                    return True
        return False

# Drone Class
class Drone(pygame.sprite.Sprite):
    def __init__(self, player, position):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, BLUE, (10, 10), 10)
        self.rect = self.image.get_rect()
        self.player = player
        self.position = position  # 0 for left, 1 for right
        
    def update(self, *args):
        # Position the drone relative to the player
        # Modified to not require player parameter from sprite group update
        offset = 30
        if self.position == 0:
            self.rect.right = self.player.rect.left - 10
        else:
            self.rect.left = self.player.rect.right + 10
        self.rect.centery = self.player.rect.centery
        
    def shoot(self):
        bullet = Bullet(self.rect.centerx, self.rect.top)
        all_sprites.add(bullet)
        bullets.add(bullet)

# Bullet class
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((5, 15))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speedy = -15
        
    def update(self):
        self.rect.y += self.speedy
        # Kill if it moves off the top of the screen
        if self.rect.bottom < 0:
            self.kill()

# Spread bullet class
class SpreadBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((5, 15))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.angle = math.radians(angle)
        self.speedy = -15 * math.cos(self.angle)
        self.speedx = 15 * math.sin(self.angle)
        
    def update(self):
        self.rect.y += self.speedy
        self.rect.x += self.speedx
        # Kill if it moves off the screen
        if self.rect.bottom < 0 or self.rect.right < 0 or self.rect.left > WIDTH:
            self.kill()

# Laser class
class Laser(pygame.sprite.Sprite):
    def __init__(self, x, y, level):
        pygame.sprite.Sprite.__init__(self)
        self.level = level
        width = 10 + (level * 5)  # Wider with higher level
        self.image = pygame.Surface((width, HEIGHT))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.damage = 5 * level
        self.duration = 500  # Laser lasts for 500ms
        self.created = pygame.time.get_ticks()
        
    def update(self):
        now = pygame.time.get_ticks()
        if now - self.created > self.duration:
            self.kill()

# Enemy classes
class Enemy(pygame.sprite.Sprite):
    def __init__(self, enemy_type="basic"):
        pygame.sprite.Sprite.__init__(self)
        self.enemy_type = enemy_type
        
        if enemy_type == "basic":
            self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, RED, [(0, 0), (40, 0), (20, 40)])
            self.rect = self.image.get_rect()
            self.health = 10
            self.speed = random.randrange(2, 5)
            self.shoot_delay = 2000
            self.score_value = 10
            
        elif enemy_type == "elite":
            self.image = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, PURPLE, [(0, 0), (60, 0), (30, 60)])
            self.rect = self.image.get_rect()
            self.health = 50
            self.speed = random.randrange(2, 5)
            self.shoot_delay = 1000
            self.score_value = 30
            
        self.rect.x = random.randrange(0, WIDTH - self.rect.width)
        self.rect.y = random.randrange(-150, -50)
        self.last_shot = pygame.time.get_ticks()
        
    def update(self):
        self.rect.y += self.speed
        # Remove if it goes off the bottom
        if self.rect.top > HEIGHT:
            self.rect.x = random.randrange(0, WIDTH - self.rect.width)
            self.rect.y = random.randrange(-150, -50)
            
        # Randomly shoot
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.shoot()
            self.last_shot = now
            
    def shoot(self):
        if self.enemy_type == "basic":
            bullet = EnemyBullet(self.rect.centerx, self.rect.bottom)
            all_sprites.add(bullet)
            enemy_bullets.add(bullet)
        elif self.enemy_type == "elite":
            for angle in range(-30, 31, 60):  # Changed from 30 to 60 (fewer bullets)
                bullet = EnemySpreadBullet(self.rect.centerx, self.rect.bottom, angle)
                all_sprites.add(bullet)
                enemy_bullets.add(bullet)
                
    def hit(self, damage):
        self.health -= damage
        if self.health <= 0:
            # Random chance to drop a power-up
            if random.random() < 0.3:
                power_up = PowerUp(self.rect.centerx, self.rect.centery)
                all_sprites.add(power_up)
                powerups.add(power_up)
            self.kill()
            return self.score_value
        return 0

# Enemy bullet classes
class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((5, 15))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.top = y
        self.speedy = 5
        self.damage = 5
        
    def update(self):
        self.rect.y += self.speedy
        # Kill if it moves off the bottom of the screen
        if self.rect.top > HEIGHT:
            self.kill()

class EnemySpreadBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((8, 8))
        self.image.fill(PURPLE)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.top = y
        self.angle = math.radians(angle)
        self.speedy = 6 * math.cos(self.angle)
        self.speedx = 6 * math.sin(self.angle)
        self.damage = 15
        
    def update(self):
        self.rect.y += self.speedy
        self.rect.x += self.speedx
        # Kill if it moves off the screen
        if self.rect.top > HEIGHT or self.rect.right < 0 or self.rect.left > WIDTH:
            self.kill()

# PowerUp class
class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.type = random.choice(["health", "shield", "weapon", "drone"])
        self.image = pygame.Surface((25, 25))
        
        if self.type == "health":
            self.image.fill(GREEN)
        elif self.type == "shield":
            self.image.fill(BLUE)
        elif self.type == "weapon":
            self.image.fill(YELLOW)
        elif self.type == "drone":
            self.image.fill(PURPLE)
            
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.speedy = 3
        
    def update(self):
        self.rect.y += self.speedy
        if self.rect.top > HEIGHT:
            self.kill()

# Boss class
class Boss(pygame.sprite.Sprite):
    def __init__(self, sector):
        pygame.sprite.Sprite.__init__(self)
        self.sector = sector
        
        # Boss visuals and stats based on sector
        if sector == 1:
            # Nova Prime Edge Boss
            self.image = pygame.Surface((100, 100), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, RED, [(0, 0), (100, 0), (100, 100), (50, 75), (0, 100)])
            self.max_health = 500
            self.shoot_delay = 800
            self.name = "Sector 1 - Edge Guardian"
        elif sector == 2:
            # Asteroid Field Anomaly
            self.image = pygame.Surface((120, 120), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (150, 75, 0), (60, 60), 60)
            self.max_health = 800
            self.shoot_delay = 700
            self.name = "Sector 2 - Asteroid Titan"
        elif sector == 3:
            # Rhovax Border Patrol
            self.image = pygame.Surface((150, 100), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, (150, 0, 150), [(0, 50), (75, 0), (150, 50), (75, 100)])
            self.max_health = 1200
            self.shoot_delay = 600
            self.name = "Sector 3 - Rhovax Dreadnought"
        elif sector == 4:
            # Dominion Shipyards
            self.image = pygame.Surface((160, 160), pygame.SRCALPHA)
            pygame.draw.rect(self.image, (0, 100, 200), (0, 0, 160, 160))
            pygame.draw.rect(self.image, (0, 0, 0), (30, 30, 100, 100))
            self.max_health = 2000
            self.shoot_delay = 500
            self.name = "Sector 4 - Shipyard Sentinel"
        elif sector == 5:
            # Cosmic Storm Nexus
            self.image = pygame.Surface((180, 150), pygame.SRCALPHA)
            pygame.draw.ellipse(self.image, (50, 50, 200), (0, 0, 180, 150))
            pygame.draw.ellipse(self.image, (100, 0, 100), (30, 30, 120, 90))
            self.max_health = 3000
            self.shoot_delay = 400
            self.name = "Sector 5 - Storm Lord"
        else:  # Sector 6 - Final Boss
            # Dominion Mothership
            self.image = pygame.Surface((200, 200), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, (200, 0, 0), [(0, 0), (200, 0), (160, 100), (200, 200), (0, 200), (40, 100)])
            self.max_health = 5000
            self.shoot_delay = 300
            self.name = "Sector 6 - Dominion Mothership"
            
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.top = 50
        self.health = self.max_health
        self.last_shot = pygame.time.get_ticks()
        self.pattern = 0  # Current attack pattern
        self.pattern_timer = pygame.time.get_ticks()
        self.pattern_delay = 5000  # Change patterns every 5 seconds
        self.speed = 2
        self.speedx = self.speed
        self.speedy = 0
        self.score_value = sector * 500  # More points for later bosses
        
    def update(self):
        # Boss movement patterns
        now = pygame.time.get_ticks()
        
        # Change attack pattern periodically
        if now - self.pattern_timer > self.pattern_delay:
            self.pattern = (self.pattern + 1) % 3  # Cycle through 3 patterns
            self.pattern_timer = now
            
        # Basic movement
        if self.pattern == 0:
            # Move back and forth horizontally
            self.rect.x += self.speedx
            if self.rect.right > WIDTH or self.rect.left < 0:
                self.speedx *= -1
        elif self.pattern == 1:
            # Move in a figure-8 pattern
            self.rect.x += self.speedx
            self.rect.y += self.speedy
            if self.rect.right > WIDTH - 50 or self.rect.left < 50:
                self.speedx *= -1
                self.speedy = self.speedx  # Change vertical direction when hitting horizontal bounds
            if self.rect.top < 50 or self.rect.bottom > HEIGHT // 3:
                self.speedy *= -1
        else:  # pattern == 2
            # Charge toward player's x position
            if player.rect.centerx > self.rect.centerx:
                self.rect.x += self.speed * 1.5
            elif player.rect.centerx < self.rect.centerx:
                self.rect.x -= self.speed * 1.5
            
            # Small vertical movement
            self.rect.y += math.sin(pygame.time.get_ticks() / 500) * 2
            
        # Stay within bounds
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.top < 10:
            self.rect.top = 10
        if self.rect.bottom > HEIGHT // 2:
            self.rect.bottom = HEIGHT // 2
            
        # Shooting based on pattern
        if now - self.last_shot > self.shoot_delay:
            self.shoot()
            self.last_shot = now
            
    def shoot(self):
        if self.pattern == 0:
            # Simple spread pattern
            for angle in range(-45, 46, 15):
                bullet = EnemySpreadBullet(self.rect.centerx, self.rect.bottom, angle)
                all_sprites.add(bullet)
                enemy_bullets.add(bullet)
        elif self.pattern == 1:
            # Circular pattern
            for angle in range(0, 360, 30):
                bullet = EnemySpreadBullet(self.rect.centerx, self.rect.centery, angle)
                bullet.speedy = 6 * math.cos(math.radians(angle))
                bullet.speedx = 6 * math.sin(math.radians(angle))
                all_sprites.add(bullet)
                enemy_bullets.add(bullet)
        else:  # pattern == 2
            # Targeted shots at player
            angle = math.degrees(math.atan2(player.rect.centery - self.rect.centery, 
                                          player.rect.centerx - self.rect.centerx))
            for i in range(-2, 3):
                bullet = EnemySpreadBullet(self.rect.centerx, self.rect.bottom, angle + (i * 10) + 90)
                all_sprites.add(bullet)
                enemy_bullets.add(bullet)
            
            # Also spawn some minions
            if random.random() < 0.3 and len(enemies) < 5:
                enemy = Enemy("elite")
                enemy.rect.centerx = self.rect.centerx
                enemy.rect.top = self.rect.bottom
                all_sprites.add(enemy)
                enemies.add(enemy)
                
    def hit(self, damage):
        self.health -= damage
        if self.health <= 0:
            # Drop multiple power-ups when boss is defeated
            for _ in range(5):
                power_up = PowerUp(self.rect.centerx + random.randint(-50, 50), 
                                  self.rect.centery + random.randint(-50, 50))
                all_sprites.add(power_up)
                powerups.add(power_up)
            self.kill()
            # Return score and signal boss death
            return self.score_value, True
        # Return 0 score and boss still alive
        return 0, False

# Game state classes
class GameState:
    def __init__(self):
        self.state = "menu"
        self.sector = 1
        self.wave = 1
        self.score = 0
        self.high_score = 0
        self.combo = 1
        self.max_combo = 1
        self.difficulty = "normal"
        self.resources = 0
        self.boss_fight = False
        self.wave_enemies = 5
        self.waves_per_sector = 5  # Waves to complete before boss
        
    def reset(self):
        self.state = "menu"
        self.sector = 1
        self.wave = 1
        self.score = 0
        self.combo = 1
        self.resources = 0
        self.boss_fight = False
        self.wave_enemies = 5
        self.waves_per_sector = 5  # Waves to complete before boss
        
    def next_wave(self):
        self.wave += 1
        if self.wave > self.waves_per_sector:
            # Boss wave
            self.boss_fight = True
            return True
        return False
        
    def next_sector(self):
        self.sector += 1
        self.wave = 1
        self.boss_fight = False
        self.resources += 100 * self.sector  # Award resources for sector completion
        # Increase difficulty
        self.wave_enemies += 2
        
        # Game completed if all sectors done
        if self.sector > 6:
            self.state = "victory"
            return True
        return False

# Function to draw text
def draw_text(surface, text, size, x, y, color=WHITE):
    font = pygame.font.SysFont("Arial", size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x, y)
    surface.blit(text_surface, text_rect)

# Function to draw a health bar
def draw_bar(surface, x, y, value, max_value, width, height, color):
    if value < 0:
        value = 0
    fill = (value / max_value) * width
    outline_rect = pygame.Rect(x, y, width, height)
    fill_rect = pygame.Rect(x, y, fill, height)
    pygame.draw.rect(surface, color, fill_rect)
    pygame.draw.rect(surface, WHITE, outline_rect, 2)

# Initialize game state and sprite groups
game_state = GameState()
all_sprites = pygame.sprite.Group()
player = Player()
bullets = pygame.sprite.Group()
enemy_bullets = pygame.sprite.Group()
enemies = pygame.sprite.Group()
powerups = pygame.sprite.Group()
bosses = pygame.sprite.Group()
all_sprites.add(player)

# Create initial enemies
for i in range(game_state.wave_enemies):
    enemy = Enemy()
    all_sprites.add(enemy)
    enemies.add(enemy)

# Upgrade menu functions
def show_upgrade_menu():
    upgrade_running = True
    selected_option = 0
    upgrade_options = [
        {"name": "Hull Integrity", "cost": 50, "effect": "Increases max health by 20"},
        {"name": "Engine Efficiency", "cost": 50, "effect": "Increases movement speed"},
        {"name": "Shield Capacity", "cost": 50, "effect": "Increases energy and regen"},
        {"name": "Drone Support", "cost": 100, "effect": "Adds a support drone"}
    ]
    
    while upgrade_running:
        clock.tick(FPS)
        
        # Process input
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    upgrade_running = False
                elif event.key == K_UP:
                    selected_option = (selected_option - 1) % len(upgrade_options)
                elif event.key == K_DOWN:
                    selected_option = (selected_option + 1) % len(upgrade_options)
                elif event.key == K_RETURN:
                    # Apply upgrade if enough resources
                    option = upgrade_options[selected_option]
                    if game_state.resources >= option["cost"]:
                        game_state.resources -= option["cost"]
                        if selected_option == 0:  # Hull Integrity
                            player.max_health += 20
                            player.health = player.max_health
                        elif selected_option == 1:  # Engine Efficiency
                            player.speed_factor = 1.2
                        elif selected_option == 2:  # Shield Capacity
                            player.max_energy += 20
                            player.energy_regen += 0.2
                            player.energy = player.max_energy
                        elif selected_option == 3:  # Drone Support
                            player.add_drone()
                        
        # Draw upgrade menu
        screen.fill(BLACK)
        
        draw_text(screen, "UPGRADE MENU", 40, WIDTH / 2, 30)
        draw_text(screen, f"Resources: {game_state.resources}", 25, WIDTH / 2, 80)
        
        for i, option in enumerate(upgrade_options):
            color = RED if game_state.resources < option["cost"] else GREEN
            highlight = ">" if i == selected_option else " "
            draw_text(screen, f"{highlight} {option['name']} (Cost: {option['cost']})", 
                    20, WIDTH / 2, 150 + (i * 40), color)
            draw_text(screen, option["effect"], 16, WIDTH / 2, 170 + (i * 40), WHITE)
            
        draw_text(screen, "Arrow keys to select, ENTER to purchase, ESC to exit", 
                18, WIDTH / 2, HEIGHT - 50)
        
        pygame.display.flip()
    
    return

# Add basic sprite cleanup to save resources
def cleanup_sprites():
    # Remove sprites that are far off screen
    for sprite in all_sprites:
        if hasattr(sprite, 'rect'):
            if (sprite.rect.top > HEIGHT + 100 or 
                sprite.rect.bottom < -100 or
                sprite.rect.right < -100 or
                sprite.rect.left > WIDTH + 100):
                sprite.kill()

# Game loop
running = True
while running:
    # Keep game running at the right speed
    clock.tick(FPS)
    
    # Process input (events)
    for event in pygame.event.get():
        # Check for closing window
        if event.type == QUIT:
            running = False
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = False
            elif event.key == K_e and game_state.state == "playing":
                player.hyper_dash()
    
    # Update game state
    if game_state.state == "playing":
        # Update all sprites
        all_sprites.update()
        
        # Check if enemy wave is cleared
        if len(enemies) == 0 and not game_state.boss_fight:
            if game_state.next_wave():
                # Spawn boss for this sector
                boss = Boss(game_state.sector)
                all_sprites.add(boss)
                bosses.add(boss)
            else:
                # Spawn new wave of enemies
                for i in range(game_state.wave_enemies):
                    if game_state.sector >= 3 and random.random() < 0.3:
                        enemy = Enemy("elite")  # More elite enemies in later sectors
                    else:
                        enemy = Enemy("basic")
                    all_sprites.add(enemy)
                    enemies.add(enemy)
                    
        # Check if boss is defeated
        if game_state.boss_fight and len(bosses) == 0:
            game_state.boss_fight = False
            # Show upgrade menu between sectors
            if game_state.next_sector():
                # Game completed!
                pass
            else:
                # Show upgrade menu
                show_upgrade_menu()
        
        # Check for bullet hits on enemies
        hits = pygame.sprite.groupcollide(enemies, bullets, False, True)
        for enemy, bullet_list in hits.items():
            score = enemy.hit(10)  # Each bullet does 10 damage
            if score > 0:  # Enemy was destroyed
                game_state.score += score * game_state.combo
                game_state.combo += 1
                game_state.resources += 5  # Resources for destroying enemies
                if game_state.combo > game_state.max_combo:
                    game_state.max_combo = game_state.combo
                    
        # Check for bullet hits on bosses
        hits = pygame.sprite.groupcollide(bosses, bullets, False, True)
        for boss, bullet_list in hits.items():
            score, boss_defeated = boss.hit(10)  # Each bullet does 10 damage
            if boss_defeated:
                game_state.score += score * game_state.combo
                game_state.combo += 1
                game_state.resources += 100  # Big resource bonus for boss
                if game_state.combo > game_state.max_combo:
                    game_state.max_combo = game_state.combo
        
        # Check for enemy bullet hits on player
        hits = pygame.sprite.spritecollide(player, enemy_bullets, True)
        for bullet in hits:
            if player.hit(bullet.damage):
                game_state.state = "game_over"
                game_state.combo = 1
        
        # Check for collisions with enemies
        hits = pygame.sprite.spritecollide(player, enemies, False)
        for enemy in hits:
            if player.hit(20):  # Collision with enemy does 20 damage
                game_state.state = "game_over"
                game_state.combo = 1
            enemy.hit(50)  # Enemy also takes damage from collision
        
        # Check for collisions with bosses
        hits = pygame.sprite.spritecollide(player, bosses, False)
        for boss in hits:
            if player.hit(30):  # Collision with boss does more damage
                game_state.state = "game_over"
                game_state.combo = 1
        
        # Check for power-up collection
        hits = pygame.sprite.spritecollide(player, powerups, True)
        for powerup in hits:
            if powerup.type == "health":
                player.health = min(player.max_health, player.health + 20)
            elif powerup.type == "shield":
                player.energy = player.max_energy
            elif powerup.type == "weapon":
                weapon_types = ["normal", "spread", "laser"]
                if player.weapon_level < 3:
                    player.weapon_level += 1
                else:
                    idx = weapon_types.index(player.weapon_type)
                    player.weapon_type = weapon_types[(idx + 1) % len(weapon_types)]
                    player.weapon_level = 1
            elif powerup.type == "drone":
                player.add_drone()
        
        # Add this line:
        cleanup_sprites()
    
    # Draw / render
    screen.fill(BLACK)
    
    if game_state.state == "menu":
        # Draw menu screen
        draw_text(screen, "SPACE FIGHTER", 64, WIDTH / 2, HEIGHT / 4)
        draw_text(screen, "WASD or Arrow keys to move, SPACE to shoot", 22, WIDTH / 2, HEIGHT / 2)
        draw_text(screen, "E for Hyper Dash, SHIFT for Energy Shield", 22, WIDTH / 2, HEIGHT / 2 + 30)
        draw_text(screen, "Press any key to begin", 18, WIDTH / 2, HEIGHT * 3 / 4)
        
        # Check for key press to start
        keystate = pygame.key.get_pressed()
        if any(keystate):
            game_state.state = "playing"
            
    elif game_state.state == "playing":
        # Draw all sprites
        all_sprites.draw(screen)
        
        # Draw player information
        draw_bar(screen, 10, 10, player.health, player.max_health, 200, 20, GREEN)
        draw_text(screen, f"Health: {int(player.health)}/{player.max_health}", 18, 110, 10)
        
        draw_bar(screen, 10, 40, player.energy, player.max_energy, 200, 20, BLUE)
        draw_text(screen, f"Energy: {int(player.energy)}/{player.max_energy}", 18, 110, 40)
        
        # Draw shield if active
        if player.shield_active:
            pygame.draw.circle(screen, BLUE, player.rect.center, 40, 2)
            
        # Draw game information
        draw_text(screen, f"Score: {game_state.score}", 22, WIDTH - 100, 10)
        draw_text(screen, f"Combo: x{game_state.combo}", 18, WIDTH - 100, 40)
        draw_text(screen, f"Sector: {game_state.sector} - Wave: {game_state.wave}", 18, WIDTH - 100, 70)
        draw_text(screen, f"Resources: {game_state.resources}", 18, WIDTH - 100, 100)
        
        # Draw boss health bar if fighting a boss
        if game_state.boss_fight and bosses:
            boss = bosses.sprites()[0]
            draw_bar(screen, WIDTH//2 - 150, HEIGHT - 30, boss.health, boss.max_health, 300, 20, RED)
            draw_text(screen, boss.name, 20, WIDTH//2, HEIGHT - 50)
            
    elif game_state.state == "game_over":
        # Draw game over screen
        draw_text(screen, "GAME OVER", 64, WIDTH / 2, HEIGHT / 4)
        draw_text(screen, f"Score: {game_state.score}", 36, WIDTH / 2, HEIGHT / 2)
        draw_text(screen, f"Max Combo: x{game_state.max_combo}", 24, WIDTH / 2, HEIGHT / 2 + 50)
        draw_text(screen, "Press any key to return to menu", 18, WIDTH / 2, HEIGHT * 3 / 4)
        
        # Check for key press to return to menu
        keystate = pygame.key.get_pressed()
        if any(keystate):
            # Reset game
            game_state.reset()
            all_sprites = pygame.sprite.Group()
            player = Player()
            bullets = pygame.sprite.Group()
            enemy_bullets = pygame.sprite.Group()
            enemies = pygame.sprite.Group()
            powerups = pygame.sprite.Group()
            bosses = pygame.sprite.Group()
            all_sprites.add(player)
            
            # Create initial enemies
            for i in range(game_state.wave_enemies):
                enemy = Enemy()
                all_sprites.add(enemy)
                enemies.add(enemy)
    
    elif game_state.state == "victory":
        # Draw victory screen
        draw_text(screen, "CONGRATULATIONS!", 64, WIDTH / 2, HEIGHT / 4)
        draw_text(screen, "You defeated the Dominion Mothership!", 36, WIDTH / 2, HEIGHT / 2 - 50)
        draw_text(screen, f"Final Score: {game_state.score}", 36, WIDTH / 2, HEIGHT / 2)
        draw_text(screen, f"Max Combo: x{game_state.max_combo}", 24, WIDTH / 2, HEIGHT / 2 + 50)
        draw_text(screen, "Press any key to return to menu", 18, WIDTH / 2, HEIGHT * 3 / 4)
        
        # Check for key press to return to menu
        keystate = pygame.key.get_pressed()
        if any(keystate):
            # Reset game
            game_state.reset()
            all_sprites = pygame.sprite.Group()
            player = Player()
            bullets = pygame.sprite.Group()
            enemy_bullets = pygame.sprite.Group()
            enemies = pygame.sprite.Group()
            powerups = pygame.sprite.Group()
            bosses = pygame.sprite.Group()
            all_sprites.add(player)
            
            # Create initial enemies
            for i in range(game_state.wave_enemies):
                enemy = Enemy()
                all_sprites.add(enemy)
                enemies.add(enemy)
    
    # After drawing everything, flip the display
    pygame.display.flip()

# Quit the game
pygame.quit()
sys.exit() 