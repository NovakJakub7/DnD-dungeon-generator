import numpy as np
import svgwrite
import queue
import os
import math
from scipy.spatial import KDTree
from numbers import Number

FLOOR: int = 0
ROCK: int = 1
RNG = np.random     
N: int = 5   # pocet iteraci CA
T: int = 5   # počet kamene kolem, aby byl prvek taky kamen

# TODO:
#   vkládání nepřátel, kořisti


class CACave:
    def __init__(self, rows: int, cols: int, seed: int, floor_probability: Number, number_of_iterations: int, rock_threshold: int) -> None:
        self._rows = rows
        self._cols = cols
        self._map = []
        self._seed = seed
        self._floor_probability = floor_probability
        self._number_of_iterations = number_of_iterations
        self._rock_threshold = rock_threshold
        self._caves = []

    def generate_map(self):
        RNG.seed(self._seed)
        # 123 pro 50x50

        self._map = self._generate_grid()

        for _ in range(self._number_of_iterations):
            self._do_simulation_step()

        # ohranicim celou mapu kamenem
        self._map[0,:] = ROCK
        self._map[-1,:] = ROCK
        self._map[:,0] = ROCK
        self._map[:,-1] = ROCK

        self._process_map()
        
        return self._map


    def make_svg_from_map(self, cell_size, save_path, file_name) -> None:
        """ Makes svg image from map and saves it to path.
        """
        # Define the size of each cell in the map
        CELL_SIZE = cell_size

        #save_path = '../static/svg/'
        #file_name = "map_ca.svg"

        # Combine the path and filename to create the full file path
        file_path = os.path.join(save_path, file_name)

        canvas_width = '{}px'.format(CELL_SIZE * self._cols)
        canvas_height = '{}px'.format(CELL_SIZE * self._rows)

        # Create a Drawing object and specify the file path
        dwg = svgwrite.Drawing(file_path, profile='full', size=(canvas_width, canvas_height))

        for x, row in enumerate(self._map):
            for y, cell in enumerate(row):
                if cell == FLOOR:
                    group = dwg.add(dwg.g())
                    group.add(dwg.rect((y*CELL_SIZE, x*CELL_SIZE), (CELL_SIZE, CELL_SIZE), fill='white', stroke='black', stroke_width=1))
                    for cave in self._caves:
                        if (x, y) in cave.cells and (x == cave.id_cell_x and y == cave.id_cell_y):
                            cave_index = self._caves.index(cave)
                            cave_id = group.add(dwg.text(str(cave_index), insert=(y * CELL_SIZE + CELL_SIZE / 2, x * CELL_SIZE + CELL_SIZE / 2), text_anchor='middle', alignment_baseline="middle", font_size='15', fill='black'))
                            #print(cave_index)
                   #dwg.add(dwg.rect((x*CELL_SIZE, y*CELL_SIZE), (CELL_SIZE, CELL_SIZE), fill='white', stroke='black', stroke_width=1))
                elif cell == 3:
                    dwg.add(dwg.rect((y*CELL_SIZE, x*CELL_SIZE), (CELL_SIZE, CELL_SIZE), fill='red'))
                else:
                    dwg.add(dwg.rect((y*CELL_SIZE, x*CELL_SIZE), (CELL_SIZE, CELL_SIZE), fill='black'))
        #dwg.viewbox(0, 0, CELL_SIZE * self._cols, CELL_SIZE * self._rows)
        dwg.save()

    def _generate_grid(self):
        """Returns two dimensional grid of FlOOR and ROCK cells.
        """
        grid = self._generate_row()

        for _ in range(self._rows - 1):
            grid = np.vstack((grid, self._generate_row()))

        return grid
    

    def _generate_row(self):
        """Return an array of FLOOR and ROCK cells based on floor_probability.
        """

        row = RNG.choice([FLOOR, ROCK], self._cols, p=[self._floor_probability, 1 - self._floor_probability])
    
        return row
    

    def _do_simulation_step(self) -> None:
        """Create new map grid based on the number of bordering rock cells for each map cell.
        """
        new_grid = np.zeros((self._rows, self._cols))

        for row_index in range(self._rows):
            for col_index in range(self._cols):
                rock_count = self._count_bordering_rocks(row_index, col_index)  
                if rock_count >= self._rock_threshold:
                    new_grid[row_index][col_index] = ROCK
                else:
                    new_grid[row_index][col_index] = FLOOR

        self._map = new_grid


    def _count_bordering_rocks(self, x: int, y: int) -> int:
        """Return number of bordering rock cells of a cell on (x,y) coordinates.

        Args:
            x (int): X coordinate
            y (int): Y coordinate
        """
        rock_count = 0
    
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                neighbour_x = x + dx
                neighbour_y = y + dy
                if not (neighbour_x == 0 and neighbour_y == 0): # nepocitam prvek (x,y)
                    if not self._is_in_map(neighbour_x, neighbour_y): # pokud je prvek mimo grid
                        rock_count += 1
                    elif self._map[neighbour_x][neighbour_y]: # pokud je prvek ROCK (1)
                        rock_count += 1
        
        return rock_count
    

    def _is_in_map(self, x, y):
        """Return True if (x,y) cell is in map, otherwise return False.

        Args:
            x (int): X coordinate of the cell
            y (int): Y coordinate of the cell
        """
        return x >= 0 and y >= 0 and x < self._rows and y < self._cols
    

    def _process_map(self, rock_threshold_size:int = 10, floor_threshold_size:int = 10):
        """Process the map by filling small unwanted regions and connecting remaining caves.

        Args:
            rock_threshold_size (int, optional): Size of a rock region to be filled. Defaults to 10.
            floor_threshold_size (int, optional): Size of a floor region to be filled. Defaults to 10.
        """
        rock_regions = self._get_regions(ROCK)

        for rock_region in rock_regions:
            if len(rock_region) < rock_threshold_size:
                for cell in rock_region:
                    cell_x, cell_y = cell
                    self._map[cell_x, cell_y] = FLOOR
        
        floor_regions = self._get_regions(FLOOR)

        for floor_region in floor_regions:
            if len(floor_region) < floor_threshold_size:
                for cell in floor_region:
                    cell_x, cell_y = cell
                    self._map[cell_x, cell_y] = ROCK
            else:
                self._caves.append(Cave(floor_region))      

        self._caves.sort(reverse=True, key=Cave.get_cave_size)

        self._caves[0].main_cave = True 
        self._caves[0].accessible_from_main_cave = True

        self._connect_close_caves()

        self._place_items()


    def _get_regions(self, cell_type: int) -> list:
        """Return all regions of cells of cell_type

        Args:
            cell_type (int): Type of cell for which regions are searched.
        """
        regions = []
        map_flags = np.zeros((self._rows, self._cols))
        for x in range(self._rows):
            for y in range(self._cols):
                if map_flags[x, y] == 0 and self._map[x, y] == cell_type:
                    new_region = self._get_cells_region(x, y)
                    regions.append(new_region)

                    for cell in new_region:
                        cell_x, cell_y = cell
                        map_flags[cell_x, cell_y] = 1

        return regions
    

    def _get_cells_region(self, start_x: int, start_y: int) -> list:
        """Return a list of cells of the same type next to each other called region. Starting at the (start_x, start_y) coordinates.

        Args:
            start_x (int): Starting X coordinate.
            start_y (int): Starting Y coordinate.
        """
        cells = []
        map_flags = np.zeros((self._rows, self._cols))
        cell_type = self._map[start_x, start_y]

        q = queue.Queue()
        q.put((start_x, start_y))

        while not q.empty():
            cell_x, cell_y = q.get()  
            if self._is_in_map(cell_x, cell_y):
                if map_flags[cell_x, cell_y] == 0 and self._map[cell_x, cell_y] == cell_type:
                    cells.append((cell_x, cell_y))
                    map_flags[cell_x, cell_y] = 1
                    q.put((cell_x+1, cell_y))
                    q.put((cell_x-1, cell_y))
                    q.put((cell_x, cell_y+1))
                    q.put((cell_x, cell_y-1))

        return cells
    

    def _connect_close_caves(self, force_access_from_main: bool = False) -> None:
        """Connect the caves that are closest to each other.
        """
        accessible_caves_from_main = []
        not_accessible_caves_from_main = []
        
        if force_access_from_main:
            for cave in self._caves:
                if cave.accessible_from_main_cave:
                    accessible_caves_from_main.append(cave)
                else:
                    not_accessible_caves_from_main.append(cave)
        else:
            accessible_caves_from_main = self._caves
            not_accessible_caves_from_main = self._caves

        best_distance = 0
        possible_connection = False

        for cave in accessible_caves_from_main:
            if not force_access_from_main:
                possible_connection = False
                if len(cave.connected_caves) > 0:
                    continue

            for other_cave in not_accessible_caves_from_main:
                if cave == other_cave or cave.is_connected(other_cave):
                    continue

                closest_pair, min_distance = self._find_closest_pair(cave.cells, other_cave.cells)
                
                if min_distance < best_distance or not possible_connection:
                    best_distance = min_distance
                    coord_a, coord_b = closest_pair
                    possible_connection = True
                    best_cave = cave
                    best_other_cave = other_cave
                
            if possible_connection and not force_access_from_main:
                self._create_passage(best_cave, best_other_cave, coord_a, coord_b)

        if possible_connection and force_access_from_main:
            self._create_passage(best_cave, best_other_cave, coord_a, coord_b)
            self._connect_close_caves(True)

        if not force_access_from_main:
            self._connect_close_caves(True)        


    def _find_closest_pair(self, region_a, region_b) -> tuple:
        """Find coordinates and distance of closest cells from two regions using KDTree.
        """
       # Convert the cells in each region to points in the 2D space
        points_a = [(x, y) for x, y in region_a]
        points_b = [(x, y) for x, y in region_b]

        # Build a k-d tree for the points in region A
        tree = KDTree(points_a)

        # Initialize the closest pair of cells and the current minimum distance
        closest_pair = None
        min_distance = float('inf')

        # Search for the closest pair of cells
        for point in points_b:
            # Query the k-d tree to find the nearest neighbor(s) within the current distance threshold
            dist, idx = tree.query(point, k=2, distance_upper_bound=min_distance)
            
            # Check if the closest pair found so far is closer than the current pair
            if dist[0] < min_distance:
                closest_pair = (point, points_a[idx[0]])
                min_distance = dist[0]

            if dist[1] < min_distance:
                closest_pair = (point, points_a[idx[1]])
                min_distance = dist[1]

        return (closest_pair, min_distance)


    def _create_passage(self, cave, other_cave, cell, other_cell):
        cave.connect_caves(other_cave)
        line = self._get_line_coordinates(cell, other_cell)
        for cord in line:
            self._draw_circle(cord, 2)


    def _draw_circle(self, cord, r):
        cx, cy = cord
        for x in range(-r, r):
            for y in range(-r, r):
                if x*x + y*y <= r*r:
                    draw_x = cx + x
                    draw_y = cy + y
                    if self._is_in_map(draw_x, draw_y):
                        self._map[draw_x, draw_y] = FLOOR


    def _get_line_coordinates(self, start, end):
        """
        Function returns a list of tuples representing the coordinates of all the points on a line
        between start coordinates and end coordinates.
        """
        x1, y1 = start
        x2, y2 = end

        coordinates = []
        dx = x2 - x1
        dy = y2 - y1
        steps = max(abs(dx), abs(dy))
        x_inc = dx / steps
        y_inc = dy / steps
        x = x1
        y = y1
        for _ in range(steps):
            coordinates.append((round(x), round(y)))
            x += x_inc
            y += y_inc
        coordinates.append((round(x2), round(y2)))
        return coordinates


    def _place_items(self):
        """Function creates the placement of loot and/or enemies inside the map."""
        number_of_caves = len(self._caves)
        large_rooms_end_index = math.floor(number_of_caves * 0.5)
        smallest_rooms_start_index = number_of_caves - math.floor(number_of_caves * 0.2)

        #print(number_of_caves, large_rooms_end_index, smallest_rooms_start_index)
        #print(self._caves[1].cells)
        #print(self._caves[1].id_cell_x, self._caves[1].id_cell_y)


