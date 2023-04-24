import numpy as np
import svgwrite
import queue
import os
from scipy.spatial import KDTree

FLOOR = 0
ROCK = 1
WALL = 2
RNG = np.random     
N = 5   # pocet iteraci CA
T = 5   # počet kamene kolem, aby byl prvek taky kamen

# TODO:
#   dokončit generování chodeb mezi místnostmi
#   začátek/vstup do dungeonu
#   vkládání nepřátel, kořisti


class CACave:
    def __init__(self, rows, cols, seed, floor_probability, number_of_iterations, rock_threshold) -> None:
        self._rows = rows
        self._cols = cols
        self._map = []
        self._seed = seed
        self._floor_probability = floor_probability
        self._number_of_iterations = number_of_iterations
        self._rock_threshold = rock_threshold
        #self.num = 0

    def generate_map(self):
        RNG.seed(self._seed)
        # 123 pro 50x50

        self._map = self._generate_grid()

        for _ in range(self._number_of_iterations):
            self._do_simulation_step()
            #self.make_svg_from_map()
            #self._num += 1

        # ohranicim celou mapu kamenem
        self._map[0,:] = ROCK
        self._map[-1,:] = ROCK
        self._map[:,0] = ROCK
        self._map[:,-1] = ROCK

        self._process_map()
        
        return self._map


    def make_svg_from_map(self):
        """Vytvoří a uloží z mapy svg soubor."""
        # Define the size of each cell in the map
        CELL_SIZE = 10

        save_path = './static/svg/'

        #file_name = "map_{}.svg".format(self._num)
        file_name = "map_oop.svg"

        # Combine the path and filename to create the full file path
        file_path = os.path.join(save_path, file_name)

        # Create a Drawing object and specify the file path
        dwg = svgwrite.Drawing(file_path)

        # Loop through the rows of the map
        for y, row in enumerate(self._map):
            # Loop through the columns of the map
            for x, cell in enumerate(row):
                # If the cell is non-zero, draw a rectangle
                if cell == FLOOR:
                    dwg.add(dwg.rect((x*CELL_SIZE, y*CELL_SIZE), (CELL_SIZE, CELL_SIZE), fill='white', stroke='black', stroke_width=1))
                elif cell == 3:
                    dwg.add(dwg.rect((x*CELL_SIZE, y*CELL_SIZE), (CELL_SIZE, CELL_SIZE), fill='red'))
                else:
                    dwg.add(dwg.rect((x*CELL_SIZE, y*CELL_SIZE), (CELL_SIZE, CELL_SIZE), fill='black'))

        # Save the SVG drawing to a file
        dwg.save()

    def _generate_grid(self):
        grid = self._generate_row()

        for _ in range(self._rows - 1):
            grid = np.vstack((grid, self._generate_row()))

        return grid
    

    def _generate_row(self):
        row = RNG.choice([FLOOR, ROCK], self._cols, p=[self._floor_probability, 1 - self._floor_probability])
    
        return row
    

    def _do_simulation_step(self):
        new_grid = np.zeros((self._rows, self._cols))

        for row_index in range(self._rows):
            for col_index in range(self._cols):
                rock_count = self._count_bordering_rocks(row_index, col_index)  
                if rock_count >= self._rock_threshold:
                    new_grid[row_index][col_index] = ROCK
                else:
                    new_grid[row_index][col_index] = FLOOR

        self._map = new_grid


    def _count_bordering_rocks(self, x, y):
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
        return x >= 0 and y >= 0 and x < self._rows and y < self._cols
    

    def _process_map(self, rock_threshold_size=10, floor_threshold_size=10):
        rock_regions = self._get_regions(ROCK)
        remaining_caves = []

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
                remaining_caves.append(Cave(floor_region, self._map))      

        remaining_caves.sort(reverse=True, key=Cave.get_cave_size)

        remaining_caves[0].main_cave = True 
        remaining_caves[0].accessible_from_main_cave = True

        self._connect_close_caves(remaining_caves)


    def _get_regions(self, cell_type):
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
    

    def _get_cells_region(self, start_x, start_y):
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
    

    def _connect_close_caves(self, all_caves, force_access_from_main=False):

        accessible_caves_from_main = []
        not_accessible_caves_from_main = []
        
        if force_access_from_main:
            for cave in all_caves:
                if cave.accessible_from_main_cave:
                    accessible_caves_from_main.append(cave)
                else:
                    not_accessible_caves_from_main.append(cave)
        else:
            accessible_caves_from_main = all_caves
            not_accessible_caves_from_main = all_caves

        possible_connection = False

        for cave in accessible_caves_from_main:
            if not force_access_from_main:
                possible_connection = False
                if len(cave.connected_caves) > 0:
                    continue

            for other_cave in not_accessible_caves_from_main:
                if cave == other_cave or cave.is_connected(other_cave):
                    continue

                if not possible_connection:
                    closest_pair = self._find_closest_pair(cave.edge_cells, other_cave.edge_cells)
                    coord_a, coord_b = closest_pair
                    possible_connection = True
                    best_cave = cave
                    best_other_cave = other_cave
                

            if possible_connection and not force_access_from_main:
                self._create_passage(best_cave, best_other_cave, coord_a, coord_b)

        if possible_connection and force_access_from_main:
            self._create_passage(best_cave, best_other_cave, coord_a, coord_b)
            self._connect_close_caves(all_caves, True)

        if not force_access_from_main:
            self._connect_close_caves(all_caves, True)        

        """
        for pair in closest_pairs:
            coord_a, coord_b = pair
            x, y = coord_a
            i, j = coord_b
            self._map[x][y] = 3
            self._map[i][j] = 3
            #line_coord = self.get_line_coordinates(coord_a, coord_b)
            #for coord in line_coord:
            #    self._draw_circle(coord, 2)
        """

    def _find_closest_pair(self, region_a, region_b):
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

        return closest_pair


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




class Cave:
    def __init__(self, cavecells, map) -> None:
        self.cells = cavecells
        self.cave_size = len(cavecells)
        self.connected_caves = []
        self.edge_cells = []
        self.main_cave = False
        self.accessible_from_main_cave = False

        for cell in self.cells:
            cell_x, cell_y = cell
            for row in range(-1, 2):
                for col in range(-1, 2):
                    neighbour_x = cell_x + row
                    neighbour_y = cell_y + col
                    if neighbour_x == cell_x or neighbour_y == cell_y:
                        if map[neighbour_x, neighbour_y] == ROCK:
                            self.edge_cells.append(cell)

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



        

ca = CACave(50, 50, 123, .5, 4, 5)
map = ca.generate_map()
ca.make_svg_from_map()