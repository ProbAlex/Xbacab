# Space Fighter - Vertical Scrolling Shooter

A pygame implementation of a vertical scrolling space shooter game with multiple weapon types, upgrades, and enemy types.

## Game Features

- **Player Ship Controls**
  - Movement: WASD or Arrow keys
  - Fire: SPACE or Left Mouse Button (rate limited to 5 shots per second)
  - Hyper Dash: SHIFT key (brief invincibility and speed boost)
  - Energy Shield: E key (absorbs damage while active)

- **Power-Ups & Upgrades**
  - Health (Green): Restores player health
  - Shield (Blue): Refills energy meter
  - Weapon (Yellow): Upgrades weapon level or changes weapon type
  - Drone (Purple): Adds support drones that fire with you

- **Weapon Types**
  - Normal: Standard bullets that upgrade to multiple shots
  - Spread: Multiple bullets fired in a spread pattern
  - Bouncing: Bullets that ricochet off walls and enemies while targeting the closest enemy
  - Homing: Smart missiles that track and follow the nearest enemy

- **Drone System**
  - Intelligent drone positioning based on quantity (cardinal or circular formation)
  - Drones fire the same weapon type as the player
  - Chance to fire bouncing bullets regardless of current weapon type
  - Maximum drones varies based on difficulty (6 on Easy, 4 on Normal, 3 on Hard)

- **Difficulty Settings**
  - Easy: More health, natural health regeneration, more resources, slower enemies
  - Normal: Balanced gameplay experience
  - Hard: Less health, faster enemies, tougher bosses, limited weapon types

- **Combat System**
  - Basic Enemies: Small ships with simple attacks
  - Elite Enemies: Larger, tougher ships with more complex attack patterns
  - Boss Fights: Unique boss encounters at the end of each sector
  - Combo System: Destroy enemies in succession to increase your score multiplier
  - Enemy projectiles despawn when their source is destroyed

- **User Interface**
  - Fullscreen display with properly centered gameplay
  - Interactive menu with buttons for game start, controls, and difficulty selection
  - Dynamic weapon indicator showing current weapon type and level
  - Resource counter and detailed game statistics
  - End-of-wave shop portals that players can enter when ready

## Installation

1. Make sure you have Python 3.x installed
2. Install pygame using pip:
```
pip install pygame
```

## Running the Game

Run the game using Python:
```
python space_shooter.py
```

## Game Controls

- **Movement**: Arrow keys or WASD
- **Fire**: SPACE or Left Mouse Button
- **Hyper Dash**: SHIFT key
- **Energy Shield**: E key
- **Enter Shop**: E key (when next to shop portal)
- **Navigate Menus**: Arrow keys/WASD, ENTER to select, ESC to back
- **Exit Game**: ESC

## Game Mechanics

- Your ship appears at the bottom center of the screen
- Waves of enemies scroll down from the top
- Avoid collisions with enemies and their bullets
- Collect power-ups to upgrade your ship and weapons
- Build up combos by destroying enemies in succession
- Progress through increasingly difficult waves and sectors
- Defeat the boss at the end of each sector to advance
- Enter the shop portal after defeating bosses to purchase upgrades

## Objective

Survive as long as possible while destroying enemy ships and achieving the highest score possible. Defeat the final boss in sector 6 to complete the game.

## Requirements

- Python 3.x
- pygame

## Credits

Made by Alexander Dial and Gavriel Rodriguez
