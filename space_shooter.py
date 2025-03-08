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
        # Add dying state
        self.dying = False
        self.dying_start = 0
        self.dying_duration = 1500
        self.blink_interval = 150
        self.visible = True
        # Track mouse position for laser aiming
        self.mouse_pos = (WIDTH // 2, 0)

    def update(self):
        # Check if dying
        if self.dying:
            now = pygame.time.get_ticks()
            # Blink effect
            if (now - self.dying_start) % self.blink_interval < self.blink_interval // 2:
                self.visible = True
            else:
                self.visible = False
                
            if now - self.dying_start > self.dying_duration:
                self.kill()
                return
                
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
        # Space or mouse button check is now handled in the main game loop
            
        # SWAPPED: Energy shield is now E key
        if keystate[K_e] and self.energy > 0:
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
                
            # Drones also shoot normal bullets
            for drone in self.drone_list:
                drone.shoot()
                
        elif self.weapon_type == "spread":
            for angle in range(-30, 31, 30):
                bullet = SpreadBullet(self.rect.centerx, self.rect.top, angle)
                all_sprites.add(bullet)
                bullets.add(bullet)
                
            # Drones also shoot spread bullets
            for drone in self.drone_list:
                drone.shoot()
                
        elif self.weapon_type == "bouncing":
            # Create a bouncing bullet that targets enemies
            bullet = BouncingBullet(self.rect.centerx, self.rect.top)
            all_sprites.add(bullet)
            bullets.add(bullet)

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
            return True
        return False
            
    def hit(self, damage):
        if not self.invincible:
            if self.shield_active:
                # Shield absorbs damage
                return False
            else:
                self.health -= damage
                if self.health <= 0 and not self.dying:
                    # Start dying animation instead of immediate kill
                    self.dying = True
                    self.dying_start = pygame.time.get_ticks()
                    return False  # Changed to False to prevent immediate game over
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
        # Position the drone relative to the player without needing player parameter
        if self.position == 0:
            self.rect.right = self.player.rect.left - 10
        else:
            self.rect.left = self.player.rect.right + 10
        self.rect.centery = self.player.rect.centery
        
    def shoot(self):
        # Get the player's current weapon type
        if self.player.weapon_type == "normal":
            bullet = Bullet(self.rect.centerx, self.rect.top)
            all_sprites.add(bullet)
            bullets.add(bullet)
        elif self.player.weapon_type == "spread":
            # Drones shoot a smaller spread (just 3 bullets)
            for angle in range(-15, 16, 15):
                bullet = SpreadBullet(self.rect.centerx, self.rect.top, angle)
                all_sprites.add(bullet)
                bullets.add(bullet)
        elif self.player.weapon_type == "bouncing":
            # Create a bouncing bullet that targets enemies
            bullet = BouncingBullet(self.rect.centerx, self.rect.top)
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

class BouncingBullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((8, 8))
        self.image.fill(GREEN)  # Green color for bouncing bullets
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed = 10  # Base speed
        
        # Find the closest enemy to target
        self.target_enemy()
        
        # If we couldn't find an enemy, use a default upward movement
        if not hasattr(self, 'speedy') or not hasattr(self, 'speedx'):
            self.speedy = -self.speed
            self.speedx = random.choice([-2, -1, 1, 2])  # Small random horizontal movement
            
        self.bounces = 0
        self.max_bounces = 3  # Maximum number of bounces before disappearing
        self.damage = 8  # Slightly less damage than regular bullets (which do 10)
        
    def target_enemy(self):
        # Get a list of all enemies and bosses
        all_targets = list(enemies) + list(bosses)
        
        if not all_targets:
            # No enemies found, will use default movement
            return
            
        # Find the closest enemy
        closest_enemy = None
        closest_distance = float('inf')
        
        for enemy in all_targets:
            # Calculate distance to this enemy
            dx = enemy.rect.centerx - self.rect.centerx
            dy = enemy.rect.centery - self.rect.centery
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance < closest_distance:
                closest_distance = distance
                closest_enemy = enemy
                
        if closest_enemy:
            # Calculate direction to the closest enemy
            dx = closest_enemy.rect.centerx - self.rect.centerx
            dy = closest_enemy.rect.centery - self.rect.centery
            
            # Normalize the direction vector
            length = max(1, math.sqrt(dx * dx + dy * dy))  # Prevent division by zero
            dx /= length
            dy /= length
            
            # Set velocity components, keep overall speed consistent
            self.speedx = dx * self.speed
            self.speedy = dy * self.speed
        
    def update(self):
        self.rect.y += self.speedy
        self.rect.x += self.speedx
        
        # Bounce off the sides of the screen
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
            self.speedx = -self.speedx
            self.bounces += 1
            self.retarget_after_bounce()
        if self.rect.left < 0:
            self.rect.left = 0
            self.speedx = -self.speedx
            self.bounces += 1
            self.retarget_after_bounce()
            
        # Bounce off the top of the screen
        if self.rect.top < 0:
            self.rect.top = 0
            self.speedy = -self.speedy
            self.bounces += 1
            self.retarget_after_bounce()
            
        # Kill if it moves off the bottom of the screen or exceeds max bounces
        if self.rect.top > HEIGHT or self.bounces >= self.max_bounces:
            self.kill()
    
    def retarget_after_bounce(self):
        # After bouncing, try to retarget toward closest enemy (50% chance)
        if random.random() < 0.5:
            self.target_enemy()
            
    def bounce_off_enemy(self):
        # Called when the bullet hits an enemy but doesn't kill it
        self.speedy = -self.speedy
        self.speedx = -self.speedx  # Reverse direction
        
        # Slightly randomize the direction for more interesting bounces
        angle_variation = random.uniform(-30, 30)  # Up to 30 degrees variation
        angle = math.degrees(math.atan2(self.speedy, self.speedx)) + angle_variation
        angle_radians = math.radians(angle)
        
        speed = math.sqrt(self.speedx**2 + self.speedy**2)
        self.speedx = math.cos(angle_radians) * speed
        self.speedy = math.sin(angle_radians) * speed
        
        self.bounces += 1
        
        # Try to retarget after bouncing (50% chance)
        if random.random() < 0.5:
            self.target_enemy()

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
    def __init__(self, x, y, level, angle=0, color=RED):
        pygame.sprite.Sprite.__init__(self)
        self.level = level
        width = 10 + (level * 5)  # Wider with higher level
        length = HEIGHT  # Length of the laser
        
        # Create a surface for the original laser pointing up
        original = pygame.Surface((width, length), pygame.SRCALPHA)
        original.fill(color)
        
        # Rotate the laser to point at the target angle
        self.image = pygame.transform.rotate(original, angle)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        
        self.damage = 5 * level
        self.duration = 800  # Increased from 500ms
        self.created = pygame.time.get_ticks()
        self.angle = angle
        
    def update(self):
        now = pygame.time.get_ticks()
        if now - self.created > self.duration:
            self.kill()

# Enemy classes
class Enemy(pygame.sprite.Sprite):
    def __init__(self, enemy_type="basic"):
        pygame.sprite.Sprite.__init__(self)
        self.enemy_type = enemy_type
        
        # Base speed calculation - scales with game sector
        base_min_speed = 2 + (game_state.sector - 1) * 0.5
        base_max_speed = 5 + (game_state.sector - 1) * 0.5
        
        if enemy_type == "basic":
            self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, RED, [(0, 0), (40, 0), (20, 40)])
            self.rect = self.image.get_rect()
            self.health = 10  # Reduced for easier gameplay
            self.speed = random.uniform(base_min_speed, base_max_speed)  # Speed scales with sector
            self.shoot_delay = 2000  # Base delay
            self.score_value = 10
            
        elif enemy_type == "elite":
            self.image = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, PURPLE, [(0, 0), (60, 0), (30, 60)])
            self.rect = self.image.get_rect()
            self.health = 50
            self.speed = random.uniform(base_min_speed, base_max_speed)
            self.shoot_delay = 1000  # Base delay
            self.score_value = 25  # Elite enemies are worth more points
            
        # Add random offset to shoot delay to prevent synchronized firing
        self.shoot_delay += random.randint(-500, 500)
        
        # Random initial delay so they don't all start firing at once
        self.last_shot = pygame.time.get_ticks() - random.randint(0, self.shoot_delay)
        
        self.rect.x = random.randrange(0, WIDTH - self.rect.width)
        self.rect.y = random.randrange(-150, -50)
        
        # Track this enemy's bullets
        self.bullets = []
        
    def update(self):
        # Update enemy position and shooting logic
        self.rect.y += self.speed
        now = pygame.time.get_ticks()
        
        # Check if it's time to shoot
        if now - self.last_shot > self.shoot_delay:
            self.shoot()
            self.last_shot = now
            
    def shoot(self):
        if self.enemy_type == "basic":
            bullet = EnemyBullet(self.rect.centerx, self.rect.bottom, self)
            all_sprites.add(bullet)
            enemy_bullets.add(bullet)
            self.bullets.append(bullet)  # Track this bullet
        elif self.enemy_type == "elite":
            for angle in range(-30, 31, 60):  # Changed from 30 to 60 (fewer bullets)
                bullet = EnemySpreadBullet(self.rect.centerx, self.rect.bottom, angle, self)
                all_sprites.add(bullet)
                enemy_bullets.add(bullet)
                self.bullets.append(bullet)  # Track this bullet
                
    def hit(self, damage):
        self.health -= damage
        if self.health <= 0:
            # Destroy all bullets fired by this enemy
            for bullet in self.bullets[:]:  # Use a copy of the list to safely iterate
                bullet.kill()
            self.bullets.clear()  # Clear the list
            
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
    def __init__(self, x, y, owner=None):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((5, 15))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.top = y
        self.speedy = 5
        self.damage = 5
        self.owner = owner  # Store reference to the enemy that fired this bullet
        
    def update(self):
        self.rect.y += self.speedy
        # Kill if it moves off the bottom of the screen
        if self.rect.top > HEIGHT:
            self.kill()
        # Remove reference from owner's bullet list when bullet is destroyed
        if self.owner and not self.alive():
            if self in self.owner.bullets:
                self.owner.bullets.remove(self)

class EnemySpreadBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle, owner=None):
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
        self.owner = owner  # Store reference to the enemy that fired this bullet
        
    def update(self):
        self.rect.y += self.speedy
        self.rect.x += self.speedx
        # Kill if it moves off the screen
        if self.rect.bottom < 0 or self.rect.top > HEIGHT or self.rect.left > WIDTH or self.rect.right < 0:
            self.kill()
        # Remove reference from owner's bullet list when bullet is destroyed
        if self.owner and not self.alive():
            if self in self.owner.bullets:
                self.owner.bullets.remove(self)

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

    def apply_effect(self, player):
        if self.type == "health":
            player.health = min(player.max_health, player.health + 20)
        elif self.type == "shield":
            player.energy = player.max_energy
        elif self.type == "weapon":
            weapon_types = ["normal", "spread", "bouncing"]
            if player.weapon_level < 3:
                player.weapon_level += 1
            else:
                idx = weapon_types.index(player.weapon_type)
                player.weapon_type = weapon_types[(idx + 1) % len(weapon_types)]
                player.weapon_level = 1
        elif self.type == "drone":
            player.add_drone()
        
        # Grant temporary invincibility
        player.invincible = True
        player.invincible_start = pygame.time.get_ticks()

# Boss class
class Boss(pygame.sprite.Sprite):
    def __init__(self, sector):
        pygame.sprite.Sprite.__init__(self)
        self.sector = sector
        
        # Initialize the dying state
        self.dying = False
        
        # Track boss bullets
        self.bullets = []
        
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
                bullet = EnemySpreadBullet(self.rect.centerx, self.rect.bottom, angle, self)
                all_sprites.add(bullet)
                enemy_bullets.add(bullet)
                self.bullets.append(bullet)  # Track this bullet
        elif self.pattern == 1:
            # Circular pattern
            for angle in range(0, 360, 30):
                bullet = EnemySpreadBullet(self.rect.centerx, self.rect.centery, angle, self)
                bullet.speedy = 6 * math.cos(math.radians(angle))
                bullet.speedx = 6 * math.sin(math.radians(angle))
                all_sprites.add(bullet)
                enemy_bullets.add(bullet)
                self.bullets.append(bullet)  # Track this bullet
        elif self.pattern == 2:
            # Aimed pattern
            angle = math.degrees(math.atan2(player.rect.centery - self.rect.centery, 
                                            player.rect.centerx - self.rect.centerx))
            for i in range(-2, 3):
                bullet = EnemySpreadBullet(self.rect.centerx, self.rect.bottom, angle + (i * 10) + 90, self)
                all_sprites.add(bullet)
                enemy_bullets.add(bullet)
                self.bullets.append(bullet)  # Track this bullet
            
            # Also spawn some minions
            if random.random() < 0.3 and len(enemies) < 5:
                enemy = Enemy("elite")
                enemy.rect.centerx = self.rect.centerx
                enemy.rect.top = self.rect.bottom
                all_sprites.add(enemy)
                enemies.add(enemy)
                
    def hit(self, damage):
        self.health -= damage
        if self.health <= 0 and not self.dying:
            self.dying = True
            
            # Destroy all bullets fired by this boss
            for bullet in self.bullets[:]:  # Use a copy of the list to safely iterate
                bullet.kill()
            self.bullets.clear()  # Clear the list
            
            # Drop several power-ups when boss is killed
            for _ in range(3 + self.sector):
                power_up = PowerUp(self.rect.centerx + random.randint(-50, 50),
                                 self.rect.centery + random.randint(-50, 50))
                all_sprites.add(power_up)
                powerups.add(power_up)
            
            # Spawn a shop portal where the boss was
            portal = ShopPortal(self.rect.centerx, self.rect.centery)
            all_sprites.add(portal)
            
            # Add portal to a new sprite group for collision detection
            if 'shop_portals' not in globals():
                global shop_portals
                shop_portals = pygame.sprite.Group()
            shop_portals.add(portal)
            
            # Remove the boss
            self.kill()
        
        # Return whether the boss is still alive
        return self.health <= 0

