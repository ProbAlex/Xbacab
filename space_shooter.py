import pygame
import sys
import random
import math
from pygame.locals import *
import os
from barrier_goliath import BarrierGoliath

# Set SDL audio driver to a fallback before initializing
os.environ['SDL_AUDIODRIVER'] = 'dummy'  # This uses a dummy audio driver

# Initialize pygame
pygame.init()
pygame.mixer.init()  # Initialize sound mixer

# Get the user's screen info for proper fullscreen
screen_info = pygame.display.Info()
SCREEN_WIDTH = screen_info.current_w
SCREEN_HEIGHT = screen_info.current_h

# Game design constants (internal resolution)
WIDTH = int(SCREEN_WIDTH * 0.8)
HEIGHT = int(SCREEN_HEIGHT * 0.8)
FPS = 60

# Calculate centering offset for gameplay elements
OFFSET_X = (SCREEN_WIDTH - WIDTH) // 2
OFFSET_Y = (SCREEN_HEIGHT - HEIGHT) // 2

# Create fullscreen display at native resolution
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Xbacab")
clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
DARK_BLUE = (0, 0, 128)
LIGHT_BLUE = (173, 216, 230)

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
        # Position player within the original game coordinates (no offset)
        self.rect.centerx = WIDTH // 2
        self.rect.bottom = HEIGHT - 20
        self.speedx = 0
        self.speedy = 0
        
        # Adjust stats based on difficulty
        if game_state.difficulty == "easy":
            self.health = 200
            self.max_health = 200
            self.energy = 150
            self.max_energy = 150
            self.energy_regen = 0.7
            self.max_drones = 6  # More drones on easy
        elif game_state.difficulty == "normal":
            self.health = 150
            self.max_health = 150
            self.energy = 100
            self.max_energy = 100
            self.energy_regen = 0.5
            self.max_drones = 4  # Standard drones
        elif game_state.difficulty == "hard":
            self.health = 100
            self.max_health = 100
            self.energy = 80
            self.max_energy = 80
            self.energy_regen = 0.3
            self.max_drones = 3  # Fewer drones on hard
        
        self.shield_active = False
        self.shield_strength = 50
        self.shoot_delay = 100  # 200ms = 5 shots per second
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
                
            # Check if dying animation is complete
            if now - self.dying_start > self.dying_duration:
                return True  # Player is fully dead
            return False  # Still in dying animation
            
        # Natural health regeneration in easy mode
        if game_state.difficulty == "easy":
            self.health = min(self.max_health, self.health + 0.02)  # Slowly regenerate health
            
        # Update keyboard controls
        keystate = pygame.key.get_pressed()
        # Update energy
        if self.shield_active:
            self.energy -= 0.5
            if self.energy <= 0:
                self.shield_active = False
        
        # Movement
        self.speedx = 0
        self.speedy = 0
        
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
        
        # Keep the player within bounds of the screen
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.bottom > HEIGHT:
            self.rect.bottom = HEIGHT
        if self.rect.top < 0:
            self.rect.top = 0
            
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
        # Check if enough time has passed since last shot (CPS limit)
        now = pygame.time.get_ticks()
        if now - self.last_shot < self.shoot_delay:
            return  # Don't shoot if firing too quickly
        
        # Update last shot time
        self.last_shot = now
        
        # Now handle the actual shooting based on weapon type
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
                
            # Drones also shoot normal bullets - let their own logic handle it
            for drone in self.drone_list:
                drone.shoot()
                
        elif self.weapon_type == "spread":
            for angle in range(-30, 31, 30):
                bullet = SpreadBullet(self.rect.centerx, self.rect.top, angle)
                all_sprites.add(bullet)
                bullets.add(bullet)
                
            # Drones also shoot spread bullets - let their own logic handle it
            for drone in self.drone_list:
                drone.shoot()
                
        elif self.weapon_type == "bouncing":
            # Create a bouncing bullet that targets enemies
            bullet = BouncingBullet(self.rect.centerx, self.rect.top)
            all_sprites.add(bullet)
            bullets.add(bullet)
            
            # Drones also shoot bouncing bullets
            for drone in self.drone_list:
                drone.shoot()
                
        elif self.weapon_type == "homing":
            # Number of homing missiles based on weapon level
            num_missiles = self.weapon_level
            
            # Create homing missiles with slight angle variations
            for i in range(num_missiles):
                # Slight offset to left/right for multiple missiles
                if num_missiles > 1:
                    offset_x = self.rect.width * (i/(num_missiles-1) - 0.5)  # Spread across ship width
                else:
                    offset_x = 0
                    
                bullet = HomingBullet(self.rect.centerx + offset_x, self.rect.top)
                all_sprites.add(bullet)
                bullets.add(bullet)
                
            # Drones also shoot homing bullets
            for drone in self.drone_list:
                drone.shoot()

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
                if self.health <= 0:
                    # Return True to indicate player death
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
        self.position = position  # Index in drone list
        
    def update(self, *args):
        # Position drones in formation around the player
        # For up to 4 drones, place them in cardinal positions
        # For more than 4, place them in circular formation
        
        if len(self.player.drone_list) <= 4:
            # Simple formation for 1-4 drones
            if self.position == 0:  # Left
                self.rect.right = self.player.rect.left - 15
                self.rect.centery = self.player.rect.centery
            elif self.position == 1:  # Right
                self.rect.left = self.player.rect.right + 15
                self.rect.centery = self.player.rect.centery
            elif self.position == 2:  # Top
                self.rect.centerx = self.player.rect.centerx
                self.rect.bottom = self.player.rect.top - 15
            elif self.position == 3:  # Bottom
                self.rect.centerx = self.player.rect.centerx
                self.rect.top = self.player.rect.bottom + 15
        else:
            # Circular formation for 5+ drones
            angle = (360 / len(self.player.drone_list)) * self.position
            radius = 50  # Distance from player
            rad_angle = math.radians(angle)
            self.rect.centerx = self.player.rect.centerx + int(math.sin(rad_angle) * radius)
            self.rect.centery = self.player.rect.centery - int(math.cos(rad_angle) * radius)

    def shoot(self):
        # First check player's current weapon type
        if self.player.weapon_type == "normal":
            if(random.random() < 0.7):
                bullet = Bullet(self.rect.centerx, self.rect.top)
                all_sprites.add(bullet)
                bullets.add(bullet)
                
        elif self.player.weapon_type == "spread":
           for angle in range(-15, 16, 15):
                if(random.random() < 0.3):
                    bullet = SpreadBullet(self.rect.centerx, self.rect.top, angle)
                    all_sprites.add(bullet)
                    bullets.add(bullet)
                    
        elif self.player.weapon_type == "bouncing":
            if(random.random() < 0.5):
                # Always fire bouncing bullets when player has bouncing weapon type
                bullet = BouncingBullet(self.rect.centerx, self.rect.top)
                all_sprites.add(bullet)
                bullets.add(bullet)
                
        elif self.player.weapon_type == "homing":
            if(random.random() < 0.2):  # 40% chance to fire
                bullet = HomingBullet(self.rect.centerx, self.rect.top)
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

class HomingBullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((8, 8))
        self.image.fill((255, 128, 0))  # Orange color for homing bullets
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed = 7  # Slower than normal bullets but constantly homing
        self.damage = 12  # More damage than normal bullets
        self.max_lifetime = 120  # Maximum frames before disappearing (2 seconds at 60 FPS)
        self.lifetime = 0
        
        # Initial velocity (will be adjusted during homing)
        self.speedx = 0
        self.speedy = -self.speed
        
        # Target the closest enemy initially
        self.find_target()
        
    def find_target(self):
        # Get all potential targets (enemies and bosses)
        all_targets = list(enemies) + list(bosses)
        
        # If no targets, maintain current direction
        if not all_targets:
            return None
            
        # Find closest target
        closest_target = None
        closest_distance = float('inf')
        
        for target in all_targets:
            dx = target.rect.centerx - self.rect.centerx
            dy = target.rect.centery - self.rect.centery
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance < closest_distance:
                closest_distance = distance
                closest_target = target
                
        return closest_target
    
    def update(self):
        # Increment lifetime
        self.lifetime += 1
        if self.lifetime >= self.max_lifetime:
            self.kill()
            return
            
        # Find target
        target = self.find_target()
        
        # If we have a target, adjust direction toward it
        if target:
            # Calculate direction to target
            dx = target.rect.centerx - self.rect.centerx
            dy = target.rect.centery - self.rect.centery
            
            # Normalize the direction vector
            distance = max(1, math.sqrt(dx * dx + dy * dy))
            dx = dx / distance
            dy = dy / distance
            
            # Gradually adjust velocity (for smooth homing effect)
            homing_strength = 0.3  # How strongly it homes in on targets
            self.speedx = self.speedx * (1 - homing_strength) + dx * self.speed * homing_strength
            self.speedy = self.speedy * (1 - homing_strength) + dy * self.speed * homing_strength
            
            # Maintain consistent speed
            current_speed = math.sqrt(self.speedx**2 + self.speedy**2)
            if current_speed > 0:
                self.speedx = self.speedx / current_speed * self.speed
                self.speedy = self.speedy / current_speed * self.speed
        
        # Update position
        self.rect.x += self.speedx
        self.rect.y += self.speedy
        
        # Kill if it moves off the screen
        if (self.rect.right < 0 or self.rect.left > WIDTH or 
            self.rect.bottom < 0 or self.rect.top > HEIGHT):
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
        
        # Base speed calculation - scales with game sector and difficulty
        difficulty_multiplier = {
            "easy": 0.8,
            "normal": 1.0,
            "hard": 1.3
        }[game_state.difficulty]
        
        base_min_speed = (2 + (game_state.sector - 1) * 0.5) * difficulty_multiplier
        base_max_speed = (5 + (game_state.sector - 1) * 0.5) * difficulty_multiplier
        
        # Common variables for all enemy types
        self.bullets = []  # Track this enemy's bullets
        self.last_shot = pygame.time.get_ticks() - random.randint(0, 2000)  # Random initial delay
        
        # Common features based on enemy type
        if enemy_type == "basic":
            self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, RED, [(0, 0), (40, 0), (20, 40)])
            self.rect = self.image.get_rect()
            
            # Adjust health based on difficulty
            if game_state.difficulty == "easy":
                self.health = 8
            elif game_state.difficulty == "normal":
                self.health = 10
            else:  # hard
                self.health = 15
                
            self.speed = random.uniform(base_min_speed, base_max_speed)  # Speed scales with sector and difficulty
            self.shoot_delay = 2000  # Base delay
            self.score_value = 10
            
        elif enemy_type == "elite":
            self.image = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, PURPLE, [(0, 0), (60, 0), (30, 60)])
            self.rect = self.image.get_rect()
            
            # Adjust health based on difficulty
            if game_state.difficulty == "easy":
                self.health = 40
            elif game_state.difficulty == "normal":
                self.health = 50
            else:  # hard
                self.health = 70
                
            self.speed = random.uniform(base_min_speed, base_max_speed)
            self.shoot_delay = 1000  # Base delay
            self.score_value = 25  # Elite enemies are worth more points
            
        # New enemy types
        elif enemy_type == "cloaked_ambusher":
            self.image = pygame.Surface((45, 45), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, (100, 100, 150), [(0, 0), (45, 0), (22, 45)])  # Light blue-purple
            self.original_image = self.image.copy()
            self.rect = self.image.get_rect()
            
            # Cloaking variables
            self.visible = True
            self.cloak_timer = random.randint(1500, 3000)  # Time until next cloak/uncloak
            self.cloak_start = pygame.time.get_ticks()
            self.cloak_duration = 1500  # How long it stays cloaked
            self.alpha = 255  # Fully visible
            
            if game_state.difficulty == "easy":
                self.health = 15
            elif game_state.difficulty == "normal":
                self.health = 20
            else:  # hard
                self.health = 30
                
            self.speed = random.uniform(base_min_speed*0.8, base_max_speed*0.8)  # Slightly slower
            self.shoot_delay = 2500  # Longer delay between shots
            self.burst_count = 3  # Number of shots in burst
            self.burst_delay = 150  # Delay between shots in burst
            self.burst_active = False
            self.burst_shots = 0
            self.score_value = 20
            
        elif enemy_type == "splitter_drone":
            self.image = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (0, 180, 180), (25, 25), 25)  # Teal color
            self.rect = self.image.get_rect()
            self.is_split = False  # Whether this is a split version
            
            if game_state.difficulty == "easy":
                self.health = 20
            elif game_state.difficulty == "normal":
                self.health = 25
            else:  # hard
                self.health = 35
                
            self.speed = random.uniform(base_min_speed*0.9, base_max_speed*0.9)
            self.shoot_delay = 2200
            self.score_value = 15
            
        elif enemy_type == "shield_bearer":
            self.image = pygame.Surface((55, 55), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (50, 150, 250), (27, 27), 27)  # Light blue
            self.rect = self.image.get_rect()
            
            # Shield variables
            self.shield_active = True
            self.shield_health = 40
            self.shield_max_health = 40
            self.shield_regen_rate = 0.02
            self.shield_radius = 80  # How far the shield extends
            
            if game_state.difficulty == "easy":
                self.health = 15
            elif game_state.difficulty == "normal":
                self.health = 20
            else:  # hard
                self.health = 30
                
            self.speed = random.uniform(base_min_speed*0.7, base_max_speed*0.7)  # Slower
            self.shoot_delay = 3000  # Shoots less often
            self.score_value = 25
            
        elif enemy_type == "energy_sapper":
            self.image = pygame.Surface((45, 55), pygame.SRCALPHA)
            pygame.draw.ellipse(self.image, (200, 100, 200), (0, 0, 45, 55))  # Pink-purple
            self.rect = self.image.get_rect()
            
            # Sapper beam variables
            self.beam_active = False
            self.beam_start = 0
            self.beam_duration = 2000
            self.beam_cooldown = 4000
            self.beam_target = None
            
            if game_state.difficulty == "easy":
                self.health = 25
            elif game_state.difficulty == "normal":
                self.health = 35
            else:  # hard
                self.health = 50
                
            self.speed = random.uniform(base_min_speed*0.6, base_max_speed*0.6)  # Very slow
            self.shoot_delay = 4000  # Rarely shoots regular bullets
            self.score_value = 30
            
        elif enemy_type == "blade_spinner":
            self.image = pygame.Surface((48, 48), pygame.SRCALPHA)
            # Draw a spinning blade-like appearance
            points = []
            center = (24, 24)
            for i in range(8):  # 8-pointed star
                angle = math.pi * i / 4
                points.append((center[0] + 24 * math.cos(angle), center[1] + 24 * math.sin(angle)))
                angle += math.pi / 8
                points.append((center[0] + 12 * math.cos(angle), center[1] + 12 * math.sin(angle)))
            pygame.draw.polygon(self.image, (255, 150, 0), points)  # Orange color
            self.rect = self.image.get_rect()
            
            # Spinning variables
            self.angle = 0
            self.spin_speed = 5
            self.original_image = self.image.copy()
            self.orbit_center = None
            self.orbit_radius = random.randint(80, 150)
            self.orbit_speed = random.uniform(0.01, 0.03)
            self.orbit_angle = random.uniform(0, math.pi*2)
            self.reflect_bullets = game_state.difficulty == "hard"  # Only reflect on hard
            
            if game_state.difficulty == "easy":
                self.health = 20
            elif game_state.difficulty == "normal":
                self.health = 30
            else:  # hard
                self.health = 45
                
            self.speed = random.uniform(base_min_speed*0.7, base_max_speed*0.7)
            self.shoot_delay = 2500
            self.score_value = 25
            
        # Add random offset to shoot delay to prevent synchronized firing
        self.shoot_delay += random.randint(-500, 500)
        
        # Random initial delay so they don't all start firing at once
        self.last_shot = pygame.time.get_ticks() - random.randint(0, self.shoot_delay)
        
        self.rect.x = random.randrange(0, WIDTH - self.rect.width)
        self.rect.y = random.randrange(-150, -50)
        
    def update(self):
        # Store previous position to calculate momentum
        prev_x = self.rect.x
        prev_y = self.rect.y
        
        now = pygame.time.get_ticks()
        
        # Movement based on enemy type
        if self.enemy_type == "basic":
            # Basic enemies just move downward at a constant speed
            self.rect.y += self.speed
            
        elif self.enemy_type == "elite":
            # Elite enemies move in a slight side-to-side pattern while moving down
            self.rect.y += self.speed
            # Add sine wave horizontal movement
            self.rect.x += math.sin(now / 500) * 2
            
            # Keep within screen boundaries
            if self.rect.left < 0:
                self.rect.left = 0
            elif self.rect.right > WIDTH:
                self.rect.right = WIDTH
            
        elif self.enemy_type == "cloaked_ambusher":
            # Cloaked ambusher moves downward, occasionally cloaking
            self.rect.y += self.speed
            
            # Handle cloaking
            if hasattr(self, 'visible'):
                if self.visible and now - self.cloak_start > self.cloak_timer:
                    # Start cloaking
                    self.visible = False
                    self.cloak_start = now
                    # Make semi-transparent
                    self.image.set_alpha(30)  # Almost invisible
                elif not self.visible and now - self.cloak_start > self.cloak_duration:
                    # Uncloak
                    self.visible = True
                    self.cloak_start = now
                    self.cloak_timer = random.randint(2000, 4000)  # Time until next cloak
                    self.image.set_alpha(255)  # Fully visible
                    
                    # Burst attack when uncloaking
                    if hasattr(self, 'burst_active'):
                        self.burst_active = True
                        self.burst_shots = 0
                        self.last_shot = now
                
                # Handle burst fire
                if hasattr(self, 'burst_active') and self.burst_active and now - self.last_shot > self.burst_delay:
                    self.shoot_cloaked_ambusher()
                    self.burst_shots += 1
                    self.last_shot = now
                    
                    # End burst after enough shots
                    if self.burst_shots >= self.burst_count:
                        self.burst_active = False
            
        elif self.enemy_type == "splitter_drone":
            # Splitter drone moves downward, splitting happens in hit() method
            self.rect.y += self.speed
            
        elif self.enemy_type == "shield_bearer":
            # Shield bearer moves downward with shield protection
            self.rect.y += self.speed
            
            # Regenerate shield if it's active
            if hasattr(self, 'shield_active') and self.shield_active:
                if hasattr(self, 'shield_health') and hasattr(self, 'shield_max_health') and hasattr(self, 'shield_regen_rate'):
                    self.shield_health = min(self.shield_max_health, self.shield_health + self.shield_regen_rate)
                
            # Check if shield should be disabled/enabled
            if hasattr(self, 'shield_active') and hasattr(self, 'shield_health'):
                if self.shield_active and self.shield_health <= 0:
                    self.shield_active = False
                elif not self.shield_active and hasattr(self, 'shield_max_health') and self.shield_health > self.shield_max_health * 0.3:
                    self.shield_active = True
                
        elif self.enemy_type == "energy_sapper":
            # Energy sapper moves slowly
            self.rect.y += self.speed * 0.7
            
            # Check if we should start/stop the beam
            if hasattr(self, 'beam_active'):
                if not self.beam_active and now - self.last_shot > self.shoot_delay:
                    self.beam_active = True
                    self.beam_start = now
                    self.last_shot = now
                elif self.beam_active and hasattr(self, 'beam_start') and hasattr(self, 'beam_duration') and now - self.beam_start > self.beam_duration:
                    self.beam_active = False
                
                # If beam is active, look for player to target
                if self.beam_active and player.rect.centerx > self.rect.left and player.rect.centerx < self.rect.right:
                    if player.rect.top > self.rect.bottom:
                        # If player is in beam, drain energy
                        if player.energy > 0:
                            player.energy = max(0, player.energy - 0.5)
                        elif player.shoot_delay < 500:
                            player.shoot_delay += 1  # Slowly increase shoot delay (reduce fire rate)
                
        elif self.enemy_type == "blade_spinner":
            # Blade spinner moves in a spinning orbit while drifting downward
            if hasattr(self, 'orbit_angle') and hasattr(self, 'orbit_speed'):
                self.orbit_angle += self.orbit_speed
                
                # Calculate orbit position
                if hasattr(self, 'orbit_radius'):
                    orbit_x = math.cos(self.orbit_angle) * self.orbit_radius
                    orbit_y = math.sin(self.orbit_angle) * self.orbit_radius
                    
                    # Update base position (drifting downward)
                    if hasattr(self, 'base_y'):
                        self.base_y += self.speed * 0.8
                        
                        # Set actual position with orbit offset
                        if hasattr(self, 'base_x'):
                            self.rect.centerx = int(self.base_x + orbit_x)
                            self.rect.centery = int(self.base_y + orbit_y)
                            
                            # Keep within screen boundaries
                            if self.rect.left < 0:
                                self.rect.left = 0
                                self.base_x = self.rect.centerx
                            elif self.rect.right > WIDTH:
                                self.rect.right = WIDTH 
                                self.base_x = self.rect.centerx
                    else:
                        # If base position not set, initialize it
                        self.base_x = self.rect.centerx
                        self.base_y = self.rect.centery
                        # And continue with basic downward movement for this frame
                        self.rect.y += self.speed * 0.8
                else:
                    # Initialize orbit radius if missing
                    self.orbit_radius = 40 + random.randint(0, 30)
            else:
                # Initialize orbit parameters if missing
                self.orbit_angle = random.random() * math.pi * 2
                self.orbit_speed = 0.05 + (random.random() * 0.05)
                self.orbit_radius = 40 + random.randint(0, 30)
                self.base_x = self.rect.centerx
                self.base_y = self.rect.centery
                # Basic movement for this frame
                self.rect.y += self.speed
                
            # Rotate blade if attribute exists
            if hasattr(self, 'blade_angle'):
                self.blade_angle += 5
                if self.blade_angle >= 360:
                    self.blade_angle = 0
            else:
                self.blade_angle = 0
        
        # Ensure all enemies stay within horizontal screen boundaries regardless of type
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.rect.left < 0:
            self.rect.left = 0
                
        # Calculate momentum (recent movement speed)
        self.momentum_x = self.rect.x - prev_x
        self.momentum_y = self.rect.y - prev_y
            
        # Check if off bottom of screen
        if self.rect.top > HEIGHT:
            self.kill()
            
        # Shooting logic
        if now - self.last_shot > self.shoot_delay:
            # Different shooting methods based on enemy type
            if self.enemy_type == "basic":
                self.shoot()
            elif self.enemy_type == "elite":
                self.shoot()  # Elite enemies use the same shooting pattern but more frequently
            elif self.enemy_type == "cloaked_ambusher":
                # Handled in the cloaked_ambusher logic above with burst fire
                if hasattr(self, 'visible') and self.visible and not (hasattr(self, 'burst_active') and self.burst_active):
                    self.shoot_cloaked_ambusher()
            elif self.enemy_type == "splitter_drone":
                self.shoot_splitter_drone()
            elif self.enemy_type == "shield_bearer":
                self.shoot_shield_bearer()
            elif self.enemy_type == "energy_sapper":
                if not (hasattr(self, 'beam_active') and self.beam_active):
                    self.shoot_energy_sapper()
            elif self.enemy_type == "blade_spinner":
                self.shoot_blade_spinner()
                
            self.last_shot = now
    
    def shoot(self):
        if self.enemy_type == "basic":
            bullet = EnemyBullet(self.rect.centerx, self.rect.bottom, self)
            all_sprites.add(bullet)
            enemy_bullets.add(bullet)
            self.bullets.append(bullet)  # Track this bullet
        elif self.enemy_type == "elite":
            for angle in range(-30, 31, 60):  # Changed from 30 to 60 (fewer bullets)
                bullet = EnemySpreadBullet(
                    self.rect.centerx,   # x
                    self.rect.bottom,    # y
                    angle,               # angle
                    self,                # owner
                    PURPLE,              # color
                    8,                   # size
                    15,                  # damage
                    6                    # speed
                )
                all_sprites.add(bullet)
                enemy_bullets.add(bullet)
                self.bullets.append(bullet)  # Track this bullet
                
        elif self.enemy_type == "cloaked_ambusher":
            self.shoot_cloaked_ambusher()
        elif self.enemy_type == "splitter_drone":
            self.shoot_splitter_drone()
        elif self.enemy_type == "shield_bearer":
            self.shoot_shield_bearer()
        elif self.enemy_type == "energy_sapper":
            self.shoot_energy_sapper()
        elif self.enemy_type == "blade_spinner":
            self.shoot_blade_spinner()
    
    def hit(self, damage):
        # For shield bearer, check if shield is active
        if self.enemy_type == "shield_bearer" and self.shield_active:
            self.shield_health -= damage
            # Only take damage if shield is down
            if self.shield_health <= 0:
                self.shield_active = False
            return 0  # No score for hitting shield
            
        # For blade spinner with reflective ability
        if self.enemy_type == "blade_spinner" and self.reflect_bullets and random.random() < 0.4:
            # 40% chance to reflect bullets in hard mode
            angle = random.randint(0, 360)
            reflected = EnemySpreadBullet(
                self.rect.centerx,   # x
                self.rect.centery,   # y
                angle,               # angle
                self,                # owner
                (255, 200, 0),       # color (brighter orange)
                8,                   # size
                15,                  # damage
                6                    # speed
            )
            all_sprites.add(reflected)
            enemy_bullets.add(reflected)
            self.bullets.append(reflected)
            return 0  # No score for reflected hits
        
        # Normal damage handling
        self.health -= damage
        if self.health <= 0:
            # Special case for splitter drone
            if self.enemy_type == "splitter_drone" and not self.is_split:
                # Create 2-3 smaller split drones
                num_splits = 2
                if game_state.difficulty == "hard":
                    num_splits = 3
                    
                for _ in range(num_splits):
                    # Create smaller split drone
                    split = Enemy("splitter_drone")
                    split.is_split = True  # Mark as a split version
                    split.health = self.health // 2  # Half health
                    split.rect.centerx = self.rect.centerx + random.randint(-20, 20)
                    split.rect.centery = self.rect.centery
                    split.speed = self.speed * 1.5  # Faster
                    # Make it smaller
                    split.image = pygame.Surface((25, 25), pygame.SRCALPHA)
                    pygame.draw.circle(split.image, (0, 200, 200), (12, 12), 12)  # Brighter teal
                    split.rect = split.image.get_rect(center=split.rect.center)
                    
                    all_sprites.add(split)
                    enemies.add(split)
            
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

    def shoot_cloaked_ambusher(self):
        # Fast smaller bullets in a burst
        bullet = EnemyBullet(self.rect.centerx, self.rect.bottom, self)
        bullet.speedy = 7  # Faster than normal
        bullet.image = pygame.Surface((3, 10))
        bullet.image.fill((150, 150, 255))  # Light blue
        all_sprites.add(bullet)
        enemy_bullets.add(bullet)
        self.bullets.append(bullet)
        
    def shoot_splitter_drone(self):
        # Shoots a single bullet straight down
        bullet = EnemyBullet(self.rect.centerx, self.rect.bottom, self)
        all_sprites.add(bullet)
        enemy_bullets.add(bullet)
        self.bullets.append(bullet)
        
    def shoot_shield_bearer(self):
        # Shoots bullets in 3 directions
        for angle in [-30, 0, 30]:
            bullet = EnemySpreadBullet(
                self.rect.centerx,   # x
                self.rect.bottom,    # y
                angle,               # angle
                self,                # owner
                PURPLE,              # color
                8,                   # size
                15,                  # damage
                6                    # speed
            )
            all_sprites.add(bullet)
            enemy_bullets.add(bullet)
            self.bullets.append(bullet)
            
    def shoot_energy_sapper(self):
        # Doesn't shoot regular bullets when beam is active
        if not self.beam_active:
            # Shoot a slow, large bullet
            bullet = EnemyBullet(self.rect.centerx, self.rect.bottom, self)
            bullet.speedy = 3  # Slower
            bullet.image = pygame.Surface((10, 20))
            bullet.image.fill((200, 100, 200))  # Pink-purple
            bullet.damage = 10  # More damage
            all_sprites.add(bullet)
            enemy_bullets.add(bullet)
            self.bullets.append(bullet)
            
    def shoot_blade_spinner(self):
        if pygame.time.get_ticks() - self.last_shot > self.shoot_delay:
            self.last_shot = pygame.time.get_ticks()
            
            # Create multiple bullets in a spiral pattern
            num_bullets = 4
            for i in range(num_bullets):
                # Create a bullet with spiral properties
                bullet = EnemySpreadBullet(
                    self.rect.centerx,          # x
                    self.rect.centery,          # y
                    0,                          # angle
                    self,                       # owner
                    (255, 100, 100),            # color (reddish)
                    10,                         # size
                    15,                         # damage
                    6                           # speed
                )
                
                # Add spiral properties
                bullet.spiral = True
                bullet.spiral_angle = (i * (2 * math.pi / num_bullets))  # Start at evenly spaced angles
                bullet.spiral_speed = 0.05  # Rotation speed
                bullet.spiral_radius = 5    # Initial radius
                bullet.base_x = float(bullet.rect.centerx)  # Store base position for spiral calculation
                bullet.base_y = float(bullet.rect.centery)
                
                all_sprites.add(bullet)
                enemy_bullets.add(bullet)
                self.bullets.append(bullet)

