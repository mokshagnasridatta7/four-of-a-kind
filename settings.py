"""Configuration and constants for the Pygame project."""

# Screen Settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TITLE = "Four of a Kind"
FPS = 60

# Colors (RGB)
COLOR_BACKGROUND = (20, 24, 32)        # Deep slate
COLOR_PLAYER = (64, 200, 120)          # Vibrant emerald green
COLOR_PLAYER_BORDER = (255, 255, 255)   # Crisp white outline
COLOR_TEXT = (230, 235, 245)            # Off-white
COLOR_MUTED = (130, 142, 160)           # Muted text/subtitle

# Hub UI Colors
COLOR_CARD_BG = (30, 36, 48)            # Unselected chapter card background
COLOR_CARD_HOVER = (45, 54, 72)         # Hovered/focused card background
COLOR_CARD_BORDER = (55, 68, 90)        # Normal card border
COLOR_SELECTED = (70, 140, 240)         # Focused chapter border & highlight
COLOR_COMPLETED = (64, 200, 120)        # Completed chapter badge color
COLOR_COMPLETED_BG = (25, 50, 38)       # Completed chapter badge background
COLOR_AVAILABLE = (100, 160, 220)       # Available chapter badge color

# Finale UI Colors
COLOR_FINALE = (255, 215, 0)            # Gold accent for Finale
COLOR_FINALE_BG = (48, 40, 18)          # Gold-tinted card background
COLOR_FINALE_HOVER = (68, 56, 24)       # Gold-tinted card hover background
COLOR_FINALE_BORDER = (200, 170, 40)    # Gold border

# Player Settings
PLAYER_WIDTH = 40
PLAYER_HEIGHT = 40
PLAYER_SPEED = 280.0  # Pixels per second (delta-time based movement)