# Add a new ShopPortal class
class ShopPortal(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        # Create a visually distinct portal
        self.image = pygame.Surface((80, 80), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (50, 255, 150), (40, 40), 35)  # Green outer circle
        pygame.draw.circle(self.image, (0, 0, 0), (40, 40), 25)       # Black inner circle
        pygame.draw.circle(self.image, (255, 255, 255), (40, 40), 15) # White core
        
        # Add pulsing effect
        self.pulse_size = 0
        self.pulse_direction = 1
        self.original_image = self.image.copy()
        
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        
        # Add hover text
        self.font = pygame.font.SysFont("Arial", 14)
        self.text = self.font.render("ENTER SHOP (Press E)", True, WHITE)
        self.text_rect = self.text.get_rect()
        
    def update(self):
        # Create a pulsing effect
        self.pulse_size += 0.1 * self.pulse_direction
        if self.pulse_size > 5:
            self.pulse_direction = -1
        elif self.pulse_size < -5:
            self.pulse_direction = 1
            
        # Pulse the portal
        size = int(80 + self.pulse_size)
        pulsed_image = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Draw the pulsing circles
        pygame.draw.circle(pulsed_image, (50, 255, 150), (size//2, size//2), size//2 - 5)
        pygame.draw.circle(pulsed_image, (0, 0, 0), (size//2, size//2), size//2 - 15)
        pygame.draw.circle(pulsed_image, (255, 255, 255), (size//2, size//2), size//2 - 25)
        
        # Update image and rect
        self.image = pulsed_image
        old_center = self.rect.center
        self.rect = self.image.get_rect()
        self.rect.center = old_center
        
        # Update text position
        self.text_rect.centerx = self.rect.centerx
        self.text_rect.top = self.rect.bottom + 10
        
    def draw(self, surface):
        # Draw the portal and text
        surface.blit(self.image, self.rect)
        surface.blit(self.text, self.text_rect)

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
        self.wave_enemies = 5  # Reduced from 8 for easier start
        self.waves_per_sector = 5  # Waves to complete before boss
        
        # Track shop purchases for price increases
        self.purchase_counts = {
            "health": 0,
            "engine": 0,
            "shield": 0,
            "drone": 0,
            "drone_slot": 0
        }
        
        # Track bosses defeated
        self.bosses_defeated = 0
        
        # Difficulty scaling
        self.difficulty_multiplier = 1.0
        
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
        
        # Increase difficulty - more gradual progression
        self.wave_enemies += 1  # Add just 1 enemy per sector instead of 2
        self.difficulty_multiplier += 0.15  # 15% increase per sector
        
        # Track bosses defeated
        self.bosses_defeated += 1
        
        # Game completed if all sectors done
        if self.sector > 6:
            self.state = "victory"
            return True
        return False

    def get_item_price(self, item_type, base_price):
        # Calculate price with 10% increase per purchase
        count = self.purchase_counts.get(item_type, 0)
        return int(base_price * (1 + (0.1 * count)))

# Function to draw text
def draw_text(surface, text, size, x, y, color=WHITE, return_rect=False):
    font = pygame.font.SysFont("Arial", size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x, y)
    surface.blit(text_surface, text_rect)
    if return_rect:
        return text_rect

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
shop_portals = pygame.sprite.Group()
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
    option_rects = []  # Store rectangles for mouse detection
    
    # Base prices
    base_prices = {
        "health": 50,
        "engine": 50,
        "shield": 50,
        "drone": 100,
        "drone_slot": 200
    }
    
    while upgrade_running:
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()
        
        # Create upgrade options dynamically
        upgrade_options = [
            {"name": "Hull Integrity", "cost": game_state.get_item_price("health", base_prices["health"]), 
             "effect": "Increases max health by 20", "type": "health"},
            {"name": "Engine Efficiency", "cost": game_state.get_item_price("engine", base_prices["engine"]), 
             "effect": "Increases movement speed", "type": "engine"},
            {"name": "Shield Capacity", "cost": game_state.get_item_price("shield", base_prices["shield"]), 
             "effect": "Increases energy and regen", "type": "shield"},
            {"name": f"Drone Support ({len(player.drone_list)}/{player.max_drones})", 
             "cost": game_state.get_item_price("drone", base_prices["drone"]), 
             "effect": "Adds a support drone", "type": "drone"}
        ]
        
        # Add drone slot expansion after 3 bosses
        if game_state.bosses_defeated >= 3:
            upgrade_options.append({
                "name": "Drone Bay Expansion", 
                "cost": game_state.get_item_price("drone_slot", base_prices["drone_slot"]), 
                "effect": "Increases max drone capacity by 1", 
                "type": "drone_slot"
            })
        
        # Process input
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    upgrade_running = False
                elif event.key == K_UP or event.key == K_w:  # Allow W for up
                    selected_option = (selected_option - 1) % len(upgrade_options)
                elif event.key == K_DOWN or event.key == K_s:  # Allow S for down
                    selected_option = (selected_option + 1) % len(upgrade_options)
                elif event.key == K_RETURN:
                    # Apply upgrade if enough resources
                    apply_upgrade(upgrade_options[selected_option])
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    # Check if click is on an option
                    for i, rect in enumerate(option_rects):
                        if rect.collidepoint(mouse_pos):
                            if i < len(upgrade_options):  # Make sure the option exists
                                apply_upgrade(upgrade_options[i])
                                break
        
        # Draw upgrade menu
        screen.fill(BLACK)
        
        draw_text(screen, "UPGRADE MENU", 40, WIDTH / 2, 30)
        draw_text(screen, f"Resources: {game_state.resources}", 25, WIDTH / 2, 80)
        
        option_rects = []  # Reset the list
        for i, option in enumerate(upgrade_options):
            color = RED if game_state.resources < option["cost"] else GREEN
            
            # If it's a drone option and player is at max, show as unavailable
            if option["type"] == "drone" and len(player.drone_list) >= player.max_drones:
                color = RED
                
            highlight = ">" if i == selected_option else " "
            
            # Calculate text position
            y_pos = 150 + (i * 40)
            text = f"{highlight} {option['name']} (Cost: {option['cost']})"
            
            # Draw option and get its rect for mouse detection
            text_rect = draw_text(screen, text, 20, WIDTH / 2, y_pos, color, return_rect=True)
            option_rects.append(text_rect)
            
            draw_text(screen, option["effect"], 16, WIDTH / 2, y_pos + 20, WHITE)
            
        draw_text(screen, "Arrow keys to select, ENTER to purchase, ESC to exit", 
                18, WIDTH / 2, HEIGHT - 50)
        draw_text(screen, "You can also click on options with your mouse", 
                18, WIDTH / 2, HEIGHT - 30)
        
        pygame.display.flip()
    
    return

# Function to apply upgrades (extracted for reuse)
def apply_upgrade(option):
    if game_state.resources >= option["cost"]:
        # Check if trying to add drone when at max
        if option["type"] == "drone" and len(player.drone_list) >= player.max_drones:
            return
            
        # Apply the upgrade
        game_state.resources -= option["cost"]
        
        if option["type"] == "health":
            player.max_health += 20
            player.health = player.max_health
            game_state.purchase_counts["health"] += 1
            
        elif option["type"] == "engine":
            player.speed_factor = 1.2
            game_state.purchase_counts["engine"] += 1
            
        elif option["type"] == "shield":
            player.max_energy += 20
            player.energy_regen += 0.2
            player.energy = player.max_energy
            game_state.purchase_counts["shield"] += 1
            
        elif option["type"] == "drone":
            success = player.add_drone()
            if success:
                game_state.purchase_counts["drone"] += 1
                
        elif option["type"] == "drone_slot":
            player.max_drones += 1
            game_state.purchase_counts["drone_slot"] += 1

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
    
    # Get mouse position for laser aiming
    mouse_pos = pygame.mouse.get_pos()
    if player is not None:  # Make sure player exists
        player.mouse_pos = mouse_pos
    
    # Process input (events)
    for event in pygame.event.get():
        # Check for closing window
        if event.type == QUIT:
            running = False
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = False
            elif event.key == K_LSHIFT and game_state.state == "playing":
                # SWAPPED: Shift now activates hyper dash
                player.hyper_dash()
        elif event.type == MOUSEBUTTONDOWN:
            # Left click to shoot
            if event.button == 1 and game_state.state == "playing":
                now = pygame.time.get_ticks()
                if now - player.last_shot > player.shoot_delay:
                    player.shoot()
                    player.last_shot = now
    
    if game_state.state == "playing":
        # Check keyboard for shooting (space bar)
        keystate = pygame.key.get_pressed()
        if keystate[K_SPACE]:
            now = pygame.time.get_ticks()
            if now - player.last_shot > player.shoot_delay:
                player.shoot()
                player.last_shot = now
    
    # Update game state
    if game_state.state == "playing":
        # Update all sprites
        all_sprites.update()
        
        # Draw player based on visibility (for dying animation)
        if player.dying and not player.visible:
            all_sprites.remove(player)
        elif player.dying and player.visible and player not in all_sprites:
            all_sprites.add(player)
        
        # Handle boss visibility for dying animation
        for boss in bosses:
            if boss.dying and not boss.visible:
                all_sprites.remove(boss)
            elif boss.dying and boss.visible and boss not in all_sprites:
                all_sprites.add(boss)
        
        # Check for powerup collection
        hits = pygame.sprite.spritecollide(player, powerups, True)
        for powerup in hits:
            powerup.apply_effect(player)
            
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
                    
        # Check for player interaction with shop portal
        portal_hits = pygame.sprite.spritecollide(player, shop_portals, False)
        if portal_hits:
            # Show "Press E to enter shop" text
            for portal in portal_hits:
                # If player presses E while touching portal
                keys = pygame.key.get_pressed()
                if keys[K_e]:
                    # Enter shop and remove the portal
                    
                    # Remove portals from both groups
                    for portal in shop_portals:
                        portal.kill()  # This removes it from all sprite groups
                    shop_portals.empty()  # This is redundant but kept for safety
                    
                    # Clear any existing bullets to prevent issues after shop
                    bullets.empty()  # Clear all player bullets
                    
                    # Show upgrade menu between sectors
                    if game_state.next_sector():
                        # Game completed!
                        pass
                    else:
                        # Show upgrade menu
                        show_upgrade_menu()
                        
                    # Double-check that portals are removed - redundant but kept for safety
                    shop_portals.empty()
        
        # Check for bullet hits on enemies
        hits = pygame.sprite.groupcollide(enemies, bullets, False, False)  # Changed to keep bullets
        for enemy, bullet_list in hits.items():
            for bullet in bullet_list:
                if isinstance(bullet, BouncingBullet):
                    # For bouncing bullets, check if enemy will die from this hit
                    if enemy.health <= bullet.damage:
                        # If enemy will die, remove the bullet
                        bullet.kill()
                        score = enemy.hit(bullet.damage)
                    else:
                        # If enemy won't die, bounce the bullet
                        enemy.hit(bullet.damage)
                        bullet.bounce_off_enemy()
                else:
                    # Normal bullets get removed
                    bullet.kill()
                    score = enemy.hit(10)  # Normal bullet damage
                
                if enemy.health <= 0:  # Enemy was destroyed
                    game_state.score += enemy.score_value * game_state.combo
                    game_state.combo += 1
                    game_state.resources += 5  # Resources for destroying enemies
                    if game_state.combo > game_state.max_combo:
                        game_state.max_combo = game_state.combo
                    
        # Check for bullet hits on bosses
        hits = pygame.sprite.groupcollide(bosses, bullets, False, False)  # Changed to keep bullets
        for boss, bullet_list in hits.items():
            for bullet in bullet_list:
                if isinstance(bullet, BouncingBullet):
                    # For bouncing bullets, always bounce off bosses unless boss will die
                    if boss.health <= bullet.damage:
                        bullet.kill()
                        boss.hit(bullet.damage)
                    else:
                        boss.hit(bullet.damage)
                        bullet.bounce_off_enemy()
                else:
                    # Normal bullets get removed
                    bullet.kill()
                    boss.hit(10)  # Normal bullet damage
                
                if boss.health <= 0:  # Boss was defeated
                    game_state.score += 500 * game_state.combo  # Boss score
                    game_state.combo += 1
                    game_state.resources += 100  # Big resource bonus for boss
        
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
        
        # Add this line:
        cleanup_sprites()
        
        # After all sprite updates and collision detections
        if player.dying and pygame.time.get_ticks() - player.dying_start > player.dying_duration:
            # Now transition to game over after the animation completes
            game_state.state = "game_over"
            game_state.combo = 1
    
    # Draw / render
    screen.fill(BLACK)
    
    if game_state.state == "menu":
        # Draw menu screen
        draw_text(screen, "SPACE FIGHTER", 64, WIDTH / 2, HEIGHT / 4)
        draw_text(screen, "WASD or Arrow keys to move, SPACE or LEFT CLICK to shoot", 22, WIDTH / 2, HEIGHT / 2)
        draw_text(screen, "SHIFT for Hyper Dash, E for Energy Shield", 22, WIDTH / 2, HEIGHT / 2 + 30)
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
            
        # Draw portal special effects and text
        for portal in shop_portals:
            portal.draw(screen)
        
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
            shop_portals = pygame.sprite.Group()
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
            shop_portals = pygame.sprite.Group()
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