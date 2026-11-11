"""Модуль, содержащий математические модели игровых объектов."""

import math
import random
from pygame.math import Vector2
import src.config as cfg


class GameObject:
    """Базовый класс для всех объектов с поддержкой тороидальной геометрии."""

    def __init__(self, position: Vector2, velocity: Vector2):
        self.position = Vector2(position)
        self.velocity = Vector2(velocity)
        self.radius = 10
        self.is_dead = False

    def update(self):
        """Обновляет позицию с учетом тороидальной геометрии (пересечение границ)[cite: 4]."""
        self.position += self.velocity
        self.position.x %= cfg.WIDTH
        self.position.y %= cfg.HEIGHT

    def collides_with(self, other: "GameObject") -> bool:
        """Проверяет коллизию на основе радиусов объектов."""
        distance = self.position.distance_to(other.position)
        return distance < self.radius + other.radius


class Ship(GameObject):
    """Класс космического корабля."""

    def __init__(self):
        super().__init__(Vector2(cfg.WIDTH / 2, cfg.HEIGHT / 2), Vector2(0, 0))
        self.angle = 0.0
        self.radius = 15
        self.is_thrusting = False

    def rotate(self, direction: int):
        """Вращает корабль (direction: -1 влево, 1 вправо)[cite: 4]."""
        self.angle += direction * cfg.ROTATION_SPEED

    def accelerate(self):
        """Ускоряет корабль по направлению его ориентации[cite: 4]."""
        self.is_thrusting = True
        direction_vec = Vector2(0, -1).rotate(self.angle)
        self.velocity += direction_vec * cfg.THRUST
        if self.velocity.length() > cfg.MAX_SPEED:
            self.velocity.scale_to_length(cfg.MAX_SPEED)

    def apply_friction(self):
        """Применяет сопротивление среды для замедления[cite: 4]."""
        self.is_thrusting = False
        self.velocity *= cfg.FRICTION


class Rocket(GameObject):
    """Класс ракеты, выпущенной кораблем."""

    def __init__(self, position: Vector2, angle: float):
        direction_vec = Vector2(0, -1).rotate(angle)
        # Ракета появляется из носа корабля[cite: 4]
        nose_position = position + direction_vec * 15
        velocity = direction_vec * cfg.ROCKET_SPEED
        super().__init__(nose_position, velocity)
        self.radius = 3
        self.lifetime = cfg.ROCKET_LIFETIME

    def update(self):
        """Обновляет позицию и уменьшает время жизни[cite: 4]."""
        super().update()
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.is_dead = True


class Asteroid(GameObject):
    """Класс астероида."""

    def __init__(self):
        # Появляются в произвольных местах[cite: 4]
        position = Vector2(random.randint(0, cfg.WIDTH), random.randint(0, cfg.HEIGHT))
        # Случайная линейная скорость[cite: 4]
        speed = random.uniform(1.0, 3.0)
        angle = random.uniform(0, 360)
        velocity = Vector2(speed, 0).rotate(angle)
        super().__init__(position, velocity)
        self.radius = random.randint(20, 40)
        # Случайная угловая скорость (для визуала)[cite: 4]
        self.angular_velocity = random.uniform(-3, 3)
        self.angle = 0.0

    def update(self):
        """Обновляет позицию и угол вращения астероида."""
        super().update()
        self.angle += self.angular_velocity
