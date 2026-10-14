# Pygame Starter Project

A clean, modular starter template for 2D game development with Pygame.

## Features

- **Standard Pygame Loop**: Clear separation between event handling, updates, drawing, and framerate capping.
- **Delta-Time Movement**: Consistent speed across varying framerates (`dt = clock.tick(FPS) / 1000.0`).
- **Normalized Vector Input**: Diagonal movement moves at the same calibrated speed rather than $1.41\times$ faster.
- **Screen Boundary Clamping**: Prevents sprites from slipping outside the visible viewport.
- **Dual Control Scheme**: Supports both **WASD** and **Arrow Keys**.
- **Pygame Sprite Class**: Demonstrates standard `pygame.sprite.Sprite` and `pygame.sprite.Group` patterns.

## Project Structure

```text
pygame-starter/
├── requirements.txt   # Dependencies (pygame-ce)
├── settings.py        # Window dimensions, FPS, colors, player constants
├── player.py          # Player sprite class with input & boundary logic
├── game_state.py      # Immutable GameState and pure transition functions
├── test_game_state.py # Unit tests confirming purity and immutability
├── main.py            # Main entry point and Game class
└── README.md          # Documentation and setup instructions
```

## Running the Project

From the project root directory:

```bash
python main.py
```

### Controls

| Key | Action |
| --- | --- |
| `W` or `Up Arrow` | Move Up |
| `S` or `Down Arrow` | Move Down |
| `A` or `Left Arrow` | Move Left |
| `D` or `Right Arrow` | Move Right |
| `Escape` | Close the game |

## Running Unit Tests

Run the test suite confirming `GameState` immutability and function purity:

```bash
python -m unittest test_game_state.py
```
