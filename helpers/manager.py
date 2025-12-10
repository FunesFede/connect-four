from helpers.generator import GridGenerator
from PIL import Image
from typing import Optional

from errors.invalidMovement import InvalidMovement
import discord


class GameManager:
    def __init__(self, rows: int, cols: int, spin_it: bool, red_id: int, yellow_id: int):
        self.rows = rows
        self.columns = cols
        self.spin_it = spin_it
        self.red_id = red_id
        self.yellow_id = yellow_id
        self.current_turn = red_id
        self.generator = GridGenerator(rows, cols)

        self.grid = [[0 for _ in range(cols)] for _ in range(rows)]
        self.last_move = None

        self.turn_count = 0
        self.current_turn = red_id
        self.tie_round = rows * self.columns / 2
        self.last_spin = 0
        self.last_spin_user = None
        self.last_move = None  # Track last move position (row, col)

    def can_play(self, player: int):
        return player == self.current_turn

    def get_grid_image(self) -> Image.Image:
        return self.generator.generate_grid(self.grid)

    def validate_placement(self, column: int) -> bool:
        inversed_grid = self.grid.copy()
        inversed_grid.reverse()

        is_valid = False

        for row in inversed_grid:
            col = row[column]
            if col == 0:
                is_valid = True
                break

        return is_valid

    def get_placement_row(self, column: int) -> int:
        for row in range(self.rows - 1, -1, -1):
            if self.grid[row][column] == 0:
                return row

        raise InvalidMovement

    def make_placement(self, column: int, player: int) -> Image.Image:
        if not self.validate_placement(column):
            raise InvalidMovement

        row = self.get_placement_row(column)
        self.grid[row][column] = 1 if player == self.red_id else 2
        self.last_move = (row, column)

        self.turn_count += 1
        self.current_turn = self.yellow_id if player == self.red_id else self.red_id
        return self.generator.generate_grid(self.grid)

    def can_spin(self, player: int):
        return self.turn_count - self.last_spin >= 2 and self.last_spin_user != player

    def spin_column(self, column: int, player: int) -> Image.Image:
        column_values = [row[column] for row in self.grid]
        column_values.reverse()

        for i, row in enumerate(self.grid):
            row[column] = column_values[i]

        for row in range(self.rows):
            if self.grid[row][column] != 0 and self.grid[row][column] == 1 if self.current_turn == self.red_id else 2:
                self.last_move = (row, column)
                break

        self.turn_count += 1
        self.current_turn = self.yellow_id if player == self.red_id else self.red_id
        self.last_spin = self.turn_count
        self.last_spin_user = player

        return self.generator.generate_grid(self.grid)

    def validate_connect(self) -> Optional[int]:
        if self.last_move is None:
            return None

        row, col = self.last_move
        player_value = self.grid[row][col]

        if player_value == 0:
            return None

        directions = [
            (0, 1),   # Horizontal
            (1, 0),   # Vertical
            (1, 1),   # Diagonal \
            (1, -1)   # Diagonal /
        ]

        for dr, dc in directions:
            count = 1

            # Check in positive direction
            for i in range(1, 4):
                r, c = row + dr * i, col + dc * i
                if 0 <= r < self.rows and 0 <= c < self.columns and self.grid[r][c] == player_value:
                    count += 1
                else:
                    break

            # Check in negative direction
            for i in range(1, 4):
                r, c = row - dr * i, col - dc * i
                if 0 <= r < self.rows and 0 <= c < self.columns and self.grid[r][c] == player_value:
                    count += 1
                else:
                    break

            # If we found 4 or more in a row
            if count >= 4:
                return self.red_id if player_value == 1 else self.yellow_id

        return None
