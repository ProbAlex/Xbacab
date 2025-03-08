import pygame
import random
import math

# Barrier class for the Barrier Goliath's protective shields
class Barrier(pygame.sprite.Sprite):
    def __init__(self, x, y, all_sprites, enemies):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((30, 30))
        self.image.fill((173, 216, 230))  # Light blue
        self.rect = self.image.get_rect(center=(x, y))
        self.health = 80
        self.all_sprites = all_sprites
        self.enemies = enemies
        # Required properties for hit function to work properly
        self.score_value = 50
        self.bullets = []  # Track bullets
        
    def hit(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.kill()
            return True  # Was destroyed
        return False  # Not destroyed yet

# Barrier Goliath Mini-Boss class
class BarrierGoliath(pygame.sprite.Sprite):
    def __init__(self, WIDTH, HEIGHT, game_state, all_sprites, enemies, enemy_bullets, powerups, PowerUp, EnemySpreadBullet):
        pygame.sprite.Sprite.__init__(self)
        
        # Store references to game objects
        self.WIDTH = WIDTH
        self.HEIGHT = HEIGHT
        self.game_state = game_state
        self.all_sprites = all_sprites
        self.enemies = enemies
        self.enemy_bullets = enemy_bullets
        self.powerups = powerups
        self.PowerUp = PowerUp
        self.EnemySpreadBullet = EnemySpreadBullet
        
        # Visual setup
        self.width = 120
        self.height = 100
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill((0, 0, 128))  # Dark blue
        self.rect = self.image.get_rect()
        
        # Position at the top of the screen at a random x position
        self.rect.centerx = random.randint(self.width // 2, WIDTH - self.width // 2)
        self.rect.top = -self.height
        
        # Health and difficulty settings
        difficulty_multipliers = {
            "easy": 0.8,
            "normal": 1.0, 
            "hard": 1.5
        }
        
        self.max_health = 350 * difficulty_multipliers[game_state.difficulty]
        self.health = self.max_health
        
        # Movement and attack patterns
        self.speedx = 1 * difficulty_multipliers[game_state.difficulty]
        self.speedy = 1 * difficulty_multipliers[game_state.difficulty]
        self.shoot_delay = 1500 // difficulty_multipliers[game_state.difficulty]
        self.last_shot = pygame.time.get_ticks()
        
        # Track bullets
        self.bullets = []
        
        # Initial movement pattern (0-horizontal, 1-diagonal)
        self.pattern = 0
        self.pattern_duration = 5000  # 5 seconds
        self.last_pattern_change = pygame.time.get_ticks()
        
        # Shield system
        self.has_shield = True
        self.shield_health = 150 * difficulty_multipliers[game_state.difficulty]
        self.max_shield_health = self.shield_health
        self.shield_regen_rate = 0.2 * difficulty_multipliers[game_state.difficulty]
        
        # Barrier system
        self.barriers = []
        self.spawn_barriers()
        
        # Score value
        self.score_value = 1000
    
    def spawn_barriers(self):
        # Spawn 3 barrier objects around the mini-boss
        barrier_positions = [
            (self.rect.centerx - 70, self.rect.centery), 
            (self.rect.centerx + 70, self.rect.centery),
            (self.rect.centerx, self.rect.centery + 70)
        ]
        
        for pos in barrier_positions:
            barrier = Barrier(pos[0], pos[1], self.all_sprites, self.enemies)
            self.barriers.append(barrier)
            self.all_sprites.add(barrier)
            self.enemies.add(barrier)
    
    def update(self):
        now = pygame.time.get_ticks()
        
        # Check if it's time to change pattern
        if now - self.last_pattern_change > self.pattern_duration:
            self.pattern = (self.pattern + 1) % 2
            self.last_pattern_change = now
        
        # Move based on current pattern
        if self.pattern == 0:  # Horizontal movement
            self.rect.x += self.speedx
            if self.rect.right > self.WIDTH - 20 or self.rect.left < 20:
                self.speedx *= -1
                
            # Slow vertical movement
            if self.rect.top < 50:
                self.rect.y += 1
        else:  # Diagonal movement
            self.rect.x += self.speedx
            self.rect.y += self.speedy
            
            if self.rect.right > self.WIDTH - 20 or self.rect.left < 20:
                self.speedx *= -1
            if self.rect.top < 20 or self.rect.bottom > self.HEIGHT // 2:
                self.speedy *= -1
        
        # Update barrier positions
        self.update_barriers()
        
        # Shield regeneration
        if self.has_shield and self.shield_health < self.max_shield_health:
            self.shield_health += self.shield_regen_rate
        
        # Shooting
        if now - self.last_shot > self.shoot_delay:
            self.shoot()
            self.last_shot = now
    
    def update_barriers(self):
        # Update positions of all barriers to follow the mini-boss
        barrier_positions = [
            (self.rect.centerx - 70, self.rect.centery), 
            (self.rect.centerx + 70, self.rect.centery),
            (self.rect.centerx, self.rect.centery + 70)
        ]
        
        for i, barrier in enumerate(self.barriers):
            if barrier.alive():
                barrier.rect.center = barrier_positions[i]
    
    def shoot(self):
        # Shoot from each living barrier
        for barrier in self.barriers:
            if barrier.alive():
                # Create a spread of bullets from each barrier
                for angle in range(-30, 31, 30):
                    bullet = self.EnemySpreadBullet(
                        barrier.rect.centerx,   # x
                        barrier.rect.bottom,    # y
                        angle,                  # angle
                        self,                   # owner
                        (173, 216, 230),        # color (light blue)
                        8,                      # size
                        15,                     # damage
                        6                       # speed
                    )
                    self.all_sprites.add(bullet)
                    self.enemy_bullets.add(bullet)
                    self.bullets.append(bullet)
        
        # If no barriers left, shoot directly from the mini-boss
        if all(not barrier.alive() for barrier in self.barriers):
            for angle in range(-45, 46, 15):
                bullet = self.EnemySpreadBullet(
                    self.rect.centerx,          # x
                    self.rect.bottom,           # y
                    angle,                      # angle
                    self,                       # owner
                    (0, 0, 128),                # color (dark blue)
                    10,                         # size
                    20,                         # damage
                    6                           # speed
                )
                self.all_sprites.add(bullet)
                self.enemy_bullets.add(bullet)
                self.bullets.append(bullet)
    
    def hit(self, damage):
        # Check shield first
        if self.has_shield:
            self.shield_health -= damage
            if self.shield_health <= 0:
                self.has_shield = False
                self.shield_health = 0
            return False  # Not destroyed yet
        
        # If no shield, take direct health damage
        self.health -= damage
        
        # Check if destroyed
        if self.health <= 0:
            # Clear any bullets this enemy fired
            for bullet in self.bullets[:]:
                if bullet in self.enemy_bullets:
                    self.enemy_bullets.remove(bullet)
                if bullet in self.all_sprites:
                    self.all_sprites.remove(bullet)
                bullet.kill()
            self.bullets.clear()
            
            # Drop multiple power-ups
            self.drop_powerups()
            
            # Give score
            self.game_state.score += self.score_value
            
            # Spawn a shop portal for game progression
            # Import the spawn function from the main module
            import sys
            main_module = sys.modules['__main__']
            if hasattr(main_module, 'spawn_shop_portal'):
                main_module.spawn_shop_portal(self.rect.centerx, self.rect.centery)
                print("Mini-boss defeated! Called spawn_shop_portal function")
            else:
                print("ERROR: spawn_shop_portal function not found in main module")
            
            # Reset boss_fight flag directly as a backup
            self.game_state.boss_fight = False
            
            # Remove the mini-boss from the game
            self.kill()
            
            return True  # Destroyed
        return False  # Not destroyed yet
    
    def drop_powerups(self):
        # Guaranteed power-ups - one of each type
        powerup_types = ["health", "weapon", "shield", "drone"]
        for i, _ in enumerate(powerup_types):
            # Create a standard PowerUp (which randomly selects its type)
            powerup = self.PowerUp(self.rect.centerx + (i-1.5)*30, self.rect.centery)
            self.all_sprites.add(powerup)
            self.powerups.add(powerup) 