#!/usr/bin/env python3
"""
Simple Snake game using pygame.

Controls:
  Arrow keys / WASD  - Move
  R                  - Restart after game over
  Esc / Q            - Quit
"""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass
from typing import Iterable

import pygame


@dataclass(frozen=True)
class Vec:
    x: int
    y: int

    def __add__(self, other: "Vec") -> "Vec":
        return Vec(self.x + other.x, self.y + other.y)


CELL_SIZE = 20
GRID_W = 32  # 32 * 20 = 640 px
GRID_H = 24  # 24 * 20 = 480 px

WIDTH = GRID_W * CELL_SIZE
HEIGHT = GRID_H * CELL_SIZE
FPS = 12

COLOR_BG = (18, 18, 22)
COLOR_GRID = (28, 28, 34)
COLOR_SNAKE = (90, 220, 140)
COLOR_HEAD = (60, 255, 120)
COLOR_FOOD = (250, 90, 90)
COLOR_TEXT = (235, 235, 245)

DIR_UP = Vec(0, -1)
DIR_DOWN = Vec(0, 1)
DIR_LEFT = Vec(-1, 0)
DIR_RIGHT = Vec(1, 0)


def draw_cell(screen: pygame.Surface, pos: Vec, color: tuple[int, int, int]) -> None:
    """Draw a single grid cell at grid position `pos`."""
    r = pygame.Rect(pos.x * CELL_SIZE, pos.y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
    pygame.draw.rect(screen, color, r)


def draw_grid(screen: pygame.Surface) -> None:
    """Draw a subtle background grid so movement reads clearly."""
    for x in range(0, WIDTH, CELL_SIZE):
        pygame.draw.line(screen, COLOR_GRID, (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, CELL_SIZE):
        pygame.draw.line(screen, COLOR_GRID, (0, y), (WIDTH, y), 1)


def random_free_cell(occupied: set[Vec]) -> Vec:
    """Pick a random cell not in `occupied`."""
    # Avoid an infinite loop if the snake fills the grid.
    if len(occupied) >= GRID_W * GRID_H:
        raise RuntimeError("No free cells left (you win).")

    while True:
        p = Vec(random.randrange(GRID_W), random.randrange(GRID_H))
        if p not in occupied:
            return p


def is_opposite(a: Vec, b: Vec) -> bool:
    """True if directions `a` and `b` are exact opposites."""
    return a.x == -b.x and a.y == -b.y


def render_text(
    screen: pygame.Surface, font: pygame.font.Font, text: str, xy: tuple[int, int]
) -> None:
    img = font.render(text, True, COLOR_TEXT)
    screen.blit(img, xy)


def render_centered(
    screen: pygame.Surface, font: pygame.font.Font, text: str, y: int
) -> None:
    img = font.render(text, True, COLOR_TEXT)
    rect = img.get_rect(center=(WIDTH // 2, y))
    screen.blit(img, rect)


def reset_game() -> tuple[list[Vec], Vec, Vec, int, bool]:
    """
    Returns: snake (head first), direction, food, score, game_over.
    """
    start = Vec(GRID_W // 2, GRID_H // 2)
    snake = [start, start + DIR_LEFT, start + DIR_LEFT + DIR_LEFT]
    direction = DIR_RIGHT
    score = 0
    food = random_free_cell(set(snake))
    return snake, direction, food, score, False


def move_snake(snake: list[Vec], direction: Vec) -> Vec:
    """Move snake 1 step in `direction` and return new head position."""
    new_head = snake[0] + direction
    snake.insert(0, new_head)
    return new_head


def out_of_bounds(p: Vec) -> bool:
    return p.x < 0 or p.x >= GRID_W or p.y < 0 or p.y >= GRID_H


def main(argv: list[str]) -> int:
    pygame.init()
    pygame.display.set_caption("Snake (pygame)")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    # Font: use pygame's default font for portability.
    font = pygame.font.Font(None, 28)
    font_big = pygame.font.Font(None, 52)

    snake, direction, food, score, game_over = reset_game()
    pending_dir: Vec | None = None

    while True:
        # --- Input handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 0

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    return 0

                if game_over and event.key == pygame.K_r:
                    snake, direction, food, score, game_over = reset_game()
                    pending_dir = None
                    continue

                # Map keys to directions. We set a "pending_dir" so multiple key
                # presses within the same frame don’t cause multiple moves.
                key_to_dir = {
                    pygame.K_UP: DIR_UP,
                    pygame.K_w: DIR_UP,
                    pygame.K_DOWN: DIR_DOWN,
                    pygame.K_s: DIR_DOWN,
                    pygame.K_LEFT: DIR_LEFT,
                    pygame.K_a: DIR_LEFT,
                    pygame.K_RIGHT: DIR_RIGHT,
                    pygame.K_d: DIR_RIGHT,
                }
                if event.key in key_to_dir and not game_over:
                    cand = key_to_dir[event.key]
                    # Prevent an immediate 180-degree reversal (classic snake rule).
                    if not is_opposite(cand, direction):
                        pending_dir = cand

        if not game_over:
            if pending_dir is not None:
                direction = pending_dir
                pending_dir = None

            # --- Game update ---
            new_head = move_snake(snake, direction)

            # Basic collision detection:
            # 1) Wall collision
            if out_of_bounds(new_head):
                game_over = True
            # 2) Self collision (head overlaps body)
            elif new_head in snake[1:]:
                game_over = True
            else:
                # 3) Food collision: grow + score
                if new_head == food:
                    score += 1
                    try:
                        food = random_free_cell(set(snake))
                    except RuntimeError:
                        # Filled the whole grid: treat as a win.
                        game_over = True
                else:
                    # Didn't eat: remove tail to maintain length.
                    snake.pop()

        # --- Render ---
        screen.fill(COLOR_BG)
        draw_grid(screen)

        # Draw food
        draw_cell(screen, food, COLOR_FOOD)

        # Draw snake (head in a brighter shade)
        for i, seg in enumerate(snake):
            draw_cell(screen, seg, COLOR_HEAD if i == 0 else COLOR_SNAKE)

        # Score counter
        render_text(screen, font, f"Score: {score}", (10, 10))

        if game_over:
            # Simple overlay text.
            render_centered(screen, font_big, "Game Over", HEIGHT // 2 - 30)
            render_centered(
                screen, font, f"Final score: {score}", HEIGHT // 2 + 10
            )
            render_centered(
                screen, font, "Press R to restart, Q/Esc to quit", HEIGHT // 2 + 40
            )

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

