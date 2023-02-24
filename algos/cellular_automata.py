import numpy as np
import svgwrite

FLOOR = 0
ROCK = 1
WALL = 2
RNG = np.random.default_rng()      
N = 5   # pocet iteraci CA
T = 5   # počet kamene kolem, aby byl prvek taky kamen

def generate_map(rows, cols, floor_probability=0.45, number_of_iterations=N, rock_threshold=T):
    """Funkce vrací mapu podle CA algoritmu."""

    map = generate_grid(rows - 2, cols - 2, floor_probability)

    for _ in range(number_of_iterations):
        map = do_simulation_step(map, rock_threshold)

    map = np.vstack((np.ones(cols - 2), map))
    map = np.vstack((map, np.ones(cols - 2)))
    map = np.hstack((map, np.ones((rows, 1))))
    map = np.hstack((np.ones((rows, 1)), map))

    return map

def generate_row(size, floor_probability):
    """Funkce vrací pole délky cols s prvky FLOOR nebo ROCK podle zadané pravděpodobnosti výskytu."""
    row = RNG.choice([FLOOR, ROCK], size, p=[floor_probability, 1 - floor_probability])
    return row

def generate_grid(rows, cols, floor_probability):
    """Funkce vrací dvourozměrné pole s prvky FLOOR nebo ROCK podle zadané pravděpodobnosti výskytu."""

    grid = generate_row(cols, floor_probability)

    for _ in range(rows - 1):
        grid = np.vstack((grid, generate_row(cols, floor_probability)))

    return grid 
    

def do_simulation_step(grid, rock_threshold):
    """Funkce vrací nové dvourozměrné pole podle zadaného pole a použitých vývojových kroků."""

    # The single rule embedded in the cellular automata characterizes the cell as rock if the neighborhood value is greater
    # than or equal to T and as floor if otherwise; T equals 5 in this paper

    rows, cols = grid.shape
    new_grid = np.zeros((rows, cols))

    for row_index in range(rows):
        for col_index in range(cols):
            rock_count = count_bordering_rocks(grid, row_index, col_index)
            
            if rock_count >= rock_threshold:
                new_grid[row_index][col_index] = ROCK
            else:
                new_grid[row_index][col_index] = FLOOR

    return new_grid


def count_bordering_rocks(grid, x, y):
    """Funkce vrací počet kamenu kolem prvku (x,y)."""
    rock_count = 0

    for row in range(-1, 2):
        for col in range(-1, 2):
            neighbour_x = x + row
            neighbour_y = y + col
            if not (neighbour_x == 0 and neighbour_y == 0): # nepocitam prvek (x,y)

                if neighbour_x < 0 or neighbour_y < 0 or neighbour_x >= len(grid) or neighbour_y >= len(grid[0]): # pokud je prvek mimo grid
                    rock_count += 1
                elif grid[neighbour_x][neighbour_y]: # pokud je prvek ROCK (1)
                    rock_count += 1

    return rock_count


def make_svg_from_map(map):
    # Define the size of each cell in the map
    CELL_SIZE = 20

    filepath = './static/svg/map.svg'

    # Create a Drawing object and specify the file path
    dwg = svgwrite.Drawing(filepath)

    # Loop through the rows of the map
    for y, row in enumerate(map):
        # Loop through the columns of the map
        for x, cell in enumerate(row):
            # If the cell is non-zero, draw a rectangle
            if cell == FLOOR:
                dwg.add(dwg.rect((x*CELL_SIZE, y*CELL_SIZE), (CELL_SIZE, CELL_SIZE), fill='white', stroke='black', stroke_width=1))
            else:
                dwg.add(dwg.rect((x*CELL_SIZE, y*CELL_SIZE), (CELL_SIZE, CELL_SIZE), fill='black'))

    # Save the SVG drawing to a file
    dwg.save()

"""
g = generate_grid(10, 10, 0.4)
print(type(g))
print("--------------------")
g2 = do_simulation_step(g, rock_threshold=5)
print(type(g2))


map = generate_map(20, 20, floor_probability=.5, number_of_iterations=4, rock_threshold=5)
#print(map)  
make_svg_from_map(map)
"""
