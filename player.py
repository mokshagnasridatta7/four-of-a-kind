"""Player sprite module."""

import pygame
from settings import (
    COLOR_PLAYER,
    COLOR_PLAYER_BORDER,
    PLAYER_WIDTH,
    PLAYER_HEIGHT,
    PLAYER_SPEED,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
)


class Player(pygame.sprite.Sprite):
    """Player sprite represented by a colored rectangle that can be moved with WASD or Arrow keys."""

    def __init__(self, x: float, y: float):
        super().__init__()

        # Create placeholder colored rectangle surface
        self.image = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT))
        self.image.fill(COLOR_PLAYER)
        # Add a subtle stylish border around the placeholder rectangle
        pygame.draw.rect(self.image, COLOR_PLAYER_BORDER, self.image.get_rect(), width=2)

        # Get rect and set starting position
        self.rect = self.image.get_rect()
        self.position = pygame.math.Vector2(x, y)
        self.rect.center = (int(self.position.x), int(self.position.y))

        # Movement attributes
        self.speed = PLAYER_SPEED
        self.velocity = pygame.math.Vector2(0, 0)

    def handle_input(self):
        """Check keyboard state for WASD and Arrow keys and compute movement direction."""
        keys = pygame.key.get_pressed()
        direction = pygame.math.Vector2(0, 0)

        # Horizontal movement (A / Left Arrow, D / Right Arrow)
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            direction.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            direction.x += 1

        # Vertical movement (W / Up Arrow, S / Down Arrow)
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            direction.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            direction.y += 1

        # Normalize direction vector so diagonal movement isn't faster
        if direction.length_squared() > 0:
            direction = direction.normalize()

        self.velocity = direction * self.speed

    def update(self, dt: float):
        """Update player position based on velocity, delta time, and clamp within screen bounds."""
        self.handle_input()

        # Update floating-point position vector
        self.position += self.velocity * dt

        # Update rect position for rendering
        self.rect.centerx = round(self.position.x)
        self.rect.centery = round(self.position.y)

        # Clamp within screen boundaries
        if self.rect.left < 0:
            self.rect.left = 0
            self.position.x = self.rect.centerx
        elif self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
            self.position.x = self.rect.centerx

        if self.rect.top < 0:
            self.rect.top = 0
            self.position.y = self.rect.centery
        elif self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT
            self.position.y = self.rect.centery