class Cave:
    def __init__(self, cavecells: list) -> None:
        self.cells = cavecells
        self.cave_size = len(cavecells)
        self.connected_caves = []
        self.main_cave = False
        self.accessible_from_main_cave = False
        self.row_min = min(cavecells)[1]
        self.col_min = min(cavecells)[0]
        self.id_cell_x, self.id_cell_y = sorted(self.cells, key=lambda a: a[0])[self.cave_size // 2]


    def get_cave_size(self):
        return self.cave_size
    
    def make_accessible_from_main(self):
        if not self.accessible_from_main_cave:
            self.accessible_from_main_cave = True
            for connected_cave in self.connected_caves:
                connected_cave.make_accessible_from_main()

    def connect_caves(self, other_cave):
        """Connects two caves."""

        if self.accessible_from_main_cave:
            other_cave.make_accessible_from_main()
        elif other_cave.accessible_from_main_cave:
            self.make_accessible_from_main()

        self.connected_caves.append(other_cave)
        other_cave.connected_caves.append(self)

    def is_connected(self, other_cave):
        """Checks if other cave is connected."""

        return other_cave in self.connected_caves


if __name__ == "__main__":
    ca = CACave(50, 50, 123, .5, 4, 5)
    map = ca.generate_map()
    ca.make_svg_from_map()