# Enemy bullet classes
class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, owner=None):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((5, 15))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.top = y
        
        # Base speed
        self.base_speed = 5
        
        # Add owner's speed if available
        self.speedx = 0
        self.speedy = self.base_speed
        
        if owner:
            # Check for momentum tracking (used by Boss)
            if hasattr(owner, 'momentum_x') and hasattr(owner, 'momentum_y'):
                self.speedx += owner.momentum_x * 0.7  # 70% of owner's horizontal momentum
                self.speedy += self.base_speed + (abs(owner.momentum_y) * 0.5)  # Add momentum to base speed
            # Check for standard speed attributes
            elif hasattr(owner, 'speed'):
                # Add a portion of the owner's speed to the bullet
                self.speedy += owner.speed * 0.5  # 50% of owner's speed
                
            if hasattr(owner, 'speedx') and not hasattr(owner, 'momentum_x'):
                # Add a portion of the owner's horizontal speed
                self.speedx += owner.speedx * 0.5  # 50% of owner's horizontal speed
            
        self.damage = 5
        self.owner = owner  # Store reference to the enemy that fired this bullet
        
    def update(self):
        self.rect.y += self.speedy
        self.rect.x += self.speedx
        
        # Kill if it moves off the screen
        if (self.rect.top > HEIGHT or self.rect.bottom < 0 or 
            self.rect.right < 0 or self.rect.left > WIDTH):
            self.kill()
            
        # Remove reference from owner's bullet list when bullet is destroyed
        if self.owner and not self.alive():
            if self in self.owner.bullets:
                self.owner.bullets.remove(self)

class EnemySpreadBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle, owner=None, color=PURPLE, size=8, damage=15, speed=6):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((size, size))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.top = y
        self.angle = math.radians(angle)
        
        # Store base speed and calculate components
        self.base_speed = speed
        self.speed = speed
        
        # Factor in owner's speed if available
        if owner:
            # Check for momentum tracking (used by Boss)
            if hasattr(owner, 'momentum_x') and hasattr(owner, 'momentum_y'):
                # Momentum is already applied in the Boss's shoot method
                pass
            # Check for standard speed attributes
            elif hasattr(owner, 'speed'):
                # Add a portion of the owner's vertical speed
                self.speed += owner.speed * 0.5  # 50% of owner's speed
                
            if hasattr(owner, 'speedx') and hasattr(owner, 'speedy'):
                # For enemies with separate x and y speeds, adjust angle slightly based on movement
                # This creates a more realistic firing arc when moving horizontally
                if abs(owner.speedx) > 0.5:  # Only if moving horizontally with some speed
                    # Adjust angle slightly in the direction of movement (max 15 degrees)
                    angle_adjustment = min(15, max(-15, owner.speedx * 3))
                    self.angle = math.radians(angle + angle_adjustment)
        
        # Calculate velocity components
        self.speedy = self.speed * math.cos(self.angle)
        self.speedx = self.speed * math.sin(self.angle)
        
        self.damage = damage
        self.owner = owner  # Store reference to the enemy that fired this bullet
        # Initialize spiral properties (will be set later if needed)
        self.spiral = False
        
    def update(self):
        # Normal movement
        self.rect.y += self.speedy
        self.rect.x += self.speedx
        
        # Special spiral motion for blade spinner projectiles
        if hasattr(self, 'spiral') and self.spiral:
            self.spiral_angle += self.spiral_speed
            # Calculate spiral offset
            spiral_x = math.cos(self.spiral_angle) * self.spiral_radius
            spiral_y = math.sin(self.spiral_angle) * self.spiral_radius
            
            # Update base position with regular movement
            self.base_x += self.speedx
            self.base_y += self.speedy
            
            # Set actual position with spiral offset
            self.rect.centerx = int(self.base_x + spiral_x)
            self.rect.centery = int(self.base_y + spiral_y)
            
            # Gradually increase spiral radius for expanding effect
            self.spiral_radius += 0.1
        
        # Kill if it moves off the screen
        if self.rect.bottom < 0 or self.rect.top > HEIGHT or self.rect.left > WIDTH or self.rect.right < 0:
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

    def apply_effect(self, player):
        if self.type == "health":
            player.health = min(player.max_health, player.health + 20)
        elif self.type == "shield":
            player.energy = player.max_energy
        elif self.type == "weapon":
            # Define weapon types based on difficulty
            if game_state.difficulty == "hard":
                weapon_types = ["normal", "spread"]  # No special bullets in hard mode
            else:
                weapon_types = ["normal", "spread", "bouncing", "homing"]
                
            if player.weapon_level < 3:
                player.weapon_level += 1
            else:
                idx = weapon_types.index(player.weapon_type) if player.weapon_type in weapon_types else 0
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
        
        # Difficulty multipliers
        difficulty_multipliers = {
            "easy": 0.8,
            "normal": 1.0, 
            "hard": 1.5
        }
        difficulty_mult = difficulty_multipliers[game_state.difficulty]
        
        # Boss visuals and stats based on sector
        if sector == 1:
            # Nova Prime Edge Boss
            self.image = pygame.Surface((100, 100), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, RED, [(0, 0), (100, 0), (100, 100), (50, 75), (0, 100)])
            self.max_health = int(500 * difficulty_mult)
            self.shoot_delay = int(800 / difficulty_mult)  # Shorter delay = faster shooting on higher difficulties
            self.name = "Sector 1 - Edge Guardian"
        elif sector == 2:
            # Asteroid Field Anomaly
            self.image = pygame.Surface((120, 120), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (150, 75, 0), (60, 60), 60)
            self.max_health = int(800 * difficulty_mult)
            self.shoot_delay = int(700 / difficulty_mult)
            self.name = "Sector 2 - Asteroid Titan"
        elif sector == 3:
            # Rhovax Border Patrol
            self.image = pygame.Surface((150, 100), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, (150, 0, 150), [(0, 50), (75, 0), (150, 50), (75, 100)])
            self.max_health = int(1200 * difficulty_mult)
            self.shoot_delay = int(600 / difficulty_mult)
            self.name = "Sector 3 - Rhovax Dreadnought"
        elif sector == 4:
            # Dominion Shipyards
            self.image = pygame.Surface((160, 160), pygame.SRCALPHA)
            pygame.draw.rect(self.image, (0, 100, 200), (0, 0, 160, 160))
            pygame.draw.rect(self.image, (0, 0, 0), (30, 30, 100, 100))
            self.max_health = int(2000 * difficulty_mult)
            self.shoot_delay = int(500 / difficulty_mult)
            self.name = "Sector 4 - Shipyard Sentinel"
        elif sector == 5:
            # Cosmic Storm Nexus
            self.image = pygame.Surface((180, 150), pygame.SRCALPHA)
            pygame.draw.ellipse(self.image, (50, 50, 200), (0, 0, 180, 150))
            pygame.draw.ellipse(self.image, (100, 0, 100), (30, 30, 120, 90))
            self.max_health = int(3000 * difficulty_mult)
            self.shoot_delay = int(400 / difficulty_mult)
            self.name = "Sector 5 - Storm Lord"
        else:  # Sector 6 - Final Boss
            # Dominion Mothership
            self.image = pygame.Surface((200, 200), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, (200, 0, 0), [(0, 0), (200, 0), (160, 100), (200, 200), (0, 200), (40, 100)])
            self.max_health = int(5000 * difficulty_mult)
            self.shoot_delay = int(300 / difficulty_mult)
            self.name = "Sector 6 - Dominion Mothership"
            
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.top = 50
        self.health = self.max_health
        self.last_shot = pygame.time.get_ticks()
        self.pattern = 0  # Current attack pattern
        self.pattern_timer = pygame.time.get_ticks()
        self.pattern_delay = 5000  # Change patterns every 5 seconds
        
        # Base speed attributes - scale with difficulty and sector
        self.base_speed = 2 + (sector * 0.2)  # Slightly faster in higher sectors
        self.speed = self.base_speed * difficulty_multipliers[game_state.difficulty]
        
        # Initial speed direction
        self.speedx = self.speed
        self.speedy = 0
        
        # Movement momentum tracking - helps with smoother projectile physics
        self.momentum_x = 0  # Tracks recent movement for more natural projectile physics
        self.momentum_y = 0
        
        self.score_value = sector * 500  # More points for later bosses
    
    def update(self):
        # Boss movement patterns
        now = pygame.time.get_ticks()
        
        # Store previous position to calculate momentum
        prev_x = self.rect.x
        prev_y = self.rect.y
        
        # Change attack pattern periodically
        if now - self.pattern_timer > self.pattern_delay:
            self.pattern = (self.pattern + 1) % 3  # Cycle through 3 patterns
            self.pattern_timer = now
            
        # Boss movement based on pattern
        if self.pattern == 0:
            # Pattern 0: Move back and forth horizontally
            self.rect.x += self.speedx
            if self.rect.right > WIDTH or self.rect.left < 0:
                self.speedx *= -1
        elif self.pattern == 1:
            # Pattern 1: Move in a figure-8 pattern
            self.rect.x += self.speedx
            self.rect.y += self.speedy
            if self.rect.right > WIDTH - 50 or self.rect.left < 50:
                self.speedx *= -1
                # When changing horizontal direction, also change vertical direction
                self.speedy = self.speedx  # This creates the figure-8 pattern
            if self.rect.top < 50 or self.rect.bottom > HEIGHT // 3:
                self.speedy *= -1
        else:  # pattern == 2
            # Pattern 2: Charge toward player's x position
            if player.rect.centerx > self.rect.centerx:
                self.rect.x += self.speed * 1.5
                self.speedx = self.speed * 1.5
            elif player.rect.centerx < self.rect.centerx:
                self.rect.x -= self.speed * 1.5
                self.speedx = -self.speed * 1.5
            else:
                self.speedx = 0
            
            # Add a small vertical movement using sine wave
            vertical_move = math.sin(now / 500) * 2
            self.rect.y += vertical_move
            self.speedy = vertical_move
            
        # Calculate momentum (recent movement speed)
        self.momentum_x = self.rect.x - prev_x
        self.momentum_y = self.rect.y - prev_y
            
        # Stay within bounds
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
            self.speedx = -abs(self.speedx)  # Reverse direction when hitting wall
        if self.rect.left < 0:
            self.rect.left = 0
            self.speedx = abs(self.speedx)  # Reverse direction when hitting wall
        if self.rect.top < 10:
            self.rect.top = 10
            self.speedy = abs(self.speedy)  # Reverse direction when hitting ceiling
        if self.rect.bottom > HEIGHT // 2:
            self.rect.bottom = HEIGHT // 2
            self.speedy = -abs(self.speedy)  # Reverse direction when hitting floor
            
        # Shooting based on pattern
        if now - self.last_shot > self.shoot_delay:
            self.shoot()
            self.last_shot = now
            
    def shoot(self):
        if self.pattern == 0:
            # Simple spread pattern - only horizontally and downward
            for angle in [-45, -30, -15, 0, 15, 30, 45]:
                # In our coordinate system, only bullets with positive speedy go downward
                # cos(0) = 1, so a 0 angle goes straight down
                bullet = EnemySpreadBullet(
                    self.rect.centerx,   # x
                    self.rect.bottom,    # y
                    angle,               # angle
                    self,                # owner
                    PURPLE,              # color
                    8,                   # size
                    15,                  # damage
                    6 + abs(self.momentum_x) * 0.3  # speed + momentum factor
                )
                
                # Add momentum to bullet trajectory
                bullet.speedx += self.momentum_x * 0.7  # 70% of boss's horizontal momentum
                
                # Ensure bullet goes downward by forcing speedy to be positive
                if bullet.speedy < 0:
                    bullet.speedy = -bullet.speedy  # Reverse if it would go upward
                
                all_sprites.add(bullet)
                enemy_bullets.add(bullet)
                self.bullets.append(bullet)  # Track this bullet
                
        elif self.pattern == 1:
            # Modified pattern - only shoot downward with wider spread
            for angle in range(-90, 91, 30):  # -90 to 90 degrees range
                bullet = EnemySpreadBullet(
                    self.rect.centerx,   # x
                    self.rect.centery,   # y
                    angle,               # angle
                    self,                # owner
                    PURPLE,              # color
                    8,                   # size
                    15,                  # damage
                    6 + (abs(self.momentum_x) + abs(self.momentum_y)) * 0.25  # speed + momentum factor
                )
                
                # Add momentum to bullet trajectory
                bullet.speedx += self.momentum_x * 0.6  # 60% of boss's horizontal momentum
                
                # Ensure bullet goes downward or horizontally
                if bullet.speedy < 0:
                    bullet.speedy = 0  # Make it go horizontally instead of upward
                
                all_sprites.add(bullet)
                enemy_bullets.add(bullet)
                self.bullets.append(bullet)  # Track this bullet
                
        elif self.pattern == 2:
            # Aimed pattern - ensure it's only aimed horizontally or downward
            target_y = max(player.rect.centery, self.rect.centery + 50)  # Force target to be below boss
            angle = math.degrees(math.atan2(target_y - self.rect.centery, 
                                          player.rect.centerx - self.rect.centerx))
            
            # Calculate bullet speed based on boss momentum and pattern
            # Pattern 2 is more aggressive, so bullets are faster
            bullet_speed = 7 + (abs(self.momentum_x) + abs(self.momentum_y)) * 0.4
            
            for i in range(-2, 3):
                bullet = EnemySpreadBullet(
                    self.rect.centerx,   # x
                    self.rect.bottom,    # y
                    angle + (i * 10) + 90,  # angle - 90 degree offset makes 0 angle point downward
                    self,                # owner
                    PURPLE,              # color
                    8,                   # size
                    15,                  # damage
                    bullet_speed         # speed with momentum factor
                )
                
                # Add momentum to bullet trajectory - more in pattern 2 for "charging" effect
                bullet.speedx += self.momentum_x * 0.8  # 80% of boss's horizontal momentum
                bullet.speedy += self.momentum_y * 0.5  # 50% of boss's vertical momentum
                
                # Double-check to make absolutely sure no bullets go upward
                if bullet.speedy < 0:
                    bullet.speedy = abs(bullet.speedy)  # Force to be positive (downward)
                
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
            spawn_shop_portal(self.rect.centerx, self.rect.centery)
            print(f"Boss defeated in sector {self.sector}! Shop portal spawned.")
            
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
        self.difficulty = "normal"  # normal, easy, hard
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
        # Store the previous state to debug issues
        prev_state = self.state if hasattr(self, 'state') else "unknown"
        
        # Explicitly set all attributes to their initial values
        self.state = "menu"  # Force to menu state
        self.sector = 1
        self.wave = 1
        self.score = 0
        self.combo = 1
        self.max_combo = 1
        self.resources = 0
        self.boss_fight = False
        self.wave_enemies = 5
        self.waves_per_sector = 5  # Waves to complete before boss
        self.bosses_defeated = 0  # Reset boss defeat counter
        
        # Make sure difficulty persists
        if not hasattr(self, 'difficulty'):
            self.difficulty = "normal"  # Default difficulty
            
        # Track changes for debugging
        print(f"GameState reset: {prev_state} -> {self.state}")
        
        # Clear endless mode
        if hasattr(self, 'endless_mode'):
            delattr(self, 'endless_mode')
        
    def next_wave(self):
        # Special handling for endless mode wave transitions
        if hasattr(self, 'endless_mode') and self.endless_mode and self.sector >= 7:
            print(f"Endless mode wave transition: Sector {self.sector}, Wave {self.wave}")
            # Make sure we don't get stuck in high sectors
            if self.wave >= self.waves_per_sector:
                print(f"Forcing wave progression in sector {self.sector}")
            
        self.wave += 1
        
        # Print debug info for wave progression
        print(f"Next wave: Sector {self.sector}, Wave {self.wave}, waves_per_sector: {self.waves_per_sector}")
        
        # Ensure boss fights happen in endless mode
        if hasattr(self, 'endless_mode') and self.endless_mode and self.sector >= 7 and self.wave > self.waves_per_sector:
            # Boss wave in endless mode
            print(f"Triggering boss wave in endless mode sector {self.sector}")
            self.boss_fight = True
            # Set a flag to indicate we want a random boss
            self.use_random_boss = True
            return True
        elif self.wave > self.waves_per_sector:
            # Normal boss wave
            self.boss_fight = True
            return True
        return False
        
    def next_sector(self):
        self.sector += 1
        self.wave = 1
        self.boss_fight = False
        
        # Debug info for sector transitions
        print(f"Moving to next sector: {self.sector}")
        
        # Award resources for sector completion
        self.resources += 100 * self.sector
        
        # Track bosses defeated
        self.bosses_defeated += 1
        
        # Game completed if reached sector 6 - transition to victory screen
        if self.sector > 6 and not hasattr(self, 'endless_mode'):
            self.state = "victory"
            return True
            
        # Handle endless mode progression
        if hasattr(self, 'endless_mode') and self.endless_mode:
            # Keep boss fights coming at a regular cadence
            self.waves_per_sector = 4  # Fewer waves between bosses in endless mode
            print(f"Endless mode sector {self.sector}, waves_per_sector set to {self.waves_per_sector}")
            
            # Increase enemy count but cap it
            self.wave_enemies = min(15, 5 + self.sector)  # Cap at 15 enemies per wave
        else:
            # Regular progression - more gradual
            self.wave_enemies = min(15, 5 + self.sector)  # Cap at 15 enemies per wave
        
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

