from PIL import Image


class GridGenerator:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols

        # Load chip images
        self.empty_chip = Image.open('images/empty_chip.png')
        self.red_chip = Image.open('images/red_chip.png')
        self.yellow_chip = Image.open('images/yellow_chip.png')

        # Get chip dimensions (assume all chips are the same size)
        self.chip_width, self.chip_height = self.empty_chip.size

    def generate_grid(self, matrix):
        """
        Generates a grid image from chip images according to the provided matrix.

        Args:
            matrix: A matrix (rows x cols) where:
                    0 = empty chip
                    1 = red chip
                    2 = yellow chip
                    matrix[0][0] is the top-left position

        Returns:
            PIL.Image: The composite image with chips arranged in a grid
        """
        # Calculate grid dimensions
        grid_width = self.chip_width * self.cols
        grid_height = self.chip_height * self.rows

        # Create a new image for the grid
        result = Image.new('RGBA', (grid_width, grid_height))

        # Iterate through the matrix and place chips
        for row in range(self.rows):
            for col in range(self.cols):
                cell_value = matrix[row][col]

                # Calculate position (top-left corner of the cell)
                x = col * self.chip_width
                y = row * self.chip_height

                # Select the appropriate chip
                if cell_value == 0:
                    chip = self.empty_chip
                elif cell_value == 1:
                    chip = self.red_chip
                elif cell_value == 2:
                    chip = self.yellow_chip
                else:
                    continue  # Invalid value

                # Paste chip with alpha channel as mask for transparency
                result.paste(chip, (x, y), chip)

        return result
