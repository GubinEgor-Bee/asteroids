"""Главный модуль, содержащий цикл игры и отрисовку."""

import pygame
import random
from pygame.math import Vector2
import src.config as cfg
from src.models import Ship, Asteroid, Rocket


class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT))
        pygame.display.set_caption("Asteroids")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)
        self.title_font = pygame.font.SysFont(None, 72)

        self.state = "MENU"  # Возможные состояния: MENU, PLAYING, GAME_OVER
        self.reset_game()

        # Для динамического фона (звезд)
        self.stars = [
            Vector2(random.randint(0, cfg.WIDTH), random.randint(0, cfg.HEIGHT))
            for _ in range(100)
        ]

    def reset_game(self):
        """Сбрасывает параметры для новой игры."""
        self.ship = Ship()
        self.asteroids = [Asteroid() for _ in range(5)]
        self.rockets = []
        self.explosions = []
        self.lives = cfg.INITIAL_LIVES
        self.score = cfg.INITIAL_SCORE
        # Прямоугольник заставки по центру[cite: 4]
        self.splash_rect = pygame.Rect(
            cfg.WIDTH // 2 - 150, cfg.HEIGHT // 2 - 75, 300, 150
        )

    def draw_text(self, text, font, color, x, y, center=False):
        """Вспомогательная функция для отрисовки текста."""
        surface = font.render(text, True, color)
        rect = surface.get_rect()
        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        self.screen.blit(surface, rect)

    def draw_ship(self):
        """Отрисовывает корабль и его двигатель в виде полигонов[cite: 4]."""
        # Базовый треугольник корабля
        points = [Vector2(0, -15), Vector2(10, 10), Vector2(-10, 10)]
        rotated_points = [
            (p.rotate(self.ship.angle) + self.ship.position) for p in points
        ]
        pygame.draw.polygon(
            self.screen, cfg.COLOR_SHIP, [(p.x, p.y) for p in rotated_points], 2
        )

        # Изменение изображения при включенном двигателе[cite: 4]
        if self.ship.is_thrusting:
            flame = [Vector2(0, 10), Vector2(5, 15), Vector2(0, 25), Vector2(-5, 15)]
            rotated_flame = [
                (p.rotate(self.ship.angle) + self.ship.position) for p in flame
            ]
            pygame.draw.polygon(
                self.screen, cfg.COLOR_FLAME, [(p.x, p.y) for p in rotated_flame]
            )

    def draw_asteroids_and_rockets(self):
        for a in self.asteroids:
            pygame.draw.circle(
                self.screen,
                cfg.COLOR_ASTEROID,
                (int(a.position.x), int(a.position.y)),
                a.radius,
                2,
            )
        for r in self.rockets:
            pygame.draw.circle(
                self.screen,
                cfg.COLOR_ROCKET,
                (int(r.position.x), int(r.position.y)),
                r.radius,
            )

    def draw_explosions(self):
        """Отрисовывает примитивную анимацию взрыва[cite: 4]."""
        for exp in self.explosions[:]:
            pygame.draw.circle(
                self.screen,
                cfg.COLOR_FLAME,
                (int(exp["pos"].x), int(exp["pos"].y)),
                exp["radius"],
            )
            exp["radius"] += 2
            exp["life"] -= 1
            if exp["life"] <= 0:
                self.explosions.remove(exp)

    def draw_background(self):
        """Отрисовывает неподвижный и динамический фон[cite: 4]."""
        self.screen.fill(cfg.COLOR_BG)
        # Динамический фон движется влево[cite: 4]
        for star in self.stars:
            star.x -= 0.5
            if star.x < 0:
                star.x = cfg.WIDTH
            pygame.draw.circle(
                self.screen, (255, 255, 255), (int(star.x), int(star.y)), 1
            )

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Начало игры только по щелчку на заставке[cite: 4]
                if self.state in [
                    "MENU",
                    "GAME_OVER",
                ] and self.splash_rect.collidepoint(event.pos):
                    self.reset_game()
                    self.state = "PLAYING"

            if event.type == pygame.KEYDOWN and self.state == "PLAYING":
                if event.key == pygame.K_SPACE:
                    self.rockets.append(Rocket(self.ship.position, self.ship.angle))
        return True

    def update_logic(self):
        if self.state != "PLAYING":
            # Астероиды генерируются и летают даже в меню
            for a in self.asteroids:
                a.update()
            return

        # Управление[cite: 4]
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.ship.rotate(-1)
        if keys[pygame.K_RIGHT]:
            self.ship.rotate(1)
        if keys[pygame.K_UP]:
            self.ship.accelerate()
        else:
            self.ship.apply_friction()

        self.ship.update()

        # Генерация новых астероидов со временем[cite: 4]
        if random.random() < 0.02 and len(self.asteroids) < 10:
            self.asteroids.append(Asteroid())

        for a in self.asteroids:
            a.update()

        for r in self.rockets[:]:
            r.update()
            if r.is_dead:
                self.rockets.remove(r)

        # Коллизии: Ракета и Астероид[cite: 4]
        for r in self.rockets[:]:
            for a in self.asteroids[:]:
                if r.collides_with(a):
                    if r in self.rockets:
                        self.rockets.remove(r)
                    if a in self.asteroids:
                        self.asteroids.remove(a)
                    self.explosions.append(
                        {"pos": a.position.copy(), "radius": 5, "life": 15}
                    )
                    self.score += 1

        # Коллизии: Корабль и Астероид[cite: 4]
        for a in self.asteroids[:]:
            if self.ship.collides_with(a):
                self.asteroids.remove(a)
                self.explosions.append(
                    {"pos": a.position.copy(), "radius": 10, "life": 20}
                )
                self.lives -= 1
                # Возрождение в центре неподвижно[cite: 4]
                self.ship.position = Vector2(cfg.WIDTH / 2, cfg.HEIGHT / 2)
                self.ship.velocity = Vector2(0, 0)

                if self.lives <= 0:
                    self.state = "GAME_OVER"

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update_logic()

            self.draw_background()

            # В состоянии игры отрисовываем объекты[cite: 4]
            if self.state == "PLAYING":
                self.draw_ship()
                self.draw_asteroids_and_rockets()
            elif self.state in ["MENU", "GAME_OVER"]:
                # Заставка[cite: 4]
                pygame.draw.rect(self.screen, (50, 50, 100), self.splash_rect)
                pygame.draw.rect(self.screen, (100, 100, 200), self.splash_rect, 3)
                self.draw_text(
                    "ASTEROIDS",
                    self.title_font,
                    (255, 255, 255),
                    cfg.WIDTH // 2,
                    cfg.HEIGHT // 2 - 20,
                    center=True,
                )
                self.draw_text(
                    "Click to Start",
                    self.font,
                    (200, 200, 200),
                    cfg.WIDTH // 2,
                    cfg.HEIGHT // 2 + 30,
                    center=True,
                )

            self.draw_explosions()

            # HUD[cite: 4]
            self.draw_text(f"Lives: {self.lives}", self.font, cfg.COLOR_TEXT, 20, 20)
            self.draw_text(
                f"Score: {self.score}", self.font, cfg.COLOR_TEXT, cfg.WIDTH - 120, 20
            )

            pygame.display.flip()
            self.clock.tick(cfg.FPS)

        pygame.quit()