# Function to draw a button and check if it's clicked
def draw_button(surface, text, size, x, y, width, height, color=BLUE, hover_color=GREEN, text_color=WHITE):
    # Get mouse position and adjust for offset if we're drawing to gameplay_surface
    mouse_pos = pygame.mouse.get_pos()
    is_gameplay_surface = surface is not screen
    
    # If we're drawing to gameplay_surface (not the main screen), adjust mouse coordinates
    if is_gameplay_surface:
        mouse_pos = (mouse_pos[0] - OFFSET_X, mouse_pos[1] - OFFSET_Y)
    
    button_rect = pygame.Rect(x - width//2, y - height//2, width, height)
    clicked = False
    
    # Check if mouse is over button
    if button_rect.collidepoint(mouse_pos):
        # Draw hover state
        pygame.draw.rect(surface, hover_color, button_rect, border_radius=10)
        # Check for click
        if pygame.mouse.get_pressed()[0]:  # Left mouse button pressed
            clicked = True
    else:
        # Draw normal state
        pygame.draw.rect(surface, color, button_rect, border_radius=10)
    
    # Draw button text
    draw_text(surface, text, size, x, y, text_color)
    
    # Draw button border
    pygame.draw.rect(surface, WHITE, button_rect, 2, border_radius=10)
    
    return clicked

# Function to show controls screen
def show_controls_screen():
    controls_running = True
    
    while controls_running:
        clock.tick(FPS)
        
        # Handle events
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    controls_running = False
        
        # Draw controls screen
        screen.fill(BLACK)
        
        # Create a gameplay surface
        controls_surface = pygame.Surface((WIDTH, HEIGHT))
        controls_surface.fill(BLACK)
        
        draw_text(controls_surface, "CONTROLS", 50, WIDTH/2, 80)
        
        controls = [
            "Movement: WASD or Arrow Keys",
            "Shoot: SPACE or Left Mouse Button",
            "Shield: E key",
            "Hyper Dash: SHIFT key",
            "Pause: ESC key",
            "Enter Shop: E key (when next to shop portal)",
            "Select Items: Arrow Keys / WASD and ENTER",
            "Exit Menus: ESC key"
        ]
        
        y_pos = 160
        for control in controls:
            draw_text(controls_surface, control, 24, WIDTH/2, y_pos)
            y_pos += 40
        
        # Back button
        if draw_button(controls_surface, "Back to Menu", 24, WIDTH/2, HEIGHT-80, 200, 50):
            controls_running = False
            
        # Draw the controls surface to the screen with offsets
        screen.blit(controls_surface, (OFFSET_X, OFFSET_Y))
        pygame.display.flip()

# Function to show difficulty selection screen
def show_difficulty_screen():
    difficulty_running = True
    selected_difficulty = game_state.difficulty
    
    while difficulty_running:
        clock.tick(FPS)
        
        # Handle events
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    difficulty_running = False
        
        # Draw difficulty screen
        screen.fill(BLACK)
        
        # Create a gameplay surface
        difficulty_surface = pygame.Surface((WIDTH, HEIGHT))
        difficulty_surface.fill(BLACK)
        
        draw_text(difficulty_surface, "SELECT DIFFICULTY", 50, WIDTH/2, 80)
        
        # Description based on difficulty
        descriptions = {
            "easy": "More health, slower enemies, more resources",
            "normal": "Standard challenge",
            "hard": "Less health, faster enemies, tougher bosses"
        }
        
        # Difficulty buttons
        button_width = 200
        button_height = 60
        button_y = 200
        spacing = 100
        
        # Easy button
        easy_color = GREEN if selected_difficulty == "easy" else BLUE
        if draw_button(difficulty_surface, "Easy", 30, WIDTH/2, button_y, button_width, button_height, easy_color):
            selected_difficulty = "easy"
            
        # Normal button
        normal_color = GREEN if selected_difficulty == "normal" else BLUE
        if draw_button(difficulty_surface, "Normal", 30, WIDTH/2, button_y + spacing, button_width, button_height, normal_color):
            selected_difficulty = "normal"
            
        # Hard button
        hard_color = GREEN if selected_difficulty == "hard" else BLUE
        if draw_button(difficulty_surface, "Hard", 30, WIDTH/2, button_y + spacing*2, button_width, button_height, hard_color):
            selected_difficulty = "hard"
        
        # Show description of selected difficulty
        draw_text(difficulty_surface, descriptions[selected_difficulty], 24, WIDTH/2, button_y + spacing*3)
        
        # Back and Confirm buttons
        if draw_button(difficulty_surface, "Back", 24, WIDTH/3, HEIGHT-80, 150, 50):
            difficulty_running = False
            
        if draw_button(difficulty_surface, "Confirm", 24, WIDTH*2/3, HEIGHT-80, 150, 50):
            game_state.difficulty = selected_difficulty
            difficulty_running = False
        
        # Draw the difficulty surface to the screen with offsets
        screen.blit(difficulty_surface, (OFFSET_X, OFFSET_Y))
        pygame.display.flip()

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
        # Adjust mouse position for gameplay surface
        adjusted_mouse_pos = (mouse_pos[0] - OFFSET_X, mouse_pos[1] - OFFSET_Y)
        
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
                        if rect.collidepoint(adjusted_mouse_pos):
                            if i < len(upgrade_options):  # Make sure the option exists
                                apply_upgrade(upgrade_options[i])
                                break
        
        # Draw upgrade menu
        screen.fill(BLACK)
        
        # Create a gameplay surface
        upgrade_surface = pygame.Surface((WIDTH, HEIGHT))
        upgrade_surface.fill(BLACK)
        
        draw_text(upgrade_surface, "UPGRADE MENU", 40, WIDTH / 2, 30)
        draw_text(upgrade_surface, f"Resources: {game_state.resources}", 25, WIDTH / 2, 80)
        
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
            text_rect = draw_text(upgrade_surface, text, 20, WIDTH / 2, y_pos, color, return_rect=True)
            option_rects.append(text_rect)
            
            draw_text(upgrade_surface, option["effect"], 16, WIDTH / 2, y_pos + 20, WHITE)
            
        draw_text(upgrade_surface, "Arrow keys to select, ENTER to purchase, ESC to exit", 
                18, WIDTH / 2, HEIGHT - 50)
        draw_text(upgrade_surface, "You can also click on options with your mouse", 
                18, WIDTH / 2, HEIGHT - 30)
        
        # Draw the upgrade surface to the screen with offsets
        screen.blit(upgrade_surface, (OFFSET_X, OFFSET_Y))
        
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

def create_random_boss(current_sector):
    """Create a random boss for endless mode.
    Instead of using the current sector's boss, this selects a random boss from sectors 1-6.
    The stats will still be enhanced based on the current endless mode sector.
    """
    # Select a random boss type from sectors 1-6
    boss_sector = random.randint(1, 6)
    print(f"Creating random boss from sector {boss_sector} for endless mode sector {current_sector}")
    
    # Create the boss with the random visual style and base stats
    boss = Boss(boss_sector)
    
    # Now enhance the stats based on current endless mode sector
    if current_sector > 6:
        # In endless mode, enhance boss based on current sector
        health_multiplier = 1 + (current_sector - 6) * 0.3  # +30% health per sector above 6
        boss.max_health *= health_multiplier
        boss.health = boss.max_health
        boss.shoot_delay = max(100, boss.shoot_delay * 0.8)  # Faster shooting (min 100ms)
        boss.score_value = 500 + (current_sector - 6) * 300  # More points in higher sectors
        
        # Add a suffix to the name to indicate it's powered up
        boss.name += f" [Endless Lv.{current_sector-6}]"
    
    # Note: The modified shoot method in the Boss class ensures no bullets go upward
    # No additional changes needed here as all Boss instances use the same shoot method
    
    return boss

def spawn_shop_portal(x, y):
    """Spawn a shop portal at the given coordinates.
    This function can be called by any entity when a shop portal should appear.
    """
    print(f"Spawning shop portal at {x}, {y}")
    
    # Create a new portal
    portal = ShopPortal(x, y)
    all_sprites.add(portal)
    
    # Ensure shop_portals is initialized
    if 'shop_portals' not in globals():
        global shop_portals
        shop_portals = pygame.sprite.Group()
    
    # Add the portal to the sprite group
    shop_portals.add(portal)
    
    # Reset boss_fight flag to allow next wave to start
    game_state.boss_fight = False
    
    return portal

# Initialize game state
if __name__ == "__main__":
    running = True

# Main game loop
while running:
    # Keep loop running at the right speed
    clock.tick(FPS)
    
    # Process input (events)
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        # Key press events
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                if game_state.state == "playing":
                    game_state.state = "menu"
                elif game_state.state == "menu":
                    running = False
            elif event.key == K_SPACE and game_state.state == "playing":
                player.shoot()
            elif event.key == K_LSHIFT and game_state.state == "playing":
                player.hyper_dash()
        # Mouse click events
        elif event.type == MOUSEBUTTONDOWN:
            if event.button == 1 and game_state.state == "playing":
                player.shoot()

    # Check mouse position for player aim direction
    if game_state.state == "playing":
        player.mouse_pos = pygame.mouse.get_pos()
        # Adjust the mouse position to the gameplay coordinates
        player.mouse_pos = (player.mouse_pos[0] - OFFSET_X, player.mouse_pos[1] - OFFSET_Y)
    
    # Update all sprites for gameplay
    if game_state.state == "playing":
        all_sprites.update()
        
        # Check player health - switch to game over if health is zero or negative
        if player.health <= 0:
            game_state.state = "game_over"
            
        # Periodically remove sprites that are far off screen
        cleanup_sprites()
        
        # Check for bullet hits on enemies
        hits = pygame.sprite.groupcollide(enemies, bullets, False, False)  # Changed to keep bullets
        for enemy, bullet_list in hits.items():
            for bullet in bullet_list:
                if isinstance(bullet, BouncingBullet):
                    # For bouncing bullets, check if enemy will die from this hit
                    if enemy.health <= bullet.damage:
                        # If enemy will die, remove the bullet
                        bullet.kill()
                        enemy.hit(bullet.damage)
                    else:
                        # If enemy won't die, bounce the bullet
                        enemy.hit(bullet.damage)
                        bullet.bounce_off_enemy()
                else:
                    # Normal bullets get removed
                    bullet.kill()
                    enemy.hit(10)  # Normal bullet damage
                
                if enemy.health <= 0:  # Enemy was destroyed
                    game_state.score += enemy.score_value * game_state.combo
                    game_state.combo += 1
                    
                    # Adjust resources based on difficulty
                    if game_state.difficulty == "easy":
                        game_state.resources += 7  # More resources on easy
                    elif game_state.difficulty == "normal":
                        game_state.resources += 5  # Standard resources
                    else:  # hard
                        game_state.resources += 3  # Fewer resources on hard
                        
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
                    
                    # Adjust boss resources based on difficulty
                    if game_state.difficulty == "easy":
                        game_state.resources += 150  # More resources on easy
                    elif game_state.difficulty == "normal":
                        game_state.resources += 100  # Standard resources
                    else:  # hard
                        game_state.resources += 75  # Fewer resources on hard
        
        # Check for enemy bullet hits on player
        hits = pygame.sprite.spritecollide(player, enemy_bullets, True)
        if hits:
            if player.hit(hits[0].damage):
                game_state.state = "game_over"
                
        # Check for collision with enemies
        hits = pygame.sprite.spritecollide(player, enemies, True)
        if hits:
            if player.hit(30):  # Collision with enemy does major damage
                game_state.state = "game_over"
                
        # Check for collision with power-ups
        hits = pygame.sprite.spritecollide(player, powerups, True)
        for power_up in hits:
            power_up.apply_effect(player)
            
        # Check for collision with bosses
        hits = pygame.sprite.spritecollide(player, bosses, False)
        if hits:
            if player.hit(30):  # Collision with boss does more damage
                game_state.state = "game_over"
                
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
        
        # Debug output before checking for wave completion
        if len(enemies) == 0 and game_state.state == "playing" and hasattr(game_state, 'endless_mode') and game_state.endless_mode:
            print(f"No enemies present. boss_fight={game_state.boss_fight}, portals={len(shop_portals) if 'shop_portals' in globals() else 'not defined'}")
        
        # Check for wave completion
        if len(enemies) == 0 and not game_state.boss_fight and 'shop_portals' in globals() and len(shop_portals) == 0:
            # Debug info for the second check
            print(f"Second wave completion check - Sector {game_state.sector}, Wave {game_state.wave}")
            
            # Check for special cases in endless mode for high sectors
            if hasattr(game_state, 'endless_mode') and game_state.endless_mode and game_state.sector >= 7 and game_state.wave >= game_state.waves_per_sector:
                print(f"Second check - Forcing boss fight for sector {game_state.sector}, wave {game_state.wave}")
                game_state.boss_fight = True
                
                # Force boss spawn directly instead of using next_wave()
                if random.random() < 0.4:  # 40% chance for mini-boss
                    mini_boss = BarrierGoliath(WIDTH, HEIGHT, game_state, all_sprites, enemies, enemy_bullets, powerups, PowerUp, EnemySpreadBullet)
                    health_multiplier = 1 + (game_state.sector - 6) * 0.2
                    mini_boss.max_health *= health_multiplier
                    mini_boss.health = mini_boss.max_health
                    all_sprites.add(mini_boss)
                    enemies.add(mini_boss)
                    print(f"Second check - Spawned mini-boss for sector {game_state.sector}")
                else:
                    # Spawn regular boss - enhanced in endless mode
                    if hasattr(game_state, 'endless_mode') and game_state.endless_mode and game_state.sector > 6:
                        # Use random boss in endless mode
                        boss = create_random_boss(game_state.sector)
                    else:
                        # Normal progression - use sector-specific boss
                        boss = Boss(game_state.sector)
                    
                    all_sprites.add(boss)
                    bosses.add(boss)
                
                game_state.wave = 1  # Reset wave counter
                continue
            
            # Standard wave progression
            if game_state.next_wave():
                # Boss fight time!
                
                # Check if we should use random boss in endless mode
                use_random_boss = (hasattr(game_state, 'endless_mode') and 
                                 game_state.endless_mode and 
                                 game_state.sector > 6)
                
                # In endless mode (after sector 6), sometimes spawn mini-boss instead
                if use_random_boss and random.random() < 0.4:
                    # This is handled by our special case above in endless mode
                    mini_boss = BarrierGoliath(WIDTH, HEIGHT, game_state, all_sprites, enemies, enemy_bullets, powerups, PowerUp, EnemySpreadBullet)
                    mini_boss.max_health *= 1 + (game_state.sector - 6) * 0.2  # +20% health per sector above 6
                    mini_boss.health = mini_boss.max_health
                    all_sprites.add(mini_boss)
                    enemies.add(mini_boss)
                    # Ensure we don't spawn regular enemies during a boss wave
                    game_state.boss_fight = True
                    print(f"Spawned mini-boss for endless sector {game_state.sector}")
                elif not use_random_boss:  # Regular game mode or early endless sectors
                    # In regular game mode, always use the correct sector boss
                    # Mini-bosses don't replace sector bosses in normal progression
                    boss = Boss(game_state.sector)
                    if hasattr(game_state, 'endless_mode') and game_state.endless_mode and game_state.sector > 6:
                        health_multiplier = 1 + (game_state.sector - 6) * 0.3  # +30% health per sector above 6
                        boss.max_health *= health_multiplier
                        boss.health = boss.max_health
                        boss.shoot_delay = max(300, boss.shoot_delay * 0.8)  # Faster shooting (min 300ms)
                        boss.score_value = 500 + (game_state.sector - 6) * 300  # More points in higher sectors
                    all_sprites.add(boss)
                    bosses.add(boss)
                    # Ensure we don't spawn regular enemies during a boss wave
                    game_state.boss_fight = True
                    print(f"Spawned sector {game_state.sector} boss")
                else: # This is the else for the use_random_boss and random.random() check
                    # Create a random boss for endless mode
                    boss = create_random_boss(game_state.sector)
                    all_sprites.add(boss)
                    bosses.add(boss)
                    # Ensure we don't spawn regular enemies during a boss wave
                    game_state.boss_fight = True
                    print(f"Created random boss from pool for endless sector {game_state.sector}")
            else:
                # Not a boss wave, spawn regular enemies
                if game_state.boss_fight:
                    # This shouldn't happen, but if it does, reset the flag
                    game_state.boss_fight = False
                    print(f"Resetting boss_fight flag in wave {game_state.wave}")
                
                # Spawn new wave of enemies
                for i in range(game_state.wave_enemies):
                    # Choose enemy type based on wave and sector
                    enemy_roll = random.random()
                    
                    # Use a weighted selection system for different enemy types
                    if enemy_roll < 0.15:  # 15% chance of elite enemy
                        enemy = Enemy("elite")
                    elif enemy_roll < 0.25:  # 10% chance of cloaked ambusher
                        enemy = Enemy("cloaked_ambusher")
                    elif enemy_roll < 0.35:  # 10% chance of splitter drone
                        enemy = Enemy("splitter_drone")
                    elif enemy_roll < 0.45:  # 10% chance of shield bearer
                        enemy = Enemy("shield_bearer")
                    elif enemy_roll < 0.55:  # 10% chance of energy sapper
                        enemy = Enemy("energy_sapper")
                    elif enemy_roll < 0.65:  # 10% chance of blade spinner
                        enemy = Enemy("blade_spinner")
                    else:  # 35% chance of basic enemy
                        enemy = Enemy("basic")
                        
                    # Place it randomly at the top of the screen with some spacing
                    enemy.rect.x = random.randint(0 + enemy.rect.width, WIDTH - enemy.rect.width)
                    enemy.rect.bottom = random.randint(-150, -20)
                    all_sprites.add(enemy)
                    enemies.add(enemy)
                
                # Chance to spawn a mini-boss (Barrier Goliath) after wave 3
                # Only if this is not a boss wave
                if game_state.wave > 3 and game_state.wave < game_state.waves_per_sector and random.random() < 0.15 and not game_state.boss_fight:
                    # Make sure we don't have too many enemies
                    if len(enemies) > 10:
                        # Too many enemies already - skip mini-boss for this wave
                        print(f"Skipping mini-boss spawn - too many enemies ({len(enemies)})")
                    else:
                        print(f"Spawning mini-boss during wave {game_state.wave}")
                        mini_boss = BarrierGoliath(WIDTH, HEIGHT, game_state, all_sprites, enemies, enemy_bullets, powerups, PowerUp, EnemySpreadBullet)
                        all_sprites.add(mini_boss)
                        enemies.add(mini_boss)
                        # Note: We don't set boss_fight to True here since this isn't a boss wave
    
    # Draw / render
    screen.fill(BLACK)
    
    # Create a gameplay surface that's the original game size
    gameplay_surface = pygame.Surface((WIDTH, HEIGHT))
    gameplay_surface.fill(BLACK)
    
    if game_state.state == "menu":
        # Draw menu screen on the gameplay surface
        draw_text(gameplay_surface, "Xbacab", 64, WIDTH / 2, HEIGHT / 4)
        
        # Menu buttons
        button_width = 200
        button_height = 60
        button_y = HEIGHT / 2
        spacing = 80
        
        # Start Game button
        if draw_button(gameplay_surface, "Start Game", 30, WIDTH/2, button_y, button_width, button_height):
            # Set up for a new game with the current difficulty
            game_state.state = "playing"
            game_state.sector = 1  # Start at sector 1
            game_state.wave = 1
            # Remove endless mode if it was set previously
            if hasattr(game_state, 'endless_mode'):
                delattr(game_state, 'endless_mode')
                
            print(f"Starting new game with difficulty: {game_state.difficulty}")
            # We don't call show_difficulty_screen() directly to avoid the issue
        
        # Endless Mode button
        if draw_button(gameplay_surface, "Endless Mode", 30, WIDTH/2, button_y + spacing, button_width, button_height):
            # Set up for endless mode - first ensure clean state
            print("Initializing Endless Mode...")
            
            # Clear any existing sprite groups to prevent state issues
            all_sprites.empty()
            bullets.empty()
            enemy_bullets.empty()
            enemies.empty()
            powerups.empty()
            bosses.empty()
            shop_portals.empty()
            
            # Reset game state for endless mode
            game_state.state = "playing"
            game_state.sector = 7  # Start at sector 7 (beyond sector 6)
            game_state.wave = 1
            game_state.score = 0
            game_state.combo = 1
            game_state.max_combo = 1
            
            # Ensure endless mode flag is set
            game_state.endless_mode = True
            game_state.waves_per_sector = 4  # Fewer waves before boss fights
            game_state.bosses_defeated = 6  # Ensure drone slot upgrades are available
            game_state.resources = 1000  # Give extra starting resources for upgrades
            game_state.boss_fight = False  # Ensure no boss fight initially
            
            # Create a completely new player instance to avoid state issues
            player = Player()
            
            # Set up powerful player for endless mode
            player.max_health = 200
            player.health = 200
            player.max_energy = 150
            player.energy = 150
            player.energy_regen = 0.7
            player.weapon_level = 3  # Start with level 3 weapons
            
            # Add player to sprites
            all_sprites.add(player)
            
            # Start with 2 drones
            player.max_drones = 4
            player.drone_list = []  # Initialize empty drone list
            for i in range(2):
                player.add_drone()
                
            # Spawn initial enemies for endless mode
            for i in range(game_state.wave_enemies):
                # Create a mix of enemy types for endless mode
                enemy_roll = random.random()
                if enemy_roll < 0.6:  # 60% chance of more challenging enemies
                    enemy_type = random.choice(["elite", "cloaked_ambusher", "splitter_drone", 
                                              "shield_bearer", "energy_sapper", "blade_spinner"])
                else:
                    enemy_type = "basic"
                    
                enemy = Enemy(enemy_type)
                enemy.rect.x = random.randint(0 + enemy.rect.width, WIDTH - enemy.rect.width)
                enemy.rect.bottom = random.randint(-150, -20)
                all_sprites.add(enemy)
                enemies.add(enemy)
                
            print("Endless Mode initialized successfully")
        
        # Controls button
        if draw_button(gameplay_surface, "Controls", 30, WIDTH/2, button_y + spacing*2, button_width, button_height):
            show_controls_screen()
            
        # Difficulty button
        if draw_button(gameplay_surface, "Difficulty", 30, WIDTH/2, button_y + spacing*3, button_width, button_height):
            # Check if we should skip the difficulty screen (for game over transitions)
            if hasattr(game_state, 'skip_difficulty') and game_state.skip_difficulty:
                # We've just come from the game over screen, skip showing difficulty
                print("Skipping difficulty screen due to game over transition")
                # Remove the flag now that we've used it
                delattr(game_state, 'skip_difficulty')
            else:
                # Normal case - show difficulty screen
                show_difficulty_screen()
        
        # Display current difficulty
        draw_text(gameplay_surface, f"Current Difficulty: {game_state.difficulty.capitalize()}", 18, WIDTH / 2, HEIGHT - 50)
        
        # Endless mode description
        draw_text(gameplay_surface, "Endless Mode: Skip to high difficulty infinite play with upgraded ship", 16, WIDTH / 2, HEIGHT - 20, color=(180, 180, 255))
            
    elif game_state.state == "playing":
        # Draw all sprites to the gameplay surface
        all_sprites.draw(gameplay_surface)
        
        # Draw player information
        draw_bar(gameplay_surface, 10, 10, player.health, player.max_health, 200, 20, GREEN)
        draw_text(gameplay_surface, f"Health: {int(player.health)}/{player.max_health}", 18, 110, 10)
        
        draw_bar(gameplay_surface, 10, 40, player.energy, player.max_energy, 200, 20, BLUE)
        draw_text(gameplay_surface, f"Energy: {int(player.energy)}/{player.max_energy}", 18, 110, 40)
        
        # Add weapon type indicator
        weapon_colors = {
            "normal": YELLOW,
            "spread": GREEN,
            "bouncing": (0, 255, 0)  # Bright green for bouncing
        }
        weapon_type = player.weapon_type.capitalize()
        weapon_level = player.weapon_level
        draw_text(gameplay_surface, f"Weapon: {weapon_type} (Lvl {weapon_level})", 18, 110, 70, weapon_colors.get(player.weapon_type, WHITE))
        
        # Draw shield if active
        if player.shield_active:
            pygame.draw.circle(gameplay_surface, BLUE, player.rect.center, 40, 2)
            
        # Draw game information
        draw_text(gameplay_surface, f"Score: {game_state.score}", 22, WIDTH - 100, 10)
        draw_text(gameplay_surface, f"Combo: x{game_state.combo}", 18, WIDTH - 100, 40)
        draw_text(gameplay_surface, f"Sector: {game_state.sector} - Wave: {game_state.wave}", 18, WIDTH - 100, 70)
        draw_text(gameplay_surface, f"Drones: {len(player.drone_list)}/{player.max_drones}", 18, WIDTH - 100, 100)
        draw_text(gameplay_surface, f"Resources: {game_state.resources}", 18, WIDTH - 100, 130)
        
        # Draw boss health bar if fighting a boss
        if game_state.boss_fight and bosses:
            boss = bosses.sprites()[0]
            draw_bar(gameplay_surface, WIDTH//2 - 150, HEIGHT - 30, boss.health, boss.max_health, 300, 20, RED)
            draw_text(gameplay_surface, boss.name, 20, WIDTH//2, HEIGHT - 50)
        
        # Draw special effects
        if player.hyper_dash_active:
            # Draw dash trail
            for i in range(5):
                trail_alpha = 150 - (i * 30)  # Fade out the trail
                s = pygame.Surface((player.rect.width, player.rect.height), pygame.SRCALPHA)
                s.fill((0, 255, 255, trail_alpha))
                trail_rect = s.get_rect()
                trail_rect.center = (player.rect.centerx, player.rect.centery + (i * 15))
                gameplay_surface.blit(s, trail_rect)
                
        # Debug output before checking for wave completion (second check)
        if len(enemies) == 0 and game_state.state == "playing" and hasattr(game_state, 'endless_mode') and game_state.endless_mode:
            print(f"Second check - No enemies present. boss_fight={game_state.boss_fight}, portals={len(shop_portals) if 'shop_portals' in globals() else 'not defined'}")
        
        # Check for wave completion
        if len(enemies) == 0 and not game_state.boss_fight and 'shop_portals' in globals() and len(shop_portals) == 0:
            # Debug info for the second check
            print(f"Second wave completion check - Sector {game_state.sector}, Wave {game_state.wave}")
            
            # Check for special cases in endless mode for high sectors
            if hasattr(game_state, 'endless_mode') and game_state.endless_mode and game_state.sector >= 7 and game_state.wave >= game_state.waves_per_sector:
                print(f"Second check - Forcing boss fight for sector {game_state.sector}, wave {game_state.wave}")
                game_state.boss_fight = True
                
                # Force boss spawn directly instead of using next_wave()
                if random.random() < 0.4:  # 40% chance for mini-boss
                    mini_boss = BarrierGoliath(WIDTH, HEIGHT, game_state, all_sprites, enemies, enemy_bullets, powerups, PowerUp, EnemySpreadBullet)
                    health_multiplier = 1 + (game_state.sector - 6) * 0.2
                    mini_boss.max_health *= health_multiplier
                    mini_boss.health = mini_boss.max_health
                    all_sprites.add(mini_boss)
                    enemies.add(mini_boss)
                    print(f"Second check - Spawned mini-boss for sector {game_state.sector}")
                else:
                    # Spawn regular boss - enhanced in endless mode
                    if hasattr(game_state, 'endless_mode') and game_state.endless_mode and game_state.sector > 6:
                        # Use random boss in endless mode
                        boss = create_random_boss(game_state.sector)
                        print(f"Random boss created for endless sector {game_state.sector}")
                    else:
                        # Normal progression - use sector-specific boss
                        boss = Boss(game_state.sector)
                        if game_state.sector > 6:
                            health_multiplier = 1 + (game_state.sector - 6) * 0.3  # +30% health per sector above 6
                            boss.max_health *= health_multiplier
                            boss.health = boss.max_health
                            boss.shoot_delay = max(300, boss.shoot_delay * 0.8)  # Faster shooting (min 300ms)
                            boss.score_value = 500 + (game_state.sector - 6) * 300  # More points in higher sectors
                        all_sprites.add(boss)
                        bosses.add(boss)
                    
                    game_state.wave = 1  # Reset wave counter
                    continue
            
            # Standard wave progression
            if game_state.next_wave():
                # Boss fight time!
                
                # Check if we should use random boss in endless mode
                use_random_boss = (hasattr(game_state, 'endless_mode') and 
                                 game_state.endless_mode and 
                                 game_state.sector > 6)
                
                # In endless mode (after sector 6), sometimes spawn mini-boss instead
                if use_random_boss and random.random() < 0.4:
                    # This is handled by our special case above in endless mode
                    mini_boss = BarrierGoliath(WIDTH, HEIGHT, game_state, all_sprites, enemies, enemy_bullets, powerups, PowerUp, EnemySpreadBullet)
                    mini_boss.max_health *= 1 + (game_state.sector - 6) * 0.2  # +20% health per sector above 6
                    mini_boss.health = mini_boss.max_health
                    all_sprites.add(mini_boss)
                    enemies.add(mini_boss)
                    # Ensure we don't spawn regular enemies during a boss wave
                    game_state.boss_fight = True
                    print(f"Spawned mini-boss for endless sector {game_state.sector}")
                elif not use_random_boss:  # Regular game mode or early endless sectors
                    # In regular game mode, always use the correct sector boss
                    # Mini-bosses don't replace sector bosses in normal progression
                    boss = Boss(game_state.sector)
                    if hasattr(game_state, 'endless_mode') and game_state.endless_mode and game_state.sector > 6:
                        health_multiplier = 1 + (game_state.sector - 6) * 0.3  # +30% health per sector above 6
                        boss.max_health *= health_multiplier
                        boss.health = boss.max_health
                        boss.shoot_delay = max(300, boss.shoot_delay * 0.8)  # Faster shooting (min 300ms)
                        boss.score_value = 500 + (game_state.sector - 6) * 300  # More points in higher sectors
                    all_sprites.add(boss)
                    bosses.add(boss)
                    # Ensure we don't spawn regular enemies during a boss wave
                    game_state.boss_fight = True
                    print(f"Spawned sector {game_state.sector} boss")
                else: # This is the else for the use_random_boss and random.random() check
                    # Create a random boss for endless mode
                    boss = create_random_boss(game_state.sector)
                    all_sprites.add(boss)
                    bosses.add(boss)
                    # Ensure we don't spawn regular enemies during a boss wave
                    game_state.boss_fight = True
                    print(f"Created random boss from pool for endless sector {game_state.sector}")
            else:
                # Not a boss wave, spawn regular enemies
                if game_state.boss_fight:
                    # This shouldn't happen, but if it does, reset the flag
                    game_state.boss_fight = False
                    print(f"Resetting boss_fight flag in wave {game_state.wave}")
                
                # Spawn new wave of enemies
                for i in range(game_state.wave_enemies):
                    # Choose enemy type based on wave and sector
                    enemy_roll = random.random()
                    
                    # Use a weighted selection system for different enemy types
                    if enemy_roll < 0.15:  # 15% chance of elite enemy
                        enemy = Enemy("elite")
                    elif enemy_roll < 0.25:  # 10% chance of cloaked ambusher
                        enemy = Enemy("cloaked_ambusher")
                    elif enemy_roll < 0.35:  # 10% chance of splitter drone
                        enemy = Enemy("splitter_drone")
                    elif enemy_roll < 0.45:  # 10% chance of shield bearer
                        enemy = Enemy("shield_bearer")
                    elif enemy_roll < 0.55:  # 10% chance of energy sapper
                        enemy = Enemy("energy_sapper")
                    elif enemy_roll < 0.65:  # 10% chance of blade spinner
                        enemy = Enemy("blade_spinner")
                    else:  # 35% chance of basic enemy
                        enemy = Enemy("basic")
                        
                    # Place it randomly at the top of the screen with some spacing
                    enemy.rect.x = random.randint(0 + enemy.rect.width, WIDTH - enemy.rect.width)
                    enemy.rect.bottom = random.randint(-150, -20)
                    all_sprites.add(enemy)
                    enemies.add(enemy)
                
                # Chance to spawn a mini-boss (Barrier Goliath) after wave 3
                # Only if this is not a boss wave
                if game_state.wave > 3 and game_state.wave < game_state.waves_per_sector and random.random() < 0.15 and not game_state.boss_fight:
                    # Make sure we don't have too many enemies
                    if len(enemies) > 10:
                        # Too many enemies already - skip mini-boss for this wave
                        print(f"Skipping mini-boss spawn - too many enemies ({len(enemies)})")
                    else:
                        print(f"Spawning mini-boss during wave {game_state.wave}")
                        mini_boss = BarrierGoliath(WIDTH, HEIGHT, game_state, all_sprites, enemies, enemy_bullets, powerups, PowerUp, EnemySpreadBullet)
                        all_sprites.add(mini_boss)
                        enemies.add(mini_boss)
                        # Note: We don't set boss_fight to True here since this isn't a boss wave
    
        # Draw portal special effects and text
        for portal in shop_portals:
            portal.draw(gameplay_surface)
    
    elif game_state.state == "game_over":
        # Draw game over screen
        draw_text(gameplay_surface, "GAME OVER", 64, WIDTH / 2, HEIGHT / 4)
        draw_text(gameplay_surface, f"Score: {game_state.score}", 36, WIDTH / 2, HEIGHT / 2)
        draw_text(gameplay_surface, f"Max Combo: x{game_state.max_combo}", 24, WIDTH / 2, HEIGHT / 2 + 50)
        
        # Add a continue button - renamed to "Main Menu" for clarity
        if draw_button(gameplay_surface, "Return to Menu", 24, WIDTH / 2, HEIGHT * 3 / 4, 250, 50):
            # Reset game
            print("Game over: Returning to main menu...")
            
            # Force direct exit from this frame loop to prevent difficulty screen
            # Instead of using global and return, set a special flag
            
            # First create a complete reset of the GameState
            # Create a new instance of GameState with default values
            temp_state = GameState()
            
            # Copy only necessary attributes from the temp state to ensure clean slate
            game_state.state = "menu"  # Explicitly set to menu state
            game_state.sector = temp_state.sector
            game_state.wave = temp_state.wave
            game_state.score = 0
            game_state.combo = 1
            game_state.max_combo = 1
            game_state.resources = 0
            game_state.boss_fight = False
            game_state.wave_enemies = temp_state.wave_enemies
            game_state.waves_per_sector = temp_state.waves_per_sector
            game_state.bosses_defeated = 0
            
            # Preserve difficulty setting only
            if not hasattr(game_state, 'difficulty'):
                game_state.difficulty = "normal"
                
            # Remove any endless mode
            if hasattr(game_state, 'endless_mode'):
                delattr(game_state, 'endless_mode')
            
            # Reset all sprite groups to a clean slate
            all_sprites.empty()
            bullets.empty()
            enemy_bullets.empty()
            enemies.empty()
            powerups.empty()
            bosses.empty()
            shop_portals.empty()
            
            # Create a new player for the menu
            player = Player()
            all_sprites.add(player)
            
            # Set a special game state flag to prevent difficulty screen transition
            game_state.skip_difficulty = True
            
            print("Game Over screen: Complete reset to menu state performed")
    
    elif game_state.state == "victory":
        # Draw victory screen
        draw_text(gameplay_surface, "CONGRATULATIONS!", 64, WIDTH / 2, HEIGHT / 4)
        draw_text(gameplay_surface, "You defeated the Dominion Mothership!", 36, WIDTH / 2, HEIGHT / 2 - 50)
        draw_text(gameplay_surface, f"Final Score: {game_state.score}", 36, WIDTH / 2, HEIGHT / 2)
        draw_text(gameplay_surface, f"Max Combo: x{game_state.max_combo}", 24, WIDTH / 2, HEIGHT / 2 + 50)
        
        # Draw information about endless mode
        draw_text(gameplay_surface, "ENDLESS MODE UNLOCKED", 28, WIDTH / 2, HEIGHT / 2 + 90)
        draw_text(gameplay_surface, "Continue with increased difficulty", 20, WIDTH / 2, HEIGHT / 2 + 120)
        
        # Add continue button
        if draw_button(gameplay_surface, "Continue", 24, WIDTH / 2 - 120, HEIGHT * 3 / 4, 200, 50):
            # Save current score as high score before resetting
            if game_state.score > game_state.high_score:
                game_state.high_score = game_state.score
            
            # Store current player attributes before continuing
            stored_player_attributes = {
                'weapon_level': player.weapon_level,
                'weapon_type': player.weapon_type,
                'drones': player.drones,
                'drone_list': player.drone_list,
                'max_health': player.max_health,
                'health': player.max_health,  # Fully heal the player
                'max_energy': player.max_energy,
                'energy': player.max_energy,  # Fully restore energy
                'speedx': player.speedx,
                'speedy': player.speedy,
                'max_drones': player.max_drones,
                'energy_regen': player.energy_regen
            }
            
            # Prepare for endless mode
            game_state.state = "playing"
            game_state.sector += 1  # Increase sector instead of resetting to 1
            game_state.wave = 1
            game_state.boss_fight = False
            game_state.endless_mode = True  # Mark as in endless mode
            
            # Adjust endless mode parameters to ensure bosses spawn
            game_state.waves_per_sector = 4  # Fewer waves before boss fights in endless mode
            
            # Ensure bosses_defeated is at least 6 for endless mode
            # This guarantees drone slot upgrades are available
            game_state.bosses_defeated = max(game_state.bosses_defeated, 6)
            
            # Increase difficulty
            game_state.wave_enemies = min(15, 5 + game_state.sector)  # More enemies as you progress
            
            # Increase resources to help player with higher difficulty
            additional_resources = 100 + (game_state.sector * 25)
            game_state.resources += additional_resources
            
            # Reset sprite groups
            all_sprites = pygame.sprite.Group()
            bullets = pygame.sprite.Group()
            enemy_bullets = pygame.sprite.Group()
            enemies = pygame.sprite.Group()
            powerups = pygame.sprite.Group()
            bosses = pygame.sprite.Group()
            shop_portals = pygame.sprite.Group()
            
            # Create new player but restore previous attributes
            player = Player()
            
            # Restore saved attributes
            for attr, value in stored_player_attributes.items():
                setattr(player, attr, value)
                
            # Recreate drone sprites if player had any
            player.drone_list = []  # Clear the list of drone references
            for i in range(stored_player_attributes['drones']):
                player.add_drone()
                
            all_sprites.add(player)
            
            # Create initial enemies
            for i in range(game_state.wave_enemies):
                enemy = Enemy()
                all_sprites.add(enemy)
                enemies.add(enemy)
                
        # Add quit button
        if draw_button(gameplay_surface, "Quit", 24, WIDTH / 2 + 120, HEIGHT * 3 / 4, 200, 50):
            print("Victory screen: Quit button clicked, returning to main menu...")
            
            # More thorough reset similar to what we did for game over screen
            # Create a temp state to get default values
            temp_state = GameState()
            
            # Copy default values from temp_state to ensure a clean reset
            game_state.state = "menu"
            game_state.sector = temp_state.sector
            game_state.wave = temp_state.wave
            game_state.score = 0
            game_state.combo = 1
            game_state.max_combo = 1
            game_state.resources = 0
            game_state.boss_fight = False
            game_state.wave_enemies = temp_state.wave_enemies
            game_state.waves_per_sector = temp_state.waves_per_sector
            
            # Preserve difficulty and high score only
            if not hasattr(game_state, 'difficulty'):
                game_state.difficulty = "normal"
                
            # Ensure high score is saved
            if not hasattr(game_state, 'high_score'):
                game_state.high_score = 0
                
            # Ensure we clear endless mode
            if hasattr(game_state, 'endless_mode'):
                delattr(game_state, 'endless_mode')
                
            # Set the skip_difficulty flag to avoid difficulty screen
            game_state.skip_difficulty = True
            
            # Clear all sprite groups
            all_sprites.empty()
            bullets.empty()
            enemy_bullets.empty()
            enemies.empty()
            powerups.empty()
            bosses.empty()
            shop_portals.empty()
            
            # Create a new fresh player to avoid carrying over state
            player = Player()
            all_sprites.add(player)
            
            print("Victory screen: Complete reset performed, ready for new game")
    
    # Draw the gameplay surface to the screen with offsets
    screen.blit(gameplay_surface, (OFFSET_X, OFFSET_Y))

    # After drawing everything, flip the display
    pygame.display.flip()

# Quit the game
pygame.quit()
sys.exit() 