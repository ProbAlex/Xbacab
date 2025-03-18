import pygame
import os
import math
import random

# Initialize pygame
pygame.init()

# Create assets directory if it doesn't exist
if not os.path.exists("assets/images"):
    os.makedirs("assets/images")

# Set up colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 120, 255)
YELLOW = (255, 255, 0)
PURPLE = (150, 30, 150)
DARK_BLUE = (0, 0, 128)
LIGHT_BLUE = (100, 200, 255)
ORANGE = (255, 150, 0)
TEAL = (0, 180, 180)

# Player ship parameters
PLAYER_WIDTH = 50
PLAYER_HEIGHT = 40

# Create player ship
def create_player_ship():
    """Create a stylized triangular player ship with details"""
    surface = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT), pygame.SRCALPHA)
    
    # Main ship body (triangle)
    pygame.draw.polygon(surface, BLUE, [
        (0, PLAYER_HEIGHT),  # Bottom left
        (PLAYER_WIDTH//2, 0),  # Top middle
        (PLAYER_WIDTH, PLAYER_HEIGHT)  # Bottom right
    ])
    
    # Add a cockpit
    pygame.draw.polygon(surface, LIGHT_BLUE, [
        (PLAYER_WIDTH//2 - 5, PLAYER_HEIGHT//3),  # Top left
        (PLAYER_WIDTH//2, PLAYER_HEIGHT//5),      # Top middle
        (PLAYER_WIDTH//2 + 5, PLAYER_HEIGHT//3),  # Top right
        (PLAYER_WIDTH//2, PLAYER_HEIGHT//2)       # Bottom middle
    ])
    
    # Add engine glow
    pygame.draw.rect(surface, (255, 100, 0), (PLAYER_WIDTH//3, PLAYER_HEIGHT-8, 5, 8))
    pygame.draw.rect(surface, (255, 100, 0), (PLAYER_WIDTH//2 - 2, PLAYER_HEIGHT-10, 4, 10))
    pygame.draw.rect(surface, (255, 100, 0), (PLAYER_WIDTH - PLAYER_WIDTH//3 - 5, PLAYER_HEIGHT-8, 5, 8))
    
    # Add wing details
    pygame.draw.line(surface, DARK_BLUE, (5, PLAYER_HEIGHT-5), (PLAYER_WIDTH//2 - 5, PLAYER_HEIGHT//2), 2)
    pygame.draw.line(surface, DARK_BLUE, (PLAYER_WIDTH-5, PLAYER_HEIGHT-5), (PLAYER_WIDTH//2 + 5, PLAYER_HEIGHT//2), 2)
    
    return surface

# Create drone
def create_drone():
    """Create a small support drone"""
    size = 20
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Main body (circle)
    pygame.draw.circle(surface, BLUE, (size//2, size//2), size//2)
    
    # Inner details
    pygame.draw.circle(surface, LIGHT_BLUE, (size//2, size//2), size//4)
    
    # Add some tech details
    pygame.draw.line(surface, DARK_BLUE, (3, size//2), (size-3, size//2), 2)
    pygame.draw.line(surface, DARK_BLUE, (size//2, 3), (size//2, size-3), 2)
    
    return surface

# Create shield bearer enemy
def create_shield_bearer():
    """Create a shield bearer enemy"""
    size = 55
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Main body (circle)
    pygame.draw.circle(surface, (50, 150, 250), (size//2, size//2), size//2)
    
    # Shield effect (outer ring)
    pygame.draw.circle(surface, LIGHT_BLUE, (size//2, size//2), size//2, 3)
    
    # Inner details
    pygame.draw.circle(surface, (30, 100, 200), (size//2, size//2), size//3)
    
    # Core
    pygame.draw.circle(surface, WHITE, (size//2, size//2), size//6)
    
    return surface

# Create energy sapper enemy
def create_energy_sapper():
    """Create energy sapper enemy"""
    width, height = 45, 55
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Main body (ellipse)
    pygame.draw.ellipse(surface, (200, 100, 200), (0, 0, width, height))
    
    # Energy beam emitter (bottom center)
    pygame.draw.rect(surface, (255, 50, 255), (width//3, height-10, width//3, 10))
    
    # Upper details
    pygame.draw.ellipse(surface, (150, 0, 150), (width//4, height//5, width//2, height//3))
    
    # Core
    pygame.draw.circle(surface, WHITE, (width//2, height//2), width//6)
    
    return surface

# Create blade spinner enemy
def create_blade_spinner():
    """Create blade spinner enemy"""
    size = 48
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    center = (size//2, size//2)
    
    # Create a spinning blade-like appearance
    points = []
    for i in range(8):  # 8-pointed star
        angle = math.pi * i / 4
        points.append((center[0] + size//2 * math.cos(angle), center[1] + size//2 * math.sin(angle)))
        angle += math.pi / 8
        points.append((center[0] + size//4 * math.cos(angle), center[1] + size//4 * math.sin(angle)))
    
    # Draw the blade shape
    pygame.draw.polygon(surface, ORANGE, points)
    
    # Add a core
    pygame.draw.circle(surface, (255, 200, 100), center, size//6)
    
    # Add some detail lines
    for i in range(4):
        angle = math.pi * i / 4
        start_x = center[0] + (size//6) * math.cos(angle)
        start_y = center[1] + (size//6) * math.sin(angle)
        end_x = center[0] + (size//2) * math.cos(angle)
        end_y = center[1] + (size//2) * math.sin(angle)
        pygame.draw.line(surface, (200, 100, 0), (start_x, start_y), (end_x, end_y), 2)
    
    return surface

# Create boss assets
def create_edge_guardian():
    """Create Sector 1 boss - Edge Guardian"""
    size = 100
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Draw the distinctive shape
    pygame.draw.polygon(surface, RED, [
        (0, 0),        # Top left
        (size, 0),     # Top right
        (size, size),  # Bottom right
        (size//2, 3*size//4),  # Middle bump
        (0, size)      # Bottom left
    ])
    
    # Add some details
    pygame.draw.line(surface, (255, 100, 100), (size//4, size//4), (3*size//4, size//4), 3)
    pygame.draw.circle(surface, (255, 200, 200), (size//2, size//2), size//6)
    
    # Add some texture/details
    pygame.draw.line(surface, (150, 0, 0), (size//5, size//2), (4*size//5, size//2), 2)
    pygame.draw.line(surface, (150, 0, 0), (size//5, 2*size//3), (4*size//5, 2*size//3), 2)
    
    return surface

def create_asteroid_titan():
    """Create Sector 2 boss - Asteroid Titan"""
    size = 120
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Draw the main asteroid body
    pygame.draw.circle(surface, (150, 75, 0), (size//2, size//2), size//2)
    
    # Add some crater details
    pygame.draw.circle(surface, (100, 50, 0), (size//3, size//3), size//8)
    pygame.draw.circle(surface, (100, 50, 0), (2*size//3, 2*size//3), size//10)
    pygame.draw.circle(surface, (100, 50, 0), (size//3, 2*size//3), size//12)
    
    # Add some texture
    for i in range(10):
        x = random.randint(size//4, 3*size//4)
        y = random.randint(size//4, 3*size//4)
        r = random.randint(2, 8)
        pygame.draw.circle(surface, (180, 90, 30), (x, y), r)
    
    return surface

def create_rhovax_dreadnought():
    """Create Sector 3 boss - Rhovax Dreadnought"""
    width, height = 150, 100
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Draw the main ship body (diamond shape)
    pygame.draw.polygon(surface, PURPLE, [
        (0, height//2),     # Left point
        (width//2, 0),      # Top point
        (width, height//2), # Right point
        (width//2, height)  # Bottom point
    ])
    
    # Add inner details
    pygame.draw.polygon(surface, (200, 100, 200), [
        (width//4, height//2),
        (width//2, height//4),
        (3*width//4, height//2),
        (width//2, 3*height//4)
    ])
    
    # Add core
    pygame.draw.circle(surface, WHITE, (width//2, height//2), height//8)
    
    # Add weapon ports
    pygame.draw.rect(surface, (100, 0, 100), (width//4-5, height-15, 10, 15))
    pygame.draw.rect(surface, (100, 0, 100), (width//2-5, height-15, 10, 15))
    pygame.draw.rect(surface, (100, 0, 100), (3*width//4-5, height-15, 10, 15))
    
    return surface

def create_shipyard_sentinel():
    """Create Sector 4 boss - Shipyard Sentinel"""
    size = 160
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Draw the main cube
    pygame.draw.rect(surface, (0, 100, 200), (0, 0, size, size))
    
    # Draw the inner void
    inner_size = size - 60
    inner_offset = 30
    pygame.draw.rect(surface, (0, 0, 0), (inner_offset, inner_offset, inner_size, inner_size))
    
    # Add some tech details on the frame
    for i in range(0, size, 20):
        pygame.draw.rect(surface, (0, 150, 255), (i, 5, 10, 10), 1)
        pygame.draw.rect(surface, (0, 150, 255), (i, size-15, 10, 10), 1)
        pygame.draw.rect(surface, (0, 150, 255), (5, i, 10, 10), 1)
        pygame.draw.rect(surface, (0, 150, 255), (size-15, i, 10, 10), 1)
    
    # Add some glowing elements
    pygame.draw.circle(surface, (100, 200, 255), (size//4, size//4), 5)
    pygame.draw.circle(surface, (100, 200, 255), (3*size//4, size//4), 5)
    pygame.draw.circle(surface, (100, 200, 255), (size//4, 3*size//4), 5)
    pygame.draw.circle(surface, (100, 200, 255), (3*size//4, 3*size//4), 5)
    
    return surface

def create_storm_lord():
    """Create Sector 5 boss - Storm Lord"""
    width, height = 180, 150
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Draw the main storm body (elliptical)
    pygame.draw.ellipse(surface, (50, 50, 200), (0, 0, width, height))
    
    # Draw the inner storm core
    pygame.draw.ellipse(surface, (100, 0, 100), (width//6, height//5, 2*width//3, 3*height//5))
    
    # Add some storm effects (lightning)
    for i in range(5):
        start_x = random.randint(width//4, 3*width//4)
        start_y = random.randint(height//4, 3*height//4)
        end_x = start_x + random.randint(-30, 30)
        end_y = start_y + random.randint(-30, 30)
        pygame.draw.line(surface, (200, 200, 255), (start_x, start_y), (end_x, end_y), 2)
    
    # Add some swirl effects
    for i in range(0, 360, 30):
        angle = math.radians(i)
        radius = 60
        x1 = width//2 + int(radius * 0.7 * math.cos(angle))
        y1 = height//2 + int(radius * 0.7 * math.sin(angle))
        x2 = width//2 + int(radius * math.cos(angle + math.radians(20)))
        y2 = height//2 + int(radius * math.sin(angle + math.radians(20)))
        pygame.draw.line(surface, (150, 100, 255), (x1, y1), (x2, y2), 2)
    
    return surface

def create_dominion_mothership():
    """Create Sector 6 boss - Dominion Mothership (final boss)"""
    size = 200
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Draw the main ship body (hexagonal shape)
    pygame.draw.polygon(surface, (200, 0, 0), [
        (0, 0),              # Top left
        (size, 0),           # Top right
        (4*size//5, size//2), # Right middle
        (size, size),        # Bottom right
        (0, size),           # Bottom left
        (size//5, size//2)    # Left middle
    ])
    
    # Add inner details and structure
    pygame.draw.polygon(surface, (150, 0, 0), [
        (size//4, size//4),
        (3*size//4, size//4),
        (2*size//3, size//2),
        (3*size//4, 3*size//4),
        (size//4, 3*size//4),
        (size//3, size//2)
    ])
    
    # Add a core
    pygame.draw.circle(surface, (255, 100, 100), (size//2, size//2), size//8)
    
    # Add weapon emplacements
    pygame.draw.rect(surface, (255, 200, 200), (size//4-10, size-20, 20, 20))
    pygame.draw.rect(surface, (255, 200, 200), (size//2-10, size-20, 20, 20))
    pygame.draw.rect(surface, (255, 200, 200), (3*size//4-10, size-20, 20, 20))
    
    # Add some tech details
    for i in range(3):
        x = size//4 + i*size//4
        pygame.draw.circle(surface, (255, 0, 0), (x, size//4), 10)
        pygame.draw.circle(surface, (255, 100, 100), (x, size//4), 5)
    
    return surface

# Generate and save the assets
def generate_assets():
    # Player ship
    player_ship = create_player_ship()
    pygame.image.save(player_ship, "assets/images/player_ship.png")
    print("Created player_ship.png")
    
    # Drone
    drone = create_drone()
    pygame.image.save(drone, "assets/images/drone.png")
    print("Created drone.png")
    
    # Shield bearer enemy
    shield_bearer = create_shield_bearer()
    pygame.image.save(shield_bearer, "assets/images/shield_bearer.png")
    print("Created shield_bearer.png")
    
    # Energy sapper enemy
    energy_sapper = create_energy_sapper()
    pygame.image.save(energy_sapper, "assets/images/energy_sapper.png")
    print("Created energy_sapper.png")
    
    # Blade spinner enemy
    blade_spinner = create_blade_spinner()
    pygame.image.save(blade_spinner, "assets/images/blade_spinner.png")
    print("Created blade_spinner.png")
    
    # Boss assets
    # Sector 1 boss
    edge_guardian = create_edge_guardian()
    pygame.image.save(edge_guardian, "assets/images/boss_1.png")
    print("Created boss_1.png (Edge Guardian)")
    
    # Sector 2 boss
    asteroid_titan = create_asteroid_titan()
    pygame.image.save(asteroid_titan, "assets/images/boss_2.png")
    print("Created boss_2.png (Asteroid Titan)")
    
    # Sector 3 boss
    rhovax_dreadnought = create_rhovax_dreadnought()
    pygame.image.save(rhovax_dreadnought, "assets/images/boss_3.png")
    print("Created boss_3.png (Rhovax Dreadnought)")
    
    # Sector 4 boss
    shipyard_sentinel = create_shipyard_sentinel()
    pygame.image.save(shipyard_sentinel, "assets/images/boss_4.png")
    print("Created boss_4.png (Shipyard Sentinel)")
    
    # Sector 5 boss
    storm_lord = create_storm_lord()
    pygame.image.save(storm_lord, "assets/images/boss_5.png")
    print("Created boss_5.png (Storm Lord)")
    
    # Sector 6 boss (final boss)
    dominion_mothership = create_dominion_mothership()
    pygame.image.save(dominion_mothership, "assets/images/boss_6.png")
    print("Created boss_6.png (Dominion Mothership)")
    
    print("All assets generated successfully!")

generate_assets()
pygame.quit()
