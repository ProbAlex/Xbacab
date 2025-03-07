# Space Fighter - Vertical Scrolling Shooter

A pygame implementation of a vertical scrolling space shooter game with multiple weapon types, upgrades, and enemy types.

## Game Features

- **Player Ship Controls**
  - Movement: WASD or Arrow keys
  - Fire: SPACE (hold for continuous fire)
  - Hyper Dash: E key (brief invincibility and speed boost)
  - Energy Shield: SHIFT key (absorbs damage while active)

- **Power-Ups & Upgrades**
  - Health (Green): Restores player health
  - Shield (Blue): Refills energy meter
  - Weapon (Yellow): Upgrades weapon level or changes weapon type
  - Drone (Purple): Adds support drones that fire with you

- **Weapon Types**
  - Normal: Standard bullets that upgrade to multiple shots
  - Spread: Multiple bullets fired in a spread pattern
  - Laser: Powerful beam that lasts for a short duration

- **Combat System**
  - Basic Enemies: Small ships with simple attacks
  - Elite Enemies: Larger, tougher ships with more complex attack patterns
  - Combo System: Destroy enemies in succession to increase your score multiplier

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
- **Fire**: SPACE
- **Hyper Dash**: E
- **Energy Shield**: SHIFT
- **Exit Game**: ESC

## Game Mechanics

- Your ship appears at the bottom center of the screen
- Waves of enemies scroll down from the top
- Avoid collisions with enemies and their bullets
- Collect power-ups to upgrade your ship and weapons
- Build up combos by destroying enemies in succession
- Progress through increasingly difficult waves and sectors

## Objective

Survive as long as possible while destroying enemy ships and achieving the highest score possible.

## Requirements

- Python 3.x
- pygame

## Credits

Created as a demonstration of pygame capabilities. 